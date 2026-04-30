package com.railwaymap.batch.job;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.batch.core.Job;
import org.springframework.batch.core.Step;
import org.springframework.batch.core.job.builder.JobBuilder;
import org.springframework.batch.core.repository.JobRepository;
import org.springframework.batch.core.step.builder.StepBuilder;
import org.springframework.batch.item.ItemReader;
import org.springframework.batch.item.ItemWriter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.transaction.PlatformTransactionManager;

import javax.sql.DataSource;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;
import java.util.stream.Stream;

/**
 * 时刻表 + 票价数据导入 Job
 * 从 railway-scripts/data/trains/ 读取爬虫输出的 JSON 文件
 */
@Configuration
public class ScheduleImportJob {

    private static final Logger log = LoggerFactory.getLogger(ScheduleImportJob.class);

    @Bean
    public Step importRoutesStep(JobRepository jobRepository,
                                  PlatformTransactionManager txManager,
                                  DataSource dataSource) {
        JdbcTemplate jdbc = new JdbcTemplate(dataSource);

        return new StepBuilder("importRoutes", jobRepository)
                .tasklet((contribution, chunkContext) -> {
                    Path trainsDir = Path.of("railway-scripts/data/trains");
                    if (!Files.exists(trainsDir)) {
                        log.warn("训练数据目录不存在: {}", trainsDir);
                        return null;
                    }

                    ObjectMapper mapper = new ObjectMapper();
                    int totalRoutes = 0, totalStops = 0, totalFares = 0;

                    try (Stream<Path> files = Files.walk(trainsDir)) {
                        Iterator<Path> it = files.filter(f -> f.toString().endsWith(".json")).iterator();
                        while (it.hasNext()) {
                            Path file = it.next();
                            try {
                                @SuppressWarnings("unchecked")
                                Map<String, Object> data = mapper.readValue(
                                        file.toFile(), Map.class);

                                String trainNo = (String) data.get("train_no");
                                if (trainNo == null) continue;

                                // 插入或更新 train_routes
                                jdbc.update(
                                    "INSERT INTO train_routes (train_no, train_type, depart_station, " +
                                    "arrive_station, depart_time, arrive_time, duration_min, " +
                                    "data_updated_at) VALUES (?,?,?,?,?,?,?,NOW()) " +
                                    "ON CONFLICT (train_no) DO UPDATE SET data_updated_at = NOW()",
                                    trainNo, data.get("train_type"),
                                    data.get("depart_station"), data.get("arrive_station"),
                                    parseTime(data.get("depart_time")),
                                    parseTime(data.get("arrive_time")),
                                    null
                                );
                                totalRoutes++;

                                // 插入途经站
                                @SuppressWarnings("unchecked")
                                List<Map<String, Object>> stops =
                                        (List<Map<String, Object>>) data.get("stops");
                                if (stops != null) {
                                    for (Map<String, Object> stop : stops) {
                                        String stationName = (String) stop.get("station_name");
                                        if (stationName == null) continue;
                                        jdbc.update(
                                            "INSERT INTO train_stops (train_no, seq, station_name, " +
                                            "arrive_time, depart_time, stay_min) " +
                                            "VALUES (?,?,?,?,?,?) " +
                                            "ON CONFLICT DO NOTHING",
                                            trainNo,
                                            parseInt(stop.get("seq")),
                                            stationName,
                                            parseTime(stop.get("arrive_time")),
                                            parseTime(stop.get("depart_time")),
                                            parseInt(stop.get("stay_min"))
                                        );
                                        totalStops++;
                                    }
                                }

                                // 插入票价
                                @SuppressWarnings("unchecked")
                                Map<String, Object> fares = (Map<String, Object>) data.get("fares");
                                if (fares != null && !fares.isEmpty()) {
                                    // 票价区间为始发站→终到站
                                    jdbc.update(
                                        "INSERT INTO train_fares (train_no, from_station, to_station, " +
                                        "price_business, price_first, price_second, " +
                                        "price_soft_sleeper_up, price_soft_sleeper_down, " +
                                        "price_hard_sleeper_up, price_hard_sleeper_mid, " +
                                        "price_hard_sleeper_down, price_hard_seat, price_no_seat) " +
                                        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?) " +
                                        "ON CONFLICT (train_no, from_station, to_station) " +
                                        "DO UPDATE SET price_second = EXCLUDED.price_second",
                                        trainNo,
                                        data.get("depart_station"),
                                        data.get("arrive_station"),
                                        toDouble(fares.get("price_business")),
                                        toDouble(fares.get("price_first")),
                                        toDouble(fares.get("price_second")),
                                        toDouble(fares.get("price_soft_sleeper_up")),
                                        toDouble(fares.get("price_soft_sleeper_down")),
                                        toDouble(fares.get("price_hard_sleeper_up")),
                                        toDouble(fares.get("price_hard_sleeper_mid")),
                                        toDouble(fares.get("price_hard_sleeper_down")),
                                        toDouble(fares.get("price_hard_seat")),
                                        toDouble(fares.get("price_no_seat"))
                                    );
                                    totalFares++;
                                }

                            } catch (Exception e) {
                                log.warn("处理文件失败: {} - {}", file, e.getMessage());
                            }
                        }
                    }

                    log.info("[IMPORT] 时刻表导入完成: {} 车次, {} 停站, {} 票价",
                            totalRoutes, totalStops, totalFares);
                    return null;
                }, txManager)
                .build();
    }

    @Bean
    public Job scheduleImportJob(JobRepository jobRepository, Step importRoutesStep) {
        return new JobBuilder("scheduleImportJob", jobRepository)
                .start(importRoutesStep)
                .build();
    }

    private static java.sql.Time parseTime(Object val) {
        if (val == null) return null;
        String s = val.toString().trim();
        if (s.isEmpty() || s.equals("--")) return null;
        try {
            if (!s.contains(":")) {
                int h = Integer.parseInt(s) / 100;
                int m = Integer.parseInt(s) % 100;
                s = String.format("%02d:%02d:00", h, m);
            }
            if (s.split(":").length == 2) s += ":00";
            return java.sql.Time.valueOf(s);
        } catch (Exception e) {
            return null;
        }
    }

    private static Integer parseInt(Object val) {
        if (val == null) return null;
        try { return Integer.parseInt(val.toString().replaceAll("[^0-9]", "")); }
        catch (NumberFormatException e) { return null; }
    }

    private static Double toDouble(Object val) {
        if (val == null) return null;
        if (val instanceof Number n) return n.doubleValue();
        try { return Double.parseDouble(val.toString()); }
        catch (NumberFormatException e) { return null; }
    }
}
