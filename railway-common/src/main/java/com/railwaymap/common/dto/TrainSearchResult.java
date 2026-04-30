package com.railwaymap.common.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class TrainSearchResult {
    private String trainNo;
    private String trainType;
    private String departStation;
    private String arriveStation;
    private LocalTime departTime;
    private LocalTime arriveTime;
    private Integer durationMin;
}
