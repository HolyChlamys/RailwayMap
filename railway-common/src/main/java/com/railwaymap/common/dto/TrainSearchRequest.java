package com.railwaymap.common.dto;

import lombok.Data;

@Data
public class TrainSearchRequest {
    private String q;
    private String type;
    private Integer limit = 20;
}
