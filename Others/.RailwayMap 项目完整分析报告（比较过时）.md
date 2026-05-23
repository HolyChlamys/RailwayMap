# RailwayMap 项目完整分析报告

> 中国铁路地图与多次中转路线规划系统 — 全栈分析
> 分析日期: 2026-05-18 | 分支: master | 提交: 4c4ff728

---

## 0. 项目识别与目录结构

### 项目概述

RailwayMap 是一个前后端分离的 Maven 多模块 monorepo，提供中国铁路地图可视化、车站/车次搜索、多次中转路线规划、矢量瓦片渲染等功能。

### 完整目录树

```
RailwayMap/
├── pom.xml                       # Maven 根 POM (Spring Boot 3.5.14 parent, 5 个子模块)
├── docker-compose.yml            # 4 服务编排: db(postgis) + redis + app(Spring Boot) + frontend(nginx)
├── Dockerfile                    # 多阶段构建: maven:3.9-temurin-21 → eclipse-temurin:21-jre
├── nginx.conf                    # 前端 SPA 托管 + /api/ 反向代理到 app:8080
├── .gitignore                    # Maven/Node/Python/IDE/Data/Claude 忽略规则
├── CLAUDE.md                     # 项目级 Claude 指令文件 (已详尽)
│
├── railway-frontend/             # Vue 3 SPA 前端 (Vite 6 + TypeScript 5.7 + Tailwind CSS 4)
│   ├── index.html                # 中文 SPA 壳, 内联 SVG favicon
│   ├── package.json              # 运行时依赖 10 个, 开发依赖 6 个
│   ├── vite.config.ts            # Vite 配置 (5173 端口, /api → localhost:10010)
│   ├── tsconfig.json             # strict 模式, ES2022, bundler 解析, @/* 别名
│   ├── public/
│   │   └── map-style.json        # MapLibre 底图样式 (MapTiler Streets v2 中文矢量瓦片)
│   └── src/
│       ├── main.ts               # 应用入口: 挂载 Pinia/Router, 自动暗色模式, mock 数据播种
│       ├── App.vue               # 根布局组件: 协调所有面板/地图/搜索/AI 助手交互
│       ├── api/                  # Axios HTTP 层 (4 文件)
│       ├── types/                # TypeScript 接口/类型 (4 文件, 手工维护)
│       ├── stores/               # Pinia 状态管理 (6 个 store)
│       ├── composables/          # 组合式函数 (6 个)
│       ├── components/           # Vue 组件 (19 个, 按 layout/map/search/panels/agent/shared 分层)
│       ├── assets/styles/        # CSS tokens/base/fonts
│       └── router/index.ts       # 单一 catch-all 路由 (SPA shell 模式)
│
├── railway-api/                  # Maven 子模块 — REST API 入口
│   ├── pom.xml                   # 依赖: spring-web, spring-security, jjwt 0.12.6
│   └── src/main/
│       ├── java/com/railwaymap/api/
│       │   ├── RailwayApiApplication.java   # @SpringBootApplication + @MapperScan
│       │   ├── controller/        # 8 个 Controller (Health/Auth/Station/Train/Transfer/Tile/User/Sync)
│       │   └── config/            # 6 个配置 (Security/JWT/CORS/Jackson/Redis)
│       └── resources/
│           ├── application.yml    # 端口 10010, PostGIS 数据源, Redis, MyBatis-Plus, 自定义 railway.* 配置
│           └── schema.sql         # DDL: 10 张表 (含 PostGIS 扩展和空间索引)
│
├── railway-service/              # Maven 子模块 — 业务逻辑层
│   ├── pom.xml                   # 依赖: jgrapht 1.5.2, spring-data-redis
│   └── src/main/java/com/railwaymap/service/
│       ├── map/                  # TileService, MapQueryService
│       ├── route/                # RouteGeoJsonService, RouteMatchingService
│       ├── search/               # StationSearchService, TrainSearchService
│       └── transfer/             # TransferGraphBuilder, TransferSearchService, TransferRankingService
│
├── railway-data/                 # Maven 子模块 — 数据访问层
│   ├── pom.xml                   # 依赖: mybatis-plus-spring-boot3-starter 3.5.16, postgresql 42.7.5
│   └── src/main/
│       ├── java/com/railwaymap/data/mapper/  # 7 个 Mapper 接口
│       └── resources/mapper/     # 3 个 MyBatis XML (RailwaySegment/Station/TrainRoute)
│
├── railway-common/               # Maven 子模块 — 共享模块
│   ├── pom.xml                   # 依赖: jts-core 1.20, pinyin4j 2.5.1, jackson, lombok
│   └── src/main/java/com/railwaymap/common/
│       ├── entity/               # 8 个实体类 (对应 8 张核心表)
│       ├── dto/                  # 7 个 DTO (请求/响应)
│       ├── enums/                # 4 个枚举 (RailwayCategory, StationCategory, TrainType, TransferPreference)
│       ├── util/                 # 3 个工具类 (GeoUtils, PinyinUtils, TileUtils)
│       └── config/               # SpatialConfig (JTS GeometryFactory SRID 4326)
│
├── railway-batch/                # Maven 子模块 — 批处理 (独立启动类)
│   ├── pom.xml                   # 依赖: spring-boot-starter-batch
│   └── src/main/java/com/railwaymap/batch/
│       ├── BatchApplication.java
│       ├── job/                  # GridImportJob, ScheduleImportJob, FileSwitchingReader
│       ├── processor/            # RailwaySegmentProcessor, StationProcessor
│       ├── reader/               # GeoJsonItemReader, GridQueueReader
│       ├── writer/               # PostgisBatchItemWriter
│       └── listener/             # ImportProgressListener
│
└── railway-scripts/              # 独立 Python 数据流水线
    ├── china_boundary.py         # Overpass API → 中国陆地边界 GeoJSON
    ├── grid_splitter.py          # 渔网网格划分 (1°×1°, 0.05° 重叠, 蛇形排序)
    ├── grid_fetcher.py           # Overpass API → 逐网格抓取铁路/车站数据 (断点续传)
    ├── import_data.py            # GeoJSON → PostgreSQL (psycopg2, 分批提交)
    ├── import_gpkg.py            # GeoPackage → PostgreSQL (备选数据源)
    ├── train_crawler.py          # liecheba.com 车次爬虫 v1 (HTMLParser)
    ├── train_crawler_playwright.py # liecheba.com 车次爬虫 v2 (正则解析, 断点续传)
    ├── fix_train_data.py         # 车次数据修复 (时间字段清理/填补)
    ├── import_trains.py          # 车次 JSON → PostgreSQL (train_routes/stops/fares)
    ├── build_topology.sql        # 铁路拓扑构建 (CROSS JOIN + ST_Intersects/DWithin)
    ├── validate_data.sql         # 8 项数据完整性校验
    └── check_progress.py         # 数据抓取进度监控 (无数据库依赖)
```

**Monorepo 管理:** Maven `<modules>` 聚合，无 Lerna/Nx/Turborepo。前端独立 npm 项目，不在 Maven 管理中。

---

## 1. 架构概览

### 前端架构

