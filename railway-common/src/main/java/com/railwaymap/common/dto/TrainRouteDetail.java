package com.railwaymap.common.dto;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalTime;
import java.util.List;

@Data
public class TrainRouteDetail {
    private String trainNo;
    private String trainType;
    private String departStation;
    private String arriveStation;
    private LocalTime departTime;
    private LocalTime arriveTime;
    private Integer durationMin;
    private List<StopInfo> stops;
    private Object segmentsGeoJson;
    private List<FareInfo> fares;

    @Data
    public static class StopInfo {
        private Integer seq;
        private String stationName;
        private Long stationId;
        private Double lon;
        private Double lat;
        private LocalTime arriveTime;
        private LocalTime departTime;
        private Integer stayMin;
    }

    @Data
    public static class FareInfo {
        private String fromStation;
        private String toStation;
        private BigDecimal priceSecond;
        private BigDecimal priceFirst;
        private BigDecimal priceBusiness;
        private BigDecimal priceSoftSleeperDown;
        private BigDecimal priceHardSleeperDown;
        private BigDecimal priceHardSeat;
    }
}
