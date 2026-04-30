-- ============================================================
-- RailwayMap 数据库初始化 DDL
-- PostgreSQL 17 + PostGIS 3.5
-- ============================================================

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- ============================================================
-- 铁路线段表
-- ============================================================
CREATE TABLE IF NOT EXISTS railway_segments (
    id            BIGSERIAL PRIMARY KEY,
    osm_id        BIGINT,
    name          VARCHAR(300),
    railway       VARCHAR(30)  NOT NULL,
    usage         VARCHAR(30),
    category      VARCHAR(30)  NOT NULL DEFAULT 'conventional',
    electrified   VARCHAR(20),
    gauge         INTEGER DEFAULT 1435,
    max_speed     INTEGER,
    track_count   INTEGER DEFAULT 1,
    geom          GEOMETRY(LINESTRING, 4326) NOT NULL,
    length_km     DOUBLE PRECISION,
    source_grid   VARCHAR(20),
    data_quality  VARCHAR(20) DEFAULT 'osm',
    created_at    TIMESTAMP DEFAULT NOW(),
    updated_at    TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rail_seg_geom ON railway_segments USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_rail_seg_category ON railway_segments(category);
CREATE INDEX IF NOT EXISTS idx_rail_seg_railway ON railway_segments(railway);
CREATE INDEX IF NOT EXISTS idx_rail_seg_name ON railway_segments(name);

-- ============================================================
-- 车站表
-- ============================================================
CREATE TABLE IF NOT EXISTS stations (
    id            BIGSERIAL PRIMARY KEY,
    osm_id        BIGINT,
    name          VARCHAR(200) NOT NULL,
    name_pinyin   VARCHAR(300),
    city          VARCHAR(100),
    province      VARCHAR(100),
    railway       VARCHAR(30),
    category      VARCHAR(30)  NOT NULL DEFAULT 'small_passenger',
    passenger     BOOLEAN DEFAULT TRUE,
    freight       BOOLEAN DEFAULT FALSE,
    is_hub        BOOLEAN DEFAULT FALSE,
    geom          GEOMETRY(POINT, 4326) NOT NULL,
    source_grid   VARCHAR(20),
    data_quality  VARCHAR(20) DEFAULT 'osm',
    created_at    TIMESTAMP DEFAULT NOW(),
    updated_at    TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_stat_geom ON stations USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_stat_name ON stations(name);
CREATE INDEX IF NOT EXISTS idx_stat_pinyin ON stations(name_pinyin);
CREATE INDEX IF NOT EXISTS idx_stat_city ON stations(city);
CREATE INDEX IF NOT EXISTS idx_stat_category ON stations(category);

-- ============================================================
-- 铁路拓扑连接表
-- ============================================================
CREATE TABLE IF NOT EXISTS railway_topology (
    id            BIGSERIAL PRIMARY KEY,
    seg_a         BIGINT REFERENCES railway_segments(id),
    seg_b         BIGINT REFERENCES railway_segments(id),
    is_connected  BOOLEAN DEFAULT FALSE,
    gap_meters    DOUBLE PRECISION,
    UNIQUE(seg_a, seg_b)
);

CREATE INDEX IF NOT EXISTS idx_rt_seg_a ON railway_topology(seg_a);
CREATE INDEX IF NOT EXISTS idx_rt_seg_b ON railway_topology(seg_b);

-- ============================================================
-- 车次主表
-- ============================================================
CREATE TABLE IF NOT EXISTS train_routes (
    id              BIGSERIAL PRIMARY KEY,
    train_no        VARCHAR(20)  NOT NULL UNIQUE,
    train_type      VARCHAR(10),
    depart_station  VARCHAR(200),
    arrive_station  VARCHAR(200),
    depart_time     TIME,
    arrive_time     TIME,
    duration_min    INTEGER,
    distance_km     DOUBLE PRECISION,
    running_days    INTEGER DEFAULT 127,
    is_valid        BOOLEAN DEFAULT TRUE,
    data_updated_at TIMESTAMP,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tr_no ON train_routes(train_no);
CREATE INDEX IF NOT EXISTS idx_tr_type ON train_routes(train_type);
CREATE INDEX IF NOT EXISTS idx_tr_valid ON train_routes(is_valid);

-- ============================================================
-- 车次途经站序表
-- ============================================================
CREATE TABLE IF NOT EXISTS train_stops (
    id            BIGSERIAL PRIMARY KEY,
    train_no      VARCHAR(20) NOT NULL
                      REFERENCES train_routes(train_no) ON DELETE CASCADE,
    seq           INTEGER NOT NULL,
    station_name  VARCHAR(200) NOT NULL,
    station_id    BIGINT REFERENCES stations(id),
    arrive_time   TIME,
    depart_time   TIME,
    stay_min      INTEGER,
    distance_km   DOUBLE PRECISION,
    is_terminal   BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_ts_train_no ON train_stops(train_no);
CREATE INDEX IF NOT EXISTS idx_ts_station_id ON train_stops(station_id);
CREATE INDEX IF NOT EXISTS idx_ts_station_name ON train_stops(station_name);

-- ============================================================
-- 车次票价表
-- ============================================================
CREATE TABLE IF NOT EXISTS train_fares (
    id                  BIGSERIAL PRIMARY KEY,
    train_no            VARCHAR(20) NOT NULL
                            REFERENCES train_routes(train_no) ON DELETE CASCADE,
    from_station        VARCHAR(200) NOT NULL,
    to_station          VARCHAR(200) NOT NULL,
    price_business      DECIMAL(8,2),
    price_first         DECIMAL(8,2),
    price_second        DECIMAL(8,2),
    price_soft_sleeper_up   DECIMAL(8,2),
    price_soft_sleeper_down DECIMAL(8,2),
    price_hard_sleeper_up   DECIMAL(8,2),
    price_hard_sleeper_mid  DECIMAL(8,2),
    price_hard_sleeper_down DECIMAL(8,2),
    price_hard_seat     DECIMAL(8,2),
    price_no_seat       DECIMAL(8,2),
    data_updated_at     TIMESTAMP,
    UNIQUE(train_no, from_station, to_station)
);

CREATE INDEX IF NOT EXISTS idx_tf_train_no ON train_fares(train_no);

-- ============================================================
-- 车次与线路段映射表
-- ============================================================
CREATE TABLE IF NOT EXISTS train_segment_mapping (
    id            BIGSERIAL PRIMARY KEY,
    train_no      VARCHAR(20) NOT NULL,
    from_station  VARCHAR(200) NOT NULL,
    to_station    VARCHAR(200) NOT NULL,
    seg_id        BIGINT REFERENCES railway_segments(id),
    seg_order     INTEGER,
    confidence    DOUBLE PRECISION DEFAULT 1.0,
    match_method  VARCHAR(20) DEFAULT 'topology',
    UNIQUE(train_no, from_station, to_station, seg_id)
);

CREATE INDEX IF NOT EXISTS idx_tsm_train ON train_segment_mapping(train_no);
CREATE INDEX IF NOT EXISTS idx_tsm_seg ON train_segment_mapping(seg_id);

-- ============================================================
-- 用户表 (Phase 7 启用, Phase 0 预留)
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id            BIGSERIAL PRIMARY KEY,
    username      VARCHAR(50)  NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email         VARCHAR(100),
    role          VARCHAR(20) DEFAULT 'USER',
    created_at    TIMESTAMP DEFAULT NOW(),
    updated_at    TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 用户收藏 (Phase 7 启用)
-- ============================================================
CREATE TABLE IF NOT EXISTS user_favorites (
    id            BIGSERIAL PRIMARY KEY,
    user_id       BIGINT REFERENCES users(id) ON DELETE CASCADE,
    type          VARCHAR(20) NOT NULL,
    target_id     VARCHAR(200) NOT NULL,
    label         VARCHAR(200),
    data          JSONB,
    created_at    TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, type, target_id)
);

-- ============================================================
-- 搜索历史 (Phase 7 启用)
-- ============================================================
CREATE TABLE IF NOT EXISTS user_search_history (
    id            BIGSERIAL PRIMARY KEY,
    user_id       BIGINT REFERENCES users(id) ON DELETE CASCADE,
    search_type   VARCHAR(20) NOT NULL,
    query_text    VARCHAR(500) NOT NULL,
    created_at    TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ush_user ON user_search_history(user_id, created_at DESC);
