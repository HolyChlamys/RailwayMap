package com.railwaymap.common.enums;

import lombok.Getter;

@Getter
public enum TrainType {
    G("G", "高速动车"),
    D("D", "动车"),
    C("C", "城际动车"),
    Z("Z", "直达特快"),
    T("T", "特快"),
    K("K", "快速"),
    Y("Y", "旅游列车"),
    S("S", "市郊列车");

    private final String code;
    private final String label;

    TrainType(String code, String label) {
        this.code = code;
        this.label = label;
    }
}
