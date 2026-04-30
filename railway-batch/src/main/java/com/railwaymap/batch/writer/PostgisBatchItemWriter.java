package com.railwaymap.batch.writer;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.batch.item.Chunk;
import org.springframework.batch.item.ItemWriter;
import org.springframework.jdbc.core.JdbcTemplate;

import javax.sql.DataSource;
import java.util.List;
import java.util.Map;

/**
 * PostGIS 批量写入器 — 每 chunk 提交一次事务
 */
public class PostgisBatchItemWriter implements ItemWriter<Map<String, Object>> {

    private static final Logger log = LoggerFactory.getLogger(PostgisBatchItemWriter.class);

    private final JdbcTemplate jdbc;
    private final String sql;
    private final String tableName;

    public PostgisBatchItemWriter(DataSource dataSource, String tableName, String sql) {
        this.jdbc = new JdbcTemplate(dataSource);
        this.tableName = tableName;
        this.sql = sql;
    }

    @Override
    public void write(Chunk<? extends Map<String, Object>> chunk) {
        List<Object[]> batchArgs = chunk.getItems().stream()
                .map(this::toParams)
                .toList();

        jdbc.batchUpdate(sql, batchArgs);
        log.debug("[WRITER] {} 写入 {} 条", tableName, chunk.size());
    }

    /**
     * 子类可覆盖此方法定义参数映射
     */
    protected Object[] toParams(Map<String, Object> row) {
        return row.values().toArray();
    }
}
