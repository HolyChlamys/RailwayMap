package com.railwaymap.api.controller;

import com.railwaymap.common.dto.StationSearchRequest;
import com.railwaymap.common.dto.StationSearchResult;
import com.railwaymap.service.map.MapQueryService;
import com.railwaymap.service.search.StationSearchService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/stations")
@RequiredArgsConstructor
public class StationController {

    private final StationSearchService stationSearchService;
    private final MapQueryService mapQueryService;

    @GetMapping("/search")
    public List<StationSearchResult> search(@ModelAttribute StationSearchRequest request) {
        if (request.getCity() != null && !request.getCity().isBlank()) {
            return stationSearchService.searchByCity(request.getCity(), request.getLimit());
        }
        return stationSearchService.search(request.getQ(), null, request.getLimit());
    }

    @GetMapping("/{id}")
    public Map<String, Object> getStation(@PathVariable Long id) {
        return mapQueryService.getStationDetail(id);
    }

    @GetMapping("/city/{city}")
    public List<StationSearchResult> getCityStations(@PathVariable String city) {
        return mapQueryService.getCityStations(city);
    }

    @GetMapping("/between")
    public List<Map<String, Object>> segmentsBetween(
            @RequestParam Long from, @RequestParam Long to) {
        return mapQueryService.findSegmentsBetween(from, to);
    }
}
