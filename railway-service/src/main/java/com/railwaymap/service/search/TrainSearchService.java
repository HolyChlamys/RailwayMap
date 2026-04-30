package com.railwaymap.service.search;

import com.railwaymap.common.dto.TrainSearchResult;
import com.railwaymap.data.mapper.TrainRouteMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class TrainSearchService {

    private final TrainRouteMapper trainRouteMapper;

    public List<TrainSearchResult> search(String q, String type, int limit) {
        if (q == null || q.isBlank()) {
            return List.of();
        }

        String keyword = q.trim();

        return trainRouteMapper.searchTrains(keyword, limit);
    }
}
