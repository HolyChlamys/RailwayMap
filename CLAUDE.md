# RailwayMap

中国铁路地图与多次中转路线规划系统 — Maven 多模块 monorepo，Spring Boot + Vue 3 前后端分离。

## 交流语言

与用户交流时使用中文。代码、注释、commit message 可使用英文或中文，视项目约定而定。大模型的内部思维链（thinking）不受此限制。

## 项目结构

```
railway-api/         Spring Boot 启动类 + REST Controller + Spring Security/JWT 配置
railway-service/     业务逻辑 (换乘图构建、搜索、矢量瓦片、GeoJSON 转换)
railway-data/        MyBatis-Plus Mapper + XML SQL (PostgreSQL/PostGIS)
railway-common/      Entity, DTO, Enum, 工具类 (JTS, pinyin4j, TileUtils)
railway-batch/       Spring Batch (OSM GeoJSON 网格数据导入)
railway-scripts/     Python 数据爬取脚本 + SQL 校验工具
railway-frontend/    Vue 3 SPA (Vite + TypeScript + Tailwind CSS 4)
```

模块依赖链: `api → service → data → common`，batch 复用 service 和 data。

## 前端 (railway-frontend/)

### 技术栈

| 类别 | 技术 | 用途 |
|------|------|------|
| 框架 | Vue 3 Composition API + `<script setup>` | SPA |
| 构建 | Vite 6 + TypeScript 5.7 (strict) | 开发/构建 |
| 状态管理 | Pinia 2.3 | 6 个 store |
| 路由 | Vue Router 4.5 | 单 catch-all 路由 (SPA shell 模式) |
| 地图 | MapLibre GL JS 5.2 | WebGL 矢量瓦片渲染 |
| 底图 | MapTiler Streets v2 | 中文矢量瓦片 (自定义 map-style.json) |
| CSS | Tailwind CSS 4 + 自定义 tokens.css | 原子化 + Railway Signal Industrial 设计系统 |
| UI 基元 | Radix Vue (Popover, ToggleGroup, Dialog) | 无样式无障碍组件 |
| 图标 | Lucide Vue Next | 轻量 stroke 图标 |
| 工具 | @vueuse/core (useDebounceFn, onClickOutside 等) | |
| HTTP | Axios (baseURL `/api`, 15s 超时) | 响应拦截器解包 response.data |

设计系统: Railway Signal Industrial — 铁路信号灯颜色体系 (signal-red/amber/green/blue/caution)，玻璃材质面板 (backdrop-filter blur)，JetBrains Mono 用于车次号/时间，Noto Serif SC 用于品牌/标题，PingFang SC 用于正文。

### 目录结构

