package com.railwaymap.api.controller;

import com.railwaymap.common.dto.TrainRouteDetail;
import com.railwaymap.common.dto.TrainSearchRequest;
import com.railwaymap.common.dto.TrainSearchResult;
import com.railwaymap.service.search.TrainRouteService;
import com.railwaymap.service.search.TrainSearchService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/trains")
@RequiredArgsConstructor
public class TrainController {

    private final TrainSearchService trainSearchService;
    private final TrainRouteService trainRouteService;

    @GetMapping("/search")
    public List<TrainSearchResult> search(@ModelAttribute TrainSearchRequest request) {
        return trainSearchService.search(request.getQ(), request.getType(), request.getLimit());
    }

    @GetMapping("/{no}/route")
    public TrainRouteDetail getRoute(@PathVariable String no) {
        return trainRouteService.getRouteDetail(no);
    }
}
