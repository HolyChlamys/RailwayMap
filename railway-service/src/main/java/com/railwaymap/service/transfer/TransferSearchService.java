package com.railwaymap.service.transfer;

import com.railwaymap.common.dto.TrainConnection;
import com.railwaymap.common.dto.TransferRequest;
import com.railwaymap.common.dto.TransferResult;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.*;

/**
 * DFS-based transfer search with four-dimensional constraint filtering.
 *
 * Philosophy: enumerate ALL feasible paths satisfying hard constraints,
 * not find the "shortest" path. Users get the full set of options.
 *
 * Constraints: T (time window), N (transfer count range), S (station filter), D (max segment duration)
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class TransferSearchService {

    private final TransferGraphBuilder graphBuilder;
    private final TransferRankingService rankingService;

    private static final int MIN_TRANSFER_MINUTES = 20;

    // ---- DFS state ----
    private static class State {
        final String station;
        final int arriveMin;       // cumulative arrival minute
        final List<TrainConnection> segments;
        final Set<String> visitedTrains;

        State(String station, int arriveMin, List<TrainConnection> segments, Set<String> visitedTrains) {
            this.station = station;
            this.arriveMin = arriveMin;
            this.segments = segments;
            this.visitedTrains = visitedTrains;
        }
    }

    public Map<String, Object> search(TransferRequest req) {
        long startTime = System.currentTimeMillis();

        String from = req.getFrom();
        String to = req.getTo();
        if (from == null || to == null || from.isBlank() || to.isBlank()) {
            return Map.of("results", List.of(), "total_found", 0,
                    "search_time_ms", 0, "error", "出发站或到达站不能为空");
        }

        Map<String, List<TrainConnection>> index = graphBuilder.getConnectionIndex();

        if (!index.containsKey(from)) {
            return Map.of("results", List.of(), "total_found", 0,
                    "search_time_ms", System.currentTimeMillis() - startTime,
                    "error", "出发站不在路网中: " + from);
        }

        // ---- Parse constraints ----
        int nMin = req.getNMin() != null ? req.getNMin() : 0;
        int nMax = req.getMaxTransfers() != null ? req.getMaxTransfers() : 2;
        int dMax = req.getDMax() != null ? req.getDMax() : 0;           // 0 = no limit
        int tStart = req.getTStart() != null ? req.getTStart() : 0;     // default: all day
        int tEnd = req.getTEnd() != null ? req.getTEnd() : 1440;        // default: all day
        int maxResults = req.getMaxResults() != null ? req.getMaxResults() : 20;
        Set<String> allowedStations = req.getAllowedStations() != null
                ? Set.copyOf(req.getAllowedStations()) : null;
        Set<String> blockedStations = req.getBlockedStations() != null
                ? Set.copyOf(req.getBlockedStations()) : null;

        String preference = req.getPreference() != null ? req.getPreference() : "least_time";

        // ---- DFS enumeration ----
        List<TransferResult> results = new ArrayList<>();
        int maxSegments = nMax + 1; // max number of ride segments

        // Stack for DFS
        Deque<State> stack = new ArrayDeque<>();
        // Initial: from station, arriveMin = 0 so first train can depart anytime
        stack.push(new State(from, -MIN_TRANSFER_MINUTES, List.of(), Set.of()));

        int examined = 0;

        while (!stack.isEmpty() && results.size() < maxResults * 3) {
            State s = stack.pop();
            examined++;

            int earliestDepart = s.arriveMin + MIN_TRANSFER_MINUTES;
            List<TrainConnection> departures = index.getOrDefault(s.station, List.of());

            for (TrainConnection conn : departures) {
                // Must depart after arrival + transfer time
                if (conn.getDepartMin() < earliestDepart) continue;

                // Don't reuse the same train
                if (s.visitedTrains.contains(conn.getTrainNo())) continue;

                // ---- Constraint: T (time window) ----
                if (!inTimeWindow(conn.getDepartMin(), conn.getArriveMin(), tStart, tEnd)) continue;

                // ---- Constraint: D (max segment duration) ----
                if (dMax > 0 && conn.getDurationMin() > dMax) continue;

                // Build new segment list
                List<TrainConnection> newSegments = new ArrayList<>(s.segments);
                newSegments.add(conn);

                int transferCount = newSegments.size() - 1;

                // ---- Reached destination? ----
                if (conn.getToStation().equals(to)) {
                    if (transferCount >= nMin && transferCount <= nMax) {
                        results.add(toResult(newSegments));
                    }
                    continue; // don't extend past destination
                }

                // ---- Constraint: S (transfer station filter) ----
                // The alighting station becomes a transfer station
                String transferStation = conn.getToStation();
                if (allowedStations != null && !allowedStations.contains(transferStation)) continue;
                if (blockedStations != null && blockedStations.contains(transferStation)) continue;

                // ---- Depth limit: don't exceed max segments ----
                if (newSegments.size() >= maxSegments) continue;

                // ---- Don't revisit stations (anti-cycle) ----
                // Cheap set copy only when actually extending
                Set<String> newVisited = new HashSet<>(s.visitedTrains);
                newVisited.add(conn.getTrainNo());

                stack.push(new State(conn.getToStation(), conn.getArriveMin(), newSegments, newVisited));
            }
        }

        // ---- Post-process ----
        // Apply soft preference ranking (sort by total time, transfer count, etc.)
        if (!results.isEmpty()) {
            results = rankingService.rank(results, preference);
        }

        // Trim to max results
        if (results.size() > maxResults) {
            results = results.subList(0, maxResults);
        }

        long elapsed = System.currentTimeMillis() - startTime;
        log.info("[TRANSFER] {}→{} N[{},{}] D≤{} T[{}-{}] S+{}/-{} → {} 结果 (examined={}, {}ms)",
                from, to, nMin, nMax, dMax, tStart, tEnd,
                allowedStations != null ? allowedStations.size() : 0,
                blockedStations != null ? blockedStations.size() : 0,
                results.size(), examined, elapsed);

        return Map.of(
                "results", results,
                "total_found", results.size(),
                "search_time_ms", elapsed,
                "connections_indexed", graphBuilder.getConnectionCount()
        );
    }

    /** Check if a connection's clock times fall within the time window. */
    private static boolean inTimeWindow(int departCumMin, int arriveCumMin, int tStart, int tEnd) {
        // No window constraint
        if (tStart == 0 && tEnd >= 1440) return true;

        int depClock = departCumMin % 1440;
        int arrClock = arriveCumMin % 1440;

        // Both depart and arrive must be within the window
        // For single-day window: both clock times in [tStart, tEnd]
        boolean depOk = depClock >= tStart && depClock <= tEnd;
        boolean arrOk = arrClock >= tStart && arrClock <= tEnd;

        // If the segment spans multiple days, the window check is per-day,
        // meaning at least the depart must be ok and we're lenient on arrival
        // for cross-midnight trains (the user explicitly allows overnight).
        if (arriveCumMin - departCumMin >= 1440) {
            return depOk; // multi-day trip, only check departure
        }

        return depOk && arrOk;
    }

    /** Convert a list of TrainConnections to a TransferResult. */
    private TransferResult toResult(List<TrainConnection> segments) {
        TransferResult r = new TransferResult();
        r.setId(UUID.randomUUID().toString().substring(0, 8));

        int totalMin = 0;
        List<TransferResult.TransferSegment> out = new ArrayList<>();

        for (TrainConnection conn : segments) {
            TransferResult.TransferSegment seg = new TransferResult.TransferSegment();
            seg.setTrainNo(conn.getTrainNo());
            seg.setTrainType(conn.getTrainType());
            seg.setFromStation(conn.getFromStation());
            seg.setToStation(conn.getToStation());
            seg.setDepartTime(formatClockTime(conn.getDepartMin()));
            seg.setArriveTime(formatClockTime(conn.getArriveMin()));
            seg.setDurationMin(conn.getDurationMin());
            out.add(seg);
            totalMin = conn.getArriveMin(); // cumulative
        }

        r.setTotalTimeMin(totalMin);
        r.setTransferCount(segments.size() - 1);
        r.setSegments(out);
        r.setScore(0.0);

        return r;
    }

    private static String formatClockTime(int cumulativeMin) {
        int h = (cumulativeMin % 1440) / 60;
        int m = cumulativeMin % 60;
        int d = cumulativeMin / 1440;
        String base = String.format("%02d:%02d", h, m);
        return d > 0 ? base + "(+%d)".formatted(d) : base;
    }
}
