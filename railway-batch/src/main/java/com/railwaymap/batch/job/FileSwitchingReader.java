package com.railwaymap.batch.job;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.railwaymap.batch.reader.GeoJsonItemReader;
import org.springframework.batch.item.ExecutionContext;
import org.springframework.batch.item.ItemStreamException;
import org.springframework.batch.item.ItemStreamReader;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

/**
 * 多文件切换读取器 — 顺序读取所有 GeoJSON 文件
 */
public class FileSwitchingReader implements ItemStreamReader<Map<String, Object>> {

    private final String dataDir;
    private final ObjectMapper mapper;
    private List<Path> files;
    private int fileIndex;
    private GeoJsonItemReader currentReader;

    public FileSwitchingReader(String dataDir) {
        this.dataDir = dataDir != null ? dataDir : "frontend/data";
        this.mapper = new ObjectMapper();
    }

    @Override
    public void open(ExecutionContext executionContext) throws ItemStreamException {
        // 从 job context 获取已发现的文件列表
        Path dir = Path.of(dataDir);
        try {
            files = Files.list(dir)
                    .filter(f -> f.getFileName().toString().matches("grid_r\\d+_c\\d+\\.geojson"))
                    .sorted()
                    .toList();
        } catch (Exception e) {
            throw new ItemStreamException("扫描文件失败: " + dir, e);
        }
        fileIndex = 0;
        currentReader = null;
    }

    @Override
    public Map<String, Object> read() {
        while (true) {
            if (currentReader != null) {
                Map<String, Object> item = currentReader.read();
                if (item != null) return item;
                // 当前文件读完
                currentReader.close();
                currentReader = null;
                fileIndex++;
            }

            if (fileIndex >= files.size()) return null;

            // 打开下一个文件
            Path file = files.get(fileIndex);
            currentReader = new GeoJsonItemReader(file, mapper);
            currentReader.open(new ExecutionContext());
        }
    }

    @Override
    public void close() throws ItemStreamException {
        if (currentReader != null) {
            currentReader.close();
        }
    }
}
