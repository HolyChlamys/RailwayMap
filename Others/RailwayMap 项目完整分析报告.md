# RailwayMap 项目完整分析报告

> 生成日期：2026-05-22 | 基于最新代码库、OpenSpec 规范、实施计划和设计文档
> 替代旧版：`.RailwayMap 项目完整分析报告（比较过时）.md`

---

## 一、项目概述

**RailwayMap** 是中国铁路地图与多次中转路线规划系统。Maven 多模块 monorepo，Spring Boot + Vue 3 前后端分离架构，支持矢量瓦片地图渲染、车站/车次搜索、多维度换乘路径规划、等时圈查询，以及 LLM 驱动的自然语言 Agent 对话。

**核心定位**：为用户提供铁路出行可能性的全面枚举，而非单一最优路径推荐。最终选择权交给用户，以 12306 实际购票情况为参考。

### 技术栈总览

| 层级 | 技术 | 版本 |
|------|------|------|
| 后端框架 | Spring Boot + Java 21 | 3.5.14 |
| ORM | MyBatis-Plus | 3.5.16 |
| 数据库 | PostgreSQL + PostGIS | 17 + 3.5 |
| 缓存 | Redis | 7 |
| 图算法 | JGraphT (Yen's K-最短路径) | 1.5.2 |
| 空间计算 | JTS | 1.20 |
| 拼音 | pinyin4j | 2.5.1 |
| 认证 | jjwt (HMAC-SHA, 24h) | 0.12.6 |
| 前端框架 | Vue 3 Composition API + `<script setup>` | 3.x |
| 构建工具 | Vite + TypeScript 5.7 (strict) | 6.x |
| 地图引擎 | MapLibre GL JS | 5.2 |
| 底图 | MapTiler Streets v2 (中文矢量瓦片) | — |
| CSS | Tailwind CSS 4 + tokens.css | 4.x |
| UI 基元 | Radix Vue (Popover, ToggleGroup, Dialog) | — |
| 图标 | Lucide Vue Next | — |
| Agent 服务 | Python FastAPI + LangGraph | 3.12 |
| Agent LLM | OpenAI 兼容接口 (DeepSeek v4-flash) | — |

### 设计语言

**Railway Signal Industrial** — 铁路信号灯工业美学：
- 颜色：signal-red `#d63031`、signal-amber `#e17055`、signal-green `#00b894`、signal-blue `#0984e3`、signal-caution `#fdcb6e`
- 字体：Noto Serif SC（品牌/标题）、PingFang SC（正文）、JetBrains Mono（车次号/时间）
- 材质：玻璃卡片 (backdrop-filter blur)、纸质纹理地图、铆钉圆角 (4/8/12px)
- 动效：信号缓动曲线、路线流动动画、信号脉冲、面板滑入

---

## 二、项目结构

```
RailwayMap/
├── railway-api/              Spring Boot 入口 + REST Controller + Security/JWT 配置
│   ├── 8 Controllers: Health, Auth, Station, Train, Transfer, Tile, User, Sync
│   └── 6 Config: SecurityConfig, JwtAuthFilter, JwtUtil, CorsConfig, RedisCacheConfig, JacksonConfig
├── railway-service/          业务逻辑层 (9 个 Service)
│   ├── TileService — PostGIS ST_AsMVT 矢量瓦片 @Cacheable("tiles") Redis 1h
│   ├── TransferGraphBuilder — 全量 JGraphT 图构建 (每次请求重建)
│   ├── TransferSearchService — Yen's K-最短路径 + 票价计算 + 偏好排序
│   ├── TransferRankingService — 多目标排序 (least_time/transfer/price)
│   ├── RouteGeoJsonService — WKT→GeoJSON FeatureCollection
│   ├── RouteMatchingService — BFS 拓扑匹配车次经行段
│   └── MapQueryService, StationSearchService, TrainSearchService
├── railway-data/             MyBatis-Plus Mapper + XML SQL (7 Mapper + 3 XML)
├── railway-common/           8 Entity, 7 DTO, 4 Enum, 3 Util
├── railway-batch/            Spring Batch (OSM GeoJSON 网格数据导入)
├── railway-scripts/          Python 数据爬取 + SQL 校验
├── railway-frontend/         Vue 3 SPA — 19 个组件、6 个 Pinia store、6 个 composable
├── agent-service/            Python Agent 微服务 (新增)
│   ├── src/
│   │   ├── main.py           FastAPI 入口 + POST /api/agent/chat
│   │   ├── config.py         Pydantic Settings (AGENT_ 前缀环境变量)
│   │   ├── state.py          AgentState TypedDict (12 字段)
│   │   ├── graph.py          LangGraph 状态图编译
│   │   ├── nodes/            5 个节点 (understand, clarify, search, relax, format_reply)
│   │   └── tools/            6 个工具 (station_search, train_query, transfer_search, isochrone, timetable)
│   └── tests/                6 个单元测试
└── docs/superpowers/plans/   实施计划
```

模块依赖：`api → service → data → common`，batch 复用 service 和 data。

---

## 三、数据库设计

### 核心表（9 张）

| 表名 | 几何类型 | 关键字段 | 索引 |
|------|---------|---------|------|
| `railway_segments` | LINESTRING | 434,398 行 | GIST 空间索引 |
| `stations` | POINT | 14,060 行 | GIST 空间索引 |
| `railway_topology` | — | 拓扑连接关系 | B-tree |
| `train_routes` | — | 车次信息 | B-tree |
| `train_stops` | — | 658,929 行 | B-tree |
| `train_fares` | — | 票价数据 | B-tree |
| `train_segment_mapping` | — | 车次-区段映射 | B-tree |
| `users` | — | 用户表 | B-tree |
| `user_favorites` | — | 用户收藏 | B-tree |
| `user_search_history` | — | 搜索历史 | B-tree |

### 车站分类体系

| 分类 | 数量 | 说明 |
|------|------|------|
| `major_hub` | 91 | 重要枢纽站 |
| `major_passenger` | 159 | 主要车站 |
| `medium_passenger` | — | 中等车站 |
| `small_passenger` | — | 小型车站 |
| `small_non_passenger` | — | 小型站 (无客运) |
| `large_yard` | — | 大型编组站 |
| 其余 6 种 | — | 编组站、货运站、线路所等 |

---

## 四、API 路由汇总

### 公开 API

| 方法 | 路径 | 用途 | 缓存 |
|------|------|------|------|
| GET | `/api/health` | 健康检查 | — |
| POST | `/api/auth/register` | 用户注册 | — |
| POST | `/api/auth/login` | 用户登录 → JWT | — |
| GET | `/api/stations/search?q=` | 车站搜索 (名称/拼音) | — |
| GET | `/api/stations/{id}` | 车站详情 + 经停车次 | — |
| GET | `/api/stations/city/{city}` | 城市车站列表 | — |
| GET | `/api/trains/search?q=` | 车次搜索 | — |
| GET | `/api/trains/{no}/route` | 车次时刻表 + 经停站 | — |
| POST | `/api/transfer/search` | 换乘路径规划 | — |
| POST | `/api/isochrone` | 等时圈查询 | — |
| GET | `/api/tiles/{layer}/{z}/{x}/{y}.pbf` | 矢量瓦片 | Redis 1h |

### 需认证 API

| 方法 | 路径 | 用途 |
|------|------|------|
| GET/POST/DELETE | `/api/favorites` | 用户收藏管理 |
| GET/POST | `/api/history` | 搜索历史 |
| POST | `/api/sync/trigger` | 数据同步触发 |

### Agent API

| 方法 | 路径 | 用途 |
|------|------|------|
| POST | `/api/agent/chat` | Agent 对话 (LLM 驱动) |
| GET | `/api/agent/health` | Agent 健康检查 |

---

## 五、换乘路径规划 — 四维约束系统

### 核心理念

**"可行路径枚举器，而非路径优化器"**。给定起点和终点，生成所有满足硬约束的路径方案。不排序、不推荐最优，只枚举存在性。

### 四维约束模型 (T/N/S/D)

| 维度 | 含义 | 类型 | 示例 |
|------|------|------|------|
| **T** (Time) | 乘车时段 `[T_start, T_end]` 分钟 | 硬约束 | "白天出发" → [360, 1080] |
| **N** (Number) | 换乘次数 `[N_min, N_max]` | 硬约束 | "最多换乘1次" → [0, 1] |
| **S** (Station) | 中转站 (白名单/黑名单) | 软约束→可松弛 | "途经武汉" |
| **D** (Duration) | 单段最大时长 (分钟) | 硬约束 | "每段不超过4小时" → D_max=240 |

### 维度兼容矩阵

| 维度对 | 关系 | 说明 |
|--------|------|------|
| N↔D | 高度兼容 | 核心协同对：短 D 驱动高 N |
| S↔D | 高冲突风险 | 指定中转站会锁定段长 |
| T↔D | 强耦合 | 白天+短段长=需要更多换乘 |
| T↔S | 基本独立 | — |
| N↔S | 强相关 | N 需要足够站点支撑 |

### 约束松弛策略

当无可行路径时，按优先级松弛：
1. 去掉中转站约束 (S: hard→soft)
2. 放宽单段时长 (D_max × 2, 上限 720min)
3. 增加换乘次数 (N + 1)
4. 放宽时段限制 (移除 T 窗口)

最多 3 轮松弛，第 4 轮返回 "即使放宽条件也没找到可用路线"。

### 冲突检测（调用前）

| 冲突 | 检测 | 处理 |
|------|------|------|
| S↔D | 指定中转站的段长 > D_max | 提示调整，不调用 API |
| N 不足 | 最低段数 > N_max + 1 | 建议提高 N |
| 直达+中转 | maxTransfers=0 且指定 via | 提醒矛盾 |

### 算法

DFS 枚举（非最短路），深度优先搜索以 N_max 为界，逐层约束过滤 (T, D, S, N)，visited-set 防环。无全局代价评估。

---

## 六、等时圈功能

### 算法

**RAPTOR 变体** — 基于轮次的可达性传播，优先队列按到达时间排序。每站记录最早到达时间，时间单调性保证无环。

### API

`POST /api/isochrone` — `{ startStationId, startTime, maxHours }` → `{ stations: [{stationId, stationName, arriveTime, elapsedMinutes, transfers}], totalCount, computeMs }`

### 方向分组

等时圈结果按方向（东/南/西/北/东北/西北/东南/西南）分组，Agent 据此引导用户选择方向，再过渡到路径规划。

### 与路径规划的协作

```
用户: "武汉周边 4 小时内能去哪"
  → 等时圈: "往东 24 站, 往南 33 站, 往北 40 站, 往西 22 站。你想去哪个方向？"
用户: "往南"
  → 自动构造 from/to → 路径规划
```

---

## 七、Agent 服务设计

### 架构

```
前端 Agent UI → POST /api/agent/chat → Python FastAPI
                                          ↓ HTTP (6 个工具)
                                       Java railway-api
```

Agent **不实现算法**，只做三件事：
1. **理解** — 模糊自然语言 → 结构化约束参数
2. **对话** — 反问澄清、引导选择、解释结果
3. **编排** — 调用工具 → 松弛约束 → 重试

### LangGraph 状态图

```
                    ┌──────────────┐
                    │  understand  │  LLM 提取意图 + 四维约束
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │ needs_clarify?│
                    └──┬────────┬──┘
                  YES  │        │  NO
                       ▼        ▼
                ┌──────────┐  ┌──────────┐
                │ clarify  │  │  search   │  并行调用 Java API
                │ (反问)    │  └────┬─────┘
                └──────────┘       │
                                   ▼
                            ┌────────────┐
                            │ has_result? │
                            └──┬──────┬──┘
                          YES  │      │  NO
                               ▼      ▼
                        ┌────────┐ ┌────────┐
                        │ format │ │ relax  │ 松弛约束 → 回到 search
                        └────────┘ └────────┘
```

### AgentState (12 字段)

| 字段 | 类型 | 说明 |
|------|------|------|
| `session_id` | str | 会话标识 |
| `messages` | list[dict] | 对话历史 |
| `user_input` | str | 当前用户输入 |
| `intent` | str\|None | 意图分类 |
| `constraints` | dict\|None | T/N/S/D 约束 |
| `missing` | list[str] | 缺失的必填字段 |
| `tool_results` | list[dict] | 工具调用结果 |
| `reply_text` | str | 回复文本 |
| `instructions` | list[dict] | 前端执行指令 |
| `suggestions` | list[str] | 快捷建议 |
| `relax_history` | list[dict] | 松弛历史 |
| `relax_exhausted` | bool | 松弛是否穷尽 |
| `station` | dict\|None | 前端车站数据 |
| `train` | dict\|None | 前端车次数据 |
| `routes_data` | list[dict]\|None | 前端路线数据 |

### 6 种意图

| 意图 | 触发条件 | 工具 |
|------|---------|------|
| `route_planning` | A→B 出行 | search_transfer |
| `isochrone` | "周边"、"小时圈" | get_isochrone |
| `station_query` | 查车站 | search_stations + get_station_detail |
| `train_query` | 查车次 | get_train_route |
| `timetable_query` | 查时刻表 | search_stations + get_station_detail |
| `clarify` | 信息不足 | 反问 |

### 6 个工具

| 工具 | Java API | 超时 |
|------|----------|------|
| `search_stations` | GET `/api/stations/search?q=` | 10s |
| `get_station_detail` | GET `/api/stations/{id}` | 10s |
| `get_train_route` | GET `/api/trains/{no}/route` | 10s |
| `search_transfer` | POST `/api/transfer/search` | 30s |
| `get_isochrone` | POST `/api/isochrone` | 30s |
| `get_station_timetable` | GET `/api/stations/{id}` | 10s |

### 前端指令系统

Agent 返回 `{ text, instructions, suggestions, station?, train?, routes? }`。

| 指令 | 参数 | 触发场景 |
|------|------|---------|
| `flyToStation` | stationId | 车站查询 |
| `highlightTrain` | trainNo | 车次查询 |
| `highlightRoutes` | routeIds | 路线规划 |
| `highlightIsochrone` | stationId | 等时圈 |
| `openPanel` | panel: station\|train\|routePlan | 打开浮窗 |
| `openModal` | modal: timetable, stationId | 打开模态窗 |
| `clearHighlights` | — | 清除高亮 |

前端 `useAgentChat.ts` 收到响应后：缓存 station/train/routes 数据 → 执行 `dispatchInstruction` → Pinia store 状态更新 → 组件响应式渲染。

### 环境配置

所有配置通过 `AGENT_` 前缀环境变量注入：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `AGENT_LLM_BASE_URL` | `https://api.openai.com/v1` | LLM API 地址 |
| `AGENT_LLM_API_KEY` | — | API 密钥 |
| `AGENT_LLM_MODEL` | `gpt-4o-mini` | 模型名 |
| `AGENT_LLM_TEMPERATURE` | `0.0` | 温度 (确定性) |
| `AGENT_JAVA_BASE_URL` | `http://app:8080` | Java 后端地址 |
| `AGENT_SESSION_TTL_MINUTES` | `30` | 会话过期 |
| `AGENT_MAX_RELAX_ROUNDS` | `3` | 松弛上限 |

当前生产配置：DeepSeek v4-flash @ `https://api.deepseek.com`

---

## 八、前端架构

### 目录结构

```
railway-frontend/src/
├── main.ts                    Vue 入口，注册 Pinia/Router
├── App.vue                    根组件 — layout shell
├── assets/styles/             tokens.css, base.css, fonts.css
├── types/                     TS 接口 (station, train, route, map, agent)
├── api/                       Axios 请求层 (client, stationApi, trainApi, routePlanApi, agentApi)
├── stores/                    6 个 Pinia store
│   ├── mapStore.ts            地图视口 + 图层可见性 + focus(state/city/train)
│   ├── searchStore.ts         搜索栏状态
│   ├── stationStore.ts        车站缓存 + 当前选中 (Map<id, Station>)
│   ├── trainStore.ts          车次缓存 + 当前选中
│   ├── routePlanStore.ts      多路线方案 + 筛选 + activePlanIndices
│   └── agentStore.ts          Agent 对话消息 + 面板 + 快捷建议 + dispatchInstruction + localStorage 持久化
├── composables/
│   ├── useMap.ts              MapLibre 实例生命周期 (shallowRef)
│   ├── useMapInteraction.ts   地图点击/hover → station
│   ├── useMapDynamicResponse.ts  地图动态响应 (watch store → MapLibre 动画)
│   ├── useStationSearch.ts    搜索防抖 200ms + 本地缓存过滤
│   ├── useAgentChat.ts        Agent 真实 API 调用 (替换 mock)
│   ├── useTrainAnimation.ts   requestAnimationFrame 虚线流动动画
│   ├── useRouteAnimation.ts   SVG 路线动画
│   └── useKeyboard.ts         ⌘K 快捷键
└── components/
    ├── layout/AppHeader.vue
    ├── map/MapContainer.vue, MapLoadingOverlay.vue, MapAtmosphere.vue,
    │     RouteAnimationLayer.vue, TrainRouteLayer.vue
    ├── search/SearchBar.vue, SearchDropdown.vue
    ├── panels/StationPanel.vue, TrainPanel.vue, TimetableModal.vue,
    │     LegendPanel.vue, MapControls.vue, RoutePlanPanel.vue
    ├── agent/AgentFab.vue, AgentPanel.vue, AgentBubble.vue, AgentRouteCard.vue
    └── shared/GlassCard.vue, HyperlinkText.vue, StopTimeline.vue, TrainTypeTag.vue
```

### 数据流

```
用户交互 → Pinia action → API / mock → store state 更新 → 组件响应式重渲染
                                                    → MapContainer watch → MapLibre flyTo/图层更新
                                                    → useMapDynamicResponse watch → 动画效果
```

### 关键设计决策

- **MapLibre shallowRef**：必须用 `shallowRef` 而非 `ref` 持有 Map 实例，Vue 深度 proxy 会 crash WebGL context
- **SPA shell 路由**：Vue Router 仅一个 catch-all 路由，所有面板切换由 Pinia + 条件渲染驱动
- **Agent 指令系统**：Agent 返回语义指令，前端翻译为具体操作。保持 Agent 与前端解耦
- **mapHolder getter**：用 `{ get value() { return mapRef.value } }` 防止 Vue 模板自动解包 shallowRef，确保 `TrainRouteLayer` 和 `useMapDynamicResponse` 收到 `{ value: Map | null }` 格式

### 路线动画规格

| 属性 | 高铁 (G) | 动车 (D/C) | 普速 (Z/T/K) |
|------|---------|-----------|-------------|
| 颜色 | `#E53E3E` | `#ED8936` | `#3182CE` |
| 虚线 | 8px 实线, 6px 间隙 | 同 | 同 |
| 流速 | 1.2 px/frame | 0.8 px/frame | 0.4 px/frame |
| 信号脉冲 | 1.5s 周期, 线宽 ×1.5 | 同 | 同 |
| 终点站 | 大圆点 + 呼吸光晕 | 同 | 同 |

>3 条路线以上简化为普通着色线 + 中转站节点（无需动效）。

---

## 九、地图矢量瓦片

### 数据源

| 瓦片层 | API 端点 | 缩放范围 |
|--------|---------|---------|
| railways | `/api/tiles/railways/{z}/{x}/{y}.pbf?v=3` | z2–16 |
| stations | `/api/tiles/stations/{z}/{x}/{y}.pbf?v=3` | z4–16 |

### 安全修复（已完成）

- `${envelope}` 字符串替换 → `ST_TileEnvelope(#{z}, #{x}, #{y})` CTE（消除 SQL 注入）
- `ST_Transform(geom, 3857)` → Web Mercator 投影修正
- 缓冲边界：tile 大小的 256/4096 倍扩展消除接缝

### 线路层

| Layer | display_group | minzoom | 样式 |
|-------|-------------|---------|------|
| `railway-trunk-hs` | trunk | 2 | `#ff3300` 实线 3.0px |
| `railway-trunk-cv` | trunk | 2 | `#33a02c` 实线 2.2px |
| `railway-branch` | branch | 2 | `#6464b5` 虚线 1.5px |
| `railway-spur` | spur | 2 | `#6464b5` 虚线 0.8px |

线宽通过 zoom 插值：zoom 2 时 branch 0.45px / spur 0.24px（亚像素不可见），随放大逐渐增粗。缩放级别过滤已从 SQL 移除，全部由前端 layer opacity/minzoom 控制平滑过渡。

### 车站层

| 缩放范围 | 显示类型 | 样式 |
|---------|---------|------|
| z < 6 | major_hub + major_passenger | 红/蓝圆点 |
| 6 ≤ z < 8 | + medium_passenger | 蓝圆点 |
| 8 ≤ z < 10 | + small_passenger | 蓝圆点 |
| z ≥ 10 | 全部类型 | — |

---

## 十、部署

### Docker Compose

```yaml
services:
  db:         postgis/postgis:17-3.5  → :5432
  redis:      redis:7-alpine           → :6379
  app:        railwaymap-app (Java)  → :10010
  agent:      railway-agent (Python) → :8000
  frontend:   nginx:alpine           → :80
```

### 本地开发

```bash
# 后端
docker compose up -d db redis app

# Agent
cd agent-service
AGENT_LLM_BASE_URL=https://api.deepseek.com \
AGENT_LLM_API_KEY=sk-xxx \
AGENT_LLM_MODEL=deepseek-v4-flash \
AGENT_JAVA_BASE_URL=http://localhost:10010 \
uvicorn src.main:app --port 8000

# 前端
cd railway-frontend && npm run dev   # :5173 proxy → Agent :8000, Java :10010
```

---

## 十一、实施状态

### 已完成 (2026-05-21 ~ 2026-05-22)

| 模块 | 内容 | 提交数 |
|------|------|--------|
| Agent 后端 | FastAPI + LangGraph 状态机 + 6 个工具 + 5 个节点 | 8 |
| Agent 前端集成 | 替换 mock、指令系统、数据缓存、localStorage 持久化 | 4 |
| 地图动画 | useTrainAnimation + TrainRouteLayer + useMapDynamicResponse | 2 |
| Docker | Dockerfile + compose agent 编排 | 1 |
| 测试 | 6 个 agent 单元测试 | 1 |
| Bug 修复 | 松弛死循环、None 容错、站名后缀、端口映射、mapRef 解包、线路断层 | 5 |
| 规范文档 | OpenSpec proposal + design + 3 specs + 实施计划 | 1 |
| SQL 安全 | 矢量瓦片注入修复、投影修正、缩放过滤优化 | 2 |
| **合计** | | **24** |

### Agent 已知局限

- 流式 SSE 未实现（request-response 模式）
- 会话状态内存存储（未迁 Redis）
- LLM intent 分类对模糊问法偶有偏差
- 换乘路线规划依赖数据库有完整 `train_routes` + `train_stops` 数据

### 全局已知问题

- 换乘图每次全量重建 (无缓存) + N+1 查询
- JWT secret 硬编码默认值、DB 密码明文
- 无 `@ControllerAdvice` 全局异常处理、无 API 文档注解
- 无前端 i18n、无 JWT 自动注入拦截器
- `train_stops.departTime` 大量 NULL、`station_id` 大部分 NULL

---

## 十二、系统架构总图

```
┌─────────────────────────────────────────────────────────────────┐
│                         Browser (:5173 dev / :80 prod)           │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │  SearchBar   │  │  MapContainer│  │  Agent Panel (FAB)     │  │
│  │  Station/Train│  │  MapLibre GL │  │  Chat + Route Cards    │  │
│  │  Dropdown    │  │  + Animations│  │  + Quick Suggestions   │  │
│  └──────┬───────┘  └──────┬───────┘  └───────────┬────────────┘  │
│         │                 │                      │               │
│         │    Pinia Stores (map, station, train, routePlan,       │
│         │     search, agent) + dispatchInstruction               │
└─────────┼─────────────────┼──────────────────────┼───────────────┘
          │                 │                      │
          ▼                 ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Vite Proxy / Nginx                            │
│          /api → :10010     /api/agent → :8000                   │
└─────────────────────┬───────────────────────┬───────────────────┘
                      │                       │
          ┌───────────▼───────────┐  ┌────────▼──────────────────┐
          │  railway-api (:10010) │  │  agent-service (:8000)    │
          │  Spring Boot 3.5      │  │  FastAPI + LangGraph      │
          │                       │  │                           │
          │  Controllers ───────────→│  understand → clarify     │
          │  Services              │  │       ↘ search ↗         │
          │  Mappers ──→ XML SQL   │  │       relax → format     │
          │                       │  │                           │
          │  JWT Auth (HMAC-SHA)  │  │  6 tools → httpx → Java  │
          │  Redis Cache (@Cache) │  │  LLM: DeepSeek v4-flash  │
          └───────────┬───────────┘  └───────────────────────────┘
                      │
          ┌───────────▼───────────┐
          │  PostgreSQL 17        │
          │  + PostGIS 3.5        │
          │  + Redis 7            │
          └───────────────────────┘
```

---

## 十三、备注

- `Others/` 目录中两个 `.docx` 文件（`最终项目-2-需求规格说明-小组12.docx`、`最终项目-4-项目文档-详细设计-小组12.docx`）是**医院预约挂号系统**的文档，与本项目无关
- 以 `.` 开头的 markdown 文件为已过时的历史分析报告
- 本报告替代 `RailwayMap 项目完整分析报告.md`（2026-05-18，已移至 `.RailwayMap 项目完整分析报告（比较过时）.md`）
