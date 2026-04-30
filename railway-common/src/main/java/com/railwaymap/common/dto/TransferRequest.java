package com.railwaymap.common.dto;

import lombok.Data;

@Data
public class TransferRequest {
    private String from;
    private String to;
    private String date;
    private Integer maxTransfers = 2;
    private String preference = "least_time";
    private Integer maxResults = 10;
}