| 维度 | 技术 | 说明 |
|------|------|------|
| 框架 | Vue 3.5 + Composition API (`<script setup>`) | SPA 单页应用 |
| 状态管理 | Pinia 2.3 | 6 个独立 store，组合式 API 风格 |
| 路由 | Vue Router 4.5 | 单一 catch-all 路由，所有面板切换由 Pinia + 条件渲染驱动 |
| UI 基元 | Radix Vue 1.9 (Popover, ToggleGroup, Dialog) | 无样式无障碍组件 |
| 图标 | Lucide Vue Next 0.468 | 轻量 stroke 图标集 |
| 地图引擎 | MapLibre GL JS 5.2 | WebGL 矢量瓦片渲染 |
| 底图 | MapTiler Streets v2 (自定义 map-style.json) | 中文矢量瓦片 |
| CSS | Tailwind CSS 4 + 自定义 tokens.css | Railway Signal Industrial 设计系统 |
| HTTP | Axios 1.7 (baseURL `/api`, 15s 超时) | 响应拦截器解包 `response.data` |
| 工具库 | @vueuse/core 12.8 (useDebounceFn, onClickOutside 等) | |
| 动画 | motion-v 2.2 | Vue 动画库 |
| 构建 | Vite 6 + TypeScript 5.7 (strict) | 开发端口 5173, proxy /api → localhost:10010 |

**设计系统 — Railway Signal Industrial:**
- **颜色体系:** 铁路信号灯颜色 (signal-red `#d63031`, amber `#fdcb6e`, green `#00b894`, blue `#0984e3`, caution `#e17055`)
- **字体:** JetBrains Mono (车次号/时间), Noto Serif SC (品牌/标题), PingFang SC (正文)
- **材质:** 玻璃面板 (backdrop-filter blur), 纸质纹理 (SVG feTurbulence)
- **动效:** 机械缓动曲线 (cubic-bezier 模仿铁路道岔运动)

### 后端架构

| 维度 | 技术 | 说明 |
|------|------|------|
| 运行时 | Java 21 | |
| 框架 | Spring Boot 3.5.14 | |
| ORM | MyBatis-Plus 3.5.16 | 混合 XML SQL + LambdaQueryWrapper |
| 安全 | Spring Security + JWT (jjwt 0.12.6) + BCrypt | 无状态会话 |
| 缓存 | Spring Data Redis (Redis 7) | 默认 TTL 1h, 专用 tiles 缓存 |
| 批处理 | Spring Batch | OSM GeoJSON 网格数据导入 |
| 图算法 | JGraphT 1.5.2 | Yen's K-最短路径 |
| 空间数据 | JTS 1.20 + PostGIS 3.5 | WGS-84 (SRID 4326), GCJ-02 坐标转换 |
| 拼音 | pinyin4j 2.5.1 | 中文站名 → 拼音搜索 |
| JSON | Jackson + JavaTimeModule | ISO-8601 时间格式 |
| 构建 | Maven + spring-boot-maven-plugin | 多阶段 Docker 构建 |

### 模块依赖链

```
railway-api (Web 层)
  ├── spring-boot-starter-web
  ├── spring-boot-starter-security
  └──→ railway-service
        ├── jgrapht-core 1.5.2
        ├── spring-boot-starter-data-redis
        └──→ railway-data
              ├── mybatis-plus-spring-boot3-starter 3.5.16
              ├── postgresql 42.7.5
              └──→ railway-common
                    ├── jts-core 1.20
                    ├── pinyin4j 2.5.1
                    ├── jackson-databind
                    └── lombok

railway-batch (独立启动类 BatchApplication)
  ├── spring-boot-starter-batch
  └──→ railway-service (复用 service + data)

railway-scripts: 独立 Python 3 脚本 (psycopg2, shapely, sqlite3)
railway-frontend: 独立 npm 项目 (Vite)
```

### 完整数据流

```
用户交互 (Vue Component 点击/输入)
  → Pinia Store action (如 searchStore.setQuery)
  → Composable watcher (如 useStationSearch 200ms 防抖)
  → 本地缓存过滤 (当前 mock 模式) 或 Axios HTTP 请求 (/api/...)
  → [开发] Vite proxy → [生产] Nginx → Spring Boot :10010
  → JwtAuthFilter (解析 Authorization: Bearer <token>)
  → Controller (参数绑定: @RequestBody/@ModelAttribute/@PathVariable)
  → Service (业务逻辑: 图构建/空间查询/路线匹配)
  → Mapper (MyBatis XML SQL 或 BaseMapper CRUD)
  → PostgreSQL + PostGIS (空间索引 GIST, ILIKE 模糊搜索, ST_AsMVT 矢量瓦片)
  → 查询结果 → Service 组装 DTO → Controller 返回 JSON
  → Axios Response interceptor (解包 response.data)
  → Pinia Store 更新响应式状态
  → Vue Component 重渲染 (Composition API 响应式追踪)
  → MapLibre GL 地图更新 (flyTo / 图层 visibility / 高亮)
```

---

## 2. 核心模块识别

### 前端核心模块

#### 路由配置
- **文件:** `railway-frontend/src/router/index.ts`
- **策略:** 单一 catch-all 路由 `/:pathMatch(.*)*`，渲染空 div
- **原因:** 所有面板切换由 Pinia store 状态 + `v-if` 条件渲染驱动，不使用页面跳转
- **预留:** 未来可能用于 query-param 驱动的深度链接导航

#### 入口与根组件
- **`main.ts`:** 创建 Vue 应用 → 安装 Pinia/Router → 导入全局 CSS → 设置自动暗色模式 (`prefers-color-scheme` 媒体查询) → 挂载到 `#app` → 播种 mock 数据到 stationStore/trainStore
- **`App.vue`:** 根布局 shell — 14 个子组件通过 `v-if` 按 store 状态条件显示。所有跨组件交互通过 `handleNavigate(type, action)` 统一分发 (站名/车次号/城市名的超链接点击)

#### 全局状态存储 (6 个 Store)
| Store | 核心状态 | 职责 |
|-------|---------|------|
| `mapStore` | viewport, entryPhase, layerVisibility, focusCity/StationId/TrainNo | 地图视口 + 图层开关 + 当前焦点 |
| `searchStore` | activeTab, query, results, isDropdownOpen | 搜索栏 UI 状态 (车站/车次/城市三 tab) |
| `stationStore` | currentStationId, stationCache (Map), allTrainsAtStation | 车站数据缓存 + 当前选中 |
| `trainStore` | currentTrainNo, trainCache (Map) | 车次数据缓存 + 当前选中 |
| `routePlanStore` | plans, activePlanIndices | 多路线方案 + 筛选状态 |
| `agentStore` | messages, panelState, isProcessing | AI 对话消息 + 面板开关 |

#### 组合式函数 (6 个)
| Composable | 返回 | 副作用 |
|------------|------|--------|
| `useMap` | map (shallowRef), flyTo, fitBounds, 图层操作方法 | 创建/销毁 MapLibre 实例, 模拟加载进度 |
| `useMapInteraction` | void | 注册地图 click/hover 事件 → station 交互回调 |
| `useStationSearch` | performSearch, getHot* | watch query+tab, 200ms 防抖本地过滤 |
| `useAgentChat` | sendMessage | 正则意图解析 → store dispatch (mock 版) |
| `useRouteAnimation` | svgContent, generateSvg | watch routePlanStore → 生成 SVG 动画路径 |
| `useKeyboard` | void | 全局 ⌘K/Escape 快捷键注册 |

### 后端核心模块

