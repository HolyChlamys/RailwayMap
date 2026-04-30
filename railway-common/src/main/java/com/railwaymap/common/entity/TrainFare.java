package com.railwaymap.common.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@TableName("train_fares")
public class TrainFare {

    @TableId(type = IdType.AUTO)
    private Long id;
    private String trainNo;
    private String fromStation;
    private String toStation;
    private BigDecimal priceBusiness;
    private BigDecimal priceFirst;
    private BigDecimal priceSecond;
    private BigDecimal priceSoftSleeperUp;
    private BigDecimal priceSoftSleeperDown;
    private BigDecimal priceHardSleeperUp;
    private BigDecimal priceHardSleeperMid;
    private BigDecimal priceHardSleeperDown;
    private BigDecimal priceHardSeat;
    private BigDecimal priceNoSeat;
    private LocalDateTime dataUpdatedAt;
}
