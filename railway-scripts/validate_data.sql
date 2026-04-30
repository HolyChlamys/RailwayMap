-- ============================================================
-- 数据完整性校验脚本
-- 执行时机: Phase 1 数据导入 + 拓扑构建完成后
-- ============================================================

\echo '========== 1. 各表数量统计 =========='

SELECT 'railway_segments' AS table_name, COUNT(*) AS count FROM railway_segments
UNION ALL
SELECT 'stations', COUNT(*) FROM stations
UNION ALL
SELECT 'railway_topology', COUNT(*) FROM railway_topology
UNION ALL
SELECT 'train_routes', COUNT(*) FROM train_routes
UNION ALL
SELECT 'train_stops', COUNT(*) FROM train_stops
UNION ALL
SELECT 'train_fares', COUNT(*) FROM train_fares
UNION ALL
SELECT 'train_segment_mapping', COUNT(*) FROM train_segment_mapping
ORDER BY table_name;

\echo ''
\echo '========== 2. 铁路线按分类统计 =========='

SELECT
    category,
    COUNT(*) AS count,
    ROUND(AVG(length_km)::numeric, 2) AS avg_length_km,
    ROUND(SUM(length_km)::numeric, 2) AS total_length_km
FROM railway_segments
GROUP BY category
ORDER BY
    CASE category
        WHEN 'high_speed' THEN 1
        WHEN 'rapid_transit' THEN 2
        WHEN 'conventional' THEN 3
        WHEN 'passenger_rail' THEN 4
        WHEN 'freight_rail' THEN 5
        WHEN 'subway' THEN 6
        WHEN 'other_rail' THEN 7
    END;

\echo ''
\echo '========== 3. 车站按分类统计 =========='

SELECT
    category,
    COUNT(*) AS count,
    COUNT(*) FILTER (WHERE passenger) AS passenger_count,
    COUNT(*) FILTER (WHERE freight) AS freight_count,
    COUNT(*) FILTER (WHERE data_quality = 'manual') AS manual_verified
FROM stations
GROUP BY category
ORDER BY
    CASE category
        WHEN 'major_hub' THEN 1
        WHEN 'major_passenger' THEN 2
        WHEN 'medium_passenger' THEN 3
        WHEN 'small_passenger' THEN 4
        WHEN 'large_yard' THEN 5
        WHEN 'medium_yard' THEN 6
        WHEN 'major_freight' THEN 7
        WHEN 'freight_yard' THEN 8
        WHEN 'emu_depot' THEN 9
        WHEN 'signal_station' THEN 10
        WHEN 'small_non_passenger' THEN 11
        WHEN 'other_facility' THEN 12
    END;

\echo ''
\echo '========== 4. 网格来源统计 =========='

SELECT
    source_grid,
    COUNT(*) AS segment_count,
    ROUND(SUM(length_km)::numeric, 2) AS total_km
FROM railway_segments
WHERE source_grid IS NOT NULL
GROUP BY source_grid
ORDER BY source_grid;

\echo ''
\echo '========== 5. 随机抽样 100 条 ST_IsValid 检查 =========='

SELECT
    COUNT(*) AS invalid_count
FROM (
    SELECT id FROM railway_segments
    ORDER BY RANDOM()
    LIMIT 100
) AS sample
WHERE NOT ST_IsValid(geom);

\echo ''
\echo '========== 6. 无名称车站/线路统计 =========='

SELECT 'stations_without_name' AS check_name, COUNT(*) AS count
FROM stations WHERE name IS NULL OR name = ''
UNION ALL
SELECT 'stations_without_pinyin', COUNT(*) FROM stations WHERE name_pinyin IS NULL OR name_pinyin = ''
UNION ALL
SELECT 'segments_without_name', COUNT(*) FROM railway_segments WHERE name IS NULL OR name = ''
UNION ALL
SELECT 'segments_zero_length', COUNT(*) FROM railway_segments WHERE length_km IS NULL OR length_km = 0;

\echo ''
\echo '========== 7. 拓扑覆盖率 =========='

WITH connected_segs AS (
    SELECT DISTINCT seg_a AS seg_id FROM railway_topology
    UNION
    SELECT DISTINCT seg_b FROM railway_topology
)
SELECT
    (SELECT COUNT(*) FROM railway_segments) AS total_segments,
    (SELECT COUNT(*) FROM connected_segs) AS connected_segments,
    ROUND(
        (SELECT COUNT(*) FROM connected_segs)::numeric
        / NULLIF((SELECT COUNT(*) FROM railway_segments), 0) * 100,
        2
    ) AS coverage_pct;

\echo ''
\echo '========== 8. 省份分布 (按车站) =========='

SELECT
    province,
    COUNT(*) AS station_count
FROM stations
WHERE province IS NOT NULL
GROUP BY province
ORDER BY station_count DESC
LIMIT 20;

\echo ''
\echo '========== 校验完成 =========='