#### Controller 层 (8 个)
| Controller | 路径前缀 | 端点 | 鉴权 | 注入依赖 |
|------------|---------|------|------|---------|
| HealthController | `/api` | GET /api/health | 公开 | 无 |
| AuthController | `/api/auth` | POST register, POST login | 公开 | JdbcTemplate, PasswordEncoder, JwtUtil |
| StationController | `/api/stations` | GET search, /{id}, /city/{city}, /between | 公开 | StationSearchService, MapQueryService |
| TrainController | `/api/trains` | GET search, GET /{no}/route | 公开 | TrainSearchService + 5 个 Mapper + RouteGeoJsonService |
| TransferController | `/api/transfer` | POST /search | 公开 | TransferSearchService |
| TileController | `/api/tiles` | GET /{layer}/{z}/{x}/{y}.pbf | 公开 | TileService |
| UserController | `/api` | CRUD /favorites, /history | 需登录 | JdbcTemplate |
| SyncController | `/api/sync` | POST /trigger | 需登录 | 无 (桩实现) |

#### Service 层 (9 个)
| Service | 核心方法 | 关键依赖 |
|---------|---------|---------|
| TileService | getTile(layer, z, x, y) → MVT bytes | RailwaySegmentMapper, StationMapper, TileUtils |
| MapQueryService | getStationDetail, findSegmentsBetween, getCityStations | StationMapper, RailwaySegmentMapper 等 |
| RouteGeoJsonService | toGeoJson(mappings) → FeatureCollection | RailwaySegmentMapper, 手写 WKT 解析 |
| RouteMatchingService | matchSegment, precomputeAllMappings (3 阶段匹配) | 6 个 Mapper, BFS 拓扑搜索 + 距离回退 |
| StationSearchService | search(q, city, limit), searchByCity | StationMapper, 拼音/关键字智能路由 |
| TrainSearchService | search(q, type, limit) | TrainRouteMapper |
| TransferGraphBuilder | buildGraph() → JGraphT 有向加权图 | 4 个 Mapper, 全量构建 (无缓存) |
| TransferSearchService | search(TransferRequest) → 路线方案列表 | TransferGraphBuilder, YenKShortestPath |
| TransferRankingService | rank(results, preference) → 排序结果 | 无 (纯排序逻辑) |

#### Mapper 层 (7 个接口 + 3 个 XML)
| Mapper | 实体 | 自定义 SQL (XML/注解) |
|--------|------|----------------------|
| RailwaySegmentMapper | RailwaySegment | getVectorTile (ST_AsMVT), findByBBox |
| StationMapper | Station | getVectorTile, findByBBox, searchByKeyword, searchByPinyin, searchByCity, updatePinyin |
| TrainRouteMapper | TrainRoute | searchTrains (ILIKE 前缀匹配) |
| TrainStopMapper | TrainStop | 无 (BaseMapper 自动 CRUD) |
| TrainFareMapper | TrainFare | 无 |
| TrainSegmentMappingMapper | TrainSegmentMapping | 无 |
| RailwayTopologyMapper | RailwayTopology | 无 |

#### 实体层 (8 个)
`RailwaySegment`, `Station`, `RailwayTopology`, `TrainRoute`, `TrainStop`, `TrainFare`, `TrainSegmentMapping`, `User`

#### DTO 层 (7 个)
`StationSearchRequest/Result`, `TrainSearchRequest/Result`, `TrainRouteDetail`, `TransferRequest`, `TransferResult`

#### 枚举层 (4 个)
`RailwayCategory` (7 值: conventional/high_speed/rapid_transit/...), `StationCategory` (12 值: major_hub 到 other_facility), `TrainType` (8 值: G/D/C/Z/T/K/Y/S), `TransferPreference` (4 值: least_time/least_transfer/night_train/least_price)

---

## 3. 依赖与构建配置

### 前端 (`package.json`)

**运行时依赖 (10):**
| 包 | 版本 | 用途 |
|----|------|------|
| vue | ^3.5.13 | 前端框架 |
| vue-router | ^4.5.0 | SPA 路由 |
| pinia | ^2.3.0 | 状态管理 |
| axios | ^1.7.9 | HTTP 客户端 |
| maplibre-gl | ^5.2.0 | WebGL 地图引擎 |
| radix-vue | ^1.9.17 | 无样式无障碍 UI 基元 |
| lucide-vue-next | ^0.468.0 | 图标库 |
| @vueuse/core | ^12.8.0 | Vue 组合式工具集 |
| motion-v | ^2.2.1 | 动画库 |

**开发依赖 (6):**
| 包 | 版本 | 用途 |
|----|------|------|
| vite | ^6.2.0 | 构建工具 |
| @vitejs/plugin-vue | ^5.2.3 | Vue SFC 编译 |
| typescript | ~5.7.3 | 类型检查 |
| vue-tsc | ^2.2.0 | Vue + TS 类型检查 |
| tailwindcss | ^4.0.0 | 原子化 CSS 框架 |
| @tailwindcss/vite | ^4.0.0 | Tailwind Vite 插件 |

**脚本命令:**
- `dev` — `vite` (开发服务器 :5173)
- `build` — `vue-tsc --noEmit && vite build` (类型检查 + 生产构建)
- `preview` — `vite preview` (预览生产构建)

### 后端 (Maven POM)

**Spring Boot 3.5.14** 继承管理所有 Spring 依赖版本。

**核心依赖版本:**

| 依赖 | 版本 | 作用域 |
|------|------|--------|
| spring-boot-starter-web | (继承) | REST API |
| spring-boot-starter-security | (继承) | 认证授权 |
| spring-boot-starter-data-redis | (继承) | Redis 缓存 |
| spring-boot-starter-batch | (继承) | 批处理 (仅 batch 模块) |
| mybatis-plus-spring-boot3-starter | 3.5.16 | ORM (data 模块) |
| postgresql | 42.7.5 | JDBC 驱动 (data 模块) |
| jgrapht-core | 1.5.2 | 图算法 (service 模块) |
| jts-core | 1.20.0 | 空间几何 (common 模块) |
| pinyin4j | 2.5.1 | 拼音转换 (common 模块) |
| jjwt (api/impl/jackson) | 0.12.6 | JWT (api 模块) |
| lombok | (继承, optional) | 代码生成 |

### 全栈共享配置

- **TypeScript:** 统一 tsconfig.json (strict, ES2022, bundler 解析)
- **Docker Compose:** 4 服务编排 (db + redis + app + frontend)
- **Nginx:** SPA 托管 + API 反向代理
- **无 ESLint/Prettier/Husky/CI 配置:** 项目目前缺少代码质量工具和 CI/CD 管道

### 环境变量

| 变量 | 默认值 | 用途 |
|------|--------|------|
| DB_HOST | localhost | PostgreSQL 主机 |
| DB_USER | railway | 数据库用户 |
| DB_PASSWORD | railway123 | 数据库密码 |
| REDIS_HOST | localhost | Redis 主机 |
| REDIS_PORT | 6379 | Redis 端口 |
| JWT_SECRET | railwaymap-production-secret-change-in-env | JWT 签名密钥 (硬编码默认值) |

---

## 4. 数据交互层

### 前端 API 封装

**Axios 客户端 (`src/api/client.ts`):**
- `baseURL: '/api'`, `timeout: 15000ms`
- **响应拦截器:** 自动解包 `response.data` (调用方直接获取业务数据)
- **错误拦截器:** 提取 `error.response.data.message` 或 `error.message`，console.error + re-throw
- **请求拦截器:** 预留 JWT token 注入位置 (当前未实现)

**API 模块 (3 个文件):**

```
stationApi:  getById(id) → GET /stations/{id}
             search(q, limit) → GET /stations/search
             getByCity(city) → GET /stations/by-city
             getAllTrains(stationId) → GET /stations/{id}/trains

trainApi:    getByNo(no) → GET /trains/{no}
             search(q, limit) → GET /trains/search

routePlanApi: plan(constraint) → POST /plan
```

