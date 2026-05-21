# RailwayMap 前端完整设计方案

## 一、设计系统：Railway Signal Industrial

### 1.1 设计哲学

以**铁路信号工业风**为审美核心——将铁路基础设施的视觉语言（信号灯、铁轨、铆接钢板、时刻表编排）转化为 UI 设计语言。在玻璃材质的现代感基底上，注入工业时代的机械精确感。

**三个核心原则：**
- **精确性** — 车次号如信号编码，时间如站台时钟，设计传达铁路系统 0 误差的精确气质
- **层次感** — 信息分层如铁轨分岔：主要信息（车次号、站名）在前景高对比度，辅助信息（时间、线路）以次级视觉权重退后
- **指引性** — 每个交互元素都有明确的方向暗示，如信号灯般引导用户注意力

### 1.2 颜色体系

```
Base Layer（底图与背景）
  --surface-map:          #e8e0d5    // 底图纸色（暖纸浆色，模拟纸质时刻表底色）
  --surface-map-dark:     #1a1c1e    // 深色模式底图
  --surface-glass:        rgba(248,247,244,0.88)  // 玻璃面板基底（偏暖，非纯白）
  --surface-steel:        #f0ece6    // 钢材底色（面板内部底色）

Semantic Signal（铁路信号灯体系）
  --signal-red:           #d63031    // 高铁 G（信号红 — 停止/重要）
  --signal-amber:         #e17055    // 动车 D（信号琥珀 — 减速/中等）
  --signal-green:         #00b894    // 普速/通行（信号绿 — 通行/一般）
  --signal-blue:          #0984e3    // 信息/链接（信号蓝 — 指引）
  --signal-caution:       #fdcb6e    // 警告/中转（信号黄 — 注意）

Route Palette（多路线色板，HSL 等距分布确保区分度）
  --route-1:              #e17055    // 珊瑚橙
  --route-2:              #0984e3    // 信号蓝
  --route-3:              #00b894    // 信号绿
  --route-4:              #6c5ce7    // 紫（偏离信号色用于第四条以上路线）
  --route-5:              #e84393    // 品红
  --route-6:              #fdcb6e    // 信号黄

Text & Surface
  --text-primary:         #2d2a26    // 暖黑（非纯黑，与纸色协调）
  --text-secondary:       #63605b    // 次级文字
  --text-tertiary:        #9c9890    // 辅助文字
  --text-inverse:         #faf9f6    // 反转文字
  --border-light:         rgba(0,0,0,0.06)
  --border-medium:        rgba(0,0,0,0.10)
```

### 1.3 字体系统

```
Display（品牌/标题）
  --font-display:  "Noto Serif SC", "Source Han Serif SC", serif
  // 用途：Logo、页头品牌字、大标题。衬线体唤起铁路时代的历史厚重感。

Body（正文/UI）
  --font-body:     "PingFang SC", "Microsoft YaHei", "Hiragino Sans GB", sans-serif
  // 用途：站名、标签、正文。中文字体栈，确保清晰可读。

Mono（编码/数字）
  --font-mono:     "JetBrains Mono", "SF Mono", "Cascadia Code", monospace
  // 用途：车次号（G1, D301）、时间（09:00）、列车编号。
  // 等宽数字防止 1/l/| 混淆，车次号具有"铁路信号编码"的视觉联想。

Type Scale
  --text-2xs: 10px;  --text-xs: 11px;  --text-sm: 12px;
  --text-base: 14px; --text-lg: 16px;  --text-xl: 18px;
  --text-2xl: 22px;  --text-3xl: 28px; --text-4xl: 36px;
```

### 1.4 空间系统

