package com.railwaymap.common.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

@Data
@TableName("railway_topology")
public class RailwayTopology {

    @TableId(type = IdType.AUTO)
    private Long id;
    private Long segA;
    private Long segB;
    private Boolean isConnected;
    private Double gapMeters;
}
