package com.railwaymap.service.map;

import com.railwaymap.common.util.TileUtils;
import com.railwaymap.data.mapper.RailwaySegmentMapper;
import com.railwaymap.data.mapper.StationMapper;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

import java.util.HexFormat;
import java.util.List;

@Service
@RequiredArgsConstructor
public class TileService {

    private static final Logger log = LoggerFactory.getLogger(TileService.class);

    private final RailwaySegmentMapper railwaySegmentMapper;
    private final StationMapper stationMapper;

    @Cacheable(value = "tiles", key = "#layer + ':' + #z + ':' + #x + ':' + #y",
               unless = "#result == null || #result.length == 0")
    public byte[] getTile(String layer, int z, int x, int y) {
        double[] bbox = TileUtils.tileToBBox(z, x, y);
        String envelope = String.format("ST_MakeEnvelope(%f, %f, %f, %f, 4326)",
                bbox[0], bbox[1], bbox[2], bbox[3]);
        log.info("[TILE] {}/{}/{}/{} bbox={}", layer, z, x, y, envelope);

        List<String> hexResults;
        return switch (layer) {
            case "railways" -> {
                if (z < 6) yield emptyTile();
                hexResults = railwaySegmentMapper.getVectorTile(envelope, z, x, y, "railways");
                log.info("[TILE] railways query returned {} results", hexResults != null ? hexResults.size() : 0);
                yield hexToBytes(hexResults);
            }
            case "stations" -> {
                if (z < 8) yield emptyTile();
                hexResults = stationMapper.getVectorTile(envelope, z, x, y, "stations");
                yield hexToBytes(hexResults);
            }
            default -> emptyTile();
        };
    }

    private byte[] hexToBytes(List<String> hexResults) {
        if (hexResults == null || hexResults.isEmpty()) {
            return emptyTile();
        }
        try {
            StringBuilder sb = new StringBuilder();
            for (String h : hexResults) {
                if (h != null) {
                    String clean = h.strip();
                    if (clean.startsWith("\"") && clean.endsWith("\"")) {
                        clean = clean.substring(1, clean.length() - 1);
                    }
                    if (clean.startsWith("\\x")) {
                        clean = clean.substring(2);
                    }
                    sb.append(clean);
                }
            }
            if (sb.isEmpty()) return emptyTile();
            return HexFormat.of().parseHex(sb.toString());
        } catch (Exception e) {
            log.error("解码 MVT hex 失败", e);
            return emptyTile();
        }
    }

    private byte[] emptyTile() {
        return new byte[0];
    }
}