```
间距（基于 4px）
  --space-1: 4px; --space-2: 8px; --space-3: 12px;
  --space-4: 16px; --space-5: 20px; --space-6: 24px;
  --space-8: 32px; --space-10: 40px; --space-12: 48px;

圆角（铁路铆接感 — 小圆角为主，关键元素可用直角）
  --radius-sm: 4px;     // 车次标签、按钮内部
  --radius-md: 8px;     // 面板、卡片
  --radius-lg: 12px;    // 模态窗
  --radius-none: 0px;   // 部分工业感元素（图例边框、分隔条）

阴影（铁路信号灯的投射感）
  --shadow-sm:  0 1px 3px rgba(0,0,0,0.06);
  --shadow-md:  0 4px 12px rgba(0,0,0,0.08);
  --shadow-lg:  0 8px 24px rgba(0,0,0,0.12);
  --shadow-signal: 0 0 16px rgba(214,48,49,0.25);  // 信号灯光晕
```

### 1.5 运动设计

```
Duration
  --duration-instant: 100ms;   // 微交互（hover, focus）
  --duration-fast: 180ms;      // 按钮 press、标签切换
  --duration-normal: 280ms;    // 面板滑入、弹窗出现
  --duration-slow: 400ms;      // 地图动画、大面板展开

Easing
  --ease-signal: cubic-bezier(0.4, 0, 0.2, 1);    // 默认缓出（标准 material）
  --ease-mechanical: cubic-bezier(0.2, 0, 0, 1);   // 机械感缓出（适合面板滑动）
  --ease-bounce: cubic-bezier(0.34, 1.56, 0.64, 1); // 弹性回弹（车站 hover）

Map Animation
  - 路线流动：stroke-dashoffset 动画，1.2s/1.8s 错开相位
  - 信号灯脉冲：scale + opacity 双属性，2s infinite
  - 面板入场：transform + opacity，280ms ease-mechanical
  - 地图入场序列（新增）：
    1. 底图淡入 300ms
    2. 线路从枢纽站向外辐射展开 600ms（stagger 120ms per 线路等级）
    3. 车站标记逐个弹出 400ms（stagger 30ms）
```

---

## 二、技术选型

### 2.1 核心技术栈

| 层级 | 技术 | 版本 | 选型理由 |
|------|------|------|---------|
| 框架 | Vue 3 (Composition API) | ^3.5 | 响应式系统 + `<script setup>` |
| 构建工具 | Vite | ^6.2 | 极速 HMR，原生 ESM |
| 类型系统 | TypeScript | ^5.7 | 全量类型覆盖 |
| 地图引擎 | MapLibre GL JS | ^5.2 | WebGL 瓦片渲染，开源，社区活跃 |
| 瓦片源 | MapTiler | Cloud | OSM 中国数据，免费 10 万次/月，支持自定义样式 |
| 状态管理 | Pinia | ^2.3 | Vue 3 官方推荐，模块化 store |
| 路由 | Vue Router | ^4.5 | 搜索状态 URL 持久化 |
| HTTP | Axios | ^1.7 | 拦截器、取消请求、超时控制 |

### 2.2 辅助技术选型

| 层级 | 技术 | 选型理由 |
|------|------|---------|
| CSS 框架 | Tailwind CSS 4 | 原子化布局 + `@theme` 可注入设计 token |
| 组件基元 | **Radix Vue** | 无样式组件（Dialog, Popover, Tabs, Toggle），提供无障碍行为但不限制视觉风格 → 与 Railway Signal Industrial 审美完全兼容 |
| 图标 | **Lucide Vue** | 轻量、可定制 stroke，铁路相关图标（Train, Route, MapPin, Search, Compass） |
| 动画 | **CSS transitions + animations** 为主，复杂编排用 `Motion` (`motion-v`) | 地图动画优先 CSS；布局动画可引入 Motion 的 `AnimatePresence` |
| 工具函数 | @vueuse/core | `useDebounceFn`, `useLocalStorage`, `useMediaQuery`, `useEventListener` |
| 地图工具 | @maplibre/maplibre-gl-directions | 可选，未来路径规划参考 |
| 部署 | Nginx + Docker | 静态资源 + API 代理（已有 Dockerfile） |

### 2.3 不选用的技术与理由

