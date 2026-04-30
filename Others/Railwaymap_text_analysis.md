# 中国铁路地图 (Railwaymap_text) — 系统分析报告

## 0. 项目识别与目录结构

```
Railwaymap_text/
├── frontend/                  # 前端 (纯静态 SPA)
│   ├── index.html             # 入口页面
│   ├── css/style.css          # 样式表
│   ├── js/map.js              # 核心地图逻辑 (344行)
│   └── data/                  # GeoJSON 数据
│       ├── railways.geojson   # 约 155 MB (全量铁路线)
│       └── stations.geojson   # 约 3 MB (全量车站)
├── app/                       # Python API 服务器
│   ├── server.py              # 主 API 服务 (403行, 零外部依赖)
│   ├── import_geojson.py      # GeoJSON → PostGIS 批量导入
│   ├── sync_all.py            # 全量数据更新编排器
│   ├── scheduler.py           # 定时更新调度器
│   └── package.json           # (仅占位, 无实际 Node 依赖)
├── scripts/                   # 数据采集脚本
│   ├── config.py              # 12 个区域定义
│   ├── fetch_railway.py       # Overpass API → GeoJSON (带重试+去重)
│   └── fetch_schedule.py      # 列车时刻表爬虫 (liecheba.com)
├── spring-backend/            # Spring Boot 多模块后端 (可选/并行)
│   ├── pom.xml                # Maven 父 POM (Spring Boot 3.3.5)
│   ├── Dockerfile             # 多阶段 Docker 构建
│   ├── src/main/resources/
│   │   └── schema.sql         # DDL (PostGIS 扩展 + 建表)
│   ├── railway-common/        # 实体类 + 工具类
│   ├── railway-data/          # MyBatis Mapper + SQL XML
│   ├── railway-service/       # 业务逻辑层
│   ├── railway-api/           # Spring Boot 启动 + REST 控制器
│   └── railway-sync/          # 同步模块 (预留)
├── docker-compose.yml         # PostgreSQL 16 + PostGIS 3.4 + Spring Boot
├── start.sh                   # 一键启动脚本
├── plan.md                    # 原型开发计划 (12 步，已执行)
├── AGENTS.md                  # Agent 操作手册
├── README.md                  # 项目说明
└── .gitignore
```

**类型判断**：前后端分离但不复杂。以 Python 为主力运行时，Spring Boot 为并行实现。无 monorepo 工具，无工作空间配置。

---

## 1. 架构概览

### 整体架构图

```
浏览器 (Leaflet + VectorGrid)
   │
   ├─ 天地图底图瓦片 (CDN)
   ├─ API 请求 → http://localhost:10010
   │
   ▼
┌──────────────────────────────────────────┐
│  Python API Server (app/server.py)       │  ← 主力
│  Spring Boot (railway-api)               │  ← 并行替代
│    ↓                                     │
│  PostGIS ST_AsMVT 动态生成矢量瓦片        │
│  返回 MVT/PBF 二进制或 JSON              │
└──────────────────────────────────────────┘
   │
   ▼
┌──────────────┐
│  PostgreSQL   │  Docker Compose
│  + PostGIS    │  image: postgis/postgis:16-3.4
└──────────────┘
```

### 前端架构

- **框架**：无框架——纯 Vanilla JavaScript（约 11KB，344 行）
- **地图引擎**：Leaflet 1.9.4 + Leaflet.VectorGrid 1.3.0
- **渲染模式**：Canvas 瓦片渲染 (`preferCanvas: true`)
- **底图**：天地图 WMTS 瓦片（两个图层：`vec_w` 矢量 + `cva_w` 标注），WKID=CGCS2000（≈ WGS84）
- **数据层**：矢量瓦片 (MVT/PBF) 动态加载，而非预生成 GeoJSON
- **UI 组件**：Leaflet 原生控件（`L.control`）+ 内联 DOM 组装
- **状态**：全局变量 (`var map, var API, var stationDataCache`)，无正式状态管理

### 后端架构

**Python 主力**：

| 层 | 实现 |
|---|------|
| HTTP 服务器 | `http.server.ThreadingHTTPServer` (stdlib, 零外部依赖) |
| 路由 | if/elif 手动分发 (`do_GET` 中解析 path) |
| 数据库 | `docker compose exec -T db psql` 持久管道（含连接池） |
| 瓦片生成 | PostGIS `ST_AsMVT` (数据库内生成 MVT) |
| 跨域 | 手动设置 `Access-Control-Allow-Origin: *` |

**Spring Boot 并行**：

