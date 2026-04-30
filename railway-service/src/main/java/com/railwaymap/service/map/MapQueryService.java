package com.railwaymap.service.map;

import com.railwaymap.common.dto.StationSearchResult;
import com.railwaymap.common.entity.*;
import com.railwaymap.data.mapper.*;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.*;

@Service
@RequiredArgsConstructor
public class MapQueryService {

    private final StationMapper stationMapper;
    private final RailwaySegmentMapper segmentMapper;
    private final TrainStopMapper trainStopMapper;
    private final TrainSegmentMappingMapper mappingMapper;

    /**
     * 站站查询 — 获取两站之间的所有铁路线段
     */
    public List<Map<String, Object>> findSegmentsBetween(Long fromStationId, Long toStationId) {
        Station from = stationMapper.selectById(fromStationId);
        Station to = stationMapper.selectById(toStationId);
        if (from == null || to == null) return List.of();

        // PostGIS 找两点之间一定缓冲区内的所有线段
        String envelope = String.format(
                "ST_Buffer(ST_MakeLine(ST_SetSRID(ST_MakePoint(%f, %f), 4326)," +
                "ST_SetSRID(ST_MakePoint(%f, %f), 4326))::geography, 5000)",
                from.getLon(), from.getLat(), to.getLon(), to.getLat());

        List<RailwaySegment> segments = segmentMapper.findByBBox(envelope, 100);
        List<Map<String, Object>> result = new ArrayList<>();
        for (RailwaySegment seg : segments) {
            Map<String, Object> m = new HashMap<>();
            m.put("id", seg.getId());
            m.put("name", seg.getName());
            m.put("category", seg.getCategory());
            m.put("railway", seg.getRailway());
            m.put("maxSpeed", seg.getMaxSpeed());
            m.put("lengthKm", seg.getLengthKm());
            result.add(m);
        }
        return result;
    }

    /**
     * 获取车站详情
     */
    public Map<String, Object> getStationDetail(Long stationId) {
        Station station = stationMapper.selectById(stationId);
        if (station == null) return null;

        Map<String, Object> detail = new HashMap<>();
        detail.put("id", station.getId());
        detail.put("name", station.getName());
        detail.put("city", station.getCity());
        detail.put("province", station.getProvince());
        detail.put("category", station.getCategory());
        detail.put("passenger", station.getPassenger());
        detail.put("freight", station.getFreight());
        detail.put("isHub", station.getIsHub());
        detail.put("lon", station.getLon());
        detail.put("lat", station.getLat());

        // 途经车次
        List<TrainStop> stops = trainStopMapper.selectList(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<TrainStop>()
                        .eq(TrainStop::getStationId, stationId)
                        .last("LIMIT 50"));
        List<String> trainNos = stops.stream()
                .map(TrainStop::getTrainNo)
                .distinct()
                .sorted()
                .toList();
        detail.put("passingTrains", trainNos);
        detail.put("trainCount", trainNos.size());

        return detail;
    }

    /**
     * 获取城市所有车站
     */
    public List<StationSearchResult> getCityStations(String city) {
        return stationMapper.searchByCity(city, 100);
    }
}
