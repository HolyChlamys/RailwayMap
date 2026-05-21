package com.railwaymap.common.dto;

import lombok.Data;

import java.util.Set;

@Data
public class IsochroneRequest {
    /** Departure station name (required) */
    private String station;

    /** Departure time in cumulative minutes from day 0 00:00 (default 480 = 08:00) */
    private int departMin = 480;

    /** Maximum total travel time in minutes (default 240 = 4 hours) */
    private int maxMinutes = 240;

    /** Maximum transfer count (0 = no limit, use departMin + maxMinutes as hard cap) */
    private int maxTransfers = 2;

    /** Whether to group results by geographic direction (N/S/E/W) */
    private boolean groupByDirection = true;
}
