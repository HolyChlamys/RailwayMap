package com.railwaymap.batch.processor;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.locationtech.jts.geom.*;
import org.locationtech.jts.io.ParseException;
import org.locationtech.jts.io.WKTReader;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.batch.item.ItemProcessor;

import java.util.*;

/**
 * GeoJSON Feature → railway_segments 实体映射
 * 包含: 数据清洗、名称规范化、OSM标签→分类映射、WKT转换
 */
public class RailwaySegmentProcessor implements ItemProcessor<Map<String, Object>, Map<String, Object>> {

    private static final Logger log = LoggerFactory.getLogger(RailwaySegmentProcessor.class);

    private final GeometryFactory geometryFactory;
    private final ObjectMapper objectMapper;

    private static final Set<String> RAILWAY_KEYS = Set.of(
            "rail", "subway", "light_rail", "narrow_gauge", "funicular", "tram", "disused", "abandoned"
    );

    public RailwaySegmentProcessor(GeometryFactory geometryFactory, ObjectMapper objectMapper) {
        this.geometryFactory = geometryFactory;
        this.objectMapper = objectMapper;
    }

    @Override
    public Map<String, Object> process(Map<String, Object> feature) {
        @SuppressWarnings("unchecked")
        Map<String, Object> props = (Map<String, Object>) feature.getOrDefault("properties", Map.of());
        @SuppressWarnings("unchecked")
        Map<String, Object> geom = (Map<String, Object>) feature.get("geometry");

        if (geom == null) return null;

        String type = (String) geom.get("type");
        if (!"LineString".equals(type)) return null;

        String railway = (String) props.getOrDefault("railway", "rail");
        if (!RAILWAY_KEYS.contains(railway)) return null;

        Map<String, Object> row = new HashMap<>();
        row.put("osm_id", props.get("osm_id"));
        row.put("name", cleanName((String) props.get("name")));
        row.put("railway", railway);
        row.put("usage", props.get("usage"));
        row.put("electrified", props.get("electrified"));
        row.put("gauge", parseGauge((String) props.get("gauge")));
        row.put("max_speed", parseMaxSpeed((String) props.get("maxspeed")));
        row.put("track_count", parseTrackCount((String) props.get("tracks")));
        row.put("category", classifyRailway(railway, (String) props.get("usage"),
                (String) props.get("highspeed")));

        // 坐标转 WKT
        @SuppressWarnings("unchecked")
        List<List<Double>> coords = (List<List<Double>>) geom.get("coordinates");
        if (coords == null || coords.size() < 2) return null;

        row.put("geom", coordinatesToWkt(coords));
        row.put("length_km", computeLengthKm(coords));
        row.put("data_quality", "osm");

        return row;
    }

    private String classifyRailway(String railway, String usage, String highspeed) {
        if ("subway".equals(railway)) return "subway";
        if ("yes".equals(highspeed) || "high_speed".equals(highspeed)) return "high_speed";
        if ("freight".equals(usage)) return "freight_rail";
        if ("main".equals(usage)) return "passenger_rail";
        if ("industrial".equals(usage) || "military".equals(usage) || "tourism".equals(usage)) {
            return "other_rail";
        }
        return "conventional";
    }

    private String cleanName(String name) {
        if (name == null) return null;
        return name.trim().replaceAll("\\s+", " ");
    }

    private Integer parseGauge(String s) {
        if (s == null) return 1435;
        try {
            return Integer.parseInt(s.replaceAll("[^0-9]", ""));
        } catch (NumberFormatException e) {
            return 1435;
        }
    }

    private Integer parseMaxSpeed(String s) {
        if (s == null) return null;
        try {
            return Integer.parseInt(s.replaceAll("[^0-9]", ""));
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private Integer parseTrackCount(String s) {
        if (s == null) return 1;
        try {
            return Integer.parseInt(s.replaceAll("[^0-9]", ""));
        } catch (NumberFormatException e) {
            return 1;
        }
    }

    @SuppressWarnings("unchecked")
    private String coordinatesToWkt(List<List<Double>> coords) {
        StringBuilder sb = new StringBuilder("LINESTRING(");
        for (int i = 0; i < coords.size(); i++) {
            List<Double> p = coords.get(i);
            if (i > 0) sb.append(", ");
            sb.append(String.format(Locale.US, "%.7f %.7f", p.get(0), p.get(1)));
        }
        sb.append(")");
        return sb.toString();
    }

    private double computeLengthKm(List<List<Double>> coords) {
        double total = 0;
        for (int i = 1; i < coords.size(); i++) {
            List<Double> a = coords.get(i - 1);
            List<Double> b = coords.get(i);
            total += haversineDistance(a.get(0), a.get(1), b.get(0), b.get(1));
        }
        return total / 1000.0;
    }

    private double haversineDistance(double lon1, double lat1, double lon2, double lat2) {
        double dLat = Math.toRadians(lat2 - lat1);
        double dLon = Math.toRadians(lon2 - lon1);
        double a = Math.sin(dLat / 2) * Math.sin(dLat / 2)
                + Math.cos(Math.toRadians(lat1)) * Math.cos(Math.toRadians(lat2))
                * Math.sin(dLon / 2) * Math.sin(dLon / 2);
        double c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return 6371000.0 * c;
    }
}
