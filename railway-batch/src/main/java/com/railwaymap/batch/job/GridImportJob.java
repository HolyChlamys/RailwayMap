package com.railwaymap.batch.job;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.railwaymap.batch.listener.ImportProgressListener;
import com.railwaymap.batch.processor.RailwaySegmentProcessor;
import com.railwaymap.batch.processor.StationProcessor;
import com.railwaymap.batch.reader.GeoJsonItemReader;
import com.railwaymap.batch.reader.GridQueueReader;
import com.railwaymap.batch.writer.PostgisBatchItemWriter;
import org.locationtech.jts.geom.GeometryFactory;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.batch.core.Job;
import org.springframework.batch.core.Step;
import org.springframework.batch.core.configuration.annotation.JobScope;
import org.springframework.batch.core.job.builder.JobBuilder;
import org.springframework.batch.core.repository.JobRepository;
import org.springframework.batch.core.step.builder.StepBuilder;
import org.springframework.batch.item.ItemProcessor;
import org.springframework.batch.item.ItemReader;
import org.springframework.batch.item.ItemWriter;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.transaction.PlatformTransactionManager;

import javax.sql.DataSource;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

/**
 * 网格数据导入 Job
 *
 * Step 1: 文件发现 — 扫描 data/ 下所有 Geojson 文件
 * Step 2: 逐文件导入 (rail/station 分两个 step)
 * Step 3: 去重 + 拓扑构建
 * Step 4: 完整性校验
 */
@Configuration
public class GridImportJob {

    private static final Logger log = LoggerFactory.getLogger(GridImportJob.class);

    private static final String RAIL_SQL =
            "INSERT INTO railway_segments (osm_id, name, railway, usage, category, " +
            "electrified, gauge, max_speed, track_count, geom, length_km, source_grid, data_quality) " +
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ST_GeomFromText(?, 4326), ?, ?, ?) " +
            "ON CONFLICT DO NOTHING";

    private static final String STATION_SQL =
            "INSERT INTO stations (osm_id, name, name_pinyin, railway, category, " +
            "passenger, geom, source_grid, data_quality) " +
            "VALUES (?, ?, ?, ?, ?, ?, ST_GeomFromText(?, 4326), ?, ?) " +
            "ON CONFLICT DO NOTHING";

    @Bean
    @JobScope
    public Step fileDiscoveryStep(JobRepository jobRepository,
                                   PlatformTransactionManager txManager,
                                   @Value("#{jobParameters['data.dir']}") String dataDir) {
        return new StepBuilder("fileDiscovery", jobRepository)
                .tasklet((contribution, chunkContext) -> {
                    Path dir = Path.of(dataDir != null ? dataDir : "frontend/data");
                    Path queuePath = dir.resolve("grid_queue.json");
                    GridQueueReader reader = new GridQueueReader(queuePath, dir, new ObjectMapper());
                    List<Path> files = reader.discoverFiles();

                    chunkContext.getStepContext().getStepExecution()
                            .getJobExecution().getExecutionContext()
                            .put("files", files.stream().map(Path::toString).toList());
                    chunkContext.getStepContext().getStepExecution()
                            .getJobExecution().getExecutionContext()
                            .put("totalFiles", files.size());

                    log.info("[IMPORT] 发现 {} 个文件待处理", files.size());
                    return null;
                }, txManager)
                .build();
    }

    @Bean
    @JobScope
    public Step importRailwaysStep(JobRepository jobRepository,
                                    PlatformTransactionManager txManager,
                                    DataSource dataSource,
                                    GeometryFactory geometryFactory,
                                    @Value("#{jobParameters['data.dir']}") String dataDir) {
        return new StepBuilder("importRailways", jobRepository)
                .<Map<String, Object>, Map<String, Object>>chunk(1000, txManager)
                .reader(new FileSwitchingReader(dataDir))
                .processor(new RailwaySegmentProcessor(geometryFactory, new ObjectMapper()))
                .writer(new PostgisBatchItemWriter(dataSource, "railway_segments", RAIL_SQL) {
                    @Override
                    protected Object[] toParams(Map<String, Object> row) {
                        return new Object[]{
                                row.get("osm_id"), row.get("name"), row.get("railway"),
                                row.get("usage"), row.get("category"), row.get("electrified"),
                                row.get("gauge"), row.get("max_speed"), row.get("track_count"),
                                row.get("geom"), row.get("length_km"), row.get("source_grid"),
                                row.get("data_quality")
                        };
                    }
                })
                .listener(new ImportProgressListener(
                        Path.of(dataDir != null ? dataDir : "frontend/data").resolve("import_errors.log"),
                        0))
                .build();
    }

    @Bean
    @JobScope
    public Step importStationsStep(JobRepository jobRepository,
                                    PlatformTransactionManager txManager,
                                    DataSource dataSource) {
        return new StepBuilder("importStations", jobRepository)
                .<Map<String, Object>, Map<String, Object>>chunk(1000, txManager)
                .reader(new FileSwitchingReader(null))
                .processor(new StationProcessor())
                .writer(new PostgisBatchItemWriter(dataSource, "stations", STATION_SQL) {
                    @Override
                    protected Object[] toParams(Map<String, Object> row) {
                        return new Object[]{
                                row.get("osm_id"), row.get("name"), row.get("name_pinyin"),
                                row.get("railway"), row.get("category"), row.get("passenger"),
                                row.get("geom"), row.get("source_grid"), row.get("data_quality")
                        };
                    }
                })
                .build();
    }

    @Bean
    public Job gridImportJob(JobRepository jobRepository,
                              Step fileDiscoveryStep,
                              Step importRailwaysStep,
                              Step importStationsStep) {
        return new JobBuilder("gridImportJob", jobRepository)
                .start(fileDiscoveryStep)
                .next(importRailwaysStep)
                .next(importStationsStep)
                .build();
    }

    /**
     * 简单的文件切换读取器：遍历所有 GeoJSON 文件，逐个读取并产出 Feature。
     * 在第一个文件读完后切换到下一个。
     */
    // FileSwitchingReader 在独立文件中实现
}
