package com.railwaymap.service.transfer;

import com.railwaymap.common.dto.TransferResult;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.Comparator;
import java.util.List;

/**
 * 多目标排序服务
 *
 * 偏好:
 *   LEAST_TIME     — 总耗时最小
 *   LEAST_TRANSFER — 换乘次数最少, 其次总耗时
 *   LEAST_PRICE    — 票价最低
 *   NIGHT_TRAIN    — 夜间乘车优先 (远期)
 */
@Service
public class TransferRankingService {

    public List<TransferResult> rank(List<TransferResult> results, String preference) {
        return switch (preference) {
            case "least_time" -> {
                results.sort(Comparator.comparingInt(TransferResult::getTotalTimeMin));
                yield results;
            }
            case "least_transfer" -> {
                results.sort(Comparator
                        .comparingInt(TransferResult::getTransferCount)
                        .thenComparingInt(TransferResult::getTotalTimeMin));
                yield results;
            }
            case "least_price" -> {
                results.sort(Comparator
                        .comparing((TransferResult r) -> r.getTotalPriceYuan() != null
                                ? r.getTotalPriceYuan() : BigDecimal.valueOf(99999)));
                yield results;
            }
            default -> {
                // 默认 = least_time
                results.sort(Comparator.comparingInt(TransferResult::getTotalTimeMin));
                yield results;
            }
        };
    }
}