| 技术 | 理由 |
|------|------|
| Naive UI | 自带视觉风格与 Railway Industrial 审美冲突，大量自定义样式抵消了组件库的效率优势 |
| Element Plus | 同上，且体积更大 |
| Pinia persistedstate | 暂不需要 localStorage 持久化，路由 query params 已覆盖分享场景 |
| GSAP / Framer Motion | CSS-only 动画足以覆盖 90% 场景，避免额外依赖 |
| OpenLayers | API 设计老旧，MapLibre 的 WebGL 渲染更适合大数据量线路 |

---

## 三、项目架构

### 3.1 目录结构

```
railway-frontend/
├── index.html
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.ts            # Tailwind 4 @theme 扩展
├── env.d.ts
│
├── public/
│   ├── favicon.svg               # 铁路信号灯式 favicon
│   └── map-style.json            # MapLibre 地图样式（MapTiler）
│
└── src/
    ├── main.ts                   # 入口：createApp + router + pinia
    ├── App.vue                   # 根组件：layout shell
    │
    ├── assets/
    │   ├── styles/
    │   │   ├── tokens.css        # 设计 token CSS 变量
    │   │   ├── base.css          # reset + 全局排版
    │   │   └── fonts.css         # @font-face（JetBrains Mono, Noto Serif SC）
    │   └── textures/
    │       └── noise.png         # 纸质噪声纹理（64×64 base64）
    │
    ├── types/                    # 全局 TypeScript 类型
    │   ├── station.ts            # Station, StationType
    │   ├── train.ts              # Train, TrainStop, TrainType
    │   ├── route.ts              # RoutePlan, RouteSegment, RouteConstraint
    │   ├── map.ts                # MapViewport, MapLayer, GeoJSON types
    │   └── agent.ts              # ChatMessage, AgentIntent, PlanResult
    │
    ├── api/                      # Axios 请求层
    │   ├── client.ts             # Axios 实例 + 请求/响应拦截器
    │   ├── stationApi.ts         # GET /api/stations/:id, /api/stations/search
    │   ├── trainApi.ts           # GET /api/trains/:no, /api/trains/search
    │   └── routePlanApi.ts       # POST /api/plan  (对接路径规划 MCP)
    │
    ├── stores/                   # Pinia stores
    │   ├── mapStore.ts           # 地图视口状态
    │   ├── searchStore.ts        # 搜索状态
    │   ├── stationStore.ts       # 车站数据 + 选中状态
    │   ├── trainStore.ts         # 车次数据 + 选中状态
    │   ├── routePlanStore.ts     # 多路线规划
    │   └── agentStore.ts         # 对话面板 + 消息
    │
    ├── composables/              # 可复用组合式函数
    │   ├── useMap.ts             # MapLibre 实例生命周期
    │   ├── useMapInteraction.ts  # 地图点击/hover 事件
    │   ├── useStationSearch.ts   # 防抖搜索 + API
    │   ├── useRouteAnimation.ts  # 路线动画管理
    │   ├── useAgentChat.ts       # Agent 对话 mock/API
    │   ├── useKeyboard.ts        # 全局快捷键
    │   └── useBreakpoint.ts      # 响应式断点
    │
    ├── components/
    │   ├── layout/
    │   │   └── AppHeader.vue     # 页头容器（Logo + SearchBar + UserMenu）
    │   │
    │   ├── map/
    │   │   ├── MapContainer.vue       # MapLibre 容器 + 生命周期
    │   │   ├── StationLayer.vue       # 车站 GeoJSON → MapLibre symbol layer
    │   │   ├── RouteLayer.vue         # 线路 GeoJSON → MapLibre line layer
    │   │   ├── RouteAnimationLayer.vue # SVG 动画叠加层（流动虚线/实线）
    │   │   └── MapLoadingOverlay.vue  # 地图加载中的骨架屏
    │   │
    │   ├── search/
    │   │   ├── SearchBar.vue          # 搜索栏（Tab 切换 + Input）
    │   │   └── SearchDropdown.vue     # 下拉建议列表（Radix Popover）
    │   │
    │   ├── panels/
    │   │   ├── StationPanel.vue       # 左侧：车站信息浮窗
    │   │   ├── TrainPanel.vue         # 左侧：车次详情 + 经停站时间轴
    │   │   ├── TimetableModal.vue     # 中央：经停车次时刻表（Radix Dialog）
    │   │   ├── LegendPanel.vue        # 右上：图例
    │   │   └── MapControls.vue        # 右上：缩放/定位/图层按钮组
    │   │
    │   ├── agent/
    │   │   ├── AgentFab.vue           # 右下浮动按钮
    │   │   ├── AgentPanel.vue         # 对话面板外壳
    │   │   ├── AgentMessages.vue      # 消息列表滚动区
    │   │   ├── AgentBubble.vue        # 单条消息气泡
    │   │   ├── AgentRouteCard.vue     # 路线方案卡片（消息内嵌）
    │   │   └── AgentInput.vue         # 输入区
    │   │
    │   └── shared/
    │       ├── HyperlinkText.vue      # 超链接文本（站名/车次号）
    │       ├── TrainTypeTag.vue       # 车次类型标签（G/D/Z）
    │       ├── StopTimeline.vue       # 经停站时间轴
    │       ├── GlassCard.vue          # 通用玻璃材质卡片
    │       └── SignalIcon.vue         # 铁路信号灯图标组件
    │
    └── router/
        └── index.ts               # 路由配置（单路由 + query params）

# 预计文件数：~55 files
```

