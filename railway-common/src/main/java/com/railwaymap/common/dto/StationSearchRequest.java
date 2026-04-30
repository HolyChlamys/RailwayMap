package com.railwaymap.common.dto;

import lombok.Data;

@Data
public class StationSearchRequest {
    private String q;
    private String city;
    private Integer limit = 20;
}
