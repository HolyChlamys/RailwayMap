package com.railwaymap.batch.processor;

import com.railwaymap.common.util.PinyinUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.batch.item.ItemProcessor;

import java.util.*;

/**
 * GeoJSON Feature → stations 实体映射
 */
public class StationProcessor implements ItemProcessor<Map<String, Object>, Map<String, Object>> {

    private static final Logger log = LoggerFactory.getLogger(StationProcessor.class);

    private static final Set<String> STATION_RAILWAY_VALUES = Set.of(
            "station", "halt", "tram_stop", "yard", "depot", "signal_box"
    );

    @Override
    public Map<String, Object> process(Map<String, Object> feature) {
        @SuppressWarnings("unchecked")
        Map<String, Object> geom = (Map<String, Object>) feature.get("geometry");

        if (geom == null || !"Point".equals(geom.get("type"))) return null;

        @SuppressWarnings("unchecked")
        Map<String, Object> props = (Map<String, Object>) feature.getOrDefault("properties", Map.of());

        String railway = (String) props.get("railway");
        String publicTransport = (String) props.get("public_transport");
        String train = (String) props.get("train");

        // 必须有 railway 或 public_transport=train 标签
        if (railway == null && !"station".equals(publicTransport)) return null;

        String name = (String) props.getOrDefault("name:zh", props.get("name"));
        if (name == null || name.isBlank()) return null;

        Map<String, Object> row = new HashMap<>();
        row.put("osm_id", props.get("osm_id"));
        row.put("name", cleanName(name));
        row.put("name_pinyin", PinyinUtils.toPinyinNoSpace(cleanName(name)));
        row.put("railway", railway);
        row.put("category", classifyStation(props));

        @SuppressWarnings("unchecked")
        List<Double> coords = (List<Double>) geom.get("coordinates");
        row.put("lon", coords.get(0));
        row.put("lat", coords.get(1));

        // WKT Point
        row.put("geom", String.format(Locale.US,
                "POINT(%.7f %.7f)", coords.get(0), coords.get(1)));

        row.put("data_quality", "osm");
        row.put("passenger", hasPassengerService(props));

        return row;
    }

    private String classifyStation(Map<String, Object> props) {
        String railway = (String) props.get("railway");
        String stationLevel = (String) props.get("station");

        if ("yard".equals(railway)) return "medium_yard";
        if ("depot".equals(railway)) return "emu_depot";
        if ("signal_box".equals(railway)) return "signal_station";
        if ("halt".equals(railway)) return "small_passenger";

        // station=hub 表示重要枢纽
        if ("hub".equals(stationLevel)) return "major_hub";

        return "small_passenger";
    }

    private boolean hasPassengerService(Map<String, Object> props) {
        String railway = (String) props.get("railway");
        if ("yard".equals(railway) || "depot".equals(railway)) return false;
        String train = (String) props.get("train");
        return !"no".equals(train);
    }

    private String cleanName(String name) {
        if (name == null) return null;
        return name.trim().replaceAll("\\s+", " ");
    }
}
