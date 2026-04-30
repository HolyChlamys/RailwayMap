package com.railwaymap.service.route;

import com.railwaymap.common.entity.TrainSegmentMapping;
import com.railwaymap.data.mapper.RailwaySegmentMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.*;

/**
 * 车次路线匹配结果 → GeoJSON FeatureCollection
 */
@Service
@RequiredArgsConstructor
public class RouteGeoJsonService {

    private final RailwaySegmentMapper segmentMapper;

    public Map<String, Object> toGeoJson(List<TrainSegmentMapping> mappings) {
        List<Map<String, Object>> features = new ArrayList<>();

        for (TrainSegmentMapping m : mappings) {
            if (m.getSegId() == null) continue;

            var seg = segmentMapper.selectById(m.getSegId());
            if (seg == null) continue;

            Map<String, Object> feature = new LinkedHashMap<>();
            feature.put("type", "Feature");
            feature.put("properties", Map.of(
                    "seg_id", seg.getId(),
                    "name", Objects.toString(seg.getName(), ""),
                    "category", Objects.toString(seg.getCategory(), "conventional"),
                    "confidence", m.getConfidence() != null ? m.getConfidence() : 1.0,
                    "match_method", Objects.toString(m.getMatchMethod(), "topology"),
                    "seg_order", m.getSegOrder() != null ? m.getSegOrder() : 0
            ));

            // 简化 WKT 转为 GeoJSON 坐标
            String wkt = seg.getGeomWkt();
            if (wkt != null) {
                feature.put("geometry", wktToGeoJson(wkt));
            }

            features.add(feature);
        }

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("type", "FeatureCollection");
        result.put("features", features);
        return result;
    }

    private Map<String, Object> wktToGeoJson(String wkt) {
        Map<String, Object> geom = new LinkedHashMap<>();
        if (wkt == null || !wkt.startsWith("LINESTRING")) {
            return geom;
        }
        geom.put("type", "LineString");

        String coordStr = wkt.replace("LINESTRING(", "").replace(")", "").trim();
        List<List<Double>> coordinates = new ArrayList<>();
        for (String pair : coordStr.split(",")) {
            String[] parts = pair.trim().split("\\s+");
            if (parts.length >= 2) {
                coordinates.add(List.of(Double.parseDouble(parts[0]), Double.parseDouble(parts[1])));
            }
        }
        geom.put("coordinates", coordinates);
        return geom;
    }
}
