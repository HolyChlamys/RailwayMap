# 中国铁路地图与多次中转路线规划 — 开发计划 v1.0

> **创建日期**: 2026-04-29
> **状态**: 计划阶段
> **原型参考**: `/home/chlamys/CODE/Project/Railwaymap_text` (OpenCode 辅助开发)
> **目标路径**: `/home/chlamys/CODE/Project/RailwayMap`

---

## 版本历史

| 版本 | 日期 | 变更摘要 |
|------|------|----------|
| v1.0 | 2026-04-29 | 初始版本：整合架构设计、原型问题总结、数据管线方案、数据库设计、分阶段实施路线 |

> **版本控制说明**：本文件按语义化版本命名（`v<MAJOR>.<MINOR>`）。MAJOR 变更表示架构方向调整或大阶段切换；MINOR 变更表示细节补充、模块方案修改。每次修改须在版本历史表中新增一行并更新文件名与文档标题。不可原地覆盖旧版本，旧版本保留为 `.md` 归档。

---

## 目录

1. [项目目标](#1-项目目标)
2. [原型项目问题总结](#2-原型项目问题总结)
3. [总体架构设计](#3-总体架构设计)
4. [数据管线设计](#4-数据管线设计)
5. [数据库设计](#5-数据库设计)
6. [后端模块设计](#6-后端模块设计)
7. [前端模块设计](#7-前端模块设计)
8. [搜索系统设计](#8-搜索系统设计)
9. [车次路线匹配算法](#9-车次路线匹配算法)
10. [多次中转换乘规划](#10-多次中转换乘规划)
11. [分阶段实施路线](#11-分阶段实施路线)
12. [待确认问题](#12-待确认问题)

---

## 1. 项目目标

### 1.1 基础目标：中国铁路在线地图

- 以交互式地图呈现全国铁路线路与车站
- 支持车站搜索、车次搜索、站站查询
- 车次经行路线在地图上高亮显示
- 矢量瓦片渲染，保证流畅的缩放与平移体验

### 1.2 创新目标：多次中转路线规划

- 12306 仅支持一次中转，本系统支持用户自定义中转次数（2-4 次）
- 将超长途旅程拆分为夜间乘车 + 白天城市游的组合方案
- 中转等待时间优化为可游览时段
- 提供多种偏好排序（最少时间 / 最少换乘 / 夜行昼游 / 最低票价）

---

## 2. 原型项目问题总结

原型项目 (`Railwaymap_text`) 验证了核心技术可行性，同时暴露了 5 个关键问题：

### 2.1 问题一：数据获取——分片缺陷

**现象**：
- Overpass API 单次请求范围过大导致超时/被限流
- 分片顺序杂乱（手动定义 12 个区域，区域间存在缝隙）
- 成都、西藏、海南南部、山东半岛等边界处数据缺失

**根因**：手动定义的矩形分片区域未系统化，缺乏网格化覆盖校验，且未对照中国实际陆地边界剔除无效海域网格。

**解决方案**：见 [4.2 网格分割策略](#42-网格分割策略)。

### 2.2 问题二：底图问题

**现象**：
- 天地图底图观感陈旧、标注细节过多（干扰铁路主题）
- 坐标系偏差导致缩放时铁路线与底图之间短暂偏移（已通过 Canvas 渲染 + `preferCanvas: true` 修复）
- 天地图 `vec_w` + `cva_w` 两层加载速度一般

**根因**：天地图为通用底图，非为铁路专题优化；CGCS2000 与 WGS84 虽近似但图层合成时机存在时序差。

**解决方案**：见 [7.1 底图方案](#71-底图方案)。

### 2.3 问题三：搜索功能需提前规划

**现象**：
- 当前仅实现了基本的关键词 ILIKE 模糊匹配
- 无拼音搜索、无车次前缀级联、无城市→车站联想
- 搜索输入框作为 Leaflet 控件内联 DOM，可维护性差

**根因**：原型阶段以验证技术可行性为主，未对搜索交互做系统设计。

**解决方案**：见 [8. 搜索系统设计](#8-搜索系统设计)。

### 2.4 问题四：车次经行段匹配不准确

**现象**：
- 车次 A→B→C→D 的路线高亮时，相邻站间的铁路线段匹配"会多识别"（匹配了不相关的线路）
- 部分路段因数据不完整导致高亮线路断续

**根因**：
- `handle_train_route` 对每对相邻车站执行 `ST_DWithin(geom, line, 10000m)` + `ST_Expand`，10km 阈值过大，会匹配到邻近但不相关的铁路线
- 未考虑铁路线的**方向连通性**——只按空间距离匹配，不按拓扑关系判断 A→B 对应的线段是否实际连通
- 部分铁路线在 OSM 中确实缺失

**解决方案**：见 [9. 车次路线匹配算法](#9-车次路线匹配算法)。

### 2.5 问题五：数据库批量导入失败

**现象**：
- `import_geojson.py` 通过 `cat tmpfile | docker compose exec psql` 管道导入时偶发失败
- 155MB 的 GeoJSON 加载到内存后构建 INSERT 字符串，内存压力大
- SQL 临时文件大小不可控，失败时无进度恢复机制
- 超时无日志反馈，排查困难

**根因**：单管道 + 全量事务模式，缺乏分批提交、断点续传和进度日志机制。

**解决方案**：见 [4.3 数据导入策略](#43-数据导入策略) 和 [11. 分阶段实施路线](#11-分阶段实施路线)。

---

## 3. 总体架构设计

### 3.1 技术选型（与原型对比）

| 层面 | 原型 (Railwaymap_text) | 新版 (RailwayMap) | 变更理由 |
|------|----------------------|-------------------|----------|
| **前端框架** | Vanilla JS 无框架 | **Vue 3** + TypeScript | 组件化、类型安全、可维护 |
| **地图引擎** | Leaflet + VectorGrid | **MapLibre GL JS** | 原生 WebGL、矢量瓦片一等公民、社区活跃 |
| **UI 框架** | 无 | **Tailwind CSS** + Naive UI | 快速开发、现代外观 |
| **底图** | 天地图 WMTS | **MapTiler/自定义底图** 候选方案（待验证） | 更现代、可定制、减少标注干扰 |
| **HTTP Server** | Python stdlib | **Spring Boot 3.3.5** | 企业级、Maven 多模块、JPA/JTS 集成 |
| **ORM** | 无（手写 SQL） | **MyBatis-Plus** | 减少样板代码，保留 SQL 控制力 |
| **瓦片服务** | PostGIS ST_AsMVT 实时生成 | PostGIS ST_AsMVT + **PMTiles 预生成**（备选） | 低频数据适合预生成，降低数据库负载 |
| **数据导入** | Python 脚本 + psql 管道 | **Spring Batch** + 分批事务 | 断点续传、日志追踪、事务控制 |
| **前端构建** | 无 | **Vite** | 现代构建工具链 |
| **数据库** | PostgreSQL 16 + PostGIS 3.4 | **保持不变** | GIS 金标准 |
| **地图坐标系** | GCJ-02 (天地图) | **WGS-84** 为主，GCJ-02 转换函数备选 | OSM 数据天然 WGS-84 |

### 3.2 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      浏览器                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Vue 3 SPA (Vite 构建)                               │   │
│  │  ├─ MapLibre GL JS    地图渲染 (WebGL)               │   │
│  │  ├─ Tailwind + Naive UI   UI 组件                   │   │
│  │  ├─ Pinia              全局状态管理                  │   │
│  │  └─ TypeScript         类型安全                      │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────┬───────────────────────────────────────────────┘
              │ HTTP/HTTPS
              ▼
┌─────────────────────────────────────────────────────────────┐
│  Nginx (反向代理 + 静态资源 + SSL)                           │
│  ├─ /api/*  → localhost:10010 (Spring Boot)                 │
│  ├─ /tiles/* → localhost:10010 或 PMTiles CDN               │
│  └─ /*      → Vue 静态文件                                  │
└─────────────┬───────────────────────────────────────────────┘
              │
    ┌─────────┼─────────┐
    ▼         ▼         ▼
┌────────┐ ┌──────┐ ┌──────────┐
│Spring  │ │PostgreSQL│ │Redis    │
│Boot    │ │+PostGIS │ │(缓存)   │
│:10010  │ │:5432   │ │:6379    │
└────────┘ └──────┘ └──────────┘
```

### 3.3 Maven 多模块结构

```
railway-map/
├── pom.xml                        # 父 POM (Spring Boot 3.3.5, Java 21)
├── railway-common/                # 公共模块
│   ├── entity/                    # JPA 实体 / MyBatis 实体
│   ├── dto/                       # 请求/响应 DTO
│   ├── enums/                     # 枚举 (RailwayType, StationLevel...)
│   ├── util/                      # 工具类 (TileUtils, GeoUtils, PinyinUtils)
│   └── config/                    # 共享配置
├── railway-data/                  # 数据访问层
│   ├── mapper/                    # MyBatis Mapper 接口
│   ├── repository/                # Spring Data JPA Repository (备选)
│   └── resources/mapper/          # MyBatis XML SQL
├── railway-service/               # 业务逻辑层
│   ├── map/                       # 地图服务 (矢量瓦片生成)
│   ├── search/                    # 搜索服务 (车站/车次/拼音)
│   ├── route/                     # 路线匹配服务 (车次经行段)
│   ├── transfer/                  # 多次中转换乘算法
│   └── sync/                      # 数据同步服务
├── railway-api/                    # Web 层
│   ├── controller/                # REST 控制器
│   ├── config/                    # Web 配置 (CORS, MVC)
│   └── RailwayMapApplication.java # 启动类
├── railway-batch/                  # 批处理模块
│   ├── job/                       # Spring Batch Job 定义
│   ├── reader/                    # GeoJSON / OSM PBF 读取器
│   ├── processor/                 # 数据清洗/转换
│   └── writer/                    # 批量入库 Writer
├── railway-scripts/                # 辅助脚本 (Python)
│   ├── grid_splitter.py           # 网格分割与逐格抓取
│   ├── schedule_crawler.py        # 时刻表爬虫
│   └── data_validator.py          # 数据完整性校验
└── railway-frontend/               # Vue 3 前端 (独立目录或子模块)
    ├── src/
    │   ├── components/            # 组件
    │   ├── views/                 # 页面
    │   ├── stores/                # Pinia stores
    │   ├── services/              # API 封装
    │   ├── utils/                 # 工具方法
    │   └── assets/                # 静态资源
    ├── vite.config.ts
    └── package.json
```

---

## 4. 数据管线设计

### 4.1 数据源策略

| 数据 | 来源 | 更新频率 | 获取方式 |
|------|------|----------|----------|
| 铁路线路几何 | OpenStreetMap (Overpass API) | 每季度 | 网格分割 + 逐格抓取 |
| 车站位置 | OpenStreetMap (Overpass API) | 每季度 | 同上 |
| 列车时刻表 | liecheba.com / 12306 接口 | 每日 | Python 爬虫按车次抓取 |
| 中国陆地边界 | OSM 或国家基础地理信息中心 | 一次性 | 用于网格过滤 |
| 底图瓦片 | MapTiler / 自定义 | - | 商业 API 或自建服务 |
| 城市旅游信息 | 高德/马蜂窝 API | 按需 | API 调用 + 缓存 |

### 4.2 网格分割策略

**代替原型的手动区域定义**，采用系统化的渔网 (Fishnet) 分割法：

```
算法: GridSplitter

输入:
  - 中国陆地边界多边形 (GeoJSON, WGS-84)
  - 网格边长 d (默认 1.0°，约 110km)
  - 重叠宽度 overlap (默认 0.05°，约 5.5km)

步骤:
  1. 计算中国陆地边界的 bbox:
     lon: [73.5°, 135.14°], lat: [18.0°, 53.56°]
  2. 以 d 为步长生成 m × n 的网格矩阵
  3. 对每个网格:
     a. 将网格扩展 overlap (四边各加 0.05°)
     b. 用 Shapely/JTS 判断扩展网格与中国边界多边形是否相交
     c. 不相交 → 跳过 (海域)
     d. 相交 → 加入待抓取队列, 按先行后列或 S形曲线排序
  4. 按排序后的队列顺序执行 Overpass API 查询
  5. 每格抓取结果去重合并

输出:
  - 抓取队列文件 (grid_queue.json)
  - 每格单独 GeoJSON (grid_{row}_{col}.geojson)
  - 合并后全量 GeoJSON
```

**关键约束**：
- 使用真实的中国陆地边界多边形（含海岸线、岛屿），而非 `china` 全量 bbox
- 网格间必须有 `overlap` 重叠（解决原型中边界缝隙导致数据缺失的问题）
- 每次请求范围控制在 1°×1° 以内（覆盖面积约 12,000 km²），避免 Overpass 超时
- 请求间间隔 ≥ 5 秒，避免 IP 限流
- 网格遍历顺序按 S 形曲线（蛇形），最小化 Overpass 负载波动

**Python 伪代码示例**：

```python
import shapely.geometry as geom
import shapely.ops as ops

def generate_grid(china_boundary: geom.Polygon, step: float = 1.0, overlap: float = 0.05):
    minx, miny, maxx, maxy = china_boundary.bounds
    queue = []

    row = 0
    y = miny
    while y < maxy:
        col = 0
        x = minx
        while x < maxx:
            cell = geom.box(x - overlap, y - overlap,
                            x + step + overlap, y + step + overlap)
            if cell.intersects(china_boundary):
                queue.append({
                    "id": f"r{row}_c{col}",
                    "bbox": f"{cell.bounds[1]},{cell.bounds[0]},{cell.bounds[3]},{cell.bounds[2]}",
                    "row": row, "col": col
                })
            col += 1
            x += step
        row += 1
        y += step

    # 蛇形排序: 偶数行正向, 奇数行反向
    queue.sort(key=lambda g: (g["row"], g["col"] if g["row"] % 2 == 0 else -g["col"]))
    return queue
```

### 4.3 数据导入策略

**代替原型的单管道全量导入**：

```
导入流程 (Spring Batch Job):

[Step 1] 文件发现
  ─ 扫描 frontend/data/ 下所有 grid_*.geojson
  ─ 生成待处理文件列表

[Step 2] 逐文件导入 (每文件一个事务)
  ─ ChunkedReader: 每次读取 1000 个 feature
  ─ Processor: 清洗名称、验证坐标、WKT 转换
  ─ BatchWriter: 批量 INSERT (每 1000 条提交一次)
  ─ 每批次完成后打印日志: "[2/42] grid_r3_c5.geojson: 850/3240 条 (26%)"

[Step 3] 去重与索引重建
  ─ 合并同名但坐标接近的铁路线
  ─ REINDEX railways, stations
  ─ ANALYZE railways, stations

[Step 4] 完整性校验
  ─ SELECT count(*) vs 预期数
  ─ 随机抽样 100 条, ST_IsValid 检查
  ─ 各区域密度热力图输出
```

**日志规范**：
```
[2026-04-29 12:00:01] [IMPORT] 开始导入, 共 48 个网格文件
[2026-04-29 12:00:05] [IMPORT] [1/48] grid_r0_c2.geojson: 1000/3240 (30%)
[2026-04-29 12:00:08] [IMPORT] [1/48] grid_r0_c2.geojson: 2000/3240 (61%)
[2026-04-29 12:00:11] [IMPORT] [1/48] grid_r0_c2.geojson: 3240/3240 (100%) ✓
[2026-04-29 12:00:12] [IMPORT] [2/48] grid_r0_c4.geojson: 1000/5800 (17%)
...
[2026-04-29 12:15:30] [IMPORT] 导入完成: 铁路线 452103 条, 车站 4128 个, 耗时 929s
[2026-04-29 12:15:31] [IMPORT] 跳过 2 个失败网格: grid_r8_c12, grid_r15_c3 → 查看 import_errors.log
```

### 4.4 时刻表数据采集

**代替原型的单次手动爬取**：

- 爬虫按铁路局管辖范围分批爬取车次列表
- 每日增量更新（仅爬取有变更的车次）
- 数据存入 `train_routes` 表（含 `updated_at` 字段判断新鲜度）
- 3 天未更新的车次自动过期，前端标记"数据可能过期"

---

## 5. 数据库设计

### 5.1 核心表

```sql
-- ============================================================
-- 空间数据表
-- ============================================================

-- 铁路线路段表（注意：是"段"而非"线"）
CREATE TABLE railway_segments (
    id          BIGSERIAL PRIMARY KEY,
    osm_id      BIGINT,                        -- OSM way ID
    name        VARCHAR(300),                  -- 线路名称 (如 "京沪线")
    railway     VARCHAR(30)  NOT NULL,         -- rail / light_rail / subway / high_speed
    usage       VARCHAR(30),                   -- main / branch / industrial
    electrified VARCHAR(20),                   -- yes / no
    gauge       INTEGER DEFAULT 1435,          -- 轨距 (mm)
    max_speed   INTEGER,                       -- 设计最高时速 (km/h)
    geom        GEOMETRY(LINESTRING, 4326) NOT NULL,
    length_km   DOUBLE PRECISION,              -- 长度
    source_grid VARCHAR(20),                   -- 来源网格 ID
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_rail_seg_geom ON railway_segments USING GIST(geom);
CREATE INDEX idx_rail_seg_railway ON railway_segments(railway);
CREATE INDEX idx_rail_seg_name ON railway_segments(name);

-- 车站表
CREATE TABLE stations (
    id          BIGSERIAL PRIMARY KEY,
    osm_id      BIGINT,
    name        VARCHAR(200) NOT NULL,         -- 站名全称 (如 "北京南")
    name_pinyin VARCHAR(300),                  -- 拼音 (如 "beijingnan")
    name_short  VARCHAR(100),                  -- 简称 (如 "北京南")
    city        VARCHAR(100),                  -- 所属城市 (如 "北京市")
    province    VARCHAR(100),                  -- 所属省份
    railway     VARCHAR(30),                   -- station / halt / tram_stop
    level       VARCHAR(20),                   -- 车站等级 (自定义: major/large/medium/small)
    passenger   BOOLEAN DEFAULT TRUE,          -- 是否办理客运
    geom        GEOMETRY(POINT, 4326) NOT NULL,
    source_grid VARCHAR(20),
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_stations_geom ON stations USING GIST(geom);
CREATE INDEX idx_stations_name ON stations(name);
CREATE INDEX idx_stations_pinyin ON stations(name_pinyin);
CREATE INDEX idx_stations_city ON stations(city);

-- 同城车站映射表
CREATE TABLE station_city_map (
    id          BIGSERIAL PRIMARY KEY,
    station_id  BIGINT REFERENCES stations(id),
    city_name   VARCHAR(100) NOT NULL,         -- 城市名
    is_main     BOOLEAN DEFAULT FALSE,         -- 是否为主要客运站
    transfer_time_min INTEGER DEFAULT 60,      -- 同城异站换乘建议时间 (分钟)
    transfer_method VARCHAR(100)               -- 建议换乘方式 (地铁/公交/出租车)
);
CREATE INDEX idx_scm_city ON station_city_map(city_name);

-- ============================================================
-- 时刻表与车次表
-- ============================================================

-- 车次主表
CREATE TABLE train_routes (
    id              BIGSERIAL PRIMARY KEY,
    train_no        VARCHAR(20)  NOT NULL UNIQUE,  -- 如 "G1", "D301"
    train_type      VARCHAR(10),                   -- G/D/C/Z/T/K/Y/S
    depart_station  VARCHAR(200),                  -- 始发站名
    arrive_station  VARCHAR(200),                  -- 终到站名
    depart_time     TIME,                          -- 始发时间
    arrive_time     TIME,                          -- 终到时间
    duration_min    INTEGER,                       -- 全程耗时 (分钟)
    running_days    INTEGER DEFAULT 127,           -- 开行日期 (bitmask, 1=Mon..7=Sun, 127=每天)
    is_valid        BOOLEAN DEFAULT TRUE,          -- 当前是否有效
    data_updated_at TIMESTAMP,                     -- 数据更新时间
    created_at      TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_tr_no ON train_routes(train_no);
CREATE INDEX idx_tr_type ON train_routes(train_type);

-- 车次途经站序表
CREATE TABLE train_stops (
    id          BIGSERIAL PRIMARY KEY,
    train_no    VARCHAR(20)  NOT NULL REFERENCES train_routes(train_no) ON DELETE CASCADE,
    seq         INTEGER NOT NULL,                 -- 站序 (1, 2, 3...)
    station_name VARCHAR(200) NOT NULL,           -- 站名
    station_id  BIGINT REFERENCES stations(id),   -- 关联车站空间数据
    arrive_time TIME,                             -- 到站时间
    depart_time TIME,                             -- 发车时间
    stay_min    INTEGER,                          -- 停站时间 (分钟)
    distance_km DOUBLE PRECISION,                 -- 距始发站里程
    is_terminal BOOLEAN DEFAULT FALSE             -- 是否为终点站
);
CREATE INDEX idx_ts_train_no ON train_stops(train_no);
CREATE INDEX idx_ts_station ON train_stops(station_name);

-- ============================================================
-- 车次与线路段的映射表（解决原型问题四）
-- ============================================================
CREATE TABLE train_segment_mapping (
    id          BIGSERIAL PRIMARY KEY,
    train_no    VARCHAR(20) NOT NULL,
    from_station VARCHAR(200) NOT NULL,            -- 出发站名
    to_station  VARCHAR(200) NOT NULL,             -- 到达站名
    seg_id      BIGINT REFERENCES railway_segments(id), -- 匹配的铁路线段
    seg_order   INTEGER,                           -- 在路段中的顺序
    confidence  DOUBLE PRECISION DEFAULT 1.0,      -- 匹配置信度 (0-1)
    UNIQUE(train_no, from_station, to_station, seg_id)
);
CREATE INDEX idx_tsm_train ON train_segment_mapping(train_no);
CREATE INDEX idx_tsm_seg ON train_segment_mapping(seg_id);
```

### 5.2 设计说明

**为什么把 `railways` 改名为 `railway_segments`**：
原型的 `railways` 表存储的是 OSM 的 way——一段铁路几何线。实际中一条"京沪线"由数百个 way 组成。明确命名为 segment 避免概念混淆。

**为什么新增 `train_stops` 表**：
原型用 JSONB 存储途经站，虽然灵活但不支持高效的空间查询。拆分为独立表后可以 JOIN `stations` 表直接获取坐标，消除前端 N+1 查询。

**为什么新增 `train_segment_mapping` 表**：
这是解决问题四的核心——预计算每对相邻车站对应的铁路线段。详细算法见 [第 9 节](#9-车次路线匹配算法)。

### 5.3 可能需要扩展的数据库字段

以下问题请确认，以便补充数据库设计：

| # | 问题 | 影响 |
|---|------|------|
| 1 | 是否需要存储票价信息？（二等座/硬卧/软卧等） | 影响 `train_routes` 表，需增加票价相关字段 |
| 2 | 是否需要存储车次的实时余票信息？ | 需要对接 12306 实时接口，设计缓存策略 |
| 3 | 中转站城市游信息由谁维护？（爬取 vs 手动录入） | 如果爬取，需增加 `city_attractions` 表 |
| 4 | 是否需要用户系统？（收藏路线、保存查询历史） | 影响整体架构，需增加 `users` 表与认证模块 |
| 5 | 是否考虑国际列车？（中老铁路、中欧班列等） | 边界数据需扩展至邻国 |
| 6 | 是否需要货运线路与客运线路的区分展示？ | `railway_segments` 已有 `usage` 字段，但 OSM 数据不完整 |

---

## 6. 后端模块设计

### 6.1 模块依赖图

```
railway-api (启动模块)
  ├── railway-service
  │     ├── railway-data
  │     │     └── railway-common
  │     └── railway-common
  └── railway-batch (Spring Batch, 可选启动)
        ├── railway-service
        └── railway-data
```

### 6.2 各模块职责

#### railway-common

```
entity/
  RailwaySegment.java    (Lombok @Data, 对应 railway_segments 表)
  Station.java           (Lombok @Data, 对应 stations 表)
  TrainRoute.java        (对应 train_routes 表)
  TrainStop.java         (对应 train_stops 表)
  TrainSegmentMapping.java (对应 train_segment_mapping 表)
dto/
  StationSearchRequest.java   (q, city, limit, offset)
  StationSearchResult.java    (id, name, city, lon, lat, level)
  TrainSearchRequest.java     (q, type, limit)
  TrainSearchResult.java      (train_no, depart_station, arrive_station, type, duration_min)
  TrainRouteResponse.java     (train_no, stops[], segments GeoJSON)
  TransferRequest.java        (from, to, date, max_transfers, preference)
  TransferResult.java         (routes[], total_time, total_price)
enums/
  RailwayType.java       (RAIL, LIGHT_RAIL, SUBWAY)
  StationLevel.java      (MAJOR, LARGE, MEDIUM, SMALL)
  TrainType.java         (G, D, C, Z, T, K)
  TransferPreference.java (LEAST_TIME, LEAST_TRANSFER, NIGHT_TRAIN_DAY_TOUR, LEAST_PRICE)
util/
  TileUtils.java         (z/x/y ↔ bbox)
  GeoUtils.java          (GCJ-02 ↔ WGS-84, 距离计算, 坐标格式化)
  PinyinUtils.java       (中文 → 拼音/首字母, 用于搜索)
config/
  SpatialConfig.java     (JTS GeometryFactory Bean)
```

#### railway-data

```
mapper/
  RailwaySegmentMapper.java  (BaseMapper + 自定义空间查询)
  StationMapper.java         (BaseMapper + 搜索 + 空间查询)
  TrainRouteMapper.java      (BaseMapper + 车次搜索)
  TrainStopMapper.java       (BaseMapper)
  TrainSegmentMappingMapper.java (BaseMapper)
resources/mapper/
  RailwaySegmentMapper.xml   (ST_AsMVT 瓦片查询等)
  StationMapper.xml          (ST_AsMVT + ILIKE + 拼音搜索)
  TrainRouteMapper.xml       (车次搜索)
```

#### railway-service

```
map/
  TileService.java           (瓦片业务: z/x/y → PBF byte[])
  MapStyleService.java       (地图样式配置)
search/
  StationSearchService.java  (车站搜索: 关键词/拼音/城市)
  TrainSearchService.java    (车次搜索: 前缀匹配/级联)
route/
  RouteMatchingService.java  (车次经行段匹配引擎) [★核心]
  RouteSimplificationService.java (线路抽稀, 减少传输数据)
transfer/
  TransferGraphBuilder.java  (铁路图构建: 车站节点+列车边)
  TransferSearchService.java (多次中转换乘算法) [★核心]
  TransferRankingService.java (方案排序与评分)
sync/
  DataSyncService.java       (数据同步调度)
  ScheduleCrawlerService.java (时刻表爬虫服务)
```

#### railway-api

```
controller/
  TileController.java        (GET /api/tiles/{layer}/{z}/{x}/{y}.pbf)
  StationController.java     (GET /api/stations/search)
  TrainController.java       (GET /api/trains/search, GET /api/trains/route)
  TransferController.java    (POST /api/transfer/search)
  SyncController.java        (POST /api/sync/trigger)
  HealthController.java      (GET /api/health)
config/
  CorsConfig.java            (CORS 配置)
  WebMvcConfig.java          (拦截器/序列化配置)
  JacksonConfig.java         (JSON 序列化: GeoJSON/Long 精度)
```

#### railway-batch

```
job/
  GridImportJob.java         (Spring Batch Job 定义)
  ScheduleImportJob.java     (时刻表导入 Job)
reader/
  GeoJsonItemReader.java     (分块读取 GeoJSON)
  GridQueueReader.java       (读取网格队列文件)
processor/
  RailwaySegmentProcessor.java (数据清洗: 名称标准化、坐标验证)
  StationProcessor.java       (车站数据清洗)
  TrainScheduleProcessor.java (时刻表数据解析)
writer/
  JdbcBatchItemWriter.java   (Spring Batch 内置) + 自定义 PostGIS 写入
listener/
  ImportProgressListener.java (进度日志 + 失败网格记录)
```

---

## 7. 前端模块设计

### 7.1 底图方案

**候选方案对比**：

| 方案 | 优点 | 缺点 | 待验证 |
|------|------|------|--------|
| **MapTiler Streets** | 专业、现代、可定制样式、免费额度 | 海外服务，国内加载速度未知 | ✓ 需测加载速度 |
| **Mapbox Streets** | 最成熟、GL JS 原生支持 | 需绑信用卡、国内受限 | 不推荐 |
| **自建底图 (OSM + Maputnik)** | 完全可控、铁路主题定制 | 开发成本高（原型阶段暂不投入） | 远期考虑 |
| **高德地图 GCJ-02** | 国内最快、免费 | 需坐标转换、风格不可定制 | 备选 |
| **天地图 + 自定义样式覆盖** | 已有 Key、国内快 | 坐标系问题、样式陈旧 | 备选 |

**推荐方案**：优先验证 **MapTiler Streets**（英文为主但可改为中文标注）+ OSM 中国底图社区瓦片作为备选。在 `vue-frontend` 中统一封装地图组件，方便切换底图源。

**验证方法**：
1. 注册 MapTiler 免费账号，获取 Key
2. 在 MapLibre GL JS 中加载 MapTiler Streets 样式
3. 测试国内城市（北京/上海/成都/拉萨）各级缩放下的加载速度
4. 对比天地图底图，评估观感与性能差异

### 7.2 前端目录结构

```
railway-frontend/
├── src/
│   ├── components/
│   │   ├── map/
│   │   │   ├── MapContainer.vue       # 地图容器 (核心)
│   │   │   ├── RailwayLayer.vue       # 铁路线矢量瓦片图层
│   │   │   ├── StationLayer.vue       # 车站图层
│   │   │   ├── TrainRouteLayer.vue    # 车次路线高亮图层
│   │   │   └── MapControls.vue        # 地图控件 (缩放/图层切换)
│   │   ├── search/
│   │   │   ├── SearchPanel.vue        # 搜索面板 (集成入口)
│   │   │   ├── StationSearch.vue      # 车站搜索组件
│   │   │   ├── TrainSearch.vue        # 车次搜索组件
│   │   │   └── SearchSuggestions.vue  # 搜索联想下拉
│   │   ├── route/
│   │   │   ├── RouteTimeline.vue      # 车次经行时间线
│   │   │   ├── RouteInfoCard.vue      # 车次信息卡片
│   │   │   └── StationPopup.vue       # 车站弹出详情
│   │   ├── transfer/
│   │   │   ├── TransferSearchForm.vue  # 中转换乘搜索表单
│   │   │   ├── TransferResultList.vue  # 换乘方案列表
│   │   │   └── TransferTimeline.vue    # 多段车程时间线
│   │   └── common/
│   │       ├── AppHeader.vue           # 顶部导航
│   │       ├── LoadingSpinner.vue      # 加载指示
│   │       └── ErrorBoundary.vue       # 错误边界
│   ├── views/
│   │   ├── MapView.vue                 # 主地图页
│   │   └── TransferView.vue            # 中转换乘页
│   ├── stores/
│   │   ├── mapStore.ts                 # 地图状态 (center, zoom, layers)
│   │   ├── searchStore.ts              # 搜索状态 (query, results, history)
│   │   ├── trainStore.ts               # 车次状态 (selected train, route data)
│   │   └── transferStore.ts            # 换乘状态 (search params, results)
│   ├── services/
│   │   ├── api.ts                      # axios 实例 + 拦截器
│   │   ├── tileService.ts             # 矢量瓦片请求封装
│   │   ├── stationService.ts          # 车站 API 封装
│   │   ├── trainService.ts            # 车次 API 封装
│   │   └── transferService.ts         # 换乘 API 封装
│   ├── types/
│   │   ├── station.ts                 # Station, StationSearchResult 等
│   │   ├── train.ts                   # TrainRoute, TrainStop 等
│   │   ├── map.ts                     # TileCoord, BBox 等
│   │   └── transfer.ts               # TransferRequest, TransferResult 等
│   ├── utils/
│   │   ├── geo.ts                     # 坐标转换 (WGS-84 ↔ GCJ-02)
│   │   ├── format.ts                  # 时间/距离/车次格式化
│   │   └── debounce.ts               # 防抖/节流
│   ├── assets/
│   │   └── styles/
│   │       ├── main.css               # Tailwind + 全局样式
│   │       └── map.css                # 地图覆盖样式
│   ├── router/
│   │   └── index.ts                   # Vue Router 配置
│   ├── App.vue
│   └── main.ts
├── public/
│   └── favicon.ico
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

### 7.3 地图组件核心逻辑

```typescript
// MapContainer.vue 核心流程

import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

// 1. 初始化 MapLibre 实例
const map = new maplibregl.Map({
  container: 'map',
  style: 'https://api.maptiler.com/maps/streets-v2/style.json?key=YOUR_KEY', // 或自定义 style.json
  center: [108.5, 35.5],   // 中国中心
  zoom: 5,
  minZoom: 4,
  maxZoom: 18
});

// 2. 添加铁路线矢量瓦片源
map.on('load', () => {
  map.addSource('railways', {
    type: 'vector',
    tiles: ['/api/tiles/railways/{z}/{x}/{y}.pbf'],
    minzoom: 6,
    maxzoom: 18
  });

  // 地铁
  map.addSource('subways', {
    type: 'vector',
    tiles: ['/api/tiles/subways/{z}/{x}/{y}.pbf'],
    minzoom: 10,
    maxzoom: 18
  });

  // 3. 添加铁路线图层 (MapLibre style expression)
  map.addLayer({
    id: 'railways-layer',
    type: 'line',
    source: 'railways',
    'source-layer': 'railways',
    paint: {
      'line-color': [
        'match', ['get', 'railway'],
        'rail', '#e74c3c',
        'light_rail', '#f39c12',
        'subway', '#3498db',
        '#e74c3c'
      ],
      'line-width': [
        'interpolate', ['linear'], ['zoom'],
        6, 1.0,
        10, 2.0,
        14, 3.5
      ],
      'line-opacity': 0.85
    }
  });
  // ... 车站图层 + 地铁图层 同理
});

// 4. 车次路线高亮 (调用时动态添加)
function highlightTrainRoute(geojson: GeoJSON.FeatureCollection) {
  // 移除旧高亮
  if (map.getSource('train-highlight')) {
    map.removeLayer('train-highlight-layer');
    map.removeSource('train-highlight');
  }
  map.addSource('train-highlight', { type: 'geojson', data: geojson });
  map.addLayer({
    id: 'train-highlight-layer',
    type: 'line',
    source: 'train-highlight',
    paint: {
      'line-color': '#ff8c00',
      'line-width': 5,
      'line-opacity': 0.9
    }
  });
}
```

---

## 8. 搜索系统设计

### 8.1 搜索架构

```
用户输入 → 前端防抖 (250ms) → API 请求 → 后端 Service → PostgreSQL 查询 → JSON 返回 → 前端下拉渲染
```

### 8.2 车站搜索

**功能规格**：

| 输入类型 | 示例 | 预期结果 |
|----------|------|----------|
| 中文全称 | "北京南" | 精确匹配 → 北京南 |
| 中文简称 | "北京" | 前缀匹配 → 北京/北京南/北京西/北京北/北京丰台 |
| 拼音全拼 | "beijingnan" | 拼音匹配 → 北京南 |
| 拼音首字母 | "bjn" | 首字母匹配 → 北京南/北京西/北京北 |
| 城市名 | "南京" | 返回南京市所有车站 |

**SQL 实现**（PostgreSQL `stationMapper.xml`）：

```sql
SELECT id, name, city, ST_X(geom) AS lon, ST_Y(geom) AS lat, level
FROM stations
WHERE
    name ILIKE '%' || #{keyword} || '%'     -- 中文模糊
    OR name_pinyin ILIKE '%' || #{keyword} || '%'  -- 拼音
    OR name_pinyin LIKE REPLACE(#{keyword}, ' ', '') || '%'  -- 首字母
    OR city = #{keyword}                     -- 精确城市
ORDER BY
    CASE WHEN name = #{keyword} THEN 0       -- 精确匹配最前
         WHEN name ILIKE #{keyword} || '%' THEN 1  -- 前缀匹配
         WHEN city = #{keyword} THEN 2       -- 城市匹配
         ELSE 3
    END,
    level                                 -- 同优先级按等级排序
LIMIT #{limit}
```

**关键规则**：
- 搜索"北京"时不要列出"北京东站"之外的无关站名（即不要自动追加"站"字做后缀匹配）
- 城市搜索时返回该城市的所有车站，按等级排序（major > large > medium > small）

### 8.3 车次搜索

**功能规格**：

| 输入 | 预期结果 |
|------|----------|
| "G" | G1, G2, G3...G9999（前缀匹配, 按车次号排序） |
| "G1" | G1, G10, G100...G199, G1000+ |
| "D3" | D3, D30-D39, D300-D399... |
| "北京" | 所有以北京为始发站或终到站的车次 |

**SQL 实现**：

```sql
SELECT train_no, train_type, depart_station, arrive_station,
       depart_time, arrive_time, duration_min
FROM train_routes
WHERE
    train_no ILIKE #{keyword} || '%'           -- 车次号前缀
    OR depart_station ILIKE '%' || #{keyword} || '%'  -- 始发站包含
    OR arrive_station ILIKE '%' || #{keyword} || '%'  -- 终到站包含
ORDER BY
    CASE WHEN train_no ILIKE #{keyword} || '%' THEN 0 ELSE 1 END,
    train_no
LIMIT #{limit}
```

### 8.4 拼音索引生成

在 `import_geojson.py` 或 Spring Batch 导入时，调用 `pinyin4j` 或 `tinypinyin` 为每个车站生成 `name_pinyin` 字段：

```java
// PinyinUtils.java
import net.sourceforge.pinyin4j.PinyinHelper;

public static String toPinyin(String chinese) {
    // 北京南 → "beijingnan"
    StringBuilder sb = new StringBuilder();
    for (char c : chinese.toCharArray()) {
        String[] pinyin = PinyinHelper.toHanyuPinyinStringArray(c);
        if (pinyin != null) {
            sb.append(pinyin[0].replaceAll("\\d", ""));
        }
    }
    return sb.toString().toLowerCase();
}
```

### 8.5 前端搜索组件交互

```
SearchPanel.vue (顶部搜索栏)
├── Tab: "车站" | "车次" | "换乘"
│
├── Tab=车站:
│   └── StationSearch.vue
│       ├── <n-auto-complete> 输入框
│       ├── 防抖 250ms
│       ├── 下拉项: [站名] [城市] [等级标签]
│       └── 选中 → 地图飞至车站 + 弹出详情
│
├── Tab=车次:
│   └── TrainSearch.vue
│       ├── <n-auto-complete> 输入框
│       ├── 防抖 300ms
│       ├── 下拉项: [车次号] [类型标签] [始发→终到] [耗时]
│       └── 选中 → 地图高亮路线 + 侧栏显示经停时间线
│
└── Tab=换乘:
    └── TransferSearchForm.vue
        ├── 出发站 (搜索选择)
        ├── 到达站 (搜索选择)
        ├── 出发日期
        ├── 最大换乘次数 (1-4)
        ├── 偏好 (最少时间/最少换乘/夜行昼游/最低票价)
        └── [搜索] 按钮 → 跳转到 TransferView
```

---

## 9. 车次路线匹配算法

### 9.1 问题定义

给定车次 G1 途经 A→B→C→D 四个车站，在地图上高亮显示从 A 到 D 的铁路线。现有原型的问题是：对每对相邻车站（A→B, B→C, C→D）直接用 `ST_DWithin(geom, line, 10000m)` 查找附近的铁路线段，会匹配到许多不相关的线段。

### 9.2 根因分析

```
           ┌─── 京沪线 (实际 A→B 线路)
    A──────┼──────B
           │
    ┌──────┼──────┐  ← 不相关的支线 (也在 10km 范围内!)
    │      │      │
    └──────┘      └── 另一个方向的线路 (也在 10km 范围内!)
```

`ST_DWithin` 是纯距离判断，不关心铁路线的**拓扑连通性**——即 A 站附近的线段是否实际连接到了 B 站附近的线段。

### 9.3 解决方案：三阶段匹配

#### 阶段一：预计算 (离线, 数据导入时执行)

在数据导入后，对所有铁路线建立**拓扑连接图**：

```sql
-- 创建铁路线拓扑连接表
CREATE TABLE railway_topology AS
SELECT
    a.id AS seg_a,
    b.id AS seg_b,
    ST_Intersects(a.geom, b.geom) AS is_connected,
    ST_Distance(a.geom, b.geom) AS gap_meters
FROM railway_segments a, railway_segments b
WHERE a.id < b.id
  AND (
    ST_Intersects(a.geom, b.geom)                           -- 直接相交
    OR ST_DWithin(a.geom::geography, b.geom::geography, 50) -- 50m 内可视为连接
  );
```

#### 阶段二：候选线段筛选 (在线, 用户查询车次时)

对每对相邻车站 (A, B)：

```sql
-- Step 1: 找到 A 站和 B 站各自的候选线段（缩小到 2km 内的线段）
WITH a_candidates AS (
    SELECT id AS seg_id, name
    FROM railway_segments
    WHERE ST_DWithin(geom::geography, ST_SetSRID(ST_MakePoint(:a_lon, :a_lat), 4326)::geography, 2000)
),
b_candidates AS (
    SELECT id AS seg_id, name
    FROM railway_segments
    WHERE ST_DWithin(geom::geography, ST_SetSRID(ST_MakePoint(:b_lon, :b_lat), 4326)::geography, 2000)
)
-- Step 2: 从 A 候选出发，在图 G 上做 BFS，限步数找到到 B 候选的路径
-- (此步在 Java Service 中实现，不在 SQL 中做)
SELECT a.seg_id AS start_seg, b.seg_id AS end_seg
FROM a_candidates a, b_candidates b
WHERE ... -- 拓扑连通判断 (见 Java 部分)
```

#### 阶段三：图搜索匹配 (Java `RouteMatchingService`)

```java
// RouteMatchingService.java 伪代码

public List<RailwaySegment> matchSegments(Station from, Station to, Map<Long, RailwaySegment> segmentGraph) {
    // 1. 找到起点站 2km 内的所有候选线段
    List<RailwaySegment> startSegs = segmentMapper.findNearby(from.getLon(), from.getLat(), 2000);

    // 2. 找到终点站 2km 内的所有候选线段
    List<RailwaySegment> endSegs = segmentMapper.findNearby(to.getLon(), to.getLat(), 2000);

    // 3. BFS: 从每个 startSeg 出发，沿拓扑连接关系搜索
    Queue<Long> queue = new LinkedList<>();
    Map<Long, Long> prev = new HashMap<>();  // 记录路径

    for (RailwaySegment seg : startSegs) {
        queue.add(seg.getId());
        prev.put(seg.getId(), null);
    }

    while (!queue.isEmpty()) {
        Long current = queue.poll();
        if (endSegIds.contains(current)) {
            // 找到终点, 回溯路径
            return reconstructPath(prev, current);
        }
        // 获取当前段的相邻段 (从 railway_topology 表)
        for (Long neighbor : topologyMap.getOrDefault(current, Collections.emptyList())) {
            if (!prev.containsKey(neighbor)) {
                prev.put(neighbor, current);
                queue.add(neighbor);
            }
        }
    }

    // BFS 未找到连通路径 → 降级为纯距离匹配（ST_DWithin 500m）
    // 并标记 confidence < 1.0
    return fallbackDistanceMatch(from, to);
}
```

### 9.4 为什么仍然可能不完美

即使有三阶段匹配，以下情况仍会导致线路不完整：

1. **OSM 数据缺失**：该段铁路线在 OSM 中根本不存在 → 只能显示断线，前端可用虚线连接两站作为提示
2. **车站不在线段端点**：车站可能在一条长线段的中点上（而非端点）→ 需要在 BFS 前对候选线段做 `ST_LineLocatePoint` 切分
3. **同名不同线**：两条平行的"京沪线"（普速和高铁）同时满足条件 → 通过 `railway` 字段（rail vs high_speed）和 `max_speed` 字段优先匹配类型一致的线路

### 9.5 预计算优化

在数据导入后、系统上线前，**批量预计算所有车次的路线匹配**，存入 `train_segment_mapping` 表：

```sql
-- 预计算：对每个车次的前两站 (A,B) 执行匹配，然后缓存
-- 后续查询直接 JOIN train_segment_mapping，无需实时 BFS
SELECT tsm.* FROM train_segment_mapping tsm
WHERE tsm.train_no = 'G1'
ORDER BY tsm.from_station, tsm.seg_order;
```

预计算耗时估计：全国约 10,000 个车次 × 平均 15 站 = 150,000 对相邻车站，每对 BFS 约 50ms → 总计约 2 小时。可在夜间批处理执行。

---

## 10. 多次中转换乘规划

### 10.1 问题建模

将铁路网建模为 **时间依赖图 (Time-Dependent Graph)**：

```
节点 = 车站 + 时间点 (到站时刻, 发车时刻)
边:
  - 运行边: (站A, 发车时刻t1) → (站B, 到站时刻t2), 权重 = t2 - t1
  - 等待边: (站A, 到站时刻t1) → (站A, 发车时刻t2), 权重 = t2 - t1 (换乘等待)
  - 同城换乘边: (站A1, 到站时刻t1) → (站A2, 发车时刻t2), 权重 = t2 - t1 + transfer_time
```

### 10.2 算法选择

基于扩展性考虑，实现两种算法，按场景选用：

| 算法 | 适用场景 | 复杂度 |
|------|----------|--------|
| **KSP (K-Shortest Paths)** | 转乘次数 ≤ 2, 查任意两站间的最优方案 | O(K·V·(E+V·logV)) |
| **改进 CSA (Connection Scan)** | 转乘次数无限制, 查某日全部可行方案 | O(C) 遍历所有时刻表连接 |

**推荐方案**：优先实现 KSP（基于 JGraphT 库的 `KShortestPaths`），因为它的模型与我们的图结构一致，且有成熟的 Java 实现。

### 10.3 夜行昼游偏好评分函数

```
评分函数 Score(方案):
  Score = w1 * 总耗时(h) + w2 * 换乘次数 + w3 * 昼间等待(h) - w4 * 中转站数量

约束:
  - 每段发车时间 ∈ [18:00, 06:00] (夜间乘车, 软约束)
  - 中转到达时间 ∈ [06:00, 22:00] (白天游览, 软约束)
  - 单段耗时 ≤ 12h (硬约束)
  - 总耗时 ≤ 72h (硬约束)
  - 换乘次数 ≤ MaxTransfers (硬约束)
```

权重 `w1-w4` 可配置，用户选择"夜行昼游"偏好时增大 `w3, w4`。

### 10.4 API 设计

```
POST /api/transfer/search
Request:
{
  "from": "北京南",
  "to": "昆明",
  "date": "2026-05-01",
  "max_transfers": 2,
  "preference": "night_train_day_tour",  // least_time | least_transfer | night_train_day_tour | least_price
  "max_results": 10
}

Response:
{
  "results": [
    {
      "id": "route_001",
      "total_time_min": 2210,
      "total_price_yuan": 876.5,
      "transfer_count": 2,
      "score": 85.2,
      "segments": [
        {
          "train_no": "D940",
          "from_station": "北京南",
          "to_station": "武汉",
          "depart_time": "19:30",
          "arrive_time": "06:45",
          "duration_min": 675,
          "is_night": true
        },
        {
          "train_no": "G1525",
          "from_station": "武汉",
          "to_station": "贵阳北",
          "depart_time": "20:15",
          "arrive_time": "05:30",
          "duration_min": 555,
          "is_night": true
        },
        {
          "train_no": "G2873",
          "from_station": "贵阳北",
          "to_station": "昆明南",
          "depart_time": "08:30",
          "arrive_time": "11:15",
          "duration_min": 165,
          "is_night": false
        }
      ],
      "city_tours": [
        {
          "city": "武汉",
          "available_hours": 13.5,
          "suggested_attractions": ["黄鹤楼", "东湖", "户部巷"]  // 未来扩展
        },
        {
          "city": "贵阳",
          "available_hours": 15.0,
          "suggested_attractions": []
        }
      ]
    },
    // ... more results
  ],
  "total_found": 23,
  "search_time_ms": 450
}
```

---

## 11. 分阶段实施路线

### Phase 0: 项目初始化与环境搭建 (预计 2 天)

```
□ 创建 Maven 多模块项目骨架 (railway-common/data/service/api/batch)
□ 创建 Vue 3 + Vite + TypeScript + Tailwind 前端项目
□ docker-compose.yml: PostgreSQL 16 + PostGIS 3.4 + Redis 7
□ 配置 Spring Boot 3.3.5 + MyBatis-Plus + JTS
□ 配置前端 MapLibre GL JS + Naive UI + Pinia + Vue Router
□ 编写 schema.sql (所有建表语句)
□ Git 初始化 + .gitignore
```

### Phase 1: 数据管线 (预计 5 天)

```
□ 1.1 中国陆地边界数据获取与验证
□ 1.2 网格分割器实现 (grid_splitter.py)
       - 渔网分割: 1°×1° 网格 + 0.05° 重叠
       - 与中国边界相交判断，过滤海域
       - 蛇形排序输出队列
□ 1.3 逐格抓取脚本 (基于 fetch_railway.py 改造)
       - 读取网格队列
       - 逐格执行 Overpass API 查询
       - 每格存为独立 GeoJSON
□ 1.4 Spring Batch 批量导入
       - GeoJsonItemReader (分块读取)
       - 数据清洗 Processor
       - 分批写入 + 进度日志
□ 1.5 数据完整性校验脚本
       - 铁路线/车站数量统计
       - 缺失网格检测
       - 密度热力图输出
□ 1.6 时刻表爬虫
       - 获取全国车次列表
       - 逐车次爬取途经站 (liecheba.com)
       - 存入 train_routes + train_stops 表
```

### Phase 2: 地图服务 (预计 4 天)

```
□ 2.1 矢量瓦片 API
       - TileController + TileService
       - 铁路线层 z≥6, 车站层 z≥11
       - MVT 格式返回 + 1h 浏览器缓存
□ 2.2 底图验证
       - MapTiler Streets 加载速度测试
       - 天地图备选方案
       - 最终选定底图源
□ 2.3 前端地图组件
       - MapContainer.vue (MapLibre 初始化)
       - RailwayLayer.vue (铁路线样式: 按类型分色, 按缩放调线宽)
       - StationLayer.vue (车站圆点 + tooltip/popup)
```

### Phase 3: 搜索系统 (预计 3 天)

```
□ 3.1 车站搜索
       - StationSearchService (中文/拼音/首字母/城市)
       - 拼音索引生成 (导入时计算 name_pinyin)
       - StationSearch.vue (带下拉联想的输入框)
□ 3.2 车次搜索
       - TrainSearchService (车次前缀/始发终到)
       - TrainSearch.vue
□ 3.3 前端搜索面板集成
       - SearchPanel.vue (三 Tab 切换)
       - 选中后地图联动
```

### Phase 4: 车次路线匹配 (预计 4 天)

```
□ 4.1 铁路拓扑连接表构建
       - 导入后执行 ST_Intersects + ST_DWithin 建图
□ 4.2 RouteMatchingService 实现
       - 三阶段匹配: 候选筛选 → BFS 图搜索 → 降级距离匹配
□ 4.3 预计算管道
       - 批量匹配所有车次, 存入 train_segment_mapping
□ 4.4 前端路线高亮
       - TrainRouteLayer.vue
       - RouteTimeline.vue (经停时间线)
□ 4.5 缺失段处理
       - 数据不完整时虚线连接 + 前端提示
```

### Phase 5: 地图基础功能完善 (预计 3 天)

```
□ 5.1 站站查询
       - 用户选择任意两站, 高亮两站间的最直接线路
□ 5.2 同城车站展示
       - 城市名搜索时展示该城市所有车站
□ 5.3 信息面板
       - 车站信息卡片: 等级/线路/途经车次
       - 铁路线段信息: 名称/类型/速度
□ 5.4 图层控制
       - 铁路线/车站/地铁 图层开关
       - 按类型筛选 (高铁/普速/地铁)
```

### Phase 6: 多次中转换乘 (预计 5 天)

```
□ 6.1 铁路图构建 (TransferGraphBuilder)
       - 基于 train_stops 构建时间依赖图
□ 6.2 KSP 算法实现 (TransferSearchService)
       - JGraphT KShortestPaths
       - 约束: 最大换乘次数/单段最大时间
□ 6.3 夜行昼游评分 (TransferRankingService)
       - 偏好权重配置
       - 方案排序
□ 6.4 前端换乘页面
       - TransferSearchForm.vue
       - TransferResultList.vue
       - TransferTimeline.vue (多段车程可视化)
```

### Phase 7: 优化与交付 (预计 3 天)

```
□ 7.1 性能优化
       - 瓦片 Redis 缓存
       - 前端懒加载
       - PMTiles 预生成评估
□ 7.2 Docker + Nginx 部署配置
□ 7.3 错误处理与边界情况
□ 7.4 文档: README, API 文档, 部署指南
```

---

## 12. 待确认问题

在 Phase 0 开始前，请确认以下事项：

1. **底图方案**：是否同意优先验证 MapTiler Streets？若不可用，天地图继续作为备选？
2. **票价数据**：Phase 1 是否需要爬取票价？需要二等座/硬卧/软卧/无座等分类存储？
3. **用户系统**：Phase 0 是否预留 `users` 表？Phase 7 是否需要登录/收藏/历史功能？
4. **地图坐标系**：确认使用 WGS-84 为主坐标系。如果最终选定天地图底图，需要 GCJ-02 转换。是否接受在两套坐标系间转换？
5. **数据更新频率**：铁路线数据每季度更新（Overpass API），时刻表数据每日更新（爬虫）。是否接受？还是需要更高频率？
6. **部署环境**：最终部署在哪里？（个人服务器/VPS/云服务商？Linux 还是 Windows？）
7. **前端组件库**：Naive UI 作为 Vue 3 组件库是否合适？还是有偏好（Element Plus / Ant Design Vue）？
8. **铁路线数据精度**：OSM 数据中部分支线/专用线可能缺失，是否接受？是否需要人工补录的入口？
9. **同城异站换乘时间**：`station_city_map.transfer_time_min` 数据如何获取？（手动录入 / 高德 API 查询市内交通时间）
10. **多次中转的"城市游"信息**：Phase 1-7 中暂不实现自动推荐旅游信息，但在 `TransferResult` 中预留 `city_tours` 字段。是否同意？

---

> **下一步**: 请阅读本计划并反馈上述 10 个待确认问题。确认后进入 Phase 0：项目初始化与环境搭建。