### 3.2 组件树

```
App.vue
│
├── AppHeader.vue                         ← 固定顶部
│   ├── BrandLogo.vue (inline)            ← Logo + "铁路地图"
│   ├── SearchBar.vue                     ← flex: 1; max-width: 520px; 居中
│   │   ├── [Tab: 车站 | 车次 | 城市]       ← Radix ToggleGroup
│   │   ├── <input>
│   │   └── SearchDropdown.vue            ← Radix Popover content
│   │       ├── ResultItem × N
│   │       └── 无结果状态
│   └── UserMenu.vue                      ← 深色模式 | 关于 | 用户头像
│
├── MapContainer.vue                      ← 绝对定位充满页头下方
│   ├── [MapLibre canvas]                  ← z-index: 0
│   ├── [StationLayer]                     ← z-index: 1 (symbol layer)
│   ├── [RouteLayer]                       ← z-index: 2 (line layers)
│   ├── [RouteAnimationLayer]              ← z-index: 3 (SVG overlay)
│   └── MapLoadingOverlay.vue              ← z-index: 10 (加载态)
│
├── <Teleport to="map-area">
│   ├── StationPanel.vue                  ← 左侧滑入浮窗
│   │   ├── GlassCard
│   │   │   ├── TrainTypeTag
│   │   │   ├── HyperlinkText (站名/城市)
│   │   │   └── [所有车次按钮 → 打开 TimetableModal]
│   │   └── GlassCard (线路信息)
│   │
│   ├── TrainPanel.vue                    ← 左侧滑入浮窗
│   │   ├── GlassCard
│   │   │   ├── TrainTypeTag
│   │   │   └── StopTimeline
│   │   │       └── HyperlinkText (经停站名) × N
│   │   └── GlassCard (全程时间等)
│   │
│   ├── TimetableModal.vue                ← 中央弹出（Radix Dialog）
│   │   └── <table>
│   │       └── HyperlinkText (站名/车次) × N
│   │
│   ├── LegendPanel.vue                   ← 右上角图例
│   │   └── [checkbox 列表]
│   │
│   ├── MapControls.vue                   ← 右上角按钮组
│   │   ├── MapControlButton × 4
│   │
│   ├── AgentFab.vue                      ← 右下圆形按钮
│   │
│   └── AgentPanel.vue                    ← 右侧滑入
│       ├── AgentMessages.vue
│       │   └── AgentBubble.vue × N
│       │       └── AgentRouteCard.vue (条件)
│       └── AgentInput.vue
│
└── [地图入场动画序列]  ← onMounted 触发
```

---

## 四、核心模块设计

### 4.1 MapLibre 集成 — `useMap` composable

