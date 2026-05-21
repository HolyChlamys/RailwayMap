package com.railwaymap.service.transfer;

import com.railwaymap.common.dto.IsochroneRequest;
import com.railwaymap.common.dto.IsochroneResponse;
import com.railwaymap.common.dto.IsochroneResponse.ReachableStation;
import com.railwaymap.common.dto.StationSearchResult;
import com.railwaymap.common.dto.TrainConnection;
import com.railwaymap.data.mapper.StationMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.stream.Collectors;

/**
 * Isochrone service — "from station X, where can I reach within N minutes?"
 *
 * Uses the pre-built connection index from {@link TransferGraphBuilder}
 * and performs a time-constrained BFS. No separate index or RAPTOR engine needed.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class IsochroneService {

    private final TransferGraphBuilder graphBuilder;
    private final StationMapper stationMapper;

    private static final int MIN_TRANSFER_MINUTES = 20;

    /**
     * BFS state: current station, cumulative arrival time, path so far.
     */
    private static class BfsState {
        final String station;
        final int arriveMin;
        final int transfers;
        final List<TrainConnection> path;

        BfsState(String station, int arriveMin, int transfers, List<TrainConnection> path) {
            this.station = station;
            this.arriveMin = arriveMin;
            this.transfers = transfers;
            this.path = path;
        }
    }

    public IsochroneResponse compute(IsochroneRequest req) {
        long startNs = System.nanoTime();

        Map<String, List<TrainConnection>> index = graphBuilder.getConnectionIndex();
        String startStation = req.getStation();

        if (!index.containsKey(startStation)) {
            IsochroneResponse resp = new IsochroneResponse();
            resp.setStations(List.of());
            resp.setTotalCount(0);
            resp.setComputeMs(0);
            return resp;
        }

        int startMin = req.getDepartMin();
        int maxMin = req.getMaxMinutes();
        int maxTransfers = req.getMaxTransfers() > 0 ? req.getMaxTransfers() : Integer.MAX_VALUE;

        // Load station metadata for direction grouping
        Map<String, StationInfo> stationMap = loadStationMap(req.isGroupByDirection());

        // Get origin coordinates
        double centerLon = 0, centerLat = 0;
        StationInfo origin = stationMap.get(startStation);
        if (origin != null) {
            centerLon = origin.lon();
            centerLat = origin.lat();
        }

        // ---- BFS with earliest-arrival pruning ----
        Map<String, ReachableStation> best = new LinkedHashMap<>();
        Queue<BfsState> queue = new ArrayDeque<>();

        // Initial: from start station, we can board any train departing >= startMin
        queue.add(new BfsState(startStation, startMin - MIN_TRANSFER_MINUTES, 0, List.of()));

        int examined = 0;

        while (!queue.isEmpty()) {
            BfsState cur = queue.poll();
            examined++;

            int earliestDepart = cur.arriveMin + MIN_TRANSFER_MINUTES;
            List<TrainConnection> departures = index.getOrDefault(cur.station, List.of());

            for (TrainConnection conn : departures) {
                // Must be able to catch this train
                if (conn.getDepartMin() < earliestDepart) continue;

                // Duration from original start to arrival at destination
                int elapsed = conn.getArriveMin() - startMin;
                if (elapsed > maxMin) continue;

                // Don't exceed max transfers
                int newTransfers = cur.transfers + (cur.path.isEmpty() ? 0 : 1);
                if (newTransfers > maxTransfers) continue;

                // Earliest-arrival pruning: only explore if we found a faster way
                String dest = conn.getToStation();
                ReachableStation existing = best.get(dest);
                if (existing != null && conn.getArriveMin() >= existing.getArriveMin()) continue;

                // Build path
                List<TrainConnection> newPath = new ArrayList<>(cur.path);
                newPath.add(conn);

                // Format sample path
                String samplePath = formatPath(newPath);

                // Direction
                String dir = "";
                StationInfo ds = stationMap.get(dest);
                if (ds != null && origin != null) {
                    dir = direction(centerLon, centerLat, ds.lon(), ds.lat());
                }

                ReachableStation rs = new ReachableStation();
                rs.setStationName(dest);
                rs.setCity(ds != null ? ds.city() : "");
                rs.setArriveMin(conn.getArriveMin());
                rs.setArriveTime(formatTime(conn.getArriveMin()));
                rs.setElapsedMinutes(elapsed);
                rs.setTransfers(newTransfers);
                rs.setSamplePath(samplePath);
                rs.setDirection(dir);
                if (ds != null) {
                    rs.setLon(ds.lon());
                    rs.setLat(ds.lat());
                }

                best.put(dest, rs);

                // Continue exploring from this destination
                if (newTransfers < maxTransfers) {
                    queue.add(new BfsState(dest, conn.getArriveMin(), newTransfers, newPath));
                }
            }
        }

        // Sort by elapsed time
        List<ReachableStation> results = new ArrayList<>(best.values());
        results.sort(Comparator.comparingInt(ReachableStation::getElapsedMinutes));

        // Group by direction
        Map<String, List<ReachableStation>> dirGroups = null;
        if (req.isGroupByDirection()) {
            dirGroups = results.stream()
                    .filter(r -> !r.getDirection().isEmpty())
                    .collect(Collectors.groupingBy(ReachableStation::getDirection,
                            LinkedHashMap::new, Collectors.toList()));
        }

        IsochroneResponse resp = new IsochroneResponse();
        resp.setStations(results);
        resp.setDirectionGroups(dirGroups);
        resp.setTotalCount(results.size());
        resp.setComputeMs((System.nanoTime() - startNs) / 1_000_000);
        resp.setCenterLon(centerLon);
        resp.setCenterLat(centerLat);

        log.info("[ISOCHRONE] {} @ {}min → {} stations (max={}min, transfers≤{}, {}ms)",
                startStation, startMin, results.size(), maxMin, maxTransfers, resp.getComputeMs());

        return resp;
    }

    // Lightweight station info with coordinates for direction grouping
    private record StationInfo(String name, String city, double lon, double lat) {}

    private Map<String, StationInfo> loadStationMap(boolean needCoords) {
        if (!needCoords) return Map.of();
        List<StationSearchResult> all = stationMapper.findAllWithCoords();
        return all.stream().collect(Collectors.toMap(
                StationSearchResult::getName,
                s -> new StationInfo(s.getName(), s.getCity(), s.getLon() != null ? s.getLon() : 0, s.getLat() != null ? s.getLat() : 0),
                (a, b) -> a));
    }

    private static String formatPath(List<TrainConnection> path) {
        if (path.isEmpty()) return "";
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < path.size(); i++) {
            TrainConnection c = path.get(i);
            if (i > 0) sb.append(", ");
            sb.append(c.getTrainNo()).append("(")
                    .append(c.getFromStation()).append("→").append(c.getToStation()).append(")");
        }
        return sb.toString();
    }

    private static String formatTime(int cumulativeMin) {
        int d = cumulativeMin / 1440;
        int h = (cumulativeMin % 1440) / 60;
        int m = cumulativeMin % 60;
        if (d == 0) return String.format("%02d:%02d", h, m);
        return String.format("+%dd %02d:%02d", d, h, m);
    }

    /** Classify a destination relative to origin into 东/南/西/北. */
    static String direction(double fromLon, double fromLat, double toLon, double toLat) {
        double dLon = toLon - fromLon;
        double dLat = toLat - fromLat;
        double angle = Math.atan2(dLon, dLat) * 180.0 / Math.PI; // 0=北, 90=东
        if (angle > -45 && angle <= 45) return "北";
        if (angle > 45 && angle <= 135) return "东";
        if (angle > 135 || angle <= -135) return "南";
        return "西";
    }
}