**当前状态:** 所有 API 模块已定义但未被 store 调用 — 项目目前使用 `mockData.ts` 中的硬编码数据 (23 个车站, 9 趟车次)。

### 前端类型定义 (4 个文件, 手工维护)

```
station.ts:  StationType (12 种), Station, StationSearchResult, CityResult
train.ts:    TrainType (8 种), Train, TrainStop, TrainTypeInfo
map.ts:      MapViewport, LayerVisibility, MapEntryPhase (6 阶段), MapStyleMode
route.ts:    RouteSegment, RoutePlan, RouteConstraint, ROUTE_PALETTE
agent.ts:    MessageRole, ChatMessage, AgentPanelState, QuickSuggestion
```

类型为手工维护，非从 OpenAPI 生成。后端 Entity/DTO 是 Java 类，前后端类型各自独立定义。

### 后端 API 路由注册

所有 Controller 使用 `@RequestMapping` 注解声明路径前缀：
- 公开端点 (SecurityConfig permitAll): `/api/health`, `/api/tiles/**`, `/api/stations/**`, `/api/trains/**`, `/api/transfer/search`, `/api/auth/**`
- 需认证端点: `/api/favorites/**`, `/api/history/**`, `/api/sync/trigger`

### 数据库实体关系

```
train_routes (1) ──→ (N) train_stops (N) ──→ (1) stations
     │                      │
     │                      └── train_segment_mapping (N) ──→ (1) railway_segments
     │                                                                  │
     └── train_fares (N)                                          railway_topology
                                                              (seg_a, seg_b 自引用)

users (1) ──→ (N) user_favorites, user_search_history
```

**关键设计点:**
- `train_stops.station_name` 是字符串 (非规范化的站名副本)，同时有可空的 `station_id` FK 到 `stations`
- `train_segment_mapping` 关联车次停站对 (`train_no, from_station, to_station`) 到线路段 (`seg_id`)，带匹配置信度
- `railway_topology` 存储线路段之间的有向连接关系 (CROSS JOIN + PostGIS 空间分析的结果)
- 所有空间表使用 GIST 索引，关键查询列使用 B-tree 索引
- `geom` 列在 Entity 中标记为 `exist = false` (不参与常规 CRUD)，通过 `ST_AsText` 在 XML SQL 中手动转换为 WKT 文本

---

## 5. 状态管理与 UI 层

### Pinia Store 详细分析

所有 6 个 store 采用 Composition API 风格 (`defineStore('name', () => { ... })`)。

#### mapStore — 地图状态中枢
```
state:  viewport: { center: [108.0, 30.0], zoom: 4.2, bearing: 0, pitch: 0 }
        entryPhase: 'idle' | 'background' | 'lines' | 'stations' | 'ui' | 'complete'
        layerVisibility: { stations: Record<type, bool>, lines: Record<type, bool> }
        focusCity / focusStationId / focusTrainNo: string | null

getters: isEntryComplete
actions: setViewport, setEntryPhase, toggleStationType, toggleLineType,
         setFocusCity, setFocusStation, setFocusTrain, clearAllFocus
```
初始视口中心 [108.0, 30.0] (中国中部), zoom 4.2 (全国视野)。默认可见: 所有客运站类型 + 干线和支线铁路，隐藏货运站和专用线。

#### searchStore — 搜索栏 UI 状态
```
state:  activeTab: 'station' | 'train' | 'city'
        query / results (SearchResultItem[]) / isDropdownOpen / loading
getters: placeholder (tab 感知提示文本), hasResults
actions: setTab, setQuery, setResults, openDropdown, closeDropdown, clear, setLoading
```
搜索结果统一为 `SearchResultItem` 联合类型，包含 `type`, `label`, `sub`, `action` 字段，支持车站/车次/城市三种结果在统一下拉列表中混合展示。

#### stationStore / trainStore — 数据缓存
```
stationStore: currentStationId, stationCache (Map<string, Station>), allTrainsAtStation
trainStore:   currentTrainNo, trainCache (Map<string, Train>)
```
缓存模式: 使用 `Map<string, Entity>` 内存缓存，避免重复 API 调用。当前由 `main.ts` 中的 mock 数据播种。`getStation(id)` / `getTrain(no)` 返回缓存或 undefined。

#### routePlanStore — 路线方案状态
```
state:  plans (RoutePlan[]), activePlanIndices (number[])
getters: hasPlans, activePlans (过滤后的方案)
actions: setPlans, filterByConstraint (按列车类型/最大换乘次数筛选), resetFilter, clear
```
支持多条路线同时在地图上高亮显示。`MOCK_ROUTE_COORDS` 提供预定义的 SVG 坐标路径。筛选操作在客户端内存中执行。

#### agentStore — AI 对话状态
```
state:  messages (ChatMessage[]), panelState ('open' | 'closed'), isProcessing
getters: isOpen, messageCount, defaultQuickSuggestions (3 个预设)
actions: openPanel (首次自动添加欢迎消息), closePanel, togglePanel,
         addMessage, setProcessing, clearMessages
```

### UI 组件树

```
App.vue (根布局 Shell)
├── AppHeader (Logo + SearchBar + 暗色模式/关于/用户按钮)
│   └── SearchBar (Tab 切换 + Input + ⌘K 快捷键)
│       └── SearchDropdown (搜索结果列表)
├── MapContainer (MapLibre 实例挂载 + 自定义矢量瓦片图层 + 入场动画)
│   └── MapLoadingOverlay (信号灯进度条动画)
├── StationPanel (左侧浮窗 — 站名/类型/城市/车次列表)
├── TrainPanel (左侧浮窗 — 车次号/类型/始发终到/经停站时间轴)
├── TimetableModal (中央模态窗 — 所有经停车次表格, Teleport to body)
├── LegendPanel (右上图例 — 可折叠, checkbox 图层开关)
├── MapControls (放大/缩小/定位/图层切换按钮组)
├── RouteAnimationLayer (SVG 叠加层 — 流动虚线/实线路线动画)
├── MapAtmosphere (纸质纹理 + 指南针 + 比例尺)
├── AgentFab (浮动操作按钮 — 红-琥珀渐变)
└── AgentPanel (右侧滑入对话面板)
    ├── AgentBubble (消息气泡 — Markdown 文本 + 内嵌路线卡片)
    │   └── AgentRouteCard (路线方案卡片)
    └── QuickSuggestion chips
```

### 布局策略

- **响应式断点:** 900px (平板) / 640px (手机)
- **左侧面板:** 360px 宽, `--panel-w` CSS 变量
- **右侧 Agent:** 400px 宽, `--agent-w` CSS 变量
- **顶部 Header:** 52px 高, `--header-h` CSS 变量
- **图例:** 240px 宽
- **z-index 分层:** 地图 0, 面板 50, Header 100, Agent 150, Modal 200
- **面板互斥:** 同一时间仅 StationPanel 或 TrainPanel 显示 (通过 store 互斥清除)

### 样式系统

```
tokens.css:  CSS 自定义属性
  ├── 颜色: --signal-red/amber/green/blue/caution, --surface-map, --route-1~6
  ├── 字体: --font-serif (Noto Serif SC), --font-sans (PingFang SC), --font-mono (JetBrains Mono)
  ├── 间距: 4px 基础单位 (--space-1 到 --space-12)
  ├── 圆角: --radius-sm/md/lg/pill
  ├── 阴影: --shadow-sm 到 --shadow-xl + --shadow-signal (信号灯辉光)
  ├── 动效: --ease-mechanical/staccato/smooth, --duration-fast/normal/slow/glacial
  └── 暗色模式: .dark 类覆盖 (玻璃/文字/边框/阴影)

base.css: CSS Reset + 全局排版 + Tailwind 导入 + MapLibre popup 覆盖
fonts.css: @font-face (JetBrains Mono 400-700, Noto Serif SC 400-700)
```

