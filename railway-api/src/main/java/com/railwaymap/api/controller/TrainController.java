package com.railwaymap.api.controller;

import com.railwaymap.common.dto.TrainRouteDetail;
import com.railwaymap.common.dto.TrainSearchRequest;
import com.railwaymap.common.dto.TrainSearchResult;
import com.railwaymap.common.entity.*;
import com.railwaymap.data.mapper.*;
import com.railwaymap.service.route.RouteGeoJsonService;
import com.railwaymap.service.search.TrainSearchService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/trains")
@RequiredArgsConstructor
public class TrainController {

    private final TrainSearchService trainSearchService;
    private final TrainRouteMapper trainRouteMapper;
    private final TrainStopMapper trainStopMapper;
    private final TrainSegmentMappingMapper mappingMapper;
    private final TrainFareMapper fareMapper;
    private final StationMapper stationMapper;
    private final RouteGeoJsonService geoJsonService;

    @GetMapping("/search")
    public List<TrainSearchResult> search(@ModelAttribute TrainSearchRequest request) {
        return trainSearchService.search(request.getQ(), request.getType(), request.getLimit());
    }

    @GetMapping("/{no}/route")
    public TrainRouteDetail getRoute(@PathVariable String no) {
        TrainRoute route = trainRouteMapper.selectOne(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<TrainRoute>()
                        .eq(TrainRoute::getTrainNo, no));
        if (route == null) return null;

        List<TrainStop> stops = trainStopMapper.selectList(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<TrainStop>()
                        .eq(TrainStop::getTrainNo, no)
                        .orderByAsc(TrainStop::getSeq));

        List<TrainSegmentMapping> mappings = mappingMapper.selectList(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<TrainSegmentMapping>()
                        .eq(TrainSegmentMapping::getTrainNo, no));

        List<TrainFare> fares = fareMapper.selectList(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<TrainFare>()
                        .eq(TrainFare::getTrainNo, no));

        TrainRouteDetail detail = new TrainRouteDetail();
        detail.setTrainNo(route.getTrainNo());
        detail.setTrainType(route.getTrainType());
        detail.setDepartStation(route.getDepartStation());
        detail.setArriveStation(route.getArriveStation());
        detail.setDepartTime(route.getDepartTime());
        detail.setArriveTime(route.getArriveTime());
        detail.setDurationMin(route.getDurationMin());

        detail.setStops(stops.stream().map(s -> {
            TrainRouteDetail.StopInfo si = new TrainRouteDetail.StopInfo();
            si.setSeq(s.getSeq());
            si.setStationName(s.getStationName());
            si.setStationId(s.getStationId());
            si.setArriveTime(s.getArriveTime());
            si.setDepartTime(s.getDepartTime());
            si.setStayMin(s.getStayMin());
            return si;
        }).collect(Collectors.toList()));

        if (!mappings.isEmpty()) {
            detail.setSegmentsGeoJson(geoJsonService.toGeoJson(mappings));
        }

        detail.setFares(fares.stream().map(f -> {
            TrainRouteDetail.FareInfo fi = new TrainRouteDetail.FareInfo();
            fi.setFromStation(f.getFromStation());
            fi.setToStation(f.getToStation());
            fi.setPriceSecond(f.getPriceSecond());
            fi.setPriceFirst(f.getPriceFirst());
            fi.setPriceBusiness(f.getPriceBusiness());
            fi.setPriceSoftSleeperDown(f.getPriceSoftSleeperDown());
            fi.setPriceHardSleeperDown(f.getPriceHardSleeperDown());
            fi.setPriceHardSeat(f.getPriceHardSeat());
            return fi;
        }).collect(Collectors.toList()));

        return detail;
    }
}