| 层 | 实现 |
|---|------|
| 框架 | Spring Boot 3.3.5 / Java 21 |
| ORM | MyBatis-Plus 3.5.7 |
| 空间库 | JTS 1.19.0 |
| 架构 | Controller → Service → Mapper → DB |
| 瓦片生成 | MyBatis XML 内嵌 PostGIS SQL (ST_AsMVT) |

### 数据流（完整链路）

```
用户操作                                Python API Server
─────────                              ──────────
1. 缩放/平移地图
   → map.js 监听 zoomend/moveend
   → L.vectorGrid.protobuf 自动请求
     → fetch('/api/tiles/railways/6/52/24.pbf')
                                        2. do_GET 解析 URL
                                        3. tile_to_bbox(z, x, y) 转换坐标
                                        4. build_tile_sql() 生成 PostGIS SQL:
                                             ST_MakeEnvelope → ST_AsMVTGeom → ST_AsMVT → hex
                                        5. DBManager.query() 通过持久 psql 管道执行
                                        6. hex 解码 → bytes
                                        7. send_pbf() 返回 MVT 二进制
3. 前端 Canvas 渲染矢量瓦片
   → VectorGrid 解码 PBF
   → railStyle() 按类型着色重绘 Canvas
```

---

## 2. 核心模块识别

### 前端模块

| 文件 | 行数 | 职责 |
|------|------|------|
| `frontend/js/map.js` | 344 | 地图初始化、矢量瓦片加载、车站搜索、车次高亮 |
| `frontend/index.html` | 22 | 入口、Leaflet CDN 引入、DOM 结构 |
| `frontend/css/style.css` | 12 | 全屏地图 + 信息面板样式 |

**前端功能模块**（均在 `map.js` 中）：
1. **地图初始化** (1-11行)：Leaflet 实例，天地图 Key：`a7e0e6643320cdb2b6da20e5e86b7d62`
2. **天地图底图图层** (15-25行)：矢量和标注两层
3. **铁路线矢量瓦片** (30-67行)：`L.vectorGrid.protobuf` + `L.canvas.tile` 渲染器
4. **车站加载** (70-133行)：通过 API 搜索接口拉取全部车站（≤5000），用 `circleMarker` 按视口渲染
5. **车次搜索** (134-260行)：防抖 300ms 输入 → `/api/trains/search` → 选择车次 → `/api/trains/route` → GeoJSON 高亮
6. **车站搜索** (262-343行)：防抖 250ms 输入 → `/api/stations/search` → 飞至车站

### 后端模块（Python）

| 文件 | 行数 | 职责 |
|------|------|------|
| `app/server.py` | 403 | API 服务器：瓦片、搜索、车次路线、健康检查、同步触发 |
| `app/import_geojson.py` | 180 | GeoJSON → PostGIS 的批量管道导入 |
| `app/sync_all.py` | 165 | 全量数据更新编排器（逐区域拉取+导入+验证） |
| `app/scheduler.py` | 74 | 定时更新调度器（环境变量控制间隔） |
| `scripts/config.py` | 19 | 12 个区域的 bbox 定义 |
| `scripts/fetch_railway.py` | 163 | Overpass API 拉取+重试+去重 |
| `scripts/fetch_schedule.py` | 225 | 列车时刻表爬虫 (liecheba.com → BeautifulSoup) |

### 后端模块（Spring Boot）

```
railway-common/  实体 + 工具
  Railway.java         (27行, 手动 getter/setter)
  Station.java         (20行)
  TileUtils.java       (13行) — z/x/y→经纬度边界
railway-data/    数据访问
  RailwayMapper.java   (12行) — MyBatis-Plus BaseMapper + 矢量瓦片查询
  StationMapper.java   (18行) — 同上 + 关键词搜索
  mapper/RailwayMapper.xml  (27行) — PostGIS ST_AsMVT SQL
  mapper/StationMapper.xml  (35行) — 同上
railway-service/ 业务逻辑
  TileService.java     (29行) — hex解码 PBF
  StationService.java  (25行) — 委托 Mapper
railway-api/     Web层 + 启动
  RailwayMapApplication.java  (11行)
  CorsConfig.java              (26行)
  GlobalExceptionHandler.java  (21行)
  StationController.java       (27行)
  TileController.java          (48行)
railway-sync/     预留框架
  SyncModuleInfo.java  (13行) — 文档说明"当前为框架预留"
```

---

## 3. 依赖与构建配置

### 前端
- **无** `package.json`，无构建工具
- 依赖通过 CDN 加载：
  - Leaflet 1.9.4 (unpkg)
  - Leaflet.VectorGrid 1.3.0 (unpkg)
- 运行时：`python3 -m http.server 10011`（纯静态服务）