```ts
// composables/useMap.ts
// 核心职责：MapLibre 实例的创建、销毁、对外暴露操控方法

import { shallowRef, ref, onMounted, onUnmounted } from 'vue'
import { Map, type MapOptions, type GeoJSONSourceSpecification } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'

export function useMap(containerId: string) {
  const map = shallowRef<Map | null>(null)   // shallowRef 避免深度 proxy
  const isLoaded = ref(false)
  const loadProgress = ref(0)                 // 0-100 用于入场动画

  onMounted(async () => {
    const options: MapOptions = {
      container: containerId,
      style: '/map-style.json',              // MapTiler 自定义样式
      center: [104.0, 36.5],                 // 中国地理中心
      zoom: 5.2,
      minZoom: 3,
      maxZoom: 18,
      maxBounds: [73, 18, 135, 54] as any,   // 限制到中国范围
      attributionControl: false,              // 自定义 attribution 位置
    }
    const instance = new Map(options)
    map.value = instance

    instance.on('load', () => {
      isLoaded.value = true
      loadProgress.value = 100
    })
  })

  onUnmounted(() => { map.value?.remove() })

  // 公开方法
  function flyTo(center: [number, number], zoom: number, options?: { duration?: number }) {}
  function fitBounds(bounds: [[number,number],[number,number]], padding?: number) {}
  function addSource(id: string, source: GeoJSONSourceSpecification) {}
  function addLineLayer(id: string, source: string, paint: any) {}
  function addSymbolLayer(id: string, source: string, paint: any, layout: any) {}
  function removeLayer(id: string) {}
  function on(event: string, handler: Function) {}
  function once(event: string, handler: Function) {}

  return {
    map,           // shallowRef<Map | null>
    isLoaded,      // Ref<boolean>
    loadProgress,  // Ref<number>
    flyTo, fitBounds, addSource, addLineLayer, addSymbolLayer,
    removeLayer, on, once,
  }
}
```

**关键设计决策：**
- `shallowRef` 而非 `ref` — MapLibre Map 对象内部有 WebGL context、大量事件监听器，Vue 的深度响应式 proxy 会导致严重性能问题甚至 crash
- 不把 map 实例放进 Pinia — DOM 绑定资源只属于组件树
- 地图视口状态（center, zoom）放入 `mapStore` 单独追踪，用于 URL 持久化和跨组件同步

### 4.2 状态管理 — Pinia Store 设计

#### mapStore

```ts
// stores/mapStore.ts
// 只存视口元数据，不存 map 实例

interface MapViewport {
  center: [number, number]
  zoom: number
  bearing: number
  pitch: number
}

// Actions:
//   setViewport(v: Partial<MapViewport>)
//   flyToStation(stationId: string)      → 从 stationStore 取坐标 → flyTo
//   fitRouteBounds(planId: string)       → 从 routePlanStore 取 bounds → fitBounds
```

#### searchStore

```ts
// stores/searchStore.ts

interface SearchState {
  activeTab: 'station' | 'train' | 'city'
  query: string
  results: SearchResult[]
  isOpen: boolean
  loading: boolean
}

// Actions:
//   setTab(tab)
//   search(q: string)                    → 防抖 200ms → API
//   selectResult(result)                  → 分发到 stationStore / trainStore / mapStore
//   clear()
```

#### stationStore

```ts
// stores/stationStore.ts

interface StationState {
  currentStationId: string | null
  stationCache: Map<string, Station>      // 已加载的车站缓存
  allTrainsAtCurrentStation: Train[]      // 当前站的经停车次
  loading: boolean
}

// Actions:
//   fetchStation(id: string)              → API → 更新 cache + currentStationId
//   fetchAllTrains(stationId: string)     → API → allTrainsAtCurrentStation
//   clear()
```

#### trainStore

```ts
// stores/trainStore.ts

interface TrainState {
  currentTrainNo: string | null
  trainCache: Map<string, Train>
  loading: boolean
}

// Actions:
//   fetchTrain(no: string)               → API → 更新 cache + currentTrainNo
//   clear()
```

