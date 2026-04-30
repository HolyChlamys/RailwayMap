package com.railwaymap.common.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;
import java.time.LocalTime;

@Data
@TableName("train_routes")
public class TrainRoute {

    @TableId(type = IdType.AUTO)
    private Long id;
    private String trainNo;
    private String trainType;
    private String departStation;
    private String arriveStation;
    private LocalTime departTime;
    private LocalTime arriveTime;
    private Integer durationMin;
    private Double distanceKm;
    private Integer runningDays;
    private Boolean isValid;
    private LocalDateTime dataUpdatedAt;
    private LocalDateTime createdAt;
}
