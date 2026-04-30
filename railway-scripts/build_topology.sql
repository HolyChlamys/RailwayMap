-- ============================================================
-- 铁路拓扑连接表构建脚本
-- 执行时机: Phase 1 数据导入完成后
-- ============================================================

-- Step 1: 清空旧拓扑数据
TRUNCATE TABLE railway_topology;

-- Step 2: 对所有相邻/相交的铁路线段建立拓扑关系
-- 条件: ST_Intersects (端点/线相交) 或 ST_DWithin 50m (地理距离)
-- 使用 a.id < b.id 避免重复
INSERT INTO railway_topology (seg_a, seg_b, is_connected, gap_meters)
SELECT
    a.id AS seg_a,
    b.id AS seg_b,
    ST_Intersects(a.geom, b.geom) AS is_connected,
    COALESCE(
        ST_Distance(a.geom::geography, b.geom::geography),
        0
    ) AS gap_meters
FROM railway_segments a
CROSS JOIN railway_segments b
WHERE a.id < b.id
  AND (
    ST_Intersects(a.geom, b.geom)
    OR ST_DWithin(a.geom::geography, b.geom::geography, 50)
  );

-- Step 3: 输出统计
SELECT
    COUNT(*) AS total_connections,
    COUNT(*) FILTER (WHERE is_connected) AS direct_intersections,
    COUNT(*) FILTER (WHERE NOT is_connected) AS near_misses,
    ROUND(AVG(gap_meters)::numeric, 2) AS avg_gap_meters,
    ROUND(MAX(gap_meters)::numeric, 2) AS max_gap_meters
FROM railway_topology;

-- Step 4: 重建索引 (导入后常规维护)
REINDEX TABLE railway_topology;
ANALYZE railway_topology;