#### routePlanStore

```ts
// stores/routePlanStore.ts

interface RoutePlanState {
  plans: RoutePlan[]                      // 当前全部路线方案
  activePlanIndices: number[]             // 当前活跃的方案索引（约束筛选后）
  loading: boolean
}

// Actions:
//   requestPlan(constraints: RouteConstraint)  → POST /api/plan
//   filterBy(constraint: Partial<RouteConstraint>)  → 本地筛选 + 更新 activePlanIndices
//   clear()
```

#### agentStore

```ts
// stores/agentStore.ts

interface AgentState {
  messages: ChatMessage[]
  isPanelOpen: boolean
  isProcessing: boolean                   // typing indicator
}

// Actions:
//   sendMessage(text: string)             → 添加用户消息 → 调用 Agent 逻辑 → 添加回复
//   clearMessages()
//   togglePanel()
//   openPanel() / closePanel()
```

### 4.3 数据流

```
┌─────────────────────────────────────────────────────────────────────┐
│                         用户交互                                     │
│                                                                     │
│  搜索 "G1"     点击车站标记     Agent 输入 "北京到广州"              │
│     │              │                  │                              │
│     ▼              ▼                  ▼                              │
│ searchStore    stationStore      agentStore                          │
│  .search()      .fetchStation()   .sendMessage()                     │
│     │              │                  │                              │
│     ▼              ▼                  ▼                              │
│ trainApi         stationApi        routePlanApi                      │
│ .search("G1")    .get("bj")        .plan(constraints)                │
│     │              │                  │                              │
│     ▼              ▼                  ▼                              │
│ trainStore       stationStore      routePlanStore                    │
│ .fetchTrain()    .fetchStation()   .setPlans()                       │
│     │              │                  │                              │
│     ├──────────────┼──────────────────┤                              │
│     │              │                  │                              │
│     ▼              ▼                  ▼                              │
│ ┌──────────────────────────────────────────────────────────────┐    │
│ │                      UI 响应层                                │    │
│ │                                                              │    │
│ │  TrainPanel      StationPanel     AgentMessages              │    │
│ │  (左侧浮窗)       (左侧浮窗)        (气泡+路线卡片)            │    │
│ │                                                              │    │
│ │  MapContainer                                                │    │
│ │  ├─ flyTo(station.coords)                                    │    │
│ │  ├─ addRouteLayer(plan.segments)                             │    │
│ │  └─ RouteAnimationLayer.draw(geojson)                         │    │
│ └──────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

**数据流规则：**
1. 所有 API 请求经 Pinia action 发起，不在组件中直接调 `api/xx`
2. Map 实例方法仅通过 `useMap` composable 调用，组件不直接访问 `map.value`
3. 跨 store 联动通过组件层 `watch` 实现，不在 store 内部相互引用（避免循环依赖）
4. URL query params 在 `watch` 中同步，作为搜索状态的持久层

### 4.4 MapLibre 图层架构

```
Layer Stack (MapLibre style)
─────────────────────────────
z=10  Station labels (symbol layer, 车站名称 hover 态)
z=9   Station markers (circle layer, 车站圆点)
z=8   Route highlight solid (line layer, 选中路线实线段)
z=7   Route highlight dashed (line layer, 选中路线虚线段)
z=6   Multi-route plan layer (N 条路线 × N 条 line layers)
z=5   SVG animation overlay (HTML overlay, 流动动画)
z=4   Railway lines (line layers, 后台线路 GeoJSON)
z=3   Terrain raster (MapTiler hillshade, 可选)
z=2   Tile basemap (MapTiler vector tiles)
z=1   Background fill
z=0   MapLibre canvas background
```

**性能策略：**
- 车站 > 200 个时切换到 MapLibre cluster source，聚合成圆形簇
- 线路 GeoJSON 简化为 Douglas-Peucker 容差 0.001°，全国线路数据压缩到 < 2MB
- 动画只在可视路线 > 0 时启动 `requestAnimationFrame`，路线清空时取消
- MapLibre 的 `symbol-placement: point` 用于全国视角，`symbol-placement: line` 用于城市级缩放

---

## 五、关键交互设计

### 5.1 地图入场动画序列

```
Timeline (页面 onMounted):
  0ms     → 底图背景 + 网格线淡入 (opacity 0→1, 500ms)
  300ms   → 铁路线路从枢纽站向外辐射展开
             高铁路线先行 (red, stagger 120ms per line)
             普铁/货运后续 (blue/brown, stagger 80ms per line)
  800ms   → 主要枢纽站标记依次弹出 (★ 星形)
             动画：scale(0) → scale(1.2) → scale(1) + fade in
             stagger: 30ms per station, 从中心向外
  1200ms  → 中等车站标记淡入
  1500ms  → 页头 + 控件组淡入（UI 层最后出现）
