package com.railwaymap.common.enums;

import lombok.Getter;

@Getter
public enum RailwayCategory {
    CONVENTIONAL("conventional", "铁路（双线/单线）"),
    HIGH_SPEED("high_speed", "高速铁路"),
    RAPID_TRANSIT("rapid_transit", "快速铁路、城际铁路"),
    PASSENGER_RAIL("passenger_rail", "普通铁路（客运）"),
    FREIGHT_RAIL("freight_rail", "普通铁路（货运）"),
    OTHER_RAIL("other_rail", "其他（专用线、联络线）"),
    SUBWAY("subway", "地铁");

    private final String code;
    private final String label;

    RailwayCategory(String code, String label) {
        this.code = code;
        this.label = label;
    }
}
