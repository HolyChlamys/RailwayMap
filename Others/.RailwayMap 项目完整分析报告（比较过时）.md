# RailwayMap 项目完整分析报告

---

## 0. 项目识别与目录结构

### 项目概述

RailwayMap — 中国铁路地图与多次中转路线规划系统。一个前后端分离的 Maven 多模块 monorepo。

### 目录结构

```
RailwayMap/
├── pom.xml                  # 根 POM (Maven 多模块管理)
├── docker-compose.yml       # 开发/部署编排
├── Dockerfile               # 后端容器化构建
├── nginx.conf               # 前端静态资源 + API 反向代理
├── .gitignore
│
├── railway-frontend/        # Vue 3 SPA 前端
├── railway-api/             # REST API (Controller + 启动类 + 安全配置)
├── railway-service/         # 业务逻辑层
├── railway-data/            # MyBatis 数据访问层
├── railway-common/          # 公共模块 (Entity/DTO/Enum/Util)
├── railway-batch/           # Spring Batch 数据导入
├── railway-scripts/         # Python 数据采集与处理脚本
└── Others/                  # 开发计划文档
```

Monorepo 工具: Maven pom.xml 聚合模块(无 Lerna/Nx/Turborepo/workspace 配置)

---

## 1. 架构概览

### 前端架构

| 维度        | 技术选型                                                          |
| ----------- | ----------------------------------------------------------------- |
| 框架        | Vue 3 (Composition API + `<script setup>`)                        |
| 状态管理    | Pinia 2.3 — 2 个 store: mapStore(地图状态), searchStore(搜索状态) |
| 路由        | Vue Router 4 — 懒加载, 2 个路由                                   |
| UI 组件库   | Naive UI 2.41                                                     |
| 样式方案    | Tailwind CSS 4 + 自定义 CSS                                       |
| 地图引擎    | MapLibre GL JS 5 — 矢量瓦片渲染                                   |
| HTTP 客户端 | Axios — 简单封装, Base URL /api, 30s 超时                         |
| 构建工具    | Vite 6 + TypeScript 5.7                                           |
| 包管理      | npm (无 pnpm/yarn workspace)                                      |

### 后端架构

