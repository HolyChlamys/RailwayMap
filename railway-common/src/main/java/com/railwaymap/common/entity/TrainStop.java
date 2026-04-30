package com.railwaymap.common.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalTime;

@Data
@TableName("train_stops")
public class TrainStop {

    @TableId(type = IdType.AUTO)
    private Long id;
    private String trainNo;
    private Integer seq;
    private String stationName;
    private Long stationId;
    private LocalTime arriveTime;
    private LocalTime departTime;
    private Integer stayMin;
    private Double distanceKm;
    private Boolean isTerminal;
}
