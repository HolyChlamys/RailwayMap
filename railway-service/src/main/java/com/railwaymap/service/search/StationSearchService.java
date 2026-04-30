package com.railwaymap.service.search;

import com.railwaymap.common.dto.StationSearchResult;
import com.railwaymap.common.util.PinyinUtils;
import com.railwaymap.data.mapper.StationMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.regex.Pattern;

@Service
@RequiredArgsConstructor
public class StationSearchService {

    private final StationMapper stationMapper;

    private static final Pattern PINYIN_PATTERN = Pattern.compile("^[a-zA-Z]+$");
    private static final Pattern TRAIN_NO_PATTERN = Pattern.compile("^[GCDZTKYSgcdztkys]\\d*$");

    public List<StationSearchResult> search(String q, String city, int limit) {
        if (q == null || q.isBlank()) {
            return List.of();
        }

        String keyword = q.trim();

        // 车次格式不搜索车站
        if (TRAIN_NO_PATTERN.matcher(keyword).matches()) {
            return List.of();
        }

        // 纯英文 → 拼音搜索，中文 → ILIKE
        boolean isPinyin = PINYIN_PATTERN.matcher(keyword).matches();

        if (isPinyin && keyword.length() <= 6) {
            // 首字母 + 拼音混合搜索
            return stationMapper.searchByPinyin(keyword.toLowerCase(), limit);
        }

        return stationMapper.searchByKeyword(keyword, limit);
    }

    public List<StationSearchResult> searchByCity(String city, int limit) {
        if (city == null || city.isBlank()) return List.of();
        return stationMapper.searchByCity(city.trim(), limit);
    }

    /**
     * 生成或更新车站的拼音索引
     */
    public void updatePinyin(Long stationId, String name) {
        if (name == null) return;
        String fullPinyin = PinyinUtils.toPinyinNoSpace(name);
        stationMapper.updatePinyin(stationId, fullPinyin);
    }
}
