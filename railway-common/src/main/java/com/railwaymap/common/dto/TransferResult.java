package com.railwaymap.common.dto;

import lombok.Data;

import java.math.BigDecimal;
import java.util.List;

@Data
public class TransferResult {
    private String id;
    private Integer totalTimeMin;
    private BigDecimal totalPriceYuan;
    private Integer transferCount;
    private Double score;
    private List<TransferSegment> segments;

    @Data
    public static class TransferSegment {
        private String trainNo;
        private String trainType;
        private String fromStation;
        private String toStation;
        private String departTime;
        private String arriveTime;
        private Integer durationMin;
        private PriceInfo price;

        @Data
        public static class PriceInfo {
            private BigDecimal second;
            private BigDecimal first;
            private BigDecimal business;
            private BigDecimal softSleeperDown;
            private BigDecimal hardSleeperDown;
            private BigDecimal hardSeat;
        }
    }
}
