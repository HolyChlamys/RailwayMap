# 中国铁路地图与多次中转路线规划 — 开发计划 v1.1

> **创建日期**: 2026-04-29
> **状态**: 计划阶段（待确认后进入 Phase 0）
> **原型参考**: `/home/chlamys/CODE/Project/Railwaymap_text`
> **目标路径**: `/home/chlamys/CODE/Project/RailwayMap`

---

## 版本历史

| 版本 | 日期 | 变更摘要 |
|------|------|----------|
| v1.0 | 2026-04-29 | 初始版本：整合架构设计、原型问题总结、数据管线方案、数据库设计、分阶段实施路线。含 10 个待确认问题。 |
| v1.1 | 2026-04-29 | 用户反馈整合版：(1) 技术栈版本锁定 Spring Boot 3.5.14 + PostgreSQL 17 + PostGIS 3.5 + MyBatis-Plus 3.5.16；(2) 新增地图图例分类体系（车站 12 类、铁路 7 类）；(3) 数据库新增票价/用户表；(4) OSM 数据人工补录方案；(5) Docker 优先部署；(6) 10 个待确认问题全部闭环，剔除城市游/同城换乘/国际列车/余票查询等暂不实现的功能 |

> **版本控制说明**：MAJOR 变更表示架构方向调整或大阶段切换；MINOR 变更表示细节补充、模块方案修改。每次修改须在版本历史表中新增一行并更新文件名与文档标题。旧版本保留为 `.md` 归档，不可原地覆盖。

---

## 目录

