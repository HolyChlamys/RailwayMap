package com.railwaymap.service.transfer;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.railwaymap.common.dto.TrainConnection;
import com.railwaymap.common.entity.TrainRoute;
import com.railwaymap.common.entity.TrainStop;
import com.railwaymap.data.mapper.TrainRouteMapper;
import com.railwaymap.data.mapper.TrainStopMapper;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.time.LocalTime;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.locks.ReentrantReadWriteLock;

/**
 * Builds and caches a connection index for DFS-based transfer search.
 *
 * Index: Map&lt;fromStation, List&lt;TrainConnection&gt;&gt;
 * Each TrainConnection represents a rideable segment between two stations
 * on the same train. For a train with N stops, N*(N-1)/2 connections
 * are generated covering all possible board→alight pairs.
 *
 * Time model: cumulative minutes from the train's departure day 00:00.
 * Cross-midnight trains accumulate minutes past 1440 (24h).
 */
@Component
@RequiredArgsConstructor
public class TransferGraphBuilder {

    private static final Logger log = LoggerFactory.getLogger(TransferGraphBuilder.class);

    private final TrainRouteMapper routeMapper;
    private final TrainStopMapper stopMapper;

    // Cached connection index: fromStation → list of outbound connections
    private volatile Map<String, List<TrainConnection>> connectionIndex = Map.of();
    private volatile int connectionCount = 0;
    private final ReentrantReadWriteLock lock = new ReentrantReadWriteLock();

    /**
     * Get the cached connection index, building on first access.
     */
    public Map<String, List<TrainConnection>> getConnectionIndex() {
        lock.readLock().lock();
        try {
            if (!connectionIndex.isEmpty()) return connectionIndex;
        } finally {
            lock.readLock().unlock();
        }

        lock.writeLock().lock();
        try {
            if (connectionIndex.isEmpty()) rebuild();
            return connectionIndex;
        } finally {
            lock.writeLock().unlock();
        }
    }

    public int getConnectionCount() { return connectionCount; }

    /**
     * Scheduled rebuild every 30 minutes.
     */
    @Scheduled(fixedRate = 30 * 60 * 1000, initialDelay = 5 * 60 * 1000)
    public void refresh() {
        long start = System.currentTimeMillis();
        rebuild();
        log.info("[CONNECTION_INDEX] 定时重建完成: {} 连接, 耗时 {}ms",
                connectionCount, System.currentTimeMillis() - start);
    }

    private void rebuild() {
        long start = System.currentTimeMillis();
        Map<String, List<TrainConnection>> index = new ConcurrentHashMap<>();
        int total = 0;

        List<TrainRoute> routes = routeMapper.selectList(
                new LambdaQueryWrapper<TrainRoute>()
                        .eq(TrainRoute::getIsValid, true));

        for (TrainRoute route : routes) {
            List<TrainStop> stops = stopMapper.selectList(
                    new LambdaQueryWrapper<TrainStop>()
                            .eq(TrainStop::getTrainNo, route.getTrainNo())
                            .orderByAsc(TrainStop::getSeq));

            if (stops.size() < 2) continue;

            // Convert times to cumulative minutes, detecting cross-midnight
            int[] cumMin = new int[stops.size()];
            int dayOffset = 0;
            int prevMin = -1;

            for (int i = 0; i < stops.size(); i++) {
                int min = localTimeToMin(stops.get(i).getDepartTime());
                if (min < 0) min = localTimeToMin(stops.get(i).getArriveTime());
                if (min < 0) { cumMin[i] = -1; continue; }

                if (prevMin >= 0 && min < prevMin) dayOffset++;
                cumMin[i] = dayOffset * 1440 + min;
                if (min >= 0) prevMin = min;
            }

            // Also compute arrive cumulative minutes (they may differ from depart)
            int[] arrCumMin = new int[stops.size()];
            for (int i = 0; i < stops.size(); i++) {
                LocalTime at = stops.get(i).getArriveTime();
                if (at != null) {
                    int min = at.getHour() * 60 + at.getMinute();
                    // Determine day offset relative to the first stop's depart day
                    int aday = cumMin[i] / 1440;
                    if (min < (cumMin[i] % 1440) && min < 720) aday++;
                    arrCumMin[i] = aday * 1440 + min;
                } else {
                    arrCumMin[i] = cumMin[i]; // fallback to depart time
                }
            }

            // Generate all (i, j) pairs where i < j and both have valid depart/arrive
            String trainType = route.getTrainType() != null ? route.getTrainType() : route.getTrainNo().substring(0, 1);

            for (int i = 0; i < stops.size(); i++) {
                if (cumMin[i] < 0) continue;
                for (int j = i + 1; j < stops.size(); j++) {
                    if (arrCumMin[j] < cumMin[i]) continue; // skip invalid

                    // Cap at 48h — longer durations indicate data errors in cross-midnight detection
                    int dur = arrCumMin[j] - cumMin[i];
                    if (dur > 48 * 60) continue;

                    TrainConnection conn = new TrainConnection();
                    conn.setTrainNo(route.getTrainNo());
                    conn.setTrainType(trainType);
                    conn.setFromStation(stops.get(i).getStationName());
                    conn.setToStation(stops.get(j).getStationName());
                    conn.setFromSeq(stops.get(i).getSeq());
                    conn.setToSeq(stops.get(j).getSeq());
                    conn.setDepartMin(cumMin[i]);
                    conn.setArriveMin(arrCumMin[j]);
                    conn.setDurationMin(dur);

                    index.computeIfAbsent(stops.get(i).getStationName(),
                            k -> Collections.synchronizedList(new ArrayList<>())).add(conn);
                    total++;
                }
            }
        }

        // Freeze lists for read safety
        Map<String, List<TrainConnection>> frozen = new ConcurrentHashMap<>();
        for (var entry : index.entrySet()) {
            frozen.put(entry.getKey(), List.copyOf(entry.getValue()));
        }

        this.connectionIndex = frozen;
        this.connectionCount = total;

        log.info("[CONNECTION_INDEX] 构建完成: {} 站 × {} 连接, 耗时 {}ms",
                frozen.size(), total, System.currentTimeMillis() - start);
    }

    private static int localTimeToMin(LocalTime t) {
        if (t == null) return -1;
        return t.getHour() * 60 + t.getMinute();
    }
}