### 国际化 (i18n)

**当前状态: 无 i18n 支持。** 所有 UI 文本硬编码为简体中文。前端无 `vue-i18n` 或类似库集成。

---

## 6. 认证与授权

### 认证流程

```
用户注册/登录 → POST /api/auth/register 或 /api/auth/login
  → AuthController (直接使用 JdbcTemplate, 无 Service 层)
    → 注册: 校验 username ≥ 3 字符, password ≥ 6 字符 → BCrypt 哈希 → INSERT users
    → 登录: SELECT password_hash FROM users WHERE username = ? → BCrypt 比对
  → JwtUtil.generateToken(username) → HMAC-SHA 签名, 默认 24h 过期
  → 返回 { token, username }

后续请求:
  → Authorization: Bearer <token>
  → JwtAuthFilter (OncePerRequestFilter) 提取 token
  → JwtUtil.validateToken(token) → 提取 username
  → SecurityContextHolder 设置 UsernamePasswordAuthenticationToken (空权限列表)
  → Controller 通过 @AuthenticationPrincipal UserDetails 获取用户身份
```

### 安全配置详情

- **CSRF:** 已禁用 (`.csrf(csrf -> csrf.disable())`) — 适用于 REST API + JWT 无状态模式
- **会话:** 无状态 (`SessionCreationPolicy.STATELESS`)
- **密码编码:** BCryptPasswordEncoder
- **JWT 密钥:** 从 `railway.jwt.secret` 配置读取，默认值 `railwaymap-production-secret-change-in-env` (硬编码)
- **Token 过期:** `railway.jwt.expiration` = 86400000ms (24 小时)
- **角色/权限:** 当前未实现 RBAC 或 ABAC — 所有认证用户拥有相同权限，`JwtAuthFilter` 使用空权限列表
- **Token 刷新:** 未实现 — 无 refresh token 机制
- **第三方登录:** 未实现

### 端点访问控制矩阵

| 端点模式 | 鉴权要求 |
|---------|---------|
| `/api/health` | 公开 |
| `/api/tiles/**` | 公开 |
| `/api/stations/**` | 公开 |
| `/api/trains/search`, `/api/trains/**` | 公开 |
| `/api/transfer/search` | 公开 |
| `/api/auth/**` | 公开 |
| `/api/favorites/**` | 需认证 |
| `/api/history/**` | 需认证 |
| 其他 | 需认证 |

---

## 7. 数据库与存储

### 数据库: PostgreSQL 17 + PostGIS 3.5

**连接配置:**
```
URL:      jdbc:postgresql://${DB_HOST:localhost}:5432/railwaymap
用户:     railway
密码:     railway123 (明文在 docker-compose.yml 和 application.yml 中)
连接池:   HikariCP (max 20, min 5 idle, 300s idle timeout, 20s connection timeout)
```

### 10 张数据表

| 表名 | 主键 | 关键列 | 空间列 | 索引 |
|------|------|--------|--------|------|
| `railway_segments` | id (BIGSERIAL) | name, railway, usage, category, electrified, gauge, max_speed, track_count, length_km | geom (LINESTRING, 4326) | GIST(geom), B-tree(category, railway, name) |
| `stations` | id (BIGSERIAL) | name, name_pinyin, city, province, category, passenger, freight, is_hub | geom (POINT, 4326) | GIST(geom), B-tree(name, name_pinyin, city, category) |
| `railway_topology` | id (BIGSERIAL) | seg_a, seg_b (FK→railway_segments), is_connected, gap_meters | — | B-tree(seg_a, seg_b), UNIQUE(seg_a, seg_b) |
| `train_routes` | id (BIGSERIAL) | train_no (UNIQUE), train_type, depart/arrive_station, depart/arrive_time, duration_min, distance_km, is_valid | — | B-tree(train_no, train_type, is_valid) |
| `train_stops` | id (BIGSERIAL) | train_no (FK), seq, station_name, station_id (FK), arrive/depart_time, stay_min | — | B-tree(train_no, station_id, station_name) |
| `train_fares` | id (BIGSERIAL) | train_no (FK), from/to_station, 10 个价格列 (DECIMAL 8,2) | — | B-tree(train_no), UNIQUE(train_no, from, to) |
| `train_segment_mapping` | id (BIGSERIAL) | train_no, from/to_station, seg_id (FK), seg_order, confidence, match_method | — | B-tree(train_no, seg_id), UNIQUE |
| `users` | id (BIGSERIAL) | username (UNIQUE), password_hash, email, role | — | — |
| `user_favorites` | id (BIGSERIAL) | user_id (FK), type, target_id, label, data (JSONB) | — | UNIQUE(user_id, type, target_id) |
| `user_search_history` | id (BIGSERIAL) | user_id (FK), search_type, query_text | — | B-tree(user_id, created_at DESC) |

### PostGIS 空间函数使用

| 函数 | 使用场景 |
|------|---------|
| `ST_AsMVT` | 矢量瓦片生成 (聚合函数, 返回 MVT 字节) |
| `ST_AsMVTGeom(geom, envelope, 4096, 256, true)` | 瓦片坐标系裁剪+量化 (4096 范围, 256 buffer, 裁剪开启) |
| `ST_Intersects(geom, envelope)` | 精确空间相交过滤 |
| `geom && envelope` | 边界框快速预过滤 (GIST 索引加速) |
| `ST_AsText(geom)` | 几何体转 WKT 文本 (供 Java WKT 解析) |
| `ST_X(geom)`, `ST_Y(geom)` | 点坐标提取 (搜索结果返回经纬度) |
| `ST_Buffer(ST_MakeLine(...)::geography, 5000)` | 车站间线段 5km 缓冲区查询 |
| `ST_DWithin(geom::geography, ..., radius)` | 地理距离范围查询 |
| `ST_MakeEnvelope(west, south, east, north, 4326)` | 瓦片边界框构造 |
| `ST_Intersects` (拓扑构建) | 铁路段端点/相交检测 |
| `ST_DWithin` (拓扑构建, 50m) | 铁路段邻近连接检测 |
| `ST_Distance` (拓扑构建) | 段间地理距离计算 |

### 缓存: Redis 7

- **默认缓存 TTL:** 1 小时 (3600s)
- **专用 `tiles` 缓存:** 1 小时 TTL, 缓存 PostGIS ST_AsMVT 生成的矢量瓦片字节
- **序列化:** GenericJackson2JsonRedisSerializer (JSON 格式存储)
- **缓存注解:** `@Cacheable("tiles")` 在 `TileService.getTile()` 方法上
- **已知问题:** 早期版本存在 `ClassCastException` (byte[] → String 类型不匹配), 已在 4c4ff728 修复

### 其他存储

- **消息队列:** 无
- **文件存储:** 无外部对象存储。GeoJSON/GPKG 数据文件本地存储在 `railway-scripts/data/`
- **搜索引擎:** 无 — 全文搜索依赖 PostgreSQL ILIKE (模糊匹配, 无索引加速)

### 数据库迁移