1. [项目目标](#1-项目目标)
2. [技术栈版本锁定](#2-技术栈版本锁定)
3. [原型项目问题总结](#3-原型项目问题总结)
4. [总体架构设计](#4-总体架构设计)
5. [地图图例分类体系](#5-地图图例分类体系)
6. [数据管线设计](#6-数据管线设计)
7. [数据库设计](#7-数据库设计)
8. [后端模块设计](#8-后端模块设计)
9. [前端模块设计](#9-前端模块设计)
10. [搜索系统设计](#10-搜索系统设计)
11. [车次路线匹配算法](#11-车次路线匹配算法)
12. [多次中转换乘规划](#12-多次中转换乘规划)
13. [Docker 部署配置](#13-docker-部署配置)
14. [OSM 数据人工补录方案](#14-osm-数据人工补录方案)
15. [分阶段实施路线](#15-分阶段实施路线)
16. [用户决策记录](#16-用户决策记录)

---

## 1. 项目目标

### 1.1 基础目标：中国铁路在线地图

- 以交互式地图呈现全国铁路线路与车站
- 支持车站搜索（中文/拼音/首字母）、车次搜索、站站查询
- 车次经行路线在地图上高亮显示
- 矢量瓦片渲染，保证流畅的缩放与平移体验
- 地图图例按铁路专业分类体系呈现（车站 12 类 + 铁路 7 类）

### 1.2 创新目标：多次中转路线规划

- 12306 仅支持一次中转，本系统支持用户自定义中转次数（2-4 次）
- 将超长途旅程拆分为夜间乘车 + 白天城市游的组合方案（远期）
- 中转等待时间优化
- 提供多种偏好排序（最少时间 / 最少换乘 / 夜行昼游 / 最低票价）

### 1.3 范围边界

| 范围 | 本阶段 (Phase 0-7) | 远期 |
|------|:---:|:---:|
| 国内铁路线路与车站 | ✓ | |
| 地图交互与搜索 | ✓ | |
| 车次路线高亮 | ✓ | |
| 多次中转换乘规划 | ✓ | |
| 票价存储与展示 | ✓ | |
| 用户登录/收藏/历史 | Phase 7 | |
| 中转站城市游信息 | | 远期 |
| 同城异站换乘时间 | | 远期 |
| 国际列车 | | 远期 |
| 实时余票查询 | | 远期（需 12306 接口） |

---

## 2. 技术栈版本锁定

### 2.1 版本核实结论

| 组件 | 版本 | 发布日期 | 核实状态 |
|------|------|----------|:---:|
| **Spring Boot** | **3.5.14** | 2026-04-23 | [已核实](https://spring.io/blog/2026/04/23/spring-boot-3-5-14-available-now) — 含 48 个 bug 修复与 6 个 CVE 补丁 |
| **Java** | **21** (LTS) | - | Spring Boot 3.5.x 最低要求 Java 17，选 21 LTS |
| **PostgreSQL** | **17** | - | 当前最新大版本 |
| **PostGIS** | **3.5** | - | Docker 镜像 `postgis/postgis:17-3.5` 已确认可用，Alpine 版含 3.5.5 |
| **MyBatis-Plus** | **3.5.16** | 2026-02 | 最新稳定版，兼容 Spring Boot 3.5.9+，适配 mybatis-spring 4.0.0 |
| **MyBatis-Plus Starter** | `mybatis-plus-spring-boot3-starter` | - | 必须使用 boot3 starter（非旧版 boot-starter），否则与 Spring Boot 3.x 不兼容 |
| **JTS** | **1.20.0** | - | Java Topology Suite，GIS 几何计算 |
| **Vue** | **3.5.x** | - | Composition API + `<script setup>` |
| **Vite** | **6.x** | - | 前端构建 |
| **MapLibre GL JS** | **5.x** | - | WebGL 地图渲染引擎 |
| **Naive UI** | **2.x** | - | Vue 3 组件库（用户确认） |
| **Tailwind CSS** | **4.x** | - | 原子化 CSS |

### 2.2 关键 Maven 依赖

```xml
<!-- 父 POM -->
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.5.14</version>
</parent>

<properties>
    <java.version>21</java.version>
    <mybatis-plus.version>3.5.16</mybatis-plus.version>
    <postgresql.version>42.7.5</postgresql.version>
    <jts.version>1.20.0</jts.version>
</properties>

<!-- MyBatis-Plus (Spring Boot 3.x 专用 starter) -->
<dependency>
    <groupId>com.baomidou</groupId>
    <artifactId>mybatis-plus-spring-boot3-starter</artifactId>
    <version>${mybatis-plus.version}</version>
</dependency>
```

### 2.3 Docker 镜像

```yaml
# docker-compose.yml
services:
  db:
    image: postgis/postgis:17-3.5        # PostgreSQL 17 + PostGIS 3.5.2 (Debian)
    # 备选: postgis/postgis:17-3.5-alpine  # 更小体积 + 更新依赖版本 (PostGIS 3.5.5)
  app:
    build:
      context: ./spring-backend
      dockerfile: Dockerfile              # 多阶段: maven:3.9-eclipse-temurin-21 → eclipse-temurin:21-jre
  redis:
    image: redis:7-alpine
```

---

## 3. 原型项目问题总结

原型项目 (`Railwaymap_text`) 验证了核心技术可行性，同时暴露了 5 个关键问题：

### 3.1 问题一：数据获取——分片缺陷

**现象**：Overpass API 单次请求超时/限流；手动定义的 12 个矩形区域存在缝隙，导致成都、西藏、海南南部、山东半岛等边界处数据缺失。

**v1.1 方案**：渔网分割法——1°×1° 网格 + 0.05° 重叠 + 中国陆地边界多边形过滤 + 蛇形排序。详见 [6.2 网格分割策略](#62-网格分割策略)。

### 3.2 问题二：底图观感与坐标偏移

**现象**：天地图底图观感陈旧、标注过多干扰铁路主题；缩放时出现短暂偏移（已通过 Canvas 渲染修复）。

**v1.1 方案**：优先验证 MapTiler Streets；坐标系统一为 WGS-84，如最终选用天地图则在 MapLibre 前端做 GCJ-02 实时转换。详见 [9.1 底图方案](#91-底图方案)。

### 3.3 问题三：搜索功能欠缺

**现象**：仅 ILIKE 模糊匹配，无拼音、无车次级联、无城市联想。

**v1.1 方案**：中文/拼音/首字母三维搜索 + 车次前缀级联 + 城市→车站联想。详见 [10. 搜索系统设计](#10-搜索系统设计)。

### 3.4 问题四：车次经行段匹配不准确

**现象**：ST_DWithin 10km 阈值过大，匹配到不相关线路；部分路段缺数据导致断续。

**v1.1 方案**：三阶段匹配——候选筛选(2km) → BFS 拓扑图搜索 → 降级距离匹配，预计算存入 `train_segment_mapping` 表。详见 [11. 车次路线匹配算法](#11-车次路线匹配算法)。

### 3.5 问题五：数据库批量导入失败

**现象**：单管道全量导入，无分批提交，内存压力大，失败无日志。

**v1.1 方案**：Spring Batch 分文件/分块导入，每 1000 条提交一次，每文件打印进度日志，失败网格独立记录。详见 [6.3 数据导入策略](#63-数据导入策略)。

---

## 4. 总体架构设计

### 4.1 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      浏览器                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Vue 3 SPA (Vite 6 构建)                             │   │
│  │  ├─ MapLibre GL JS 5.x   地图渲染 (WebGL)           │   │
│  │  ├─ Tailwind CSS 4 + Naive UI 2   UI 层             │   │
│  │  ├─ Pinia                全局状态管理                │   │
│  │  └─ TypeScript           类型安全                    │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────┬───────────────────────────────────────────────┘
              │ HTTP/HTTPS
              ▼
┌─────────────────────────────────────────────────────────────┐
│  Nginx (反向代理 + 静态资源)                                 │
│  ├─ /api/*   → app:10010 (Spring Boot)                      │
│  ├─ /tiles/* → app:10010                                    │
│  └─ /*      → Vue 静态文件                                  │
└─────────────┬───────────────────────────────────────────────┘
              │
    ┌─────────┼─────────┐
    ▼         ▼         ▼
┌────────┐ ┌──────┐ ┌──────────┐
│Spring  │ │PostgreSQL│ │Redis    │
│Boot    │ │17+PostGIS│ │7-Alpine │
│3.5.14  │ │3.5       │ │(缓存)   │
│:10010  │ │:5432     │ │:6379    │
└────────┘ └──────┘ └──────────┘
```

### 4.2 Docker Compose 拓扑

```
services:
  db       → postgis/postgis:17-3.5       (端口 5432)
  redis    → redis:7-alpine                (端口 6379)
  app      → railway-map:latest            (端口 10010, 多阶段构建)
  frontend → nginx:alpine                  (端口 80, 静待 + 反向代理)
```

### 4.3 Maven 多模块结构

```
railway-map/
├── pom.xml                        # 父 POM (Spring Boot 3.5.14, Java 21)
├── railway-common/                # 公共模块 — 实体/DTO/枚举/工具
├── railway-data/                  # 数据访问层 — MyBatis Mapper
├── railway-service/               # 业务逻辑层 — 地图/搜索/路线/换乘/同步
├── railway-api/                    # Web 层 — REST 控制器 + 启动类
├── railway-batch/                  # 批处理模块 — Spring Batch 导入
├── railway-scripts/                # Python 脚本 — 网格分割/爬虫/校验
└── railway-frontend/               # Vue 3 前端 (独立目录)
```

模块依赖链：`api → service → data → common`，`batch → service → data → common`

### 4.4 数据流（完整链路）

```
用户操作                                后端处理
─────────                              ──────────
1. 缩放/平移地图                       
   → MapLibre 请求矢量瓦片              
     → fetch('/api/tiles/railways/6/52/24.pbf')
                                        2. TileController 解析 z/x/y
                                        3. TileUtils.tileToBBox() 坐标转换
                                        4. MyBatis XML → PostGIS ST_AsMVT
                                        5. hex 解码 → PBF byte[]
                                        6. 返回 Content-Type: application/vnd.mapbox-vector-tile
                                            Cache-Control: public, max-age=3600
3. MapLibre WebGL 渲染矢量瓦片          
   → style expression 按 railway 类型着色  
```

---

## 5. 地图图例分类体系

> **依据**：用户提供的铁路专业分类标准。此分类体系同时作为数据库字段设计、前端样式映射、地图图例 UI 的统一数据源。

### 5.1 车站分类（12 类）

| 编码 | 分类名称 | 数据库值 | 前端渲染 | OSM 映射 |
|------|----------|----------|----------|----------|
| MAJOR_HUB | 重要枢纽（客/货） | `major_hub` | ★ 五角星, 红色, r=8 | `railway=station` + `station=hub` (人工标注) |
| MAJOR_PASSENGER | 主要车站（客/货） | `major_passenger` | ● 大圆, 红色, r=7 | `railway=station` + 城市主站 |
| MEDIUM_PASSENGER | 中等车站（客/货） | `medium_passenger` | ● 中圆, 橙色, r=5 | `railway=station` + 地级市站 |
| SMALL_PASSENGER | 小型车站（客/货） | `small_passenger` | ● 小圆, 橙色, r=4 | `railway=station` + 县级站 |
| SMALL_NON_PASSENGER | 小型车站（无旅客服务）| `small_non_passenger` | ● 小圆, 灰色, r=3 | `railway=station` + OSM 无客运标签 |
| LARGE_YARD | 大型编组站 | `large_yard` | ◇ 菱形, 蓝色, r=6 | `railway=yard` (人工标注) |
| MEDIUM_YARD | 中小编组站 | `medium_yard` | ◇ 菱形, 蓝色, r=4 | `railway=yard` |
| MAJOR_FREIGHT | 重要货运车站 | `major_freight` | ■ 方形, 棕色, r=6 | `railway=station` + `usage=freight` |
| SIGNAL_STATION | 线路所 / 信号站 | `signal_station` | △ 三角, 绿色, r=3 | `railway=signal_box` / `railway=halt` |
| OTHER_FACILITY | 其他铁路设施 | `other_facility` | ✕ 叉号, 灰色, r=3 | `railway=*` 其他值 |
| FREIGHT_YARD | 铁路货场 | `freight_yard` | ■ 方形, 棕色, r=4 | `railway=yard` + `usage=freight` |
| EMU_DEPOT | 动车整备场 | `emu_depot` | ▲ 三角, 紫色, r=4 | `railway=depot` (人工标注) |

### 5.2 铁路线分类（7 类）

| 编码 | 分类名称 | 数据库值 | 前端渲染 | OSM 映射 |
|------|----------|----------|----------|----------|
| DOUBLE_TRACK | 铁路（双线/单线）| `conventional` | 赤色 #e74c3c, w=2.5 | `railway=rail` |
| HIGH_SPEED | 高速铁路 | `high_speed` | 深红 #ff481a, w=3.0 | `railway=rail` + `highspeed=yes` 或 `usage=main` + 高速 |
| RAPID_TRANSIT | 快速铁路、城际铁路 | `rapid_transit` | 橙红 #ffa31a, w=2.5 | `railway=rail` + 城际标签 (人工标注) |
| PASSENGER_RAIL | 普通铁路（客运）| `passenger_rail` | 蓝色 #6ed568, w=2.0 | `railway=rail` + `usage=main` (客运为主) |
| FREIGHT_RAIL | 普通铁路（货运）| `freight_rail` | 棕色 #d3ff4f, w=2.0 | `railway=rail` + `usage=freight` |
| OTHER_RAIL | 其他（专用线、联络线）| `other_rail` | 灰色 #708bbb, w=1.5, 虚线 | `railway=rail` + `usage=industrial/military/tourism` |
| SUBWAY | 地铁 | `subway` | 浅蓝 #85C1E9, w=1.5 | `railway=subway` |

### 5.3 分类数据来源

原型 OSM 数据仅能区分 `railway=rail/subway/light_rail` 和 `usage=main/branch`。上述详细分类（如"高速铁路""快速铁路""编组站""动车整备场"）OSM 无法直接提供。**在 Phase 1 数据导入时**：

1. OSM 标签映射到基础分类（约 60% 自动化）
2. 无法自动分类的条目默认归入 `conventional` / `small_passenger`
3. 通过 [人工补录接口](#14-osm-数据人工补录方案) 逐条修正

### 5.4 图例 UI 组件

前端 `MapLegend.vue` 组件：
- 底部可折叠面板，列出所有分类及对应符号/颜色
- 每个分类带复选框，控制图层的显示/隐藏
- 按车站和铁路线分两组展示

---

## 6. 数据管线设计

### 6.1 数据源策略

| 数据 | 来源 | 更新频率 | 获取方式 |
|------|------|----------|----------|
| 铁路线路几何 | OpenStreetMap (Overpass API) | 每季度 | 网格分割 + 逐格抓取 |
| 车站位置 | OpenStreetMap (Overpass API) | 每季度 | 同上 |
| 列车时刻表 | liecheba.com | 每日 | Python 爬虫逐车次抓取 |
| 票价数据 | liecheba.com | 每日 | 爬虫同时抓取票价信息 |
| 中国陆地边界 | OSM 关系 270056 (China) | 一次性 | 用于网格过滤 |
| 底图瓦片 | MapTiler Streets | - | 免费额度 (200K reqs/month) |

### 6.2 网格分割策略

**代替原型的手动区域定义**，采用系统化的渔网 (Fishnet) 分割法：

```
算法: GridSplitter

输入:
  - 中国陆地边界多边形 (GeoJSON, WGS-84, 来自 OSM relation 270056)
  - 网格边长 d = 1.0° (约 110km)
  - 重叠宽度 overlap = 0.05° (约 5.5km)

输出:
  - 抓取队列文件 grid_queue.json
  - 每格 GeoJSON: grid_r{row}_c{col}.geojson
  - 跳过网格列表 skipped_grids.json

步骤:
  1. 计算中国陆地边界 bbox:
     lon: [73.5°, 135.14°], lat: [18.0°, 53.56°]
  2. 以 d 为步长生成 m × n 的网格矩阵
  3. 对每个网格:
     a. 扩展 overlap (四边各加 0.05°)
     b. 用 Shapely 判断扩展网格与中国边界是否相交
     c. 不相交 → 跳过 (海域/境外)
     d. 相交 → 加入队列
  4. 蛇形排序 (S-curve): 偶数行正向, 奇数行反向
  5. 按队列顺序执行 Overpass API 查询 (>5s 间隔, 5 次重试)
```

**预估网格数量**：中国陆地面积约 960 万 km²，1°×1° 网格覆盖约 12,000 km²/格，理论约 800 格。实际与边界相交的约 350-400 格（大部为海域/境外被过滤）。

**单格抓取耗时**：约 30-120 秒（取决于该格铁路密度），**全量抓取总耗时约 4-8 小时**（含重试与间隔）。

**Python 核心逻辑**：

```python
import shapely.geometry as geom
import json

def generate_grid(china_boundary: geom.Polygon, step: float = 1.0, overlap: float = 0.05):
    minx, miny, maxx, maxy = china_boundary.bounds
    queue = []
    skipped = []

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
            else:
                skipped.append(f"r{row}_c{col}")
            col += 1
            x += step
        row += 1
        y += step

    # 蛇形排序: 偶数行正向，奇数行反向
    queue.sort(key=lambda g: (g["row"], g["col"] if g["row"] % 2 == 0 else -g["col"]))

    with open("grid_queue.json", "w") as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)
    with open("skipped_grids.json", "w") as f:
        json.dump(skipped, f, ensure_ascii=False, indent=2)

    print(f"总网格: {len(queue)} 格待抓取, {len(skipped)} 格跳过")
    return queue
```

### 6.3 数据导入策略

**代替原型的单管道全量导入**，采用 Spring Batch 分批事务：

```
导入流程 (Spring Batch Job: gridImportJob):

[Step 1] 文件发现
  ─ 扫描 frontend/data/ 下所有 grid_r*_c*.geojson
  ─ 读取 grid_queue.json 对比，检测缺失网格
  ─ 生成待处理文件列表

[Step 2] 逐文件导入 (每文件一个事务)
  ─ GeoJsonItemReader: 每次读取 1000 个 feature (避免 155MB 全量加载)
  ─ RailwaySegmentProcessor: 清洗名称、验证坐标、WKT 转换、分类映射
  ─ JdbcBatchItemWriter: 每 1000 条提交一次
  ─ 每 10 批次打印进度日志

[Step 3] 去重与拓扑构建
  ─ 合并不同网格间的重复线路 (按 osm_id + 端点匹配)
  ─ 构建 railway_topology 连接表
  ─ REINDEX + ANALYZE

[Step 4] 完整性校验
  ─ SELECT count(*) vs 网格抓取日志
  ─ 随机抽样 100 条 ST_IsValid 检查
  ─ 缺失网格告警输出到 import_errors.log
```

**日志规范**：

```
[2026-04-29 12:00:01] [IMPORT] ========== 开始导入 ==========
[2026-04-29 12:00:01] [IMPORT] 待处理网格: 358 个, 总文件大小: 187 MB
[2026-04-29 12:00:05] [IMPORT] [1/358] grid_r0_c2.geojson (1.2MB): 1000/3240 (30%)
[2026-04-29 12:00:08] [IMPORT] [1/358] grid_r0_c2.geojson: 2000/3240 (61%)
[2026-04-29 12:00:11] [IMPORT] [1/358] grid_r0_c2.geojson: 3240/3240 (100%) ✓ 铁路线3240 车站12
[2026-04-29 12:00:13] [IMPORT] [2/358] grid_r0_c4.geojson (2.1MB): 1000/5800 (17%)
...
[2026-04-29 13:45:30] [IMPORT] ========== 导入完成 ==========
[2026-04-29 13:45:30] [IMPORT] 成功: 356 格, 失败: 2 格 → 见 import_errors.log
[2026-04-29 13:45:30] [IMPORT] 铁路线: 452103 条, 车站: 4128 个, 总耗时 10529s
[2026-04-29 13:45:31] [IMPORT] 失败网格: grid_r8_c12 (超时), grid_r15_c3 (解析错误)
```

### 6.4 时刻表与票价采集

**数据来源**：`liecheba.com/{车次}.html`（服务端渲染 HTML，无需 API Key）

**爬取策略**：
1. 从已爬取的车次索引页获取全国车次列表
2. 逐车次爬取途经站 + 时刻表 + 票价信息
3. 请求间隔 ≥ 1.5 秒（避免限流）
4. 每日增量更新（检查 `updated_at`，仅爬取已过期的车次）

**票价解析**：从 liecheba.com 页面提取各席别价格

| 席别 | 数据库字段 | 说明 |
|------|-----------|------|
| 商务座 / 特等座 | `price_business` | G/D 字头 |
| 一等座 | `price_first` | G/D/C 字头 |
| 二等座 | `price_second` | G/D/C 字头 |
| 软卧上/下 | `price_soft_sleeper_up/down` | Z/T/K 字头 |
| 硬卧上/中/下 | `price_hard_sleeper_up/mid/down` | Z/T/K 字头 |
| 硬座 | `price_hard_seat` | K/普快 |
| 无座 | `price_no_seat` | 所有车次 |

---

## 7. 数据库设计

### 7.1 空间数据表

```sql
-- ============================================================
-- 铁路线段表
-- ============================================================
CREATE TABLE railway_segments (
    id            BIGSERIAL PRIMARY KEY,
    osm_id        BIGINT,
    name          VARCHAR(300),                    -- 线路名称 (如 "京沪线")
    railway       VARCHAR(30)  NOT NULL,           -- rail / subway / light_rail
    usage         VARCHAR(30),                     -- main / branch / industrial / military / tourism
    category      VARCHAR(30)  NOT NULL DEFAULT 'conventional',
        -- 地图分类编码: conventional / high_speed / rapid_transit /
        --               passenger_rail / freight_rail / other_rail / subway
    electrified   VARCHAR(20),                     -- yes / no / contact_line
    gauge         INTEGER DEFAULT 1435,            -- 轨距 (mm)
    max_speed     INTEGER,                         -- 设计最高时速 (km/h)
    track_count   INTEGER DEFAULT 1,               -- 轨道数 (1=单线, 2=双线, 4=四线)
    geom          GEOMETRY(LINESTRING, 4326) NOT NULL,
    length_km     DOUBLE PRECISION,
    source_grid   VARCHAR(20),                     -- 来源网格 ID (如 r8_c12)
    data_quality  VARCHAR(20) DEFAULT 'osm',       -- osm / manual / verified
    created_at    TIMESTAMP DEFAULT NOW(),
    updated_at    TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_rail_seg_geom ON railway_segments USING GIST(geom);
CREATE INDEX idx_rail_seg_category ON railway_segments(category);
CREATE INDEX idx_rail_seg_railway ON railway_segments(railway);
CREATE INDEX idx_rail_seg_name ON railway_segments(name);

-- ============================================================
-- 车站表
-- ============================================================
CREATE TABLE stations (
    id            BIGSERIAL PRIMARY KEY,
    osm_id        BIGINT,
    name          VARCHAR(200) NOT NULL,            -- 站名全称 (如 "北京南")
    name_pinyin   VARCHAR(300),                     -- 拼音 (如 "beijingnan")
    city          VARCHAR(100),                     -- 所属城市 (如 "北京市")
    province      VARCHAR(100),                     -- 所属省份
    railway       VARCHAR(30),                      -- station / halt / tram_stop
    category      VARCHAR(30)  NOT NULL DEFAULT 'small_passenger',
        -- 地图分类编码: major_hub / major_passenger / medium_passenger /
        --               small_passenger / small_non_passenger / large_yard /
        --               medium_yard / major_freight / signal_station /
        --               other_facility / freight_yard / emu_depot
    passenger     BOOLEAN DEFAULT TRUE,             -- 是否办理客运
    freight       BOOLEAN DEFAULT FALSE,            -- 是否办理货运
    is_hub        BOOLEAN DEFAULT FALSE,            -- 是否枢纽站
    geom          GEOMETRY(POINT, 4326) NOT NULL,
    source_grid   VARCHAR(20),
    data_quality  VARCHAR(20) DEFAULT 'osm',        -- osm / manual / verified
    created_at    TIMESTAMP DEFAULT NOW(),
    updated_at    TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_stat_geom ON stations USING GIST(geom);
CREATE INDEX idx_stat_name ON stations(name);
CREATE INDEX idx_stat_pinyin ON stations(name_pinyin);
CREATE INDEX idx_stat_city ON stations(city);
CREATE INDEX idx_stat_category ON stations(category);

-- ============================================================
-- 铁路拓扑连接表 (预计算)
-- ============================================================
CREATE TABLE railway_topology (
    id            BIGSERIAL PRIMARY KEY,
    seg_a         BIGINT REFERENCES railway_segments(id),
    seg_b         BIGINT REFERENCES railway_segments(id),
    is_connected  BOOLEAN DEFAULT FALSE,             -- 是否直接相交
    gap_meters    DOUBLE PRECISION,                  -- 间距 (米)
    UNIQUE(seg_a, seg_b)
);

CREATE INDEX idx_rt_seg_a ON railway_topology(seg_a);
CREATE INDEX idx_rt_seg_b ON railway_topology(seg_b);
```

### 7.2 时刻表与票价表

```sql
-- ============================================================
-- 车次主表
-- ============================================================
CREATE TABLE train_routes (
    id              BIGSERIAL PRIMARY KEY,
    train_no        VARCHAR(20)  NOT NULL UNIQUE,     -- 如 "G1", "D301"
    train_type      VARCHAR(10),                      -- G/D/C/Z/T/K/Y/S
    depart_station  VARCHAR(200),                     -- 始发站名
    arrive_station  VARCHAR(200),                     -- 终到站名
    depart_time     TIME,                             -- 始发时间
    arrive_time     TIME,                             -- 终到时间
    duration_min    INTEGER,                          -- 全程耗时 (分钟)
    distance_km     DOUBLE PRECISION,                 -- 全程里程
    running_days    INTEGER DEFAULT 127,              -- 开行日期 (bitmask)
    is_valid        BOOLEAN DEFAULT TRUE,             -- 当前是否有效
    data_updated_at TIMESTAMP,                        -- 数据更新时间
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tr_no ON train_routes(train_no);
CREATE INDEX idx_tr_type ON train_routes(train_type);
CREATE INDEX idx_tr_valid ON train_routes(is_valid);

-- ============================================================
-- 车次途经站序表 (代替原型的 JSONB)
-- ============================================================
CREATE TABLE train_stops (
    id            BIGSERIAL PRIMARY KEY,
    train_no      VARCHAR(20) NOT NULL
                      REFERENCES train_routes(train_no) ON DELETE CASCADE,
    seq           INTEGER NOT NULL,                   -- 站序 (1, 2, 3...)
    station_name  VARCHAR(200) NOT NULL,              -- 站名
    station_id    BIGINT REFERENCES stations(id),     -- 关联车站空间数据
    arrive_time   TIME,                               -- 到站时间
    depart_time   TIME,                               -- 发车时间
    stay_min      INTEGER,                            -- 停站时间 (分钟)
    distance_km   DOUBLE PRECISION,                   -- 距始发站里程
    is_terminal   BOOLEAN DEFAULT FALSE               -- 是否为终点站
);

CREATE INDEX idx_ts_train_no ON train_stops(train_no);
CREATE INDEX idx_ts_station_id ON train_stops(station_id);
CREATE INDEX idx_ts_station_name ON train_stops(station_name);

-- ============================================================
-- 车次票价表
-- ============================================================
CREATE TABLE train_fares (
    id                  BIGSERIAL PRIMARY KEY,
    train_no            VARCHAR(20) NOT NULL
                            REFERENCES train_routes(train_no) ON DELETE CASCADE,
    from_station        VARCHAR(200) NOT NULL,        -- 出发站名
    to_station          VARCHAR(200) NOT NULL,        -- 到达站名
    price_business      DECIMAL(8,2),                 -- 商务座/特等座
    price_first         DECIMAL(8,2),                 -- 一等座
    price_second        DECIMAL(8,2),                 -- 二等座
    price_soft_sleeper_up   DECIMAL(8,2),             -- 软卧上铺
    price_soft_sleeper_down DECIMAL(8,2),             -- 软卧下铺
    price_hard_sleeper_up   DECIMAL(8,2),             -- 硬卧上铺
    price_hard_sleeper_mid  DECIMAL(8,2),             -- 硬卧中铺
    price_hard_sleeper_down DECIMAL(8,2),             -- 硬卧下铺
    price_hard_seat     DECIMAL(8,2),                 -- 硬座
    price_no_seat       DECIMAL(8,2),                 -- 无座
    data_updated_at     TIMESTAMP,                    -- 票价数据更新时间
    UNIQUE(train_no, from_station, to_station)
);

CREATE INDEX idx_tf_train_no ON train_fares(train_no);

-- ============================================================
-- 车次与线路段映射表 (预计算, 解决问题四)
-- ============================================================
CREATE TABLE train_segment_mapping (
    id            BIGSERIAL PRIMARY KEY,
    train_no      VARCHAR(20) NOT NULL,
    from_station  VARCHAR(200) NOT NULL,              -- 出发站名
    to_station    VARCHAR(200) NOT NULL,              -- 到达站名
    seg_id        BIGINT REFERENCES railway_segments(id),
    seg_order     INTEGER,                            -- 在路段中的顺序
    confidence    DOUBLE PRECISION DEFAULT 1.0,       -- 匹配置信度 (0-1)
    match_method  VARCHAR(20) DEFAULT 'topology',     -- topology / distance / manual
    UNIQUE(train_no, from_station, to_station, seg_id)
);

CREATE INDEX idx_tsm_train ON train_segment_mapping(train_no);
CREATE INDEX idx_tsm_seg ON train_segment_mapping(seg_id);
```

### 7.3 用户相关表（Phase 7 启用, Phase 0 仅建表）

```sql
-- 用户表（Phase 0 预留，Phase 7 启用）
CREATE TABLE users (
    id            BIGSERIAL PRIMARY KEY,
    username      VARCHAR(50)  NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email         VARCHAR(100),
    role          VARCHAR(20) DEFAULT 'USER',         -- USER / ADMIN
    created_at    TIMESTAMP DEFAULT NOW(),
    updated_at    TIMESTAMP DEFAULT NOW()
);

-- 用户收藏（Phase 7 启用）
CREATE TABLE user_favorites (
    id            BIGSERIAL PRIMARY KEY,
    user_id       BIGINT REFERENCES users(id) ON DELETE CASCADE,
    type          VARCHAR(20) NOT NULL,               -- station / train / transfer_route
    target_id     VARCHAR(200) NOT NULL,              -- 收藏目标的标识
    label         VARCHAR(200),                       -- 用户自定义标签
    data          JSONB,                              -- 收藏时的快照数据
    created_at    TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, type, target_id)
);

-- 搜索历史（Phase 7 启用）
CREATE TABLE user_search_history (
    id            BIGSERIAL PRIMARY KEY,
    user_id       BIGINT REFERENCES users(id) ON DELETE CASCADE,
    search_type   VARCHAR(20) NOT NULL,               -- station / train / transfer
    query_text    VARCHAR(500) NOT NULL,
    created_at    TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_ush_user ON user_search_history(user_id, created_at DESC);
```

### 7.4 表汇总

| 表名 | Phase | 用途 |
|------|:---:|------|
| `railway_segments` | 1 | 铁路线段几何 + 分类 |
| `stations` | 1 | 车站位置 + 分类 |
| `railway_topology` | 1 | 线段拓扑连接关系 |
| `train_routes` | 1 | 车次基本信息 |
| `train_stops` | 1 | 车次途经站序 |
| `train_fares` | 1 | 车次票价 |
| `train_segment_mapping` | 4 | 车次→线段匹配（预计算） |
| `users` | 0 (预留) | 用户账户 |
| `user_favorites` | 7 | 用户收藏 |
| `user_search_history` | 7 | 搜索历史 |

---

## 8. 后端模块设计

### 8.1 Maven 模块依赖图

```
railway-api (Spring Boot 启动)
  ├── railway-service (业务逻辑)
  │     ├── railway-data (MyBatis Mapper)
  │     │     └── railway-common (实体/DTO/枚举/工具)
  │     └── railway-common
  └── railway-batch (Spring Batch, 可选启动)
        ├── railway-service
        └── railway-data
```

### 8.2 railway-common

```
entity/
  RailwaySegment.java         (Lombok @Data, 对应 railway_segments)
  Station.java                (Lombok @Data, 对应 stations)
  TrainRoute.java             (对应 train_routes)
  TrainStop.java              (对应 train_stops)
  TrainFare.java              (对应 train_fares)
  TrainSegmentMapping.java    (对应 train_segment_mapping)
  User.java                   (对应 users, Phase 7)
dto/
  StationSearchRequest.java   (q, city, limit)
  StationSearchResult.java    (id, name, city, lon, lat, category)
  TrainSearchRequest.java     (q, type, limit)
  TrainSearchResult.java      (train_no, type, depart/arrive, duration)
  TrainRouteDetail.java       (train_no, stops[], segments GeoJSON, fares)
  TransferRequest.java        (from, to, date, max_transfers, preference)
  TransferResult.java         (segments[], total_time, total_price, score)
enums/
  RailwayCategory.java        (conventional/high_speed/rapid_transit/...)
  StationCategory.java        (major_hub/major_passenger/.../emu_depot)
  TrainType.java              (G/D/C/Z/T/K/Y/S)
  TransferPreference.java     (LEAST_TIME/LEAST_TRANSFER/NIGHT_TRAIN/LEAST_PRICE)
util/
  TileUtils.java              (z/x/y ↔ bbox 转换)
  GeoUtils.java               (WGS-84 ↔ GCJ-02, 距离, ST_Simplify 参数)
  PinyinUtils.java            (中文 → 拼音/首字母, 基于 pinyin4j 或 tinypinyin)
config/
  SpatialConfig.java          (JTS GeometryFactory Bean 配置)
```

### 8.3 railway-data

```
mapper/
  RailwaySegmentMapper.java   (BaseMapper + getVectorTile + findByBBox + search)
  StationMapper.java          (BaseMapper + getVectorTile + search + findByCity)
  TrainRouteMapper.java       (BaseMapper + search + findByStation)
  TrainStopMapper.java        (BaseMapper + findByTrainNo)
  TrainFareMapper.java        (BaseMapper)
  TrainSegmentMappingMapper.java (BaseMapper + findByTrainNo)
resources/mapper/
  RailwaySegmentMapper.xml    (ST_AsMVT 瓦片 + 空间查询)
  StationMapper.xml           (ST_AsMVT + ILIKE + 拼音搜索)
  TrainRouteMapper.xml        (车次搜索 + 前缀匹配)
  TrainStopMapper.xml         (途经站查询)
```

### 8.4 railway-service

```
map/
  TileService.java            (瓦片: z/x/y → PBF byte[], hex解码)
search/
  StationSearchService.java   (车站搜索: 中文/拼音/首字母/城市)
  TrainSearchService.java     (车次搜索: 前缀/始发终到站)
route/
  RouteMatchingService.java   ([核心] 车次经行段匹配引擎 — 三阶段算法)
  RouteGeoJsonService.java    (匹配结果 → GeoJSON FeatureCollection)
transfer/
  TransferGraphBuilder.java   (铁路时间依赖图构建)
  TransferSearchService.java  ([核心] 多次中转换乘 — KSP 算法)
  TransferRankingService.java (多目标方案排序)
sync/
  DataSyncService.java        (数据同步调度触发)
```

### 8.5 railway-api

```
controller/
  TileController.java         (GET /api/tiles/{layer}/{z}/{x}/{y}.pbf)
  StationController.java      (GET /api/stations/search)
  TrainController.java        (GET /api/trains/search, GET /api/trains/{no}/route)
  TransferController.java     (POST /api/transfer/search)
  SyncController.java         (POST /api/sync/trigger)
  HealthController.java       (GET /api/health)
config/
  CorsConfig.java             (CORS 配置)
  WebMvcConfig.java           (拦截器/静态资源配置)
  JacksonConfig.java          (GeoJSON/Long 精度序列化)
```

### 8.6 railway-batch

```
job/
  GridImportJob.java          (网格数据导入 Job — Step 1-3)
  ScheduleImportJob.java      (时刻表 + 票价导入 Job)
reader/
  GeoJsonItemReader.java      (分块读取 GeoJSON features)
  GridQueueReader.java        (读取 grid_queue.json)
processor/
  RailwaySegmentProcessor.java   (数据清洗 + 分类映射)
  StationProcessor.java          (车站数据清洗 + 分类映射)
  TrainScheduleProcessor.java    (时刻表 HTML 解析 → train_stops)
  TrainFareProcessor.java        (票价 HTML 解析 → train_fares)
writer/
  PostgisBatchItemWriter.java (PostGIS 批量写入 + 事务管理)
listener/
  ImportProgressListener.java (进度日志 + 失败记录 + 通知)
```

---

## 9. 前端模块设计

### 9.1 底图方案

| 方案 | 状态 |
|------|------|
| **MapTiler Streets** | **优先验证** — 注册免费账号，测试国内各城市加载速度 |
| 天地图 | 备选 — 如果 MapTiler 国内加载慢，退回到天地图 + GCJ-02 转换 |

**坐标系策略**：数据库存储 WGS-84。如果选用天地图底图，MapLibre 前端通过 `transformRequest` 钩子做 GCJ-02 转换。

### 9.2 前端目录结构

```
railway-frontend/
├── src/
│   ├── components/
│   │   ├── map/
│   │   │   ├── MapContainer.vue        # 地图容器 (核心组件)
│   │   │   ├── RailwayLayer.vue        # 铁路线图层
│   │   │   ├── StationLayer.vue        # 车站图层
│   │   │   ├── TrainRouteLayer.vue     # 车次高亮图层
│   │   │   ├── MapLegend.vue           # 图例面板 (折叠/展开/筛选)
│   │   │   └── MapControls.vue         # 地图控件
│   │   ├── search/
│   │   │   ├── SearchPanel.vue         # 搜索面板 (Tab 切换)
│   │   │   ├── StationSearch.vue       # 车站搜索 (自动完成)
│   │   │   ├── TrainSearch.vue         # 车次搜索 (自动完成)
│   │   │   └── SearchSuggestions.vue   # 联想下拉
│   │   ├── route/
│   │   │   ├── RouteTimeline.vue       # 车次途经站时间线
│   │   │   └── RouteInfoCard.vue       # 车次信息 + 票价卡片
│   │   ├── transfer/
│   │   │   ├── TransferSearchForm.vue   # 换乘搜索表单
│   │   │   ├── TransferResultList.vue   # 换乘方案列表
│   │   │   └── TransferTimeline.vue     # 多段车程时间线
│   │   └── common/
│   │       ├── AppHeader.vue            # 顶部导航
│   │       └── LoadingSpinner.vue       # 加载指示器
│   ├── views/
│   │   ├── MapView.vue                  # 主地图页
│   │   └── TransferView.vue             # 换乘查询页
│   ├── stores/
│   │   ├── mapStore.ts                  # 地图状态
│   │   └── searchStore.ts              # 搜索/车次状态
│   ├── services/
│   │   ├── api.ts                       # axios 实例 + base URL + 错误处理
│   │   ├── stationService.ts           # 车站 API
│   │   ├── trainService.ts             # 车次 API
│   │   └── transferService.ts          # 换乘 API
│   ├── types/
│   │   ├── station.ts
│   │   ├── train.ts
│   │   ├── map.ts
│   │   └── transfer.ts
│   ├── utils/
│   │   ├── geo.ts                      # 坐标转换 (WGS-84 ↔ GCJ-02)
│   │   └── debounce.ts                # 防抖/节流
│   ├── assets/styles/
│   │   ├── main.css                    # Tailwind + 全局
│   │   └── map.css                     # 地图覆盖样式
│   ├── router/index.ts                 # Vue Router
│   ├── App.vue
│   └── main.ts
├── public/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

### 9.3 地图组件核心逻辑

```typescript
// MapContainer.vue 核心流程

import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

const map = new maplibregl.Map({
  container: 'map',
  style: 'https://api.maptiler.com/maps/streets-v2/style.json?key=YOUR_KEY',
  center: [108.5, 35.5],
  zoom: 5,
  minZoom: 4,
  maxZoom: 18
});

map.on('load', () => {
  // 铁路线矢量瓦片源
  map.addSource('railways', {
    type: 'vector',
    tiles: ['/api/tiles/railways/{z}/{x}/{y}.pbf'],
    minzoom: 6, maxzoom: 18
  });

  // 铁路线图层 — 按 category 字段着色
  map.addLayer({
    id: 'railways-layer',
    type: 'line',
    source: 'railways',
    'source-layer': 'railways',
    paint: {
      'line-color': [
        'match', ['get', 'category'],
        'conventional',    '#e74c3c',
        'high_speed',      '#c0392b',
        'rapid_transit',   '#e67e22',
        'passenger_rail',  '#3498db',
        'freight_rail',    '#8B4513',
        'other_rail',      '#95a5a6',
        'subway',          '#85C1E9',
        '#e74c3c'  // default
      ],
      'line-width': ['interpolate', ['linear'], ['zoom'],
        6, 1.0, 10, 2.0, 14, 3.5],
      'line-opacity': 0.85
    }
  });

  // 车站图层 — 按 category 字段改变符号
  map.addSource('stations', {
    type: 'vector',
    tiles: ['/api/tiles/stations/{z}/{x}/{y}.pbf'],
    minzoom: 8, maxzoom: 18
  });

  map.addLayer({
    id: 'stations-layer',
    type: 'circle',
    source: 'stations',
    'source-layer': 'stations',
    paint: {
      'circle-color': [
        'match', ['get', 'category'],
        'major_hub',      '#e74c3c',
        'major_passenger', '#e74c3c',
        'medium_passenger','#f39c12',
        'small_passenger', '#f39c12',
        'large_yard',     '#3498db',
        'medium_yard',    '#3498db',
        'major_freight',  '#8B4513',
        'signal_station', '#27ae60',
        '#95a5a6'  // default
      ],
      'circle-radius': ['interpolate', ['linear'], ['zoom'],
        8, 2, 12, 5, 16, 8]
    }
  });
});
```

---

## 10. 搜索系统设计

### 10.1 车站搜索

| 输入类型 | 示例 | 预期结果 |
|----------|------|----------|
| 中文全称 | "北京南" | 精确匹配 → 北京南 |
| 中文简称 | "北京" | 前缀匹配 → 北京 / 北京南 / 北京西 / 北京北 / 北京丰台 |
| 拼音全拼 | "beijingnan" | 拼音匹配 → 北京南 |
| 拼音首字母 | "bjn" | 首字母匹配 → 北京南 / 北京西 / 北京北 |
| 城市名 | "南京" | 返回南京市所有车站，按等级排序 |

**规则**：

- **不要**自动在用户输入后追加"站"字做后缀匹配（避免"北京"匹配到"北京东站"以外的无关项）
- 城市搜索时返回该城市所有车站，按 `category` 排序

**SQL**：

```sql
SELECT id, name, city, province, category,
       ST_X(geom) AS lon, ST_Y(geom) AS lat
FROM stations
WHERE
    name ILIKE '%' || #{keyword} || '%'
    OR name_pinyin ILIKE '%' || #{keyword} || '%'
    OR REPLACE(name_pinyin, ' ', '') LIKE REPLACE(#{keyword}, ' ', '') || '%'
    OR city = #{keyword}
ORDER BY
    CASE WHEN name = #{keyword} THEN 0
         WHEN name ILIKE #{keyword} || '%' THEN 1
         WHEN city = #{keyword} THEN 2
         ELSE 3
    END,
    CASE category
        WHEN 'major_hub' THEN 0
        WHEN 'major_passenger' THEN 1
        WHEN 'medium_passenger' THEN 2
        ELSE 3
    END
LIMIT #{limit}
```

### 10.2 车次搜索

| 输入 | 预期结果 |
|------|----------|
| "G" | G1, G2, G3...（前缀匹配，按车次号数字排序） |
| "G1" | G1, G10, G100-G199, G1000+ |
| "北京" | 所有始发站或终到站含"北京"的车次 |

```sql
SELECT train_no, train_type, depart_station, arrive_station,
       depart_time, arrive_time, duration_min
FROM train_routes
WHERE
    is_valid = TRUE
    AND (
        train_no ILIKE #{keyword} || '%'
        OR depart_station ILIKE '%' || #{keyword} || '%'
        OR arrive_station ILIKE '%' || #{keyword} || '%'
    )
ORDER BY
    CASE WHEN train_no ILIKE #{keyword} || '%' THEN 0 ELSE 1 END,
    train_no
LIMIT #{limit}
```

### 10.3 前端的 Input 搜索处理示例

```typescript
// StationSearch.vue
// 用户输入 "G1" 时，不将 G1 当作车站搜索词去匹配车站
// 用户输入城市名时，返回该城市所有车站并标注等级

function handleSearch(query: string) {
  if (/^[GCDZTKYSgcdztkys]\d*$/.test(query.trim())) {
    // 是车次格式，提示用户切换到"车次"Tab
    message.info('检测到车次格式，请切换到"车次"搜索')
    return
  }
  // 正常车站搜索
  stationService.search(query)
}
```

---

## 11. 车次路线匹配算法

> 解决问题四：车次 A→B→C→D 的中间线路段精确匹配

### 11.1 问题回顾

原型用 `ST_DWithin(geom, line, 10000m)` 直接匹配，导致：
1. 阈值过大，匹配到不相关的平行/相交线路
2. 不考虑拓扑连通性，匹配结果可能不构成连续路径
3. 数据缺失时高亮断续

### 11.2 三阶段匹配

#### 阶段一：拓扑预计算（离线, Phase 1 导入后执行）

```sql
-- 对所有相邻/相交的铁路线段建立拓扑关系
INSERT INTO railway_topology (seg_a, seg_b, is_connected, gap_meters)
SELECT
    a.id, b.id,
    ST_Intersects(a.geom, b.geom) AS is_connected,
    COALESCE(ST_Distance(a.geom::geography, b.geom::geography), 0) AS gap_meters
FROM railway_segments a
CROSS JOIN railway_segments b
WHERE a.id < b.id
  AND (
    ST_Intersects(a.geom, b.geom)            -- 端点/线相交
    OR ST_DWithin(a.geom::geography, b.geom::geography, 50)  -- 50m 内
  );
```

#### 阶段二：候选筛选（在线, 用户查询时）

```
对相邻车站 (A, B):
  Step 1: 从 stations 表获取 A 的坐标 (lon_a, lat_a)
  Step 2: 找 A 站 2km 内的所有线段 → a_candidates (通常 1-5 条)
  Step 3: 找 B 站 2km 内的所有线段 → b_candidates
  Step 4: 从 a_candidates 出发，BFS 沿 railway_topology 搜索
  Step 5: 找到 b_candidates 中的线段 → 回溯路径
  Step 6: 如果 BFS 未找到 → 降级为 ST_DWithin 500m 纯距离匹配 (confidence=0.5)
```

#### 阶段三：预计算缓存（离线, Phase 4 执行）

```java
// RouteMatchingService.java
public void precomputeAllMappings() {
    List<TrainRoute> routes = trainRouteMapper.selectAllValid();
    int total = routes.size();
    int done = 0;

    for (TrainRoute route : routes) {
        List<TrainStop> stops = trainStopMapper.findByTrainNo(route.getTrainNo());
        for (int i = 0; i < stops.size() - 1; i++) {
            TrainStop from = stops.get(i);
            TrainStop to = stops.get(i + 1);

            // 查找或计算 from→to 的匹配线段
            List<TrainSegmentMapping> existing =
                mappingMapper.findByTrainAndStops(route.getTrainNo(), from.getName(), to.getName());

            if (existing.isEmpty()) {
                List<TrainSegmentMapping> result = matchSegments(from, to);
                mappingMapper.batchInsert(result);
            }
        }
        done++;
        if (done % 100 == 0) {
            log.info("[PRECOMPUTE] {}/{} 车次完成", done, total);
        }
    }
    log.info("[PRECOMPUTE] 全部完成: {} 车次", total);
}
```

预估：10,000 车次 × 平均 15 站 ≈ 150,000 对相邻站，每对 BFS 约 50ms → **总计约 2 小时**。

### 11.3 对数据缺失的处理

- `confidence < 0.8` 的线段在前端以**虚线**渲染
- 完全无法匹配的站间（`confidence = 0`）用红色虚线直线连接两站，表示"无数据"
- `match_method` 字段记录匹配方式，人工可逐条修正后设为 `manual`

---

## 12. 多次中转换乘规划

### 12.1 图模型

```
节点: 车站 + 时间点 (到达时刻 / 发车时刻)
边:
  - 运行边: (站A, 发车t1) → (站B, 到站t2), 权重 = t2 - t1
  - 等待边: (站A, 到站t1) → (站A, 发车t2), 权重 = t2 - t1 (换乘等待)
```

### 12.2 算法

**优先方案**：KSP (K-Shortest Paths)，基于 JGraphT 库的 `KShortestPaths`。

```java
// TransferSearchService.java
public List<TransferResult> search(TransferRequest req) {
    // 1. 构建时间依赖图
    Graph<String, DefaultWeightedEdge> graph = buildTimeDependentGraph(req.getDate());

    // 2. K 优路径搜索
    KShortestPaths<String, DefaultWeightedEdge> ksp =
        new KShortestPaths<>(graph, req.getMaxResults());
    List<GraphPath<String, DefaultWeightedEdge>> paths =
        ksp.getPaths(req.getFrom(), req.getTo());

    // 3. 约束过滤
    List<TransferResult> results = paths.stream()
        .filter(p -> getTransferCount(p) <= req.getMaxTransfers())
        .filter(p -> getMaxSegmentDuration(p) <= 12 * 60) // 单段 ≤12h
        .filter(p -> getTotalDuration(p) <= 72 * 60)      // 总 ≤72h
        .map(p -> toResult(p, req.getPreference()))
        .collect(Collectors.toList());

    // 4. 偏好排序
    return rankingService.rank(results, req.getPreference());
}
```

### 12.3 评分函数

```
Score(方案) = w1 × 总耗时_normalized + w2 × 换乘次数 - w3 × 中转可行性

权重按用户偏好调整:
  LEAST_TIME:      w1=1.0, w2=0.2, w3=0
  LEAST_TRANSFER:  w1=0.5, w2=1.0, w3=0
  NIGHT_TRAIN:     w1=0.6, w2=0.3, w3=0.5  (夜间乘车加分)
  LEAST_PRICE:     Price 替代 Time 作为主因子
```

### 12.4 API 设计

```
POST /api/transfer/search
Request:
{
  "from": "北京南",
  "to": "昆明",
  "date": "2026-05-01",
  "max_transfers": 2,
  "preference": "least_time",
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
          "train_type": "D",
          "from_station": "北京南",
          "to_station": "武汉",
          "depart_time": "19:30",
          "arrive_time": "06:45",
          "duration_min": 675,
          "price": { "second": 315.0, "soft_sleeper_down": 580.0 }
        },
        // ... 更多段
      ]
    }
  ],
  "total_found": 23,
  "search_time_ms": 450
}
```

---

## 13. Docker 部署配置

### 13.1 docker-compose.yml

```yaml
services:
  db:
    image: postgis/postgis:17-3.5
    environment:
      POSTGRES_DB: railwaymap
      POSTGRES_USER: railway
      POSTGRES_PASSWORD: railway123
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./spring-backend/src/main/resources/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U railway -d railwaymap"]
      interval: 5s
      timeout: 3s
      retries: 10
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redisdata:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      retries: 5
    restart: unless-stopped

  app:
    build:
      context: ./spring-backend
      dockerfile: Dockerfile
    ports:
      - "10010:8080"
    environment:
      SPRING_DATASOURCE_URL: jdbc:postgresql://db:5432/railwaymap
      SPRING_DATASOURCE_USERNAME: railway
      SPRING_DATASOURCE_PASSWORD: railway123
      SPRING_REDIS_HOST: redis
      SPRING_REDIS_PORT: 6379
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  frontend:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./railway-frontend/dist:/usr/share/nginx/html:ro
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - app
    restart: unless-stopped

volumes:
  pgdata:
  redisdata:
```

### 13.2 Spring Boot Dockerfile（多阶段构建）

```dockerfile
# ===== 构建阶段 =====
FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /build

# 分层缓存依赖
COPY pom.xml .
COPY railway-common/pom.xml railway-common/
COPY railway-data/pom.xml    railway-data/
COPY railway-service/pom.xml railway-service/
COPY railway-api/pom.xml     railway-api/
COPY railway-batch/pom.xml   railway-batch/

RUN mvn dependency:go-offline -B -q

# 编译
COPY . .
RUN mvn package -pl railway-api -am -DskipTests -B -q

# ===== 运行阶段 =====
FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /build/railway-api/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```

### 13.3 Nginx 配置

```nginx
server {
    listen 80;
    server_name localhost;

    # Vue 前端静态文件
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # API 反向代理
    location /api/ {
        proxy_pass http://app:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 13.4 完整部署命令

```bash
# 开发环境 (Linux VM)
docker compose up -d                    # 启动所有服务
docker compose logs -f app              # 查看 Spring Boot 日志
docker compose exec db psql -U railway -d railwaymap  # 进入数据库

# 导入数据
docker compose exec app java -jar app.jar --batch.import.enabled=true

# 访问
# 前端: http://localhost
# API:  http://localhost/api/health
```

---

## 14. OSM 数据人工补录方案

### 14.1 补录触发场景

- 某铁路段在 OSM 中完全缺失 → 前端显示数据缺失提示
- 某车站分类错误（如"主要车站"被标记为"小型车站"）
- 新增线路（如刚开通的高铁线）OSM 尚未更新
- 车站缺少 `city` / `province` / `name_pinyin` 等信息

### 14.2 补录接口设计

```
POST /api/admin/segments/{id}
  → 修改 railway_segments 的 category、name、max_speed、electrified 等字段
  → 设置 data_quality = 'manual'

POST /api/admin/stations/{id}
  → 修改 stations 的 category、city、province、passenger、freight 等字段
  → 设置 data_quality = 'manual'

POST /api/admin/segments
  → 手动新增铁路线段 (GeoJSON)

POST /api/admin/train-segment-mapping
  → 手动修正车次→线段匹配
```

### 14.3 操作方式

**Phase 1-7 开发阶段**：直接通过数据库管理工具（DBeaver/pgAdmin）或 SQL 脚本修改，按 `id` 定位记录：

```sql
-- 示例：将北京南站分类改为 "主要车站 (客运)"
UPDATE stations SET category = 'major_passenger', data_quality = 'manual'
WHERE id = 1234;

-- 示例：将京沪高铁某一段标记为 "高速铁路"
UPDATE railway_segments SET category = 'high_speed', max_speed = 350, data_quality = 'manual'
WHERE id = 5678;
```

**远期**：在管理后台做一个简单的 Web 编辑器界面——点击地图上的线段/车站 → 弹窗修改属性 → 保存。此功能不在 Phase 0-7 范围内。

---

## 15. 分阶段实施路线

### Phase 0: 项目初始化 (预计 2 天)

```
□ 创建 Maven 多模块项目骨架
      父 POM: Spring Boot 3.5.14, Java 21
      子模块: common, data, service, api, batch
□ 创建 Vue 3 + Vite + TypeScript + Tailwind + Naive UI 前端项目
□ docker-compose.yml (PostgreSQL 17 + PostGIS 3.5 + Redis 7 + Nginx)
□ Spring Boot Dockerfile (多阶段构建)
□ Nginx 配置
□ application.yml (datasource, mybatis-plus, server port)
□ schema.sql (所有建表语句, 含 users/user_favorites/user_search_history 预留)
□ Git 初始化 + .gitignore
```

### Phase 1: 数据管线 (预计 5 天)

```
□ 1.1 中国陆地边界数据获取
      OSM relation 270056 → GeoJSON → 验证完整性
□ 1.2 网格分割器 (grid_splitter.py)
      渔网: 1°×1° + 0.05° overlap
      中国边界相交判断 → 蛇形排序 → 输出队列
□ 1.3 逐格抓取脚本
      网格队列读取 → Overpass API 查询 → 每格独立 GeoJSON
      5 次重试 + 递增间隔 + 429 特殊处理
□ 1.4 Spring Batch 批量导入
      GridImportJob: 文件发现 → 逐文件分块导入 → 进度日志
      失败网格独立记录到 import_errors.log
□ 1.5 拓扑连接表构建
      railway_topology: ST_Intersects + ST_DWithin 50m
□ 1.6 时刻表爬虫 + 票价爬虫
      从 liecheba.com 获取车次列表 → 逐车次爬取
      解析途经站 + 各席别票价 → 存入 train_routes/train_stops/train_fares
□ 1.7 数据完整性校验
      各区域数量统计 → 缺失网格告警 → 密度报告
```

### Phase 2: 地图服务 (预计 4 天)

```
□ 2.1 矢量瓦片 API
      TileController + TileService → PostGIS ST_AsMVT
      铁路线层 z≥6, 车站层 z≥11
      MVT 格式 + 1h 浏览器缓存
□ 2.2 底图验证
      MapTiler Streets 国内各城市加载速度测试
      天地图备选验证
      最终选定并记录
□ 2.3 前端地图组件
      MapContainer.vue + RailwayLayer.vue + StationLayer.vue
      按 category 字段着色 (第 5 节分类体系)
      MapLegend.vue (图例面板)
```

### Phase 3: 搜索系统 (预计 3 天)

```
□ 3.1 车站搜索
      StationSearchService (中文/拼音/首字母/城市)
      PinyinUtils 拼音索引生成
      StationSearch.vue (自动完成 + 分类标签)
□ 3.2 车次搜索
      TrainSearchService (前缀/始发终到)
      TrainSearch.vue
□ 3.3 前端搜索面板
      SearchPanel.vue (Tab: 车站/车次/换乘)
      选中后地图联动
□ 3.4 输入防误处理
      车次格式自动识别 → 提示切换 Tab
      城市搜索时不做"城市名+站"后缀匹配
```

### Phase 4: 车次路线匹配 (预计 4 天)

```
□ 4.1 RouteMatchingService 实现
      三阶段: 候选筛选(2km) → BFS 拓扑搜索 → 降级距离匹配
□ 4.2 预计算管道
      批量匹配所有车次 → train_segment_mapping 表
      约 150,000 对，预计耗时 ~2h
□ 4.3 车次路线 API
      GET /api/trains/search → 车次列表
      GET /api/trains/{no}/route → 途经站 + 线段 GeoJSON + 票价
□ 4.4 前端路线高亮
      TrainRouteLayer.vue (橙色粗线)
      RouteTimeline.vue (途经站时间线)
      RouteInfoCard.vue (车次信息 + 票价卡片)
□ 4.5 缺失段处理
      confidence < 0.8 → 虚线渲染
      match_method='distance' → 前端提示"路线待确认"
```

### Phase 5: 地图功能完善 (预计 3 天)

```
□ 5.1 站站查询
      选择两站 → 高亮区间线路
□ 5.2 城市车站列表
      搜索城市 → 展示该城市所有车站 + 分类
□ 5.3 信息面板
      车站: 名称/等级/线路/途经车次
      线段: 名称/类型/设计时速
□ 5.4 图层控制
      按分类筛选 (高铁/普速/货运/地铁/...)
      图例面板交互完善
```

### Phase 6: 多次中转换乘 (预计 5 天)

```
□ 6.1 时间依赖图构建 (TransferGraphBuilder)
      基于 train_stops 构建
      支持同站换乘 (默认 30min 最小间隔)
□ 6.2 KSP 算法实现 (TransferSearchService)
      JGraphT KShortestPaths
      硬约束: max_transfers, max_segment_12h, max_total_72h
□ 6.3 偏好排序 (TransferRankingService)
      LEAST_TIME / LEAST_TRANSFER / NIGHT_TRAIN / LEAST_PRICE
□ 6.4 TransferController
      POST /api/transfer/search
□ 6.5 前端换乘页面
      TransferSearchForm.vue + TransferResultList.vue + TransferTimeline.vue
```

### Phase 7: 用户系统与优化 (预计 4 天)

```
□ 7.1 用户认证
      Spring Security + JWT
      登录/注册/Token 刷新
□ 7.2 用户功能
      收藏车站/车次/路线
      搜索历史
□ 7.3 性能优化
      瓦片 Redis 缓存 (key: layer/z/x/y, TTL: 1h)
      车次路线查询结果缓存 (TTL: 24h)
      PMTiles 预生成评估
□ 7.4 Docker 完整部署
      docker compose up -d 一键启动
      数据导入文档
      API 文档 (Swagger/OpenAPI)
```

---

## 16. 用户决策记录

| # | 问题 | 决策 | 日期 |
|---|------|------|------|
| 1 | 底图方案 | 优先验证 MapTiler Streets；天地图备选 | 2026-04-29 |
| 2 | 票价数据 | Phase 1 爬取，8 种席别分类存储 | 2026-04-29 |
| 3 | 用户系统 | Phase 0 预留 users 表，Phase 7 实现 | 2026-04-29 |
| 4 | 坐标系 | WGS-84 为主，接受 GCJ-02 转换 | 2026-04-29 |
| 5 | 数据更新频率 | 线路季度/时刻表每日，接受 | 2026-04-29 |
| 6 | 部署环境 | 开发阶段 Linux 虚拟机，Docker 部署 | 2026-04-29 |
| 7 | 前端组件库 | Naive UI 2.x | 2026-04-29 |
| 8 | OSM 数据缺失 | 接受缺失，<br>人工补录：Phase 1-7 数据库直改；远期 Web 编辑器 | 2026-04-29 |
| 9 | 同城异站换乘时间 | 暂不获取 | 2026-04-29 |
| 10 | 城市游信息 | 远期功能，Phase 0-7 不涉及 | 2026-04-29 |
| 11 | 地图图例分类 | 按用户提供的 12 类车站 + 7 类铁路线分类体系 | 2026-04-29 |
| 12 | 技术版本 | Spring Boot 3.5.14 + PostgreSQL 17 + PostGIS 3.5 + MyBatis-Plus 3.5.16 | 2026-04-29 |

---

> **下一步**: 确认本计划 v1.1 后，进入 **Phase 0：项目初始化与环境搭建**。届时将创建完整的 Maven 多模块骨架、Vue 3 前端项目、Docker Compose 编排文件及所有建表 DDL。
