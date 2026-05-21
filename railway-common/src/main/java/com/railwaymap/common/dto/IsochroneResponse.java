package com.railwaymap.common.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.Map;

@Data
public class IsochroneResponse {
    /** All reachable stations sorted by elapsed time */
    private List<ReachableStation> stations;
    /** Results grouped by geographic direction: "东"/"南"/"西"/"北" */
    private Map<String, List<ReachableStation>> directionGroups;
    /** Total number of reachable stations */
    private int totalCount;
    /** Computation time in milliseconds */
    private long computeMs;
    /** The reference station's coordinates (for frontend centering) */
    private double centerLon;
    private double centerLat;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ReachableStation {
        private String stationName;
        private String city;
        /** Cumulative arrival minute (may exceed 1440 for cross-midnight) */
        private int arriveMin;
        /** Formatted clock time, e.g. "10:30" or "+1d 08:00" */
        private String arriveTime;
        /** Minutes elapsed since departure */
        private int elapsedMinutes;
        /** Number of transfers to reach this station */
        private int transfers;
        /** Station longitude */
        private double lon;
        /** Station latitude */
        private double lat;
        /** Representative path: "G5(北京→上海), G1001(上海→杭州)" */
        private String samplePath;
        /** Direction label: "东"/"南"/"西"/"北" */
        private String direction;
    }
}
