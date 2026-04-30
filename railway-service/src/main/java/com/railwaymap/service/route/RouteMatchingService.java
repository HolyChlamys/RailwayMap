package com.railwaymap.service.route;

import com.railwaymap.common.entity.*;
import com.railwaymap.data.mapper.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.*;

/**
 * 三阶段车次经行段匹配引擎
 *
 * 阶段一 (离线): 拓扑预计算 → railway_topology 表
 * 阶段二 (在线): 候选筛选 (2km) → BFS 拓扑图搜索 → 降级距离匹配
 * 阶段三 (离线): 预计算缓存 → train_segment_mapping 表
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class RouteMatchingService {

    private final StationMapper stationMapper;
    private final RailwaySegmentMapper segmentMapper;
    private final TrainSegmentMappingMapper mappingMapper;
    private final RailwayTopologyMapper topologyMapper;
    private final TrainRouteMapper routeMapper;
    private final TrainStopMapper stopMapper;
    private final TrainFareMapper fareMapper;

    private static final double CANDIDATE_RADIUS_M = 2000.0;
    private static final double FALLBACK_RADIUS_M = 500.0;
    private static final double DANGLE_TOLERANCE_M = 50.0;

    /**
     * 阶段三: 预计算所有有效车次的经行段映射
     */
    public void precomputeAllMappings() {
        List<TrainRoute> routes = routeMapper.selectList(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<TrainRoute>()
                        .eq(TrainRoute::getIsValid, true));
        int total = routes.size();
        int done = 0;

        for (TrainRoute route : routes) {
            List<TrainStop> stops = stopMapper.selectList(
                    new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<TrainStop>()
                            .eq(TrainStop::getTrainNo, route.getTrainNo())
                            .orderByAsc(TrainStop::getSeq));

            for (int i = 0; i < stops.size() - 1; i++) {
                TrainStop from = stops.get(i);
                TrainStop to = stops.get(i + 1);

                // 检查是否已有缓存
                List<TrainSegmentMapping> existing = mappingMapper.selectList(
                        new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<TrainSegmentMapping>()
                                .eq(TrainSegmentMapping::getTrainNo, route.getTrainNo())
                                .eq(TrainSegmentMapping::getFromStation, from.getStationName())
                                .eq(TrainSegmentMapping::getToStation, to.getStationName()));

                if (existing.isEmpty()) {
                    List<TrainSegmentMapping> result = matchSegment(from, to, route.getTrainNo());
                    if (!result.isEmpty()) {
                        for (TrainSegmentMapping m : result) {
                            mappingMapper.insert(m);
                        }
                    }
                }
            }
            done++;
            if (done % 100 == 0) {
                log.info("[PRECOMPUTE] {}/{} 车次完成", done, total);
            }
        }
        log.info("[PRECOMPUTE] 全部完成: {} 车次", total);
    }

    /**
     * 阶段二: 匹配相邻两站之间的铁路线段
     */
    public List<TrainSegmentMapping> matchSegment(TrainStop from, TrainStop to, String trainNo) {
        // Step 1: 获取车站坐标
        Station stationA = stationMapper.selectById(from.getStationId());
        Station stationB = stationMapper.selectById(to.getStationId());

        if (stationA == null || stationB == null) {
            return List.of();
        }

        List<RailwaySegment> aCandidates = findNearbySegments(stationA, CANDIDATE_RADIUS_M);
        List<RailwaySegment> bCandidates = findNearbySegments(stationB, CANDIDATE_RADIUS_M);

        if (aCandidates.isEmpty() || bCandidates.isEmpty()) {
            return List.of();
        }

        // Step 2-5: BFS 从 aCandidates → bCandidates
        List<TrainSegmentMapping> result = bfsMatch(aCandidates, bCandidates, trainNo,
                from.getStationName(), to.getStationName(), from.getSeq());

        // Step 6: 降级距离匹配
        if (result.isEmpty()) {
            result = fallbackDistanceMatch(stationA, stationB, trainNo,
                    from.getStationName(), to.getStationName(), from.getSeq());
        }

        return result;
    }

    private List<RailwaySegment> findNearbySegments(Station station, double radiusMeters) {
        // 使用 PostGIS ST_DWithin 查询
        return segmentMapper.selectList(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<RailwaySegment>()
                        .last("AND ST_DWithin(geom::geography, ST_SetSRID(ST_MakePoint("
                                + station.getGeomWkt().replace("POINT(", "").replace(")", "")
                                + "), 4326)::geography, " + radiusMeters + ")")
                        .last("LIMIT 10"));
    }

    private List<TrainSegmentMapping> bfsMatch(
            List<RailwaySegment> starts, List<RailwaySegment> targets,
            String trainNo, String fromStation, String toStation, int fromSeq) {

        Set<Long> targetIds = new HashSet<>();
        for (RailwaySegment t : targets) {
            targetIds.add(t.getId());
        }

        // BFS
        Queue<Long> queue = new LinkedList<>();
        Map<Long, Long> parent = new HashMap<>();
        Map<Long, RailwaySegment> segMap = new HashMap<>();
        Set<Long> visited = new HashSet<>();

        for (RailwaySegment s : starts) {
            queue.add(s.getId());
            visited.add(s.getId());
            segMap.put(s.getId(), s);
        }

        Long foundTarget = null;
        while (!queue.isEmpty() && foundTarget == null) {
            Long current = queue.poll();
            // 查找拓扑邻居
            List<RailwayTopology> neighbors = topologyMapper.selectList(
                    new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<RailwayTopology>()
                            .eq(RailwayTopology::getSegA, current)
                            .or().eq(RailwayTopology::getSegB, current)
                            .eq(RailwayTopology::getIsConnected, true));

            for (RailwayTopology topo : neighbors) {
                Long neighbor = topo.getSegA().equals(current) ? topo.getSegB() : topo.getSegA();
                if (!visited.contains(neighbor)) {
                    visited.add(neighbor);
                    parent.put(neighbor, current);
                    queue.add(neighbor);

                    // 加载 segment
                    if (!segMap.containsKey(neighbor)) {
                        RailwaySegment seg = segmentMapper.selectById(neighbor);
                        if (seg != null) segMap.put(neighbor, seg);
                    }

                    if (targetIds.contains(neighbor)) {
                        foundTarget = neighbor;
                        break;
                    }
                }
            }
        }

        if (foundTarget == null) return List.of();

        // 回溯路径
        List<TrainSegmentMapping> result = new ArrayList<>();
        Long current = foundTarget;
        int order = 0;
        while (current != null) {
            TrainSegmentMapping m = new TrainSegmentMapping();
            m.setTrainNo(trainNo);
            m.setFromStation(fromStation);
            m.setToStation(toStation);
            m.setSegId(current);
            m.setSegOrder(order++);
            m.setConfidence(1.0);
            m.setMatchMethod("topology");
            result.add(0, m);

            current = parent.get(current);
            if (current != null && current.equals(starts.get(0).getId())) break;
        }
        return result;
    }

    private List<TrainSegmentMapping> fallbackDistanceMatch(
            Station a, Station b, String trainNo,
            String fromStation, String toStation, int fromSeq) {

        // 用 FALLBACK_RADIUS_M 直接匹配
        List<RailwaySegment> segments = segmentMapper.selectList(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<RailwaySegment>()
                        .last("AND ST_DWithin(geom::geography, ST_SetSRID(ST_MakeLine("
                                + "ST_SetSRID(ST_MakePoint("
                                + a.getGeomWkt().replace("POINT(", "").replace(")", "")
                                + "), 4326), "
                                + "ST_SetSRID(ST_MakePoint("
                                + b.getGeomWkt().replace("POINT(", "").replace(")", "")
                                + "), 4326)"
                                + "), 4326)::geography, " + FALLBACK_RADIUS_M + ")")
                        .last("LIMIT 5"));

        if (segments.isEmpty()) return List.of();

        List<TrainSegmentMapping> result = new ArrayList<>();
        for (int i = 0; i < segments.size(); i++) {
            TrainSegmentMapping m = new TrainSegmentMapping();
            m.setTrainNo(trainNo);
            m.setFromStation(fromStation);
            m.setToStation(toStation);
            m.setSegId(segments.get(i).getId());
            m.setSegOrder(i);
            m.setConfidence(0.5);
            m.setMatchMethod("distance");
            result.add(m);
        }
        return result;
    }
}
