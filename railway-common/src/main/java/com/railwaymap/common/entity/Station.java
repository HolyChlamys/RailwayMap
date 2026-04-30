package com.railwaymap.common.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("stations")
public class Station {

    @TableId(type = IdType.AUTO)
    private Long id;
    private Long osmId;
    private String name;
    private String namePinyin;
    private String city;
    private String province;
    private String railway;
    private String category;
    private Boolean passenger;
    private Boolean freight;
    private Boolean isHub;

    @TableField(exist = false)
    private Object geom;

    @TableField(exist = false)
    private String geomWkt;

    @TableField(exist = false)
    private Double lon;

    @TableField(exist = false)
    private Double lat;

    private String sourceGrid;
    private String dataQuality;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