**无 Flyway/Liquibase 或 Prisma/Alembic 迁移管理。** DDL 通过 `schema.sql` 中 `CREATE TABLE IF NOT EXISTS` 幂等执行 (Docker Compose 启动时挂载到 `/docker-entrypoint-initdb.d/`)。这意味着:
- 无版本化的 schema 变更追踪
- 生产环境 schema 变更需手动管理
- 无法回滚

---

## 8. 环境与部署配置

### Docker Compose 部署架构

```
┌─────────────────────────────────────────────────────────┐
│ docker compose up -d                                    │
│                                                         │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────┐ │
│  │    db    │   │  redis   │   │   app    │   │front │ │
│  │ postgis  │   │  redis:7 │   │ :8080    │   │nginx │ │
│  │ :5432    │   │  :6379   │   │  Java 21 │   │:80   │ │
│  └──────────┘   └──────────┘   └──────────┘   └──────┘ │
│       ↑              ↑              ↑              ↑    │
│  healthcheck     healthcheck    depends_on     / → SPA │
│  schema.sql      redisdata      DB+Redis      /api →app│
│  pgdata vol      vol            healthy                  │
└─────────────────────────────────────────────────────────┘
```

### Dockerfile (多阶段构建)

```
阶段 1 (build):
  FROM maven:3.9-eclipse-temurin-21
  → 复制所有 pom.xml → mvn dependency:go-offline (依赖缓存)
  → 复制源代码 → mvn package -pl railway-api -am -DskipTests
  → 产出: railway-api/target/*.jar

阶段 2 (run):
  FROM eclipse-temurin:21-jre
  → COPY --from=build jar → EXPOSE 8080 → java -jar app.jar
```

### Nginx 配置

```
location /           → try_files $uri $uri/ /index.html  (SPA history mode)
location /api/       → proxy_pass http://app:8080  (反向代理, 携带原始 Headers)
```

### 环境配置管理

- **Spring Boot profiles:** `application.yml` 为主配置, 通过 `-Dspring-boot.run.profiles=dev` 激活开发 profile
- **外部化配置:** 数据库/Redis/JWT 配置通过环境变量注入 (`${DB_HOST:localhost}` 模式)
- **Docker 环境变量:** 在 `docker-compose.yml` 中直接设置 (`DB_HOST: db`, `DB_USER: railway` 等)
- **安全风险:** 数据库密码 `railway123`、JWT 默认密钥硬编码在源码中

### CI/CD

**无 CI/CD 管道配置。** 仓库中未发现:
- `.github/workflows/` 目录
- `.gitlab-ci.yml`
- Jenkinsfile
- 任何自动化构建/测试/部署脚本

### 部署清单

| 项目 | 状态 | 说明 |
|------|------|------|
| Docker Compose | ✅ 已配置 | 4 服务 + healthcheck + restart policy |
| Dockerfile | ✅ 已配置 | 多阶段构建, 无测试执行 (`-DskipTests`) |
| Nginx | ✅ 已配置 | SPA + API 反向代理 |
| CI/CD | ❌ 缺失 | 无自动化管道 |
| 环境隔离 | ⚠️ 部分 | dev profile 存在但无 staging/prod 配置 |
| 密钥管理 | ❌ 缺失 | 密码和密钥硬编码 |
| HTTPS/TLS | ❌ 缺失 | 无 SSL 配置 |
| 健康检查 | ✅ 已配置 | /api/health 端点 + Docker healthcheck |
| API 文档 | ⚠️ 部分 | springdoc 已配置但无注解 |

---

## 9. 代码逻辑深潜 — 关键业务路径

### 路径 1: 矢量瓦片渲染 (端到端)

**触发:** 用户平移/缩放地图 → MapLibre GL 请求瓦片

**前端 → 后端:**
```
1. MapContainer.vue (useMap composable) 初始化 MapLibre 实例
2. map.on('load') → 添加自定义 source (vector tile URL pattern):
   source = { type: 'vector', tiles: ['/api/tiles/railways/{z}/{x}/{y}.pbf'] }
3. MapLibre 根据视口自动计算需要的瓦片 → HTTP GET 请求
```

**后端处理 (TileController → TileService → Mapper → PostGIS):**
```
1. TileController.getTile(layer, z, x, y)
   → 参数验证 → tileService.getTile(layer, z, x, y)
2. TileService:
   → TileUtils.tileToBBox(z, x, y) 计算 WGS-84 边界框
   → TileUtils.tileToEnvelopeSql(z, x, y) 生成 ST_MakeEnvelope SQL
   → 根据 layer 路由到 mapper:
     - "railways" → railwaySegmentMapper.getVectorTile(envelope, z, x, y, "railways")
     - "stations" → stationMapper.getVectorTile(envelope, z, x, y, "stations")
   → 最小缩放限制: railways z≥2, stations z≥5
3. RailwaySegmentMapper.xml (getVectorTile):
   → SELECT ST_AsMVT(tile, 'railways', 4096, 'geom') FROM (
       SELECT id, name, category, ST_AsMVTGeom(geom, envelope, 4096, 256, true) AS geom
       FROM railway_segments
       WHERE geom && envelope AND ST_Intersects(geom, envelope)
         AND category IN ('conventional', 'high_speed', 'other_rail')
     ) AS tile
   → ST_AsMVTGeom: 将 WGS-84 坐标裁剪到瓦片范围，量化到 4096×4096 网格
   → ST_AsMVT: 聚合行数据为 Mapbox Vector Tile 二进制格式
4. TileService 接收 hex 编码的 MVT 字符串:
   → 处理 "\x" 前缀和双引号包裹
   → HexFormat.of().parseHex(hexString) 解码为 byte[]
5. TileController 返回 byte[]:
   → Content-Type: application/vnd.mapbox-vector-tile
   → Cache-Control: public, max-age=3600
   → 空瓦片返回 204 No Content
```

**@Cacheable("tiles") 机制:**
- Redis 缓存 key 由 `layer + z + x + y` 组合生成
- TTL 1 小时
- 缓存的是解码后的 byte[] 数组 (修复后的行为)

**前端渲染:**
```
MapLibre 接收 MVT bytes → GPU 解码 → 根据 MapContainer 中添加的图层样式渲染:
  - 铁路线: line-color 按 category/usage 分层, line-width zoom 插值 (0.8px~5px)
  - 车站: circle-color 按 category, circle-radius zoom 插值 (2px~8px)
```

### 路径 2: 多次中转路线搜索

**触发:** POST /api/transfer/search `{ from: "北京", to: "广州", maxTransfers: 2, preference: "least_time" }`

```
1. TransferController.search(@RequestBody TransferRequest)
   → transferSearchService.search(req)

2. TransferSearchService.search():
   a. graphBuilder.buildGraph() — 全量图构建 (每次请求, 无缓存):
      → 查询所有有效车次 (train_routes WHERE is_valid=TRUE)  — 第 1 次 DB 查询
      → 对每个车次, 查询经停站 (train_stops WHERE train_no=?)  — N 次 DB 查询 (N+1 问题!)
      → 相邻停站对添加有向边: weight = depart→arrive 时间差 (分钟)
      → 同一站添加自环: weight = 30 分钟 (换乘等待)
      → 节点命名: "STATION:站名" (问题: 同名不同站会冲突)

   b. YenKShortestPath.getPaths(fromNode, toNode, maxResults * 3)
      → JGraphT Yen's 算法: O(K * V * (E + V * log V))

   c. 路径转换 toTransferResult(): 对每条路径:
      → 遍历相邻站点对 (vertexList)
      → 查找到发车次: EXISTS 子查询 (train_stops WHERE station_name=from
        AND EXISTS same train_no at to station with next seq)  — N 次 DB 查询
      → 查找到达时间: train_stops WHERE train_no=? AND station_name=?  — N 次 DB 查询
      → 查询票价: train_fares WHERE train_no=? AND from=? AND to=?  — N 次 DB 查询
      → 计算总时间, 总票价

   d. 过滤: transferCount ≤ maxTransfers && totalTime ≤ 72h
   e. TransferRankingService.rank(): 按偏好排序 (least_time / least_transfer / least_price)
   f. 截断到 maxResults

3. 返回 JSON:
   {
     "results": [{ id, totalTimeMin, totalPriceYuan, transferCount, score,
                   segments: [{ trainNo, trainType, fromStation, toStation,
                                departTime, arriveTime, durationMin, price: {...} }] }],
     "total_found": N,
     "search_time_ms": M
   }
```

