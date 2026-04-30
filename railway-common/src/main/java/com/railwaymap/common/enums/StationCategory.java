package com.railwaymap.common.enums;

import lombok.Getter;

@Getter
public enum StationCategory {
    MAJOR_HUB("major_hub", "重要枢纽（客/货）"),
    MAJOR_PASSENGER("major_passenger", "主要车站（客/货）"),
    MEDIUM_PASSENGER("medium_passenger", "中等车站（客/货）"),
    SMALL_PASSENGER("small_passenger", "小型车站（客/货）"),
    SMALL_NON_PASSENGER("small_non_passenger", "小型车站（无旅客服务）"),
    LARGE_YARD("large_yard", "大型编组站"),
    MEDIUM_YARD("medium_yard", "中小编组站"),
    MAJOR_FREIGHT("major_freight", "重要货运车站"),
    SIGNAL_STATION("signal_station", "线路所 / 信号站"),
    OTHER_FACILITY("other_facility", "其他铁路设施"),
    FREIGHT_YARD("freight_yard", "铁路货场"),
    EMU_DEPOT("emu_depot", "动车整备场");

    private final String code;
    private final String label;

    StationCategory(String code, String label) {
        this.code = code;
        this.label = label;
    }
}