```
src/
├── main.ts                   Vue 应用入口，注册 Pinia/Router，seeds mock 数据
├── App.vue                   根组件 — layout shell，协调所有面板/地图/搜索交互
├── assets/styles/
│   ├── tokens.css            CSS 自定义属性 (颜色、字体、间距、阴影、动画)
│   ├── base.css              Reset + 全局排版 + Tailwind 导入
│   └── fonts.css             @font-face (JetBrains Mono, Noto Serif SC)
├── types/                    手工维护的 TS 接口 (station, train, route, map, agent)
├── api/                      Axios 请求层 (client, stationApi, trainApi, routePlanApi)
│   └── mockData.ts           开发用 mock 数据 (22 个车站, 9 趟车次)
├── stores/                   Pinia stores
│   ├── mapStore.ts           地图视口 + 图层可见性 + 当前焦点 (station/train/city)
│   ├── searchStore.ts        搜索栏状态 (tab, query, results, dropdown open/close)
│   ├── stationStore.ts       车站缓存 (Map<id, Station>) + 当前选中
│   ├── trainStore.ts         车次缓存 (Map<no, Train>) + 当前选中
│   ├── routePlanStore.ts     多路线方案 + 筛选 + mock 路线坐标
│   └── agentStore.ts         Agent 对话消息 + 面板状态 + 快捷建议
├── composables/              可复用组合式函数
│   ├── useMap.ts             MapLibre 实例生命周期 (shallowRef 避免 proxy crash)
│   ├── useMapInteraction.ts  地图点击/hover 事件 → station 交互
│   ├── useStationSearch.ts   搜索防抖 200ms + 本地缓存过滤 (目前纯前端)
│   ├── useAgentChat.ts       Agent 意图解析 (车次查询/车站查询/路线规划/筛选) mock 版
│   ├── useRouteAnimation.ts  多路线 SVG 动画路径生成
│   └── useKeyboard.ts        ⌘K 搜索 / Esc 关闭快捷键
├── components/
│   ├── layout/AppHeader.vue  页头 (Logo + SearchBar + 深色模式/关于/用户)
│   ├── map/
│   │   ├── MapContainer.vue   MapLibre 实例挂载 + 自定义图层 (demo GeoJSON 线路/车站)
│   │   ├── MapLoadingOverlay.vue 加载进度条
│   │   ├── MapAtmosphere.vue  纸质纹理 + 指南针 + 比例尺
│   │   └── RouteAnimationLayer.vue SVG 叠加层 (流动虚线/实线动画)
│   ├── search/
│   │   ├── SearchBar.vue      搜索栏 (Tab 切换 + Input + 下拉)
│   │   └── SearchDropdown.vue 搜索结果列表
│   ├── panels/
│   │   ├── StationPanel.vue   左侧浮窗 — 车站信息
│   │   ├── TrainPanel.vue     左侧浮窗 — 车次详情 + 经停站时间轴
│   │   ├── TimetableModal.vue 中央模态窗 — 所有经停车次表格
│   │   ├── LegendPanel.vue    右上图例 (可折叠, checkbox 图层开关)
│   │   └── MapControls.vue    右上按钮组 (放大/缩小/定位/图层切换)
│   ├── agent/
│   │   ├── AgentFab.vue       右下浮动按钮
│   │   ├── AgentPanel.vue     右侧滑入对话面板
│   │   ├── AgentBubble.vue    消息气泡 (Markdown 文本 + 内嵌路线卡片)
│   │   └── AgentRouteCard.vue 路线方案卡片 (嵌入 Agent 消息)
│   └── shared/                共享 UI 组件
│       ├── GlassCard.vue      玻璃材质卡片
│       ├── HyperlinkText.vue  超链接文本 (站名/车次号可点击跳转)
│       ├── StopTimeline.vue   经停站时间轴 (竖向, 带圆点)
│       └── TrainTypeTag.vue   车次类型标签 (G/D/Z 等彩色小标签)
└── router/index.ts            Vue Router (catch-all 路由)
```

### 前端数据流

所有交互通过 Pinia actions 驱动，不在组件中直接调 `api/xx`。跨 store 联动在组件层通过 `watch` 实现，store 内部不互相引用。

```
用户交互 → Pinia action → API / mock → store state 更新 → 组件响应式重渲染
                                                    → MapContainer watch → MapLibre flyTo/图层更新
```

搜索目前完全在前端本地缓存中过滤。Agent 对话使用 mock 意图解析（正则匹配）。`useMap` 使用 `shallowRef` 持有 MapLibre 实例避免 Vue 深度 proxy 导致 WebGL 崩溃。

## 后端

### 技术栈

