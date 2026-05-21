package com.railwaymap.common.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.Set;

@Data
public class TransferRequest {
    // ---- Required ----
    private String from;
    private String to;

    // ---- Optional: intended travel date (future use) ----
    private String date;

    // ---- N: transfer count range ----
    @JsonProperty("nMin")
    private Integer nMin = 0;
    private Integer maxTransfers = 2;

    // ---- D: max single-segment duration in minutes (0 = no limit) ----
    @JsonProperty("dMax")
    private Integer dMax = 0;

    // ---- T: time window in clock minutes (0-1439) ----
    @JsonProperty("tStart")
    private Integer tStart = 0;
    @JsonProperty("tEnd")
    private Integer tEnd = 1440;

    // ---- S: transfer station filter ----
    /** Optional whitelist — only allow transfers at these stations */
    private Set<String> allowedStations;
    /** Optional blacklist — forbid transfers at these stations */
    private Set<String> blockedStations;

    // ---- Output ----
    /** Soft preference for ranking (least_time / least_transfer / least_price) */
    private String preference = "least_time";
    /** Maximum results to return */
    private Integer maxResults = 20;
}