### Python (app/)
- `package.json` 是空的占位（无实际 Node 依赖）
- **零外部 pip 依赖**——`server.py` 只用了 `http.server`, `json`, `subprocess`, `threading`, `select` 等 stdlib
- `fetch_railway.py` 依赖 `requests`
- `fetch_schedule.py` 依赖 `requests`, `beautifulsoup4`, `lxml`

### Spring Boot
- **Java 21**, Spring Boot 3.3.5 (parent POM)
- Maven 聚合工程，5 个子模块
- 关键依赖：`mybatis-plus-spring-boot3-starter:3.5.7`, `postgresql:42.7.3`, `jts-core:1.19.0`
- 构建工具：Maven，无 CI/CD 配置，无代码检查工具

### 共享
- `.gitignore` 覆盖 Python、Node、IDE、OS 文件
- 无 ESLint/Prettier/Husky
- 无 CI/CD pipeline

---

## 4. 数据交互层

### API 端点 (7个)

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/tiles/railways/{z}/{x}/{y}.pbf` | GET | 铁路线矢量瓦片 (MVT), z≥6 |
| `/api/tiles/stations/{z}/{x}/{y}.pbf` | GET | 车站矢量瓦片 (MVT), z≥11 |
| `/api/stations/search?q=&limit=` | GET | 车站搜索 (ILIKE), limit≤5000 |
| `/api/trains/search?q=` | GET | 车次前缀搜索 |
| `/api/trains/route?q=` | GET | 车次路线 (途经站+GeoSegment) |
| `/api/health` | GET | 健康检查 |
| `/api/sync/trigger?region=` | POST | 触发数据同步 |

### 前端 HTTP 客户端

**无封装**——直接使用 `fetch()` 原生 API：

```javascript
// 车次搜索 - 防抖 300ms
fetch(API + '/api/trains/search?q=' + encodeURIComponent(q))

// 车次路线高亮
fetch(API + '/api/trains/route?q=' + encodeURIComponent(trainNo))

// 车站搜索 - 防抖 250ms
fetch(API + '/api/stations/search?q=' + encodeURIComponent(q) + '&limit=10')
```

- 无请求/响应拦截器
- 无 JWT 或 Token 管理（无需认证）
- 错误处理：`.catch(function () {})` 空处理或简单更新 DOM
- API base 硬编码为 `http://localhost:10010`

### 数据模型

**PostgreSQL 表** (`schema.sql`)：

```sql
railways (id BIGSERIAL PK, osm_id BIGINT, name VARCHAR(200),
          railway VARCHAR(30), usage VARCHAR(30), electrified VARCHAR(20),
          geom GEOMETRY(LINESTRING, 4326), sync_at TIMESTAMP)
  + GIST spatial index on geom

stations (id BIGSERIAL PK, osm_id BIGINT, name VARCHAR(200) NOT NULL,
          railway VARCHAR(30), geom GEOMETRY(POINT, 4326), sync_at TIMESTAMP)
  + GIST spatial index on geom

train_routes (train_no PK, train_type, depart_station, arrive_station,
              depart_time, arrive_time, duration_min, stations JSONB, updated_at)
  (不在 schema.sql 中，由 fetch_schedule.py 动态创建)
```

数据字典：
- `railways.railway`: rail / light_rail / subway
- `railways.usage`: main / branch / industrial / military / tourism
- `railways.electrified`: yes / no / contact_line

**前端无共享类型**——前后端类型各自定义，无 OpenAPI/Swagger 生成。

---

## 5. 状态管理与 UI 层

### 状态管理

**无正式状态管理**。全局变量列表：

| 变量 | 类型 | 用途 |
|------|------|------|
| `map` | `L.Map` | 地图实例 |
| `API` | string | API 基地址 |
| `railGrid` | `L.VectorGrid` | 铁路线矢量瓦片图层 |
| `stationMarkers` | `L.LayerGroup` | 车站 Marker 容器 |
| `loadedStationTiles` | Object | 已加载的瓦片标记（实际未使用） |
| `stationDataCache` | Array | 全量车站数据缓存 |
| `trainRouteLayer` | `L.LayerGroup` | 车次路线图层 |
| `trainTimer` / `searchTimer` | number | 防抖定时器 ID |

### UI 组件库

**无组件库**——所有 UI 通过 Leaflet 原生 `L.control` + 内联 HTML 字符串构建：
- 车次搜索框：`input#train-search` + `div#train-results` + `button#train-clear`
- 车站搜索框：`input#station-search` + `div#search-results`
- 信息面板：`div#info-panel` (DOM 中预定义)

### 样式