| 维度     | 技术选型                                            |
| -------- | --------------------------------------------------- |
| 运行时   | Java 21                                             |
| 框架     | Spring Boot 3.5.14                                  |
| ORM      | MyBatis-Plus 3.5.16 (混合 XML SQL + Lambda Wrapper) |
| 安全     | Spring Security + JWT (jjwt 0.12.6) + BCrypt        |
| 缓存     | Spring Data Redis (Redis 7, 默认 TTL 1h)            |
| 批处理   | Spring Batch (GeoJSON 网格数据导入)                 |
| 图算法   | JGraphT 1.5.2 (Yen's K-最短路径换乘搜索)            |
| 空间数据 | JTS 1.20 (Java Topology Suite) + PostGIS            |
| 拼音     | pinyin4j 2.5.1 (中文→拼音转换)                      |
| JSON     | Jackson (JavaTimeModule, ISO 格式)                  |
| 构建     | Maven (Spring Boot plugin, JRE 21 Docker 镜像)      |

### 模块依赖链

```
railway-api ──→ railway-service ──→ railway-data ──→ railway-common
       ↓               ↓                (PostGIS,      (Entity, DTO,
    Spring Web     JGraphT,          MyBatis-Plus)    Enum, Util)
    Spring Security Spring Data Redis

railway-batch ──→ railway-service (复用)
       ↓
    Spring Batch, railway-data

railway-scripts: 独立 Python 脚本 (数据爬取/处理)
railway-frontend: 独立 Vue 3 项目 (Vite)
```

### 数据流

```
用户操作 (Vue Component)
→ Pinia Store action / 直接调用 service
→ Axios HTTP 请求 (/api/...)
→ Nginx 反向代理 (开发环境 Vite proxy) → Spring Boot :10010
→ JwtAuthFilter (解析 Bearer Token)
→ Controller (@RestController, 参数绑定 @RequestBody/@ModelAttribute)
→ Service (@Service, 业务逻辑 + 组合多个 Mapper 调用)
→ Mapper (@Mapper, 执行 MyBatis XML SQL 或 BaseMapper CRUD)
→ PostgreSQL (PostGIS 空间查询, ILIKE 模糊搜索)
→ Service 组装 DTO → Controller 返回 JSON
→ Axios Response → 组件更新响应式数据 → UI 重渲染
```

---

## 2. 核心模块识别

### 前端

入口文件: `railway-frontend/src/main.ts` — 创建 Vue 应用, 注册 Pinia、Router、Naive UI, 挂载 `#app`

路由表 (`src/router/index.ts`):

- `/` → MapView.vue (主地图页)
- `/transfer` → TransferView.vue (换乘查询页)

组件层级:

```
App.vue (NLayout + AppHeader + <router-view>)
├── MapView.vue
│   ├── MapContainer.vue (MapLibre GL 初始化 + 矢量瓦片源 + 图层配置)
│   ├── SearchPanel.vue (NTabs 切换 车站/车次/换乘)
│   │   ├── StationSearch.vue (NAutoComplete + Pinia mapStore)
│   │   └── TrainSearch.vue (NAutoComplete + Pinia mapStore)
│   ├── MapLegend.vue (NCollapse 显示铁路线/车站图例 + 开关控制)
│   ├── MapControls.vue (占位, 未实现)
│   ├── RailwayLayer.vue (占位)
│   ├── StationLayer.vue (占位)
│   └── TrainRouteLayer.vue (高亮路线 GeoJSON 渲染)
├── TransferView.vue
│   ├── TransferSearchForm.vue (NInput + NSelect + NDatePicker + API 调用)
│   ├── TransferResultList.vue (NCard 列表)
│   └── TransferTimeline.vue (NTimeline 详细时间线)
├── RouteInfoCard.vue (车次详情卡片)
└── RouteTimeline.vue (途经站时间线)
```

全局 Store:

- mapStore: center [108.5, 35.5] (居中于中国), zoom 5, selectedStationId, highlightedTrainNo, routeGeoJson, layerVisibility
- searchStore: activeTab, stationResults, trainResults, searchQuery, isSearching

通用工具:

- `utils/debounce.ts` — 标准防抖函数
- `utils/geo.ts` — WGS-84 ↔ GCJ-02 坐标转换 (前端版)

### 后端

#### Controller 层 (railway-api)

| Controller         | 路径          | 职责                                        |
| ------------------ | ------------- | ------------------------------------------- |
| HealthController   | /api          | GET /health 健康检查                        |
| AuthController     | /api/auth     | 注册/登录, JWT 签发, JdbcTemplate 直接查 DB |
| StationController  | /api/stations | 搜索/详情/城市/站间查询                     |
| TrainController    | /api/trains   | 搜索/路线详情 (含 GeoJSON)                  |
| TransferController | /api/transfer | POST 换乘搜索                               |
| TileController     | /api/tiles    | 矢量瓦片 (MVT PBF)                          |
| UserController     | /api          | 收藏/历史 (JWT 鉴权)                        |
| SyncController     | /api/sync     | 数据同步触发 (Phase 1 占位)                 |

#### Service 层 (railway-service, 9 个 Service)

| Service                | 职责                                               |
| ---------------------- | -------------------------------------------------- |
| TileService            | 矢量瓦片生成, Redis 缓存 (@Cacheable)              |
| MapQueryService        | 站站查询, 车站详情 (途经车次), 城市车站列表        |
| StationSearchService   | 拼音/中文混合搜索, 车次格式过滤                    |
| TrainSearchService     | 车次搜索                                           |
| TransferSearchService  | K-最短路径换乘搜索, 票价计算, 偏好排序             |
| TransferGraphBuilder   | 构建铁路时间依赖图 (JGraphT DirectedWeightedGraph) |
| TransferRankingService | 多目标排序 (时间/换乘/票价)                        |
| RouteGeoJsonService    | WKT → GeoJSON FeatureCollection 转换               |
| RouteMatchingService   | 三阶段车次经行段匹配引擎 (BFS 拓扑匹配)            |

#### Data 层 (railway-data, 7 个 Mapper)

- StationMapper — XML SQL: 矢量瓦片, BBox 查询, 关键字/拼音/城市搜索
- RailwaySegmentMapper — XML SQL: 矢量瓦片, BBox 查询
- TrainRouteMapper — XML SQL: 车次搜索 (ILIKE)
- TrainStopMapper — BaseMapper (纯 Lambda 查询)
- TrainFareMapper — BaseMapper
- TrainSegmentMappingMapper — BaseMapper
- RailwayTopologyMapper — BaseMapper

#### Entity 层 (railway-common, 8 个实体, 4 个枚举, 7 个 DTO)

实体: Station, RailwaySegment, RailwayTopology, TrainRoute, TrainStop, TrainFare, TrainSegmentMapping, User

DTO: StationSearchRequest/Result, TrainSearchRequest/Result, TrainRouteDetail, TransferRequest/Result

枚举: TrainType (G/D/C/Z/T/K/Y/S), RailwayCategory (7 类), StationCategory (12 类), TransferPreference (4 种)

#### 全局配置 (railway-api/config)

- SecurityConfig — Spring Security 无状态 JWT, 公开/受保护路径分离
- JwtAuthFilter — OncePerRequestFilter, Bearer Token 解析
- JwtUtil — HMAC-SHA 签名, 24h 过期
- CorsConfig — 全允许 CORS (开发阶段)
- RedisCacheConfig — 缓存管理器, Jackson JSON 序列化
- JacksonConfig — JavaTimeModule, ISO 日期格式

---

## 3. 依赖与构建配置

### 前端 (package.json)

| 类型 | 依赖                                  | 用途             |
| ---- | ------------------------------------- | ---------------- |
| 框架 | vue 3.5, vue-router 4.5, pinia 2.3    | SPA 核心         |
| UI   | naive-ui 2.41                         | 组件库           |
| 地图 | maplibre-gl 5.2                       | 矢量瓦片地图引擎 |
| HTTP | axios 1.7                             | API 请求         |
| 构建 | vite 6.2, typescript 5.7, vue-tsc 2.2 | 开发与构建       |
| 样式 | tailwindcss 4, @tailwindcss/vite      | 原子化 CSS       |
| 其他 | @vitejs/plugin-vue 5.2                | Vite 插件        |

脚本: dev (vite), build (vue-tsc --noEmit && vite build), preview

### 后端 (Maven)

Spring Boot 3.5.14 管理的依赖: spring-boot-starter-web, spring-boot-starter-security, spring-boot-starter-data-redis, spring-boot-starter-batch

自定义版本: MyBatis-Plus 3.5.16, PostgreSQL JDBC 42.7.5, JTS 1.20.0, pinyin4j 2.5.1, JGraphT 1.5.2, jjwt 0.12.6

### 部署

| 文件               | 用途                                                                            |
| ------------------ | ------------------------------------------------------------------------------- |
| Dockerfile         | 多阶段构建: maven:3.9 编译 → eclipse-temurin:21-jre 运行                        |
| docker-compose.yml | 4 服务: db (PostGIS 17), redis (7-alpine), app (Java), frontend (nginx:alpine)  |
| nginx.conf         | SPA try_files + /api/ 反代到 app:8080                                           |
| .gitignore         | 忽略 target/, node_modules/, dist/, .env, pycache/, .venv/, *.geojson, .claude/ |

无 CI/CD 配置文件 (无 .github/workflows, .gitlab-ci.yml)

---

## 4. 数据交互层

### API 定义与封装

前端 (src/services/):

- `api.ts` → `axios.create({ baseURL: '/api', timeout: 30000 })` + response 拦截器 (错误日志)
- `stationService` → searchStations(q, city?, limit), getStation(id)
- `trainService` → searchTrains(q, type?, limit), getTrainRoute(no)
- `transferService` → searchTransfer(TransferRequest) → POST /api/transfer/search

后端 API 路由汇总:

| 方法   | 路径                               | 控制器             | 鉴权   |
| ------ | ---------------------------------- | ------------------ | ------ |
| GET    | /api/health                        | HealthController   | 公开   |
| POST   | /api/auth/register                 | AuthController     | 公开   |
| POST   | /api/auth/login                    | AuthController     | 公开   |
| GET    | /api/stations/search               | StationController  | 公开   |
| GET    | /api/stations/{id}                 | StationController  | 公开   |
| GET    | /api/stations/city/{city}          | StationController  | 公开   |
| GET    | /api/stations/between              | StationController  | 公开   |
| GET    | /api/trains/search                 | TrainController    | 公开   |
| GET    | /api/trains/{no}/route             | TrainController    | 公开   |
| POST   | /api/transfer/search               | TransferController | 公开   |
| GET    | /api/tiles/{layer}/{z}/{x}/{y}.pbf | TileController     | 公开   |
| GET    | /api/favorites                     | UserController     | 需登录 |
| POST   | /api/favorites                     | UserController     | 需登录 |
| DELETE | /api/favorites/{id}                | UserController     | 需登录 |
| GET    | /api/history                       | UserController     | 需登录 |
| POST   | /api/history                       | UserController     | 需登录 |
| POST   | /api/sync/trigger                  | SyncController     | 需登录 |

请求/响应模型: 统一使用 com.railwaymap.common.dto 下的 DTO, 从后端直接返回 JSON。前端 types/ 下有手工维护的 TypeScript 接口, 与后端并非自动同步 (无 OpenAPI 生成)。

参数校验: 前端无表单校验库, 后端无 JSR-303/class-validator 注解, 仅 AuthController 有基本字符串长度检查。

API 版本控制: 无版本号策略, 路径直接以 /api/ 前缀。

### 数据模型

数据库: PostgreSQL 17 + PostGIS 3.5, 共 9 张表:

- railway_segments (铁路线段, LINESTRING 4326 空间索引)
- stations (车站, POINT 4326 空间索引, 拼音索引)
- railway_topology (线段连通关系, UNIQUE(seg_a, seg_b))
- train_routes (车次主表, UNIQUE train_no)
- train_stops (途经站序, FK→train_routes, FK→stations)
- train_fares (票价, UNIQUE(train_no, from_station, to_station))
- train_segment_mapping (车次↔铁路线段映射, 含置信度/匹配方法)
- users (用户, BCrypt 哈希, UNIQUE username)
- user_favorites (收藏, JSONB data, UNIQUE(user, type, target))
- user_search_history (搜索历史)

索引策略: 所有空间列都有 GIST 索引, 关键查询列有 B-tree 索引 (name, name_pinyin, city, train_no, station_id)。软删除: train_routes.is_valid (非 MyBatis-Plus 全局逻辑删除, 硬编码)。

前端类型: 手工维护 types/station.ts, types/train.ts, types/transfer.ts, types/map.ts, 与后端 DTO 不完全一致 (例如 TrainSearchResult 后端 LocalTime 类型, 前端 string)。

---

## 5. 状态管理与 UI 层

### 状态管理 (Pinia)

**mapStore — 地图全局状态:**

- center: [108.5, 35.5] # 地图中心点 (经纬度)
- zoom: 5 # 缩放级别
- selectedStationId: null # 当前选中车站
- highlightedTrainNo: null # 高亮车次
- routeGeoJson: null # 高亮路线 GeoJSON 数据
- layerVisibility: { railways, stations }

**searchStore — 搜索状态:**

- activeTab: 'station' # 当前搜索标签
- stationResults: [] # 车站搜索结果
- trainResults: [] # 车次搜索结果
- searchQuery: '' # 搜索关键词
- isSearching: false # 搜索进行中

服务端状态缓存: 无 React Query/SWR。TileService 后端使用 @Cacheable("tiles") Redis 缓存, TTL 1h。

### UI 资源

组件库: Naive UI 2.41 — 使用 NLayout, NAutoComplete, NTabs, NCollapse, NCard, NTimeline, NInput, NSelect, NButton, NDatePicker, NTag, NSpin, NSwitch, NDescriptions, NH3, NMenu 等组件。

样式方案: Tailwind CSS 4 (`@import "tailwindcss"`) + 自定义 CSS (main.css, map.css)

国际化: 无 i18n 配置, 界面固定为中文。

静态资源: /vite.svg 作为 favicon, HTML 语言为 zh-CN。

主题: 使用 Naive UI 默认主题, 无自定义主题覆盖。

---

## 6. 认证与授权

### 认证流程

1. POST /api/auth/register { username, password } → BCrypt 哈希, INSERT users, 返回 JWT
2. POST /api/auth/login { username, password } → SELECT password_hash, BCrypt matches, 返回 JWT
3. 前端存储: JWT 通过 Authorization: Bearer `<token>` 头发送 (目前前端 Axios 未配置 JWT 拦截器自动注入)
4. JwtAuthFilter: 解析 Bearer Token, 验证签名/过期, 设置 SecurityContextHolder, 无 Role 信息 (Collections.emptyList())

### 权限控制

SecurityConfig:

- 公开路径: /api/health, /api/tiles/**, /api/stations/**, /api/trains/**, /api/transfer/search, /api/auth/**
- 受保护路径: /api/favorites/**, /api/history/** → authenticated()
- 其他: authenticated()

Token 配置: HMAC-SHA 签名, railway.jwt.secret 可配置 (环境变量 JWT_SECRET), 默认 24h 过期

问题:

- JWT secret 有硬编码默认值 railwaymap-production-secret-change-in-env (application.yml line 49)
- 无 Token 刷新机制 (前端的 api.ts 拦截器仅 catch error, 不做刷新)
- 无 Role-based 权限 (所有通过认证的用户权限相同)
- CSRF 已禁用 (.csrf(csrf -> csrf.disable())), 因为使用 JWT 无状态方案
- .env 文件被 .gitignore 忽略, 但默认密码 railway123 在 docker-compose.yml 和 application.yml 中明文暴露

---

## 7. 数据库与存储

### 数据库迁移

DDL: `railway-api/src/main/resources/schema.sql` — 作为 Docker 初始化脚本挂载到 `/docker-entrypoint-initdb.d/01-schema.sql`。全部使用 CREATE EXTENSION IF NOT EXISTS 和 CREATE TABLE IF NOT EXISTS 确保幂等。无 Flyway/Liquibase 版本管理。

种子数据: 无。数据来源: OSM GeoJSON 网格 → Spring Batch 导入; 列车时刻表 → Python 爬虫 → import_trains.py

SQL 工具脚本 (railway-scripts/):

- validate_data.sql — 数据完整性校验
- build_topology.sql — 拓扑连接构建

### 其他存储

Redis 7: 仅用于 Spring Cache (@Cacheable("tiles")), 矢量瓦片缓存 TTL 1h。无 Session 存储、消息队列集成。

文件存储: 无 S3/OSS。GeoJSON 网格文件存储在 railway-scripts/data/ 本地, .gitignore 忽略。

消息队列: 无 RabbitMQ/Kafka。

### 数据库连接配置

```yaml
# application.yml

spring.datasource:
  url: jdbc:postgresql://${DB_HOST:localhost}:5432/railwaymap
  username: ${DB_USER:railway}
  password: ${DB_PASSWORD:railway123}
  driver: org.postgresql.Driver
  hikari: max 20, min 5, idle 5min

spring.data.redis:
  host: ${REDIS_HOST:localhost}
  port: ${REDIS_PORT:6379}
```

环境变量通过 Docker Compose environment 块注入: DB_HOST: db, DB_USER: railway, 等。

---

## 8. 环境与部署配置

### 环境配置

| 文件                | 用途                                      |
| ------------------- | ----------------------------------------- |
| application.yml     | 默认配置 (生产环境变量注入)               |
| application-dev.yml | 开发环境覆盖 (localhost 直连, DEBUG 日志) |

应用自定义配置 (railway.*):

- railway.jwt.secret: ${JWT_SECRET:railwaymap-production-secret-change-in-env}
- railway.jwt.expiration: 86400000 (24h)
- railway.tile.cache-ttl: 3600
- railway.tile.railway-min-zoom: 6
- railway.tile.station-min-zoom: 8
- railway.transfer.max-segment-hours: 12
- railway.transfer.max-total-hours: 72
- railway.transfer.default-transfer-wait: 30

### 容器化部署

**Dockerfile (多阶段):**

1. Build: maven:3.9-eclipse-temurin-21 → mvn dependency:go-offline + mvn package -pl railway-api -am
2. Run: eclipse-temurin:21-jre, 仅打包 railway-api, 暴露 8080

**docker-compose.yml:**

- db: PostGIS 17-3.5, 端口 5432, 持久卷 pgdata, healthcheck pg_isready
- redis: redis:7-alpine, 端口 6379, 持久卷 redisdata
- app: 从 Dockerfile 构建, 端口 10010:8080, 依赖健康检查
- frontend: nginx:alpine, 端口 80:80, 静态文件 railway-frontend/dist, nginx 配置挂载

Nginx: try_files $uri $uri/ /index.html (SPA fallback), API 反代到 app:8080 添加 X-Forwarded-* 头

### 开发环境

- 前端: npm run dev → Vite :5173, proxy /api → localhost:10010
- 后端: 启动 RailwayApiApplication, 读取 application-dev.yml, 需要本地 PostgreSQL + Redis
- 无 CI/CD 配置, 无 Kubernetes 配置

---

## 9. 代码逻辑深潜

### 路径 1 (前端): 车站搜索与地图定位

StationSearch.vue:

    用户输入关键词
    → NAutoComplete.onSearch → searchStations(q) [stationService.ts:4]
    → api.get('/stations/search', { params }) [api.ts:3]
    → Vite proxy → Spring Boot → StationController.search() [StationController.java:22]
    → StationSearchService.search() [StationSearchService.java:21]
       → 判断纯英文 → searchByPinyin(keyword) [StationMapper.xml:52]
       → 判断中文 → searchByKeyword(keyword) [StationMapper.xml:29]
       → PostgreSQL ILIKE + CASE WHEN 排序 (精确匹配优先, 枢纽优先)
    → 返回 List<StationSearchResult> → JSON 序列化
    → Axios response → options[] = { label, value, station } [StationSearch.vue:32]
    → 用户选择: mapStore.setCenter(lon, lat) + setZoom(14) + selectStation(id)
    → MapContainer 不响应 store 变化 (缺少 watch)

**关键发现:** 搜索结果是单向的 — 搜索结果仅更新 AutoComplete 下拉框。StationSearch 中有 mapStore.setCenter/setZoom/selectStation, 但 MapContainer 未 watch 这些 store 属性来实际移动地图 — 所以选中车站后地图不会飞过去。

### 路径 2 (前端): 车次路线高亮

TrainSearch.vue:

    用户输入车次号 (如 "G1")
    → 正则匹配 ^[GCDZTKYS] → searchTrains(q) → trainService
    → 用户选择 → highlightTrain(trainNo) + getTrainRoute(trainNo)
    → TrainController.getRoute(no) [TrainController.java:35]
       → 4 次独立 DB 查询: route, stops, mappings, fares (无事务/无 join)
       → 组装 TrainRouteDetail (StopInfo, FareInfo)
       → RouteGeoJsonService.toGeoJson(mappings) [RouteGeoJsonService.java:19]
          → 遍历 mappings → segmentMapper.selectById (N+1 问题!)
          → WKT 文本解析 → GeoJSON FeatureCollection (手写 WKT 解析)
    → 前端 mapStore.routeGeoJson = data.segmentsGeoJson
    → TrainRouteLayer.vue watch effect:
       → 移除旧 source/layer
       → map.addSource('highlighted-route', geojson)
       → 添加发光层 + 主线层 (confidence 颜色, match_method 虚线)

**关键问题:**

1. RouteGeoJsonService.toGeoJson 有 N+1 查询 — 每个 mapping 逐条 selectById
2. WKT 解析是手写的字符串操作, Station.getGeomWkt() 返回的是不存在于 Mapper 结果中的字段 (需要 ST_AsText)
3. segmentsGeoJson 字段类型是 Object (失去类型安全)

### 路径 3 (后端): 换乘搜索 (核心算法)

POST /api/transfer/search { from, to, date, maxTransfers, preference, maxResults }
→ TransferController.search → TransferSearchService.search [TransferSearchService.java:30]

Step 1: TransferGraphBuilder.buildGraph() [TransferGraphBuilder.java:47]

- 查询所有 isValid=true 的 train_routes (全量!)
- 逐车次查询 train_stops (N+1 查询)
- 构建 JGraphT DefaultDirectedWeightedGraph
  - 节点: "STATION:stationName"
  - 边: 相邻站间运行边 (权重 = 运行时间 分钟)
  - 自环: 同站换乘边 (权重 = 30 分钟)

Step 2: YenKShortestPath.getPaths(from, to, maxResults*3)
→ 获取 3 倍于请求数量的候选路径

Step 3: toTransferResult(path, req) [TransferSearchService.java:75]
→ 遍历路径顶点 → 查 train_stops (每对相邻站又一次 N+1)
→ 查 train_fares → 计算票价
→ computeDuration → 再次查询同车次全部 stops

Step 4: 过滤 (换乘数 ≤ maxTransfers, 总耗时 ≤ 72h)

Step 5: TransferRankingService.rank(results, preference)
→ least_time: 按 totalTimeMin 升序
→ least_transfer: 按 transferCount 再 totalTimeMin
→ least_price: 按 totalPriceYuan (default 99999)
→ 截取前 maxResults

Step 6: 返回 { results, total_found, search_time_ms }

**关键问题:**

1. 每次搜索请求都全量重建图 (从 DB 拉所有车次) — 无图缓存
2. 多层 N+1 查询: buildGraph + toTransferResult + computeDuration
3. toTransferResult 中使用字符串拼接构建 SQL (last("AND EXISTS ...")) — SQL 注入风险
4. 图节点键是站名 (STATION:stationName), 不是唯一 ID — 同名站会冲突
5. 换乘边是自环设计 (graph.addEdge(vertex, vertex)) — 对 JGraphT 标准 API 语义不太正确

### 路径 4 (后端): 矢量瓦片生成

GET /api/tiles/{layer}/{z}/{x}/{y}.pbf
→ TileController.getTile → @Cacheable("tiles")
→ TileService.getTile [TileService.java:26]
   → TileUtils.tileToBBox(z,x,y) → Web Mercator → WGS-84 边界框
   → switch(layer):
      "railways" (z≥6): segmentMapper.getVectorTile → StationMapper.xml:6
          → PostGIS ST_AsMVT(ST_AsMVTGeom(...), 'railways', 4096, 'geom')
          → 返回 hex 编码的 MVT 二进制
      "stations" (z≥8): stationMapper.getVectorTile
      default: 空瓦片
   → hexToBytes(): 将 PostGIS 返回的 hex 字符串拼接 + HexFormat 解码
→ ResponseEntity<byte[]> (Content-Type: application/vnd.mapbox-vector-tile, Cache-Control: 1h)

**关键问题:**

1. $envelope 在 XML SQL 中使用 ${envelope} (字符串替换, 不是 #{} 参数化) — SQL 注入风险
2. hex 解析有额外字符串处理 (\\x 前缀) — 脆弱
3. emptyTile() 返回 new byte[0], 和 null 都会跳过缓存 (unless)

---

## 10. 潜在问题与最佳实践

### 安全性

| 问题                                           | 严重程度 | 位置                                                |
| ---------------------------------------------- | -------- | --------------------------------------------------- |
| SQL 注入: StationMapper.xml 使用 ${envelope}   | 中       | 仅 envelope 输入, 由后端构造, 非用户输入            |
| SQL 注入: TransferSearchService 字符串拼接 SQL | 高       | line 93: .last("AND EXISTS ... '" + toName + "'"))" |
| 硬编码 JWT Secret                              | 高       | application.yml line 49                             |
| DB 密码明文                                    | 中       | docker-compose.yml + application.yml                |
| CORS 全放开                                    | 低       | CorsConfig.java (开发阶段)                          |
| BCrypt 密码强度                                | 低       | 使用默认 cost factor, 可以                          |
| Token 无刷新机制                               | 中       | JWT 24h 过期后需重新登录                            |
| .env 被 .gitignore 忽略                        | 好       | 但默认值在 yml 中仍是硬编码                         |

### 性能

| 问题                   | 位置                                       | 建议                                  |
| ---------------------- | ------------------------------------------ | ------------------------------------- |
| 换乘搜索每次全量重建图 | TransferGraphBuilder:47                    | 图应缓存 (Redis/内存), 车次变更时失效 |
| 多层 N+1 查询          | RouteGeoJsonService, TransferSearchService | 使用 JOIN 或批量查询                  |
| 矢量瓦片缓存仅 1h      | RedisCacheConfig:28                        | 矢量瓦片是静态数据, 可永久缓存        |
| 前端无图片优化         | -                                          | 无懒加载/virtual scrolling            |

### 代码质量

| 问题                             | 描述                                                                                                            |
| -------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| 占位组件                         | MapControls, RailwayLayer, StationLayer, SearchSuggestions 均为空组件                                           |
| 类型安全                         | segmentsGeoJson: Object, geom: Object, 多处 Map<String, Object> 作为返回类型                                    |
| Mapper 字段映射不完整            | Station.geomWkt 标注 @TableField(exist=false) 但在 XML 中通过 ST_AsText(geom) AS geom_wkt 返回 — 实际应该能映射 |
| Controller 直接使用 Mapper       | TrainController 注入了 5 个 Mapper, 应该通过 Service 层                                                         |
| AuthController 使用 JdbcTemplate | 没有 UserService, 直接操作 DB                                                                                   |
| 无测试                           | 整个项目无任何测试文件 (.spec.ts, *Test.java)                                                                   |
| SyncController 是占位            | 仅返回 {status: "triggered"}                                                                                    |
| 无请求日志/异常处理              | 无 @ControllerAdvice 全局异常处理, 无 request logging filter                                                    |
| 前端 Pinia store 与组件脱节      | mapStore.selectStation 没有对应的 MapContainer.watch 联动                                                       |

### 可维护性

| 问题                 | 描述                                                              |
| -------------------- | ----------------------------------------------------------------- |
| 无 API 文档自动生成  | 虽有 springdoc 配置, 但无 Swagger 注解 (无 @Operation, @Schema)   |
| 无数据库迁移版本控制 | 全量 DDL, 无 Flyway/Liquibase                                     |
| 前后端类型不同步     | TypeScript 接口手工维护, 无 OpenAPI 生成                          |
| 硬编码配置值         | mapStore 初始 center [108.5, 35.5], zoom 5 硬编码                 |
| 日志级别 DEBUG       | application.yml 设置了 com.railwaymap: DEBUG, 生产环境应改为 INFO |

---

## 总结

已完成的核心功能:

- 矢量瓦片地图渲染 (MapLibre GL + PostGIS ST_AsMVT)
- 7 类铁路线 + 12 类车站的图层样式 (match/interpolate 表达式)
- 车站中文/拼音/首字母搜索 (PostgreSQL ILIKE)
- 车次查询与路线 GeoJSON 高亮 (BFS 拓扑匹配)
- K-最短路径多次换乘搜索 (JGraphT Yen's algorithm)
- JWT 用户认证 (注册/登录/收藏/历史)
- Docker Compose 一键部署

Phase 标注未完成的功能 (来自开发计划文档及占位代码):

- Phase 2: 独立的 RailwayLayer/StationLayer 组件 (目前逻辑在 MapContainer 内)
- Phase 3: 搜索建议面板
- Phase 5: 地图控件 (图层筛选/全屏/测距)
- Phase 7: 用户系统完善 (邮箱验证/角色管理/OAuth)
- 数据同步触发器

最有价值的改进方向:

1. 换乘图缓存 (避免每次请求全量重建)
2. 消除 N+1 查询 (批量查询、JOIN)
3. 全局异常处理 @ControllerAdvice
4. Backend API 文档 (springdoc 注解)
5. TrainController 业务逻辑下沉到 Service 层
6. 前端 make MapContainer 响应 mapStore 的变化 (watch)
```