**性能问题:** 每次请求至少 1 + N_trains + N_paths * 3 次数据库查询，加上全量图构建开销。无缓存。

### 路径 3: 前端搜索交互 (当前 Mock 模式)

```
1. 用户在 SearchBar 输入 "北京"
   → searchStore.setQuery("北京") → query 响应式更新

2. useStationSearch composable (在 App.vue 中激活):
   → watch([query, activeTab], { debounce: 200ms })
   → 当 query 非空时, 调用 performSearch():
     → 本地遍历 stationStore.stationCache (Map 迭代)
     → 过滤条件: name.includes(query) || city.includes(query)
     → 映射为 SearchResultItem[]
     → searchStore.setResults(filtered)
   → 当 query 为空时, 显示热门建议 (getHotStations/ getHotTrains/ getHotCities)

3. SearchDropdown 响应式渲染:
   → v-for searchStore.results → 根据 type 渲染不同样式:
     - station: 彩色圆点 + 名称 + 城市
     - train: TrainTypeTag + 车次号 + 始发→终到
     - city: 蓝色圆点 + 城市名 + 车站数

4. 用户点击结果:
   → emit('select', item)
   → AppHeader 转发 → App.vue handleSearchSelect(item)
   → 根据 item.type: openStation(action) / openTrain(action) / focusCity(action)
   → 设置 stationStore/trainStore 当前选中 → v-if 显示 StationPanel/TrainPanel
   → 设置 mapStore focus → MapContainer watch 触发 flyTo + 高亮
```

**注意:** 搜索目前完全在前端 mock 数据上运行。`useStationSearch.ts` 中有注释掉的真实 API 调用代码，待后端数据就绪后切换。

### 路径 4: 认证流程

```
注册:
  POST /api/auth/register { username, password }
  → AuthController.register():
    → if (username.length < 3 || password.length < 6) return 400
    → BCryptPasswordEncoder.encode(password)
    → jdbcTemplate.update("INSERT INTO users (username, password_hash, role) VALUES (?,?,?)", ...)
    → jwtUtil.generateToken(username)
    → return { token, username }

登录:
  POST /api/auth/login { username, password }
  → AuthController.login():
    → jdbcTemplate.queryForObject("SELECT password_hash, role FROM users WHERE username = ?", ...)
    → BCryptPasswordEncoder.matches(password, storedHash)
    → jwtUtil.generateToken(username)
    → return { token, username, role }

JWT 验证:
  → Authorization: Bearer <token>
  → JwtAuthFilter.doFilterInternal():
    → header.startsWith("Bearer ") → 提取 token
    → jwtUtil.validateToken(token) (HMAC-SHA 签名验证 + 过期检查)
    → jwtUtil.getUsername(token) (解析 claims)
    → SecurityContextHolder 设置 UsernamePasswordAuthenticationToken(username, null, [])
```

---

## 10. 潜在问题与最佳实践

### 安全性

| 问题 | 严重度 | 位置 | 说明 |
|------|--------|------|------|
| JWT 密钥硬编码 | 🔴 高 | application.yml:49 | 默认值 `railwaymap-production-secret-change-in-env` 在源码中，生产环境必须通过环境变量覆盖 |
| 数据库密码明文 | 🔴 高 | docker-compose.yml:7, application.yml:10 | 密码 `railway123` 明文出现在多个文件中 |
| SQL 注入风险 | 🟡 中 | TransferSearchService.java:93-94 | `.last()` 方法中字符串拼接站名到 SQL (toName 直接拼入) |
| MyBatis `${}` 字符串替换 | 🟡 中 | RailwaySegmentMapper.xml, StationMapper.xml | `${envelope}` 使用字符串替换而非参数化 (`#{}`) — 但 envelope 值由后端 TileUtils 生成，非用户输入，风险较低 |
| CSRF 完全禁用 | 🟡 中 | SecurityConfig.java:23 | REST API 无状态模式下可接受，但需确保无 cookie-based 认证混用 |
| CORS 全允许 | 🟡 中 | CorsConfig.java | `.allowedOriginPatterns("*")` 允许所有来源 |
| 无速率限制 | 🟡 中 | 全局 | 无 rate-limiting filter — 登录/注册/搜索端点易受暴力破解和滥用 |
| 无输入消毒 | 🟡 中 | 所有 Controller | 无 @Valid 注解, 无统一参数校验 (仅有 AuthController 手动校验) |
| 密码最小长度 6 | 🟢 低 | AuthController.java | 行业标准建议 ≥ 8 字符 + 复杂度要求 |
| 密码哈希无盐 | 🟢 低 | — | BCrypt 自带 salt，无需额外处理 |
| 无 refresh token | 🟡 中 | 全局 | JWT 24h 过期后需重新登录 |
| 角色权限未实现 | 🟡 中 | JwtAuthFilter.java:32 | `Collections.emptyList()` — JWT 中包含 role 信息但未提取到 GrantedAuthority |

### 性能

| 问题 | 严重度 | 位置 | 说明 |
|------|--------|------|------|
| 换乘图每次全量重建 | 🔴 高 | TransferGraphBuilder.java:47 | 每次搜索都查询全部车次 + N 次经停站查询, 构建完整有向图 |
| N+1 查询 (图构建) | 🔴 高 | TransferGraphBuilder:56 | 对每条车次单独查询经停站 (loop 内 selectList) |
| N+1 查询 (路线转换) | 🔴 高 | TransferSearchService:90-127 | 每个路径段 3 次独立 DB 查询 (车次查找 + 到达时间 + 票价) |
| 拓扑构建 O(n²) | 🔴 高 | build_topology.sql | `CROSS JOIN railway_segments` 对百万级段将是灾难 |
| 前端全量缓存遍历 | 🟡 中 | useStationSearch.ts | 搜索过滤使用 Map 迭代 + Array.filter, 数据量大时需 Web Worker 或后端搜索 |
| 矢量瓦片缓存仅 1h | 🟢 低 | RedisCacheConfig.java | 瓦片数据不常变, 可考虑更长 TTL 或 CDN 缓存 |
| MapLibre style 切换重新加载 | 🟡 中 | App.vue:68 | `map.setStyle()` 会销毁所有 source/layer 并重建 |
| 无数据库连接池监控 | 🟢 低 | — | HikariCP 连接池已配置但无 metrics 暴露 |

### 代码质量