- 12 行 CSS（全屏地图 + 信息面板定位）
- 无 CSS 预处理器、无 Tailwind、无 CSS Modules
- 无主题系统、无国际化配置、无暗黑模式

---

## 6. 认证与授权

**无需认证**。这是一个纯公开浏览项目：
- 无登录/注册
- 无 Token/JWT
- 无角色/权限
- CORS 全开放 (`Access-Control-Allow-Origin: *`)

---

## 7. 数据库与存储

### 数据库

- **PostgreSQL 16 + PostGIS 3.4**（Docker 容器）
- 连接参数：`jdbc:postgresql://localhost:5432/railwaymap`, 用户 `railway`, 密码 `railway123`
- 无 Redis、无消息队列、无文件存储

### 数据量

- 铁路线：约 44 万条（GeoJSON 155MB）
- 车站：约 4,000+（GeoJSON 3MB）
- 列车时刻表：按需爬取，数量取决于爬取车次数

### 备份与迁移

- **无 migration 工具**（如 Flyway/Liquibase）。DDL 通过 `schema.sql` 在 Docker 首次启动时执行
- 无种子数据，通过 `import_geojson.py` 导入
- GeoJSON 备份：`sync_all.py` 在拉取前自动备份 `.geojson.bak`

---

## 8. 环境与部署配置

### 配置管理

| 层面 | 位置 | 方式 |
|------|------|------|
| Python API | `server.py` 顶部常量 | 硬编码 `DB_SERVICE="db"`, `DB_USER="railway"` |
| Spring Boot | `application.yml` | YAML 配置 |
| 数据库连接 | `docker-compose.yml` + `application.yml` | 环境变量/硬编码 |
| 区域定义 | `scripts/config.py` | 字典常量 |
| 天地图 Key | `map.js:2` | 硬编码 `a7e0e6643320cdb2b6da20e5e86b7d62` |
| 同步调度 | `scheduler.py` 环境变量 | `SYNC_INTERVAL`, `SYNC_ON_START` |

### Docker

```
docker-compose.yml:
  db:    postgis/postgis:16-3.4 (端口 5432, 持久化 volume pgdata)
  app:   spring-backend/Dockerfile (多阶段: maven build → jre run, 端口 10010)
```

### 无 CI/CD 配置

- 无 `.github/workflows`
- 无 `.gitlab-ci.yml`
- 无 `Makefile`

---

## 9. 代码逻辑深潜

### 前端：车次路线高亮完整流程

```
1. 用户输入车次 "G1" (防抖 300ms)
2. map.js:159 → fetch('/api/trains/search?q=G1')
3. 返回: [{train_no: "G1", train_type: "高速", depart_station: "北京南", ...}]
4. 渲染下拉列表 (data-train 属性存储车次)
5. 用户点击选项
6. map.js:183 → highlightTrainRoute("G1")
7. fetch('/api/trains/route?q=G1')
8. 返回: {
     train_no: "G1",
     stations: [{seq:1, name:"北京南", arrive:null, depart:"09:00"}, ...],
     segments: [{geometry:{type:"LineString",coordinates:[...]}, properties:{from:"北京南",to:"天津南"}}, ...]
   }
9. 将 segments 转为 GeoJSON FeatureCollection
10. L.geoJSON 渲染为橙色 (#ff8c00) 粗线 (weight:4)
11. 为每个途经站逐次调用 /api/stations/search 获取坐标
12. L.circleMarker 标注各站 + tooltip
13. 更新 stats 显示车次信息
```

**问题**：第 11 步对每个站点发起独立 fetch（N+1 查询），如 G1 停在 12 站则有 12 个顺序请求。

### 后端：矢量瓦片生成完整流程（Python）

```
1. HTTP 请求: GET /api/tiles/railways/6/52/24.pbf
2. server.py:122 → handle_tile("railways", path)
3. 解析: z=6, x=52, y=24
4. build_tile_sql("railways", 6, 52, 24):
   - tile_to_bbox(6, 52, 24) → (lon,lat)4 边界
   - 生成 SQL:
     WITH bounds AS (SELECT ST_MakeEnvelope(...))
     tile_data AS (SELECT id, name, railway, usage,
                   ST_AsMVTGeom(geom, bounds.bbox, 4096, 256, true) AS mvt_geom
                   FROM railways, bounds
                   WHERE geom && bounds.bbox AND (6 >= 6))
     SELECT encode(ST_AsMVT(tile_data.*, 'railways', 4096, 'mvt_geom'), 'hex')
5. DBManager.query(sql):
   - 通过持久 psql 管道写入 SQL + 分隔符 (___OPC_EOR___)
   - 读取输出直到遇到分隔符
   - 返回 hex 字符串
6. handle_tile: hex → bytes.fromhex → send_pbf(data)
   - Content-Type: application/vnd.mapbox-vector-tile
   - Cache-Control: public, max-age=3600
```