```

### 5.2 路线切换过渡

```
场景：从单条车次切换到多路线规划

Before:  单条 G1 红色动画虚线
After:   3 条多色路线 + 虚实交替段落

Transition:
  1. 旧路线 opacity 1 → 0.2 (300ms)  [保留淡化，不立即移除]
  2. 背景线路 opacity 1 → 0.15 (300ms) [非相关线路大幅淡化]
  3. 新路线 opacity 0 → 1 (400ms, 每条 stagger 100ms)
  4. 中转站标记同时弹出
  5. 旧路线移除 (200ms after 新路线完全显示)
```

### 5.3 面板动画

```
左侧浮窗（StationPanel / TrainPanel）：
  - 展开：translateX(-100%) → translateX(0), 280ms ease-mechanical
  - 切换内容：内部内容 opacity 0→1, 200ms, delay 100ms（给面板滑入留时间）
  - 关闭：translateX(0) → translateX(-100%), 200ms ease-mechanical

中央模态窗（TimetableModal）：
  - 展开：scale(0.92) + opacity(0) → scale(1) + opacity(1), 250ms ease-signal
          + backdrop opacity 0→1, 200ms
  - 关闭：反向，200ms

Agent 对话面板：
  - 展开：translateX(100%) → translateX(0), 350ms ease-mechanical
          + 右上角控件组同步左移 (right: 16px → 436px, 350ms ease-mechanical)
  - 消息气泡：opacity 0 + translateY(8px) → opacity 1 + translateY(0), 250ms
              每条约 80ms stagger
```

---

## 六、实现路线图

### Phase 1 — 项目骨架（Day 1）

```
□ 初始化 Vite + Vue 3 + TS 项目
□ 安装依赖：maplibre-gl, pinia, vue-router, axios, radix-vue,
             lucide-vue-next, @vueuse/core, tailwindcss 4
