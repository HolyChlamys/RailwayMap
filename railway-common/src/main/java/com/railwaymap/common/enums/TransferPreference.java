package com.railwaymap.common.enums;

import lombok.Getter;

@Getter
public enum TransferPreference {
    LEAST_TIME("least_time", "最少时间"),
    LEAST_TRANSFER("least_transfer", "最少换乘"),
    NIGHT_TRAIN("night_train", "夜行昼游"),
    LEAST_PRICE("least_price", "最低票价");

    private final String code;
    private final String label;

    TransferPreference(String code, String label) {
        this.code = code;
        this.label = label;
    }
}
