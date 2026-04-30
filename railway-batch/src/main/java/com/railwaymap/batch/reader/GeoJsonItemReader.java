package com.railwaymap.batch.reader;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.batch.item.ExecutionContext;
import org.springframework.batch.item.ItemStreamException;
import org.springframework.batch.item.ItemStreamReader;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;

/**
 * 分块读取 GeoJSON FeatureCollection
 */
public class GeoJsonItemReader implements ItemStreamReader<Map<String, Object>> {

    private final Path filePath;
    private final ObjectMapper mapper;
    private Iterator<Map<String, Object>> featureIterator;
    private int count;

    public GeoJsonItemReader(Path filePath, ObjectMapper mapper) {
        this.filePath = filePath;
        this.mapper = mapper;
    }

    @Override
    public void open(ExecutionContext executionContext) throws ItemStreamException {
        try {
            String content = Files.readString(filePath);
            Map<String, Object> geojson = mapper.readValue(content,
                    new TypeReference<Map<String, Object>>() {});
            @SuppressWarnings("unchecked")
            List<Map<String, Object>> features = (List<Map<String, Object>>) geojson.get("features");
            this.featureIterator = features != null ? features.iterator() : Collections.emptyIterator();
            this.count = 0;
        } catch (IOException e) {
            throw new ItemStreamException("读取 GeoJSON 失败: " + filePath, e);
        }
    }

    @Override
    public Map<String, Object> read() {
        if (featureIterator.hasNext()) {
            count++;
            return featureIterator.next();
        }
        return null;
    }

    @Override
    public void close() throws ItemStreamException {
        this.featureIterator = null;
    }

    public int getCount() {
        return count;
    }

    public Path getFilePath() {
        return filePath;
    }
}