| 问题 | 严重度 | 位置 | 说明 |
|------|--------|------|------|
| Controller 直接使用 JdbcTemplate | 🟡 中 | AuthController.java, UserController.java | 绕过 Service 层, 业务逻辑和 SQL 混杂在 Controller 中 |
| Controller 直接注入 Mapper | 🟡 中 | TrainController.java | 注入 5 个 Mapper + 1 个 Service, 未通过 Service 层封装 |
| 手写 WKT 解析 | 🟡 中 | RouteGeoJsonService.java:60-70 | 字符串 split 解析 LINESTRING WKT, 错误处理不完善 |
| 图节点使用站名而非 ID | 🔴 高 | TransferGraphBuilder.java:65-66 | `"STATION:" + name` — 同名站 (如多个城市的 "北京南") 会冲突 |
| 无全局异常处理 | 🟡 中 | 全局 | 无 `@ControllerAdvice` / `@ExceptionHandler`, 异常直接返回 500 + stacktrace |
| 无测试代码 | 🔴 高 | 全局 | 前后端均无单元测试、集成测试或 E2E 测试 |
| 无输入校验注解 | 🟡 中 | DTO 类 | 无 `@NotNull`, `@Min`, `@Max` 等 Bean Validation 注解 |
| mockData 与真实类型不一致 | 🟡 中 | mockData.ts vs types/ | mock 数据结构可能与后端实际返回不匹配 |
| TrainStop 无唯一约束 | 🟢 低 | schema.sql:105-118 | import_trains.py 中 ON CONFLICT DO NOTHING 因此无效 |
| 日志级别 DEBUG | 🟢 低 | application.yml:42 | 生产环境可能产生大量日志 |
| import_gpkg.py 引用缺失列 | 🟡 中 | import_gpkg.py | 引用了 schema 中不存在的 bridge/tunnel/layer 列 |

### 可维护性

| 问题 | 严重度 | 说明 |
|------|--------|------|
| 无数据库迁移工具 | 🟡 中 | 无 Flyway/Liquibase — schema 变更无版本追踪 |
| 前后端类型各自维护 | 🟡 中 | 无 OpenAPI 生成或共享类型定义 |
| .env 文件未 gitignore | 🔴 高 | .gitignore 中有 `.env` 但前一行注释为 `# ===== Docker =====`，确认 .env 未被提交 |
| 无 CI/CD | 🟡 中 | 无自动化构建/测试/部署管道 |
| 无代码风格检查 | 🟢 低 | 无 ESLint/Prettier/Checkstyle 配置 |
| Springdoc 配置但无注解 | 🟡 中 | API 文档路径已配置但未生成有效文档 |
| 硬编码配置值 | 🟡 中 | 多处魔法数字 (最大换乘次数 2, 最大总时间 72h, 换乘等待 30min 等) |

### 架构与设计

| 观察 | 说明 |
|------|------|
| 总体架构合理 | 标准分层 (Controller→Service→Mapper), Maven 模块边界清晰 |
| 前端设计系统完善 | Railway Signal Industrial 设计体系完整, CSS tokens 组织良好, 暗色模式支持到位 |
| 批处理独立得当 | railway-batch 有独立启动类, 正确复用 service/data 模块 |
| Python 数据流水线完整 | 从数据获取→清洗→导入→拓扑构建→验证形成完整闭环, 支持断点续传 |
| SPA Shell 路由策略 | 单一路由 + Pinia 条件渲染是成熟的 SPA 模式, 适合地图应用 |
| mock 数据驱动开发 | 前后端可独立开发, API 层就绪后切换成本低 |
| shallowRef 使用 | 正确识别 MapLibre 实例不能被 Vue 深度代理的问题 |

---

## 附录 A: 数据流水线

完整的数据获取→处理→导入流水线:

```
① china_boundary.py
   Overpass API → data/china_boundary.geojson (中国陆地边界)

② grid_splitter.py
   边界 → 1°×1° 渔网网格 (0.05° 重叠, 蛇形排序)
   → data/grid_queue.json + data/cell_r*_c*.geojson

③ grid_fetcher.py
   grid_queue.json → 逐网格 Overpass API 查询
   → data/grids/grid_{id}.geojson (铁路+车站要素)
   → progress.log + failed_grids.json (断点续传)

④ import_data.py 或 import_gpkg.py
   GeoJSON/GPKG → PostgreSQL railway_segments + stations
   (psycopg2 批量插入, ON CONFLICT 去重)

⑤ build_topology.sql
   railway_segments → CROSS JOIN + ST_Intersects/DWithin
   → railway_topology (段间连接关系)

⑥ train_crawler_playwright.py
   liecheba.com → data/trains/{train_no}.json
   (车次时刻表 + 票价, 断点续传, train_progress.json)

⑦ fix_train_data.py
   清理/填补 JSON 中的时间字段 (交叉填充, 正则校验)

⑧ import_trains.py
   JSON → PostgreSQL train_routes + train_stops + train_fares
   (ON CONFLICT upsert)

⑨ validate_data.sql
   8 项数据完整性校验 (行计数/分类统计/几何有效性/缺失数据/拓扑覆盖率)
```

## 附录 B: 前端入口动画序列

MapContainer 在首次加载时执行 6 阶段入场动画:

```
idle → background → lines → stations → ui → complete
 0ms     800ms       1600ms    2400ms    3200ms   4000ms

background: 底图逐渐淡入 (opacity 0 → 1)
lines:      铁路线图层依次出现 (trunk → branch → spur, staggered)
stations:   车站圆圈从枢纽到小站依次弹出
ui:         控制面板 (图例/缩放按钮) 滑入
complete:   移除 loading overlay, 标注"就绪"
```

## 附录 C: 关键文件索引

| 文件 | 行数 (估计) | 重要性 | 说明 |
|------|-----------|--------|------|
| CLAUDE.md | 199 | ⭐⭐⭐⭐⭐ | 项目指令与架构概述 |
| railway-api/.../application.yml | 65 | ⭐⭐⭐⭐⭐ | 所有后端配置 |
| railway-api/.../schema.sql | 205 | ⭐⭐⭐⭐⭐ | 完整数据库 DDL |
| railway-api/.../SecurityConfig.java | 45 | ⭐⭐⭐⭐ | 安全策略 |
| railway-service/.../TransferSearchService.java | 178 | ⭐⭐⭐⭐ | 核心换乘算法 |
| railway-service/.../TransferGraphBuilder.java | 99 | ⭐⭐⭐⭐ | 图构建 |
| railway-service/.../RouteMatchingService.java | ~200 | ⭐⭐⭐⭐ | 车次-线路段匹配 |
| railway-service/.../TileService.java | ~80 | ⭐⭐⭐⭐ | 矢量瓦片生成 |
| railway-data/.../StationMapper.xml | ~90 | ⭐⭐⭐⭐ | 空间搜索 SQL |
| railway-data/.../RailwaySegmentMapper.xml | ~50 | ⭐⭐⭐⭐ | 瓦片生成 SQL |
| railway-frontend/src/App.vue | 253 | ⭐⭐⭐⭐⭐ | 前端根组件 |
| railway-frontend/src/stores/mapStore.ts | 87 | ⭐⭐⭐⭐ | 地图状态 |
| railway-frontend/src/composables/useMap.ts | ~200 | ⭐⭐⭐⭐ | MapLibre 集成 |
| railway-frontend/src/composables/useAgentChat.ts | ~150 | ⭐⭐⭐ | Agent 对话 |
| railway-frontend/src/components/map/MapContainer.vue | ~300 | ⭐⭐⭐⭐⭐ | 地图容器+图层 |
| railway-scripts/grid_fetcher.py | ~250 | ⭐⭐⭐⭐ | 数据采集核心 |
| railway-scripts/train_crawler_playwright.py | ~300 | ⭐⭐⭐⭐ | 车次采集核心 |
| docker-compose.yml | 65 | ⭐⭐⭐⭐ | 部署编排 |