**性能关键点**：`DBManager` 使用持久 `psql` 管道（而非每次 `docker exec`），将瓦片延迟从约 2 秒降到约 16ms（AGENTS.md 记录）。

### 后端：数据导入流程

```
import_geojson.py (3阶段):
  [1/3] TRUNCATE railways + stations RESTART IDENTITY (通过 docker exec psql)
  [2/3] 加载 GeoJSON (json.load) → 遍历 features →
        构建 INSERT SQL: ("name", 'rail', 'main', 'yes', ST_GeomFromText('LINESTRING(...)', 4326))
        每 5 万条打印进度
  [3/3] 写入临时文件 → cat | docker compose exec psql 管道导入
        最后执行 SELECT setval() 重置序列
  总耗时 ~1.5 分钟 (44 万条)
```

---

## 10. 潜在问题与最佳实践

### 安全隐患

| 问题 | 位置 | 严重度 |
|------|------|--------|
| **API Key 硬编码** | `map.js:2` 天地图 Key 公开在代码中 | 中 |
| **数据库密码硬编码** | `server.py`, `application.yml`, `docker-compose.yml` 多处明文 | 中 |
| **SQL 注入风险** | `server.py` 使用字符串拼接生成 SQL（虽然有 `q.replace("'", "''")` 做转义，但 PostGIS 函数参数是双写单引号而非参数化，仍有风险） | 中 |
| **CORS 全开放** | `Access-Control-Allow-Origin: *` | 低（公开项目无敏感数据） |
| **无 CSRF 防护** | 无 Token 机制 | 低（无状态修改操作） |
| **异常信息泄露** | `GlobalExceptionHandler` 返回完整异常类名和消息给客户端 | 中 |

### 性能问题

| 问题 | 位置 | 影响 |
|------|------|------|
| **车次路线 N+1 查询** | `map.js:232-249` 对每个途经站发起独立 fetch | 用户体验差 |
| **全量车站缓存** | `map.js:93` 一次加载 5000 个车站 | 首次加载延迟 |
| **GeoJSON 文件巨大** | 155MB railways.geojson 加载到内存 | 数据导入时内存压力 |
| **无 HTTP/2 或长连接** | `http.server` 默认 HTTP/1.1 | 并发瓦片请求效率低 |

### 代码质量问题

| 问题 | 说明 |
|------|------|
| **全局变量滥用** | 11 个全局变量，无模块化 |
| **重复 SQL** | Python `server.py` 和 MyBatis XML 中各自维护相同的 PostGIS SQL |
| **双后端维护** | Python 和 Spring Boot 两套实现，需同步功能更新 |
| **无测试** | 0 个测试文件 |
| **无类型安全** | JavaScript 无 TypeScript，Python 无类型注解 |
| **实体类手动 getter/setter** | Spring Boot 中没用 Lombok，27 行 Railway.java 有 16 行是 getter/setter |
| **SyncModuleInfo 空壳** | `railway-sync` 模块只有 13 行文档类 |

### 优点

| 方面 | 说明 |
|------|------|
| **PostGIS 矢量瓦片** | 利用 `ST_AsMVT` 在数据库端生成 MVT，避免应用层几何处理 |
| **持久 psql 管道** | 智能优化——消除 docker exec 启动开销，延迟降低 100 倍 |
| **区域去重机制** | `fetch_railway.py` 按 (首坐标, 名称) 去重，增量合并已有数据 |
| **区域边界重叠** | AGENTS.md 详细记录了边界缝隙问题和解决方案（成都、西藏等） |
| **重试与容错** | Overpass API 5 次重试，指数退避，429 限流特殊处理 |
| **Docker Compose 健康检查** | DB 就绪后才启动 app |
| **干净的分层架构** | Spring Boot 严格按 Maven 多模块分层 |

---

### 总结

这是一个**原型阶段的铁路地图 Web 应用**。核心技术选型合理（Leaflet + PostGIS 矢量瓦片 + 天地图底图），以 Python 零依赖 HTTP 服务器为主力运行，Spring Boot 作为 Java 替代方案并行开发。架构简单直接，代码量小（约 1500 行 Python + 600 行 JavaScript/HTML + 200 行 Java + XML），适合作为后续开发的基础。主要需要在**安全性（敏感信息管理）**、**代码复用（消除双后端 SQL 重复）**和**前端工程化（模块化、类型安全）**三个维度进行加固。