□ 创建 src/assets/styles/ (tokens.css, base.css, fonts.css)
□ 编写完整的 CSS 设计 token（颜色 / 字体 / 间距 / 阴影 / 动画）
□ 配置 Tailwind 4 @theme 注入 token
□ 创建 src/types/ 全部类型定义
□ 创建 src/api/client.ts Axios 实例
□ 创建 src/router/index.ts
□ 搭建 App.vue 布局骨架（Header + Map + 各面板占位）
□ 验证 tsconfig + vite dev server 正常运行
```

### Phase 2 — 地图核心（Day 2-3）

```
□ 实现 useMap composable
□ 实现 MapContainer.vue（MapLibre 实例 mount + 瓦片底图渲染）
□ 接入 MapTiler API key + map-style.json 配置
□ 实现 MapLoadingOverlay.vue（入场动画骨架屏）
□ 实现 useMapInteraction composable（点击/hover 事件分发）
□ 实现地图入场动画序列
□ 实现 mapStore（视口状态）
□ 实现 StationLayer（GeoJSON → symbol layer）
□ 实现 RouteLayer（后台线路 GeoJSON 静态渲染）
```

### Phase 3 — 搜索与页头（Day 3-4）

```
□ 实现 AppHeader.vue + BrandLogo
□ 实现 SearchBar.vue（Tab 切换 + Input）
□ 实现 SearchDropdown.vue（Radix Popover + 结果列表）
□ 实现 searchStore
□ 实现 useStationSearch composable（防抖 + API）
□ 实现 stationApi + trainApi（mock 数据先行）
□ 实现 stationStore + trainStore
□ 实现搜索 → 地图联动（flyTo + 高亮）
□ 实现 UserMenu.vue（深色模式 toggle + 关于）
```

### Phase 4 — 左侧浮窗（Day 4-5）

```
□ 实现 StationPanel.vue（GlassCard 外壳 + 滑入动画）
□ 实现 TrainPanel.vue（经停站时间轴）
□ 实现 StopTimeline.vue（共享组件）
□ 实现 TrainTypeTag.vue（共享组件）
□ 实现 HyperlinkText.vue（共享组件）
□ 实现 TimetableModal.vue（Radix Dialog + 6 列表格）
□ 实现地图点击车站 → StationPanel 联动
□ 实现超链接跳转：车站名 ↔ 车次号
□ 实现左侧面板返回导航
```

### Phase 5 — 图例与控件（Day 5）

```
□ 实现 LegendPanel.vue（可折叠图例）
□ 实现 MapControls.vue（按钮组）
□ 实现 MapControlButton.vue（共享按钮组件）
□ 实现图层 checkbox 开关 → MapLibre layer visibility
□ 实现深色模式 → 切换 MapTiler 样式 URL
□ 实现指南针控件（MapLibre NavigationControl）
```

### Phase 6 — Agent 对话与路径规划（Day 6-7）

```
□ 实现 AgentFab.vue（圆形浮动按钮）
□ 实现 AgentPanel.vue（面板外壳 + 滑入动画）
□ 实现 AgentMessages.vue（消息列表 + 自动滚到底部）
□ 实现 AgentBubble.vue（左右气泡布局 + Markdown 渲染）
□ 实现 AgentRouteCard.vue（路线方案卡片）
□ 实现 AgentInput.vue
□ 实现 agentStore
□ 实现 useAgentChat composable（mock 对话逻辑）
□ 实现 routePlanStore
□ 实现多路线可视化（RouteAnimationLayer + 色板映射）
□ 实现虚实交替段落区分
□ 实现中转站标记动画
□ 实现约束筛选 → 路线淡入/淡出
□ 实现 Agent 查询 → 地图联动
```

### Phase 7 — 地图细节与打磨（Day 8-9）

```
□ 车站 label 背景保护条
□ 指南针图标（地图角落）
□ 比例尺控件
□ 纸质纹理叠加层（mix-blend-mode: multiply）
□ 路线过渡动画（交叉淡入淡出）
□ 图例 signal-icon 替换为 Lucide 图标
□ 车站 marker 弹性 hover 效果
□ 移动端响应式适配（768px + 480px 两个断点）
```

### Phase 8 — 深色模式与收尾（Day 10）

```
□ 深色模式完整 token 定义
□ 深色地图样式（MapTiler dark 预设）
□ @media (prefers-color-scheme: dark) 自动切换
□ 键盘导航（Tab 在搜索结果中移动、Enter 确认）
□ 全局快捷键（⌘K, Esc）
□ 性能检查：MapLibre source/layer 泄漏、watch 内存泄漏
□ TypeScript strict 模式通过
□ 构建验证：vite build 无错误
```

---

## 七、待确认问题

1. **JetBrains Mono 字体** — ✅ 已确认：引入 woff2 子集化版本（~40KB），用于车次号和时间显示。
2. **车站标记渲染策略** — ✅ 已确认：从一开始就使用 MapLibre symbol layer 渲染车站标记，确保全国 6000+ 车站场景下的性能。仅在少量主要枢纽站（< 50 个）保留 DOM overlay 用于复杂交互（如 hover 弹窗）。
3. **Agent 对话后端** — ✅ 已确认：当前阶段 Agent 对话仅进行前端视觉风格设计（面板布局、气泡样式、路线卡片样式），消息逻辑使用前端 mock。后端功能实现后再对接真实 API。
