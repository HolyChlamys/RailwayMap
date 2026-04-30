package com.railwaymap.common.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

@Data
@TableName("train_segment_mapping")
public class TrainSegmentMapping {

    @TableId(type = IdType.AUTO)
    private Long id;
    private String trainNo;
    private String fromStation;
    private String toStation;
    private Long segId;
    private Integer segOrder;
    private Double confidence;
    private String matchMethod;
}
