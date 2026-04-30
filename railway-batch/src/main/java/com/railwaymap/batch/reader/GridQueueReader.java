package com.railwaymap.batch.reader;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 读取 grid_queue.json 并发现待导入网格文件
 */
public class GridQueueReader {

    private static final Logger log = LoggerFactory.getLogger(GridQueueReader.class);

    private final Path queuePath;
    private final Path dataDir;
    private final ObjectMapper mapper;

    public GridQueueReader(Path queuePath, Path dataDir, ObjectMapper mapper) {
        this.queuePath = queuePath;
        this.dataDir = dataDir;
        this.mapper = mapper;
    }

    /**
     * 扫描数据目录，发现所有 grid_r*_c*.geojson 文件，与队列对比检测缺失。
     * @return 待处理文件路径列表
     */
    public List<Path> discoverFiles() {
        List<Path> existingFiles = new ArrayList<>();
        try {
            Files.list(dataDir).forEach(f -> {
                String name = f.getFileName().toString();
                if (name.matches("grid_r\\d+_c\\d+\\.geojson")) {
                    existingFiles.add(f);
                }
            });
        } catch (IOException e) {
            log.error("扫描数据目录失败: {}", dataDir, e);
            return List.of();
        }

        // 检测缺失网格
        if (Files.exists(queuePath)) {
            try {
                String content = Files.readString(queuePath);
                Map<String, Object> queueData = mapper.readValue(content,
                        new TypeReference<Map<String, Object>>() {});
                @SuppressWarnings("unchecked")
                List<Map<String, Object>> grids = (List<Map<String, Object>>) queueData.get("grids");

                if (grids != null) {
                    Set<String> expected = grids.stream()
                            .map(g -> "grid_" + g.get("id") + ".geojson")
                            .collect(Collectors.toSet());
                    Set<String> actual = existingFiles.stream()
                            .map(p -> p.getFileName().toString())
                            .collect(Collectors.toSet());

                    Set<String> missing = new HashSet<>(expected);
                    missing.removeAll(actual);

                    if (!missing.isEmpty()) {
                        log.warn("缺失网格 ({}个): {}", missing.size(), missing);
                    }
                }
            } catch (IOException e) {
                log.warn("读取队列文件失败: {}", queuePath, e);
            }
        }

        // 按大小排序 (小的先处理)
        existingFiles.sort(Comparator.comparingLong(p -> {
            try {
                return Files.size(p);
            } catch (IOException e) {
                return 0;
            }
        }));

        log.info("发现 {} 个待处理 GeoJSON 文件", existingFiles.size());
        return existingFiles;
    }
}