Java 21, Spring Boot 3.5.14, MyBatis-Plus 3.5.16, PostgreSQL 17 + PostGIS 3.5, Redis 7, JGraphT 1.5.2 (Yen's K-最短路径), JTS 1.20 (空间), pinyin4j 2.5.1, jjwt 0.12.6

### 模块

**railway-api** — 入口模块:
- `RailwayApiApplication` — `@SpringBootApplication(scanBasePackages="com.railwaymap")`, `@MapperScan("com.railwaymap.data.mapper")`
- 8 个 Controller: Health, Auth, Station, Train, Transfer, Tile, User, Sync
- 6 个 Config: SecurityConfig (无状态 JWT), JwtAuthFilter, JwtUtil (HMAC-SHA 24h), CorsConfig (全允许), RedisCacheConfig, JacksonConfig
- `application.yml` — 端口 10010, PostGIS 数据源, Redis, MyBatis-Plus 配置, 自定义 `railway.*` 配置
- `schema.sql` — DDL (CREATE TABLE IF NOT EXISTS, 9 张表 + PostGIS 扩展)

**railway-service** — 9 个 Service:
- `TileService` — PostGIS ST_AsMVT 矢量瓦片生成, @Cacheable("tiles") Redis 1h 缓存
- `TransferGraphBuilder` — 全量构建 JGraphT 图 (每次请求重建，无缓存)
- `TransferSearchService` — Yen's K-最短路径 + 票价计算 + 偏好排序
- `TransferRankingService` — 多目标排序 (least_time/least_transfer/least_price)
- `RouteGeoJsonService` — WKT→GeoJSON FeatureCollection (N+1 查询问题)
- `RouteMatchingService` — BFS 拓扑匹配车次经行段
- 其余: MapQueryService, StationSearchService, TrainSearchService

**railway-data** — 7 个 Mapper + 3 个 XML SQL:
- StationMapper.xml — 矢量瓦片 MVT, BBox 查询, ILIKE 关键字/拼音搜索
- RailwaySegmentMapper.xml — 矢量瓦片, BBox 查询
- TrainRouteMapper.xml — ILIKE 车次搜索

**railway-common** — 8 Entity, 7 DTO, 4 Enum, 3 Util (GeoUtils, PinyinUtils, TileUtils)

### API 路由汇总

| 方法 | 路径 | 鉴权 |
|------|------|------|
| GET | /api/health | 公开 |
| POST | /api/auth/register, /api/auth/login | 公开 |
| GET | /api/stations/search, /{id}, /city/{city}, /between | 公开 |
| GET | /api/trains/search, /{no}/route | 公开 |
| POST | /api/transfer/search | 公开 |
| GET | /api/tiles/{layer}/{z}/{x}/{y}.pbf | 公开 |
| GET/POST/DELETE | /api/favorites | 需登录 |
| GET/POST | /api/history | 需登录 |
| POST | /api/sync/trigger | 需登录 |

### 数据库 (PostgreSQL 17 + PostGIS 3.5)

9 张表: railway_segments (LINESTRING), stations (POINT), railway_topology, train_routes, train_stops, train_fares, train_segment_mapping, users, user_favorites, user_search_history。空间列 GIST 索引，关键列 B-tree 索引。无 Flyway/Liquibase — DDL 在 schema.sql 中通过 IF NOT EXISTS 幂等执行。

## 开发运行

```bash
# 后端 (需要本地 PostgreSQL + Redis)
cd railway-api
mvn spring-boot:run -Dspring-boot.run.profiles=dev

# 前端
cd railway-frontend
npm run dev        # Vite :5173, proxy /api → localhost:10010

# Docker Compose 一键部署
docker compose up -d
```

## 关键设计决策

- **MapLibre shallowRef**: 必须用 `shallowRef` 而非 `ref` 持有 Map 实例，Vue 深度 proxy 会 crash WebGL context
- **SPA shell 路由**: Vue Router 仅一个 catch-all 路由，所有面板切换由 Pinia + 条件渲染驱动，无页面跳转
- **Mock 数据先行**: 前端搜索/Agent 对话完全在前端 mock 上运行，不需要后端即可开发 UI。API 层已就绪，届时切换到真实 API
- **设计系统 CSS-only**: 所有设计 token 通过 CSS 自定义属性 (`--signal-red` 等) 注入，不依赖 UI 组件库的主题系统
- **换乘图无缓存**: 当前每次搜索全量从 DB 构建 JGraphT 图，存在性能问题 (已知 N+1 查询)
- **图节点使用站名**: JGraphT 节点键是站名字符串而非唯一 ID，同名站会冲突
- **矢量瓦片 hex 解码**: PostGIS ST_AsMVT 返回 hex 字符串，后端拼接后用 HexFormat 转 byte[]

## 工作流程

每完成一个独立功能或修复后必须立即提交 git，保持每次提交粒度小、可独立回溯：

```bash
git add <相关文件>           # 精确指定，不 git add -A
git commit -m "<类型>: <简述>"
```

类型前缀：`feat:` 新功能 / `fix:` 修复 / `refactor:` 重构 / `docs:` 文档 / `data:` 数据修复。

## 已知问题与改进方向

- 换乘图每次全量重建 (无缓存) + 多层 N+1 查询
- SQL 注入风险: TransferSearchService 字符串拼接 SQL, XML 中 `${envelope}` 字符串替换
- JWT secret 硬编码默认值, DB 密码明文在 docker-compose.yml
- 无测试 (前后端均无), 无全局异常处理 @ControllerAdvice
- 无 API 文档生成 (springdoc 已配置但无注解)
- 前端无 i18n, 无 JWT 自动注入拦截器
- TrainController 直接注入 Mapper (应通过 Service), AuthController 使用 JdbcTemplate
- RouteGeoJsonService 手写 WKT 解析 + N+1 查询
- 前端 StationPanel 和 MapContainer 之间缺少 watch 联动
