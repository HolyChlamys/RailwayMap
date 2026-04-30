package com.railwaymap.common.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("railway_segments")
public class RailwaySegment {

    @TableId(type = IdType.AUTO)
    private Long id;
    private Long osmId;
    private String name;
    private String railway;
    private String usage;
    private String category;
    private String electrified;
    private Integer gauge;
    private Integer maxSpeed;
    private Integer trackCount;

    @TableField(exist = false)
    private Object geom;

    @TableField(exist = false)
    private String geomWkt;

    private Double lengthKm;
    private String sourceGrid;
    private String dataQuality;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
