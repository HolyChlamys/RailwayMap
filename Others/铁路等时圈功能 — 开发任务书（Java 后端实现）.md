# 铁路等时圈功能 — 开发任务书（Java 后端实现）

## 一、业务需求

### 1.1 功能定义

给定**出发站 + 出发时刻 + 时间上限**，计算从该站出发在指定时间内**能到达的所有车站**及对应的**最早到达时间**。

```
示例：
  输入：北京南站, 2026-05-21 08:00, 12 小时
  输出：
    - 天津站     → 08:35 到达（直达）
    - 济南西站   → 10:22 到达（直达）
    - 南京南站   → 12:15 到达（1 次换乘：北京南→济南西→南京南）
    - 上海虹桥站 → 13:50 到达（1 次换乘）
    - ...
```

### 1.2 核心问题

| 问题             | 结论                                                    |
| ---------------- | ------------------------------------------------------- |
| 是否只能直达？   | **否**，支持换乘                                        |
| 换乘时间怎么算？ | **最小换乘时间 MCT**，站级配置（大站 15min，小站 5min） |
| 环路问题？       | 时刻表是**有向时间图**，时间单向递增，环路被自动剪枝    |
| 性能？           | 全国 ~2500 站、~1 万车次/天，RAPTOR 算法秒级可算        |

### 1.3 约束条件

```
1. 换乘约束：到达时间 + 最小换乘时间 ≤ 下一车次发车时间
2. 总时间硬上限：总耗时 ≤ 用户指定的 maxDuration（如 12 小时）
3. 时间单向性：路径上时间严格递增，不会倒流
4. 不跨天（一期简化）：所有车次在同一日历日内
5. 不考虑：票价、席别、站票、列车类型偏好（可二期扩展）
```

---

## 二、数据模型

### 2.1 数据库表

```sql
-- 车站表
CREATE TABLE station (
    id           VARCHAR(10) PRIMARY KEY,   -- 车站代码，如 'VNP'
    name         VARCHAR(50) NOT NULL,       -- 车站名，如 '北京南'
    mct_minutes  INT DEFAULT 10             -- 最小换乘时间（分钟）
);

-- 车次停靠表
CREATE TABLE trip_stop (
    id           BIGINT PRIMARY KEY AUTO_INCREMENT,
    trip_id      VARCHAR(20) NOT NULL,       -- 车次号，如 'G1'
    station_id   VARCHAR(10) NOT NULL,
    stop_index   INT NOT NULL,               -- 站序（0-based）
    arrive_time  TIME,                       -- 到达时间（NULL 表示始发站）
    depart_time  TIME,                       -- 发车时间（NULL 表示终到站）
    INDEX idx_trip_station (trip_id, station_id),
    INDEX idx_trip_order (trip_id, stop_index),
    INDEX idx_station_depart (station_id, depart_time)
);
```

### 2.2 Java 实体

```java
// 车站
public class Station {
    private String id;          // 车站代码
    private String name;        // 车站名
    private int mctMinutes;     // 最小换乘时间（分钟）
}

// 停靠点
public class Stop {
    private String stationId;
    private LocalTime arrive;   // 到站时间
    private LocalTime depart;   // 离站时间
    private int index;          // 站序
}

// 车次
public class Trip {
    private String id;          // 车次号
    private List<Stop> stops;   // 按站序排列
}
```

---

## 三、算法设计

### 3.1 算法选型：RAPTOR 变体

采用基于 **RAPTOR (Round-bAsed Public Transit Routing)** 的可达性传播算法。以**轮次**为单位逐步扩展，非常适合铁路时刻表的等时圈计算。

### 3.2 核心数据结构

```java
// 1. 最早到达时间表
Map<String, LocalTime> earliest = new HashMap<>();
// key = 车站ID, value = 从起点出发到达该站的最早时间

// 2. 优先队列（按到达时间升序）
PriorityQueue<Node> pq = new PriorityQueue<>(Comparator.comparing(n -> n.arriveTime));
// Node = (车站ID, 到达时间)

// 3. 站→车次索引（预处理构建）
Map<String, List<Trip>> tripsByStation;
// key = 车站ID, value = 经过该站的车次列表（按停靠点发车时间排序）
```

### 3.3 算法伪代码

```java
public Map<String, LocalTime> computeIsochrone(
    String startStationId,
    LocalTime startTime,
    Duration maxDuration
) {
    // 1. 初始化
    Map<String, LocalTime> earliest = new HashMap<>();
    earliest.put(startStationId, startTime);
  
    PriorityQueue<Node> pq = new PriorityQueue<>();
    pq.offer(new Node(startStationId, startTime));
  
    // 2. 主循环
    while (!pq.isEmpty()) {
        Node curr = pq.poll();
      
        // ---- 剪枝 ----
        LocalTime knownBest = earliest.get(curr.stationId);
        if (knownBest != null && curr.arriveTime.isAfter(knownBest)) {
            continue;  // 已有更优解
        }
        if (Duration.between(startTime, curr.arriveTime).compareTo(maxDuration) > 0) {
            continue;  // 超时
        }
      
        // ---- 扩展：搭乘从本站经过的所有车次 ----
        List<Trip> trips = tripsByStation.get(curr.stationId);
        for (Trip trip : trips) {
            int stopIdx = findStopIndex(trip, curr.stationId);
            if (stopIdx < 0) continue;
          
            Stop currStop = trip.stops.get(stopIdx);
            // 本站在该车次的发车时间
            LocalTime departTime = currStop.depart;
            if (departTime == null) continue;  // 终到站
          
            // 换乘约束：到达时间 + MCT ≤ 发车时间
            Station station = stationMap.get(curr.stationId);
            LocalTime earliestBoard = curr.arriveTime.plusMinutes(station.getMctMinutes());
            if (departTime.isBefore(earliestBoard)) continue;  // 赶不上
          
            // 沿途：遍历后续停靠站
            for (int i = stopIdx + 1; i < trip.stops.size(); i++) {
                Stop nextStop = trip.stops.get(i);
                if (nextStop.arrive == null) continue;
              
                Duration elapsed = Duration.between(startTime, nextStop.arrive);
                if (elapsed.compareTo(maxDuration) > 0) break;  // 后续更远，剪枝
              
                String sid = nextStop.stationId;
                if (!earliest.containsKey(sid) || 
                    nextStop.arrive.isBefore(earliest.get(sid))) {
                    earliest.put(sid, nextStop.arrive);
                    pq.offer(new Node(sid, nextStop.arrive));
                }
            }
        }
    }
  
    return earliest;
}
```

### 3.4 换乘时间处理

```java
// 最小换乘时间配置
// station 表的 mct_minutes 字段
// 典型值：大型枢纽站 15min，普通站 10min，小站 5min

// 判断能否赶上车
private boolean canBoard(
    Trip trip, 
    String stationId, 
    LocalTime arriveAtStation,
    int mctMinutes
) {
    Stop stop = findStop(trip, stationId);
    if (stop == null || stop.depart == null) return false;
    return !arriveAtStation.plusMinutes(mctMinutes).isAfter(stop.depart);
    // 等价于: arriveAtStation + mctMinutes ≤ depart
}
```

### 3.5 环路处理

环路在时间约束下自然剪枝：

```
A (08:00)
  → B (09:30) [G101 次]
    → C (11:00) [G201 次]
      → A (14:00) [G301 次]     ← 回到 A，但已花 6h
        → B (16:00) [G102 次]   ← earliest[B]=09:30, 16:00 > 09:30，剪枝
```

无需特殊处理，`earliest` 字典的自然性质保证不会死循环。

---

## 四、架构设计

### 4.1 服务分层

```
┌─────────────────────────────────────────────────────┐
│                   Controller 层                       │
│          IsochroneController (REST API)              │
├─────────────────────────────────────────────────────┤
│                   Service 层                          │
│          IsochroneService (算法编排)                  │
├─────────────────────────────────────────────────────┤
│                Engine 层（核心算法）                    │
│          RaptorEngine                                 │
│          ├── TripIndex          (时刻表索引)           │
│          ├── IsochroneResult    (结果封装)             │
│          └── PathResolver       (路径回溯，可选)       │
├─────────────────────────────────────────────────────┤
│                   Repository 层                        │
│          TripStopRepository (MyBatis-Plus/JPA)        │
│          StationRepository                           │
└─────────────────────────────────────────────────────┘
```

### 4.2 包结构

```
com.example.railway.isochrone
├── controller
│   └── IsochroneController.java
├── service
│   └── IsochroneService.java
├── engine
│   ├── RaptorEngine.java
│   ├── TripIndex.java
│   └── IsochroneResult.java
├── model
│   ├── dto
│   │   ├── IsochroneRequest.java
│   │   └── IsochroneResponse.java
│   ├── entity
│   │   ├── Station.java
│   │   └── TripStop.java
│   └── domain
│       ├── Trip.java
│       └── Stop.java
└── repository
    ├── StationRepository.java
    └── TripStopRepository.java
```

### 4.3 REST API

```java
@RestController
@RequestMapping("/api/isochrone")
public class IsochroneController {

    @PostMapping
    public ResponseEntity<IsochroneResponse> compute(
        @Valid @RequestBody IsochroneRequest request
    ) {
        IsochroneResponse response = isochroneService.compute(request);
        return ResponseEntity.ok(response);
    }
}

// 请求体
public class IsochroneRequest {
    @NotBlank
    private String startStationId;    // 出发站代码
  
    @NotNull
    private LocalTime startTime;      // 出发时刻
  
    @Min(1) @Max(48)
    private int maxHours;             // 最大时长（小时）
}

// 响应体
public class IsochroneResponse {
    private List<ReachableStation> stations;  // 可达车站列表
    private int totalCount;                   // 总数
    private long computeMs;                   // 计算耗时（ms）
}

public class ReachableStation {
    private String stationId;
    private String stationName;
    private LocalTime arriveTime;
    private long elapsedMinutes;      // 已用分钟数
    private int transfers;            // 换乘次数
}
```

### 4.4 算法与 Agent 的关系（可选）

```
无 Agent 的场景（默认）：
  Vue → Spring Boot Controller → IsochroneService → RaptorEngine

有 Agent 的场景（可选附加）：
  Vue → Spring Boot Gateway → Python Agent → 回调 Spring Boot 算法接口
                                                     ↓
                                              IsochroneService → RaptorEngine
```

**关键说明**：Agent 是**可选附加层**。Agent 不直接实现算法，而是通过 FeignClient 回调 Spring Boot 的 `POST /api/isochrone` 接口，RaptorEngine 仍然在 Java 端运行。

---

## 五、数据准备与预处理

### 5.1 索引构建（启动时一次性加载）

```java
@Component
public class TripIndex {
  
    // 站→车次列表
    private Map<String, List<Trip>> tripsByStation;
  
    // 站→（按发车时间排序的停靠点）
    private Map<String, List<TimedStop>> departuresByStation;
  
    @PostConstruct
    public void buildIndex() {
        // 从 DB 加载所有车次停靠记录
        List<TripStop> allStops = tripStopRepository.findAll();
      
        // 按车次分组并按站序排序
        Map<String, List<TripStop>> grouped = allStops.stream()
            .collect(Collectors.groupingBy(TripStop::getTripId));
      
        // 构建 Trip 对象
        List<Trip> trips = new ArrayList<>();
        for (Map.Entry<String, List<TripStop>> entry : grouped.entrySet()) {
            List<Stop> stops = entry.getValue().stream()
                .sorted(Comparator.comparingInt(TripStop::getStopIndex))
                .map(ts -> new Stop(ts.getStationId(), ts.getArriveTime(), 
                     ts.getDepartTime(), ts.getStopIndex()))
                .toList();
            trips.add(new Trip(entry.getKey(), stops));
        }
      
        // 构建站→车次索引
        tripsByStation = new HashMap<>();
        for (Trip trip : trips) {
            for (Stop stop : trip.stops()) {
                tripsByStation
                    .computeIfAbsent(stop.getStationId(), k -> new ArrayList<>())
                    .add(trip);
            }
        }
    }
}
```

### 5.2 算法调用的前置条件

```java
// 算法执行前必须确保索引已构建
// 建议在项目启动时 @PostConstruct 完成加载
// 如果数据量大可考虑异步加载 + 状态检查

@Service
public class IsochroneService {
  
    private final TripIndex tripIndex;
    private final StationRepository stationRepo;
  
    public IsochroneResponse compute(IsochroneRequest request) {
        // 1. 获取车站 MCT 信息
        Map<String, Station> stationMap = stationRepo.findAll().stream()
            .collect(Collectors.toMap(Station::getId, Function.identity()));
      
        // 2. 调用算法引擎
        RaptorEngine engine = new RaptorEngine(
            tripIndex, stationMap
        );
      
        long start = System.currentTimeMillis();
        Map<String, LocalTime> result = engine.compute(
            request.getStartStationId(),
            request.getStartTime(),
            Duration.ofHours(request.getMaxHours())
        );
        long cost = System.currentTimeMillis() - start;
      
        // 3. 组装响应
        return buildResponse(result, stationMap, cost);
    }
}
```

---

## 六、边界情况处理

### 6.1 需要覆盖的场景

| 场景               | 处理方式                                                  |
| ------------------ | --------------------------------------------------------- |
| **始发站**         | `arrive_time IS NULL`，`depart_time` 有效                 |
| **终到站**         | `depart_time IS NULL`，`arrive_time` 有效                 |
| **跨天车次**       | 一期假设同一天；若 `arrive < depart` 视为次日到达，先跳过 |
| **边界时间**       | 到达时间 ≤ 出发时间 + maxDuration 即算可达，边界值算可达  |
| **无车次车站**     | 不在索引中，不会出现在结果里                              |
| **同站不同名**     | 按车站 ID 严格匹配，"北京南" ≠ "北京"                     |
| **多车次先后到达** | `earliest` 取最早的到达时间                               |

### 6.2 性能优化方向

```java
// 1. 二分查找优化：departuresByStation 按发车时间排序后二分
int idx = Collections.binarySearch(departures, cutoff, 
    Comparator.comparing(TimedStop::getDepart));

// 2. 状态去重
if (earliest.containsKey(stationId) && 
    !arriveTime.isBefore(earliest.get(stationId))) {
    continue;
}

// 3. 距离剪枝（可选，需站坐标数据）
double maxKm = elapsedHours * 350;  // 高铁约 300km/h

// 4. 提前终止：优先队列全为空时结束
```

---

## 七、阶段规划

### Phase 1 — 核心功能

```
1. 数据库表建好，导入时刻表数据
2. TripIndex 索引构建（启动时加载）
3. RaptorEngine 核心算法（直达 + 换乘）
4. Controller + Service 层 REST API
5. 结果组装返回（JSON）
```

### Phase 2 — 体验增强

```
1. 路径回溯（用户可看具体乘车方案）
2. 换乘次数限制（如最多 3 次换乘）
3. 前端展示（地图标记 + 表格）
4. 算法缓存（相同入参直接返回缓存）
```

### Phase 3 — 扩展（按需）

```
1. 跨天车次支持
2. 列车类型筛选（高铁/普速）
3. Python Agent 对接（可选附加）
4. GeoJSON 等时面输出
```

---

## 八、发给 Claude Code 的 Prompt

你可以直接把以下内容发给 Claude Code：

---

> **需求**：为 Spring Boot 多模块项目增加铁路等时圈功能。
>
> **背景**：全国铁路时刻表数据，约 2500 个车站，每天约 1 万车次。从 A 站出发，给定出发时间和最大时长（如 12 小时），计算能到达的所有车站及最早到达时间。
>
> **技术栈**：Java 17+, Spring Boot, MyBatis-Plus, MySQL/PostgreSQL
>
> **关键约束**：
> 1. 支持换乘（不限次数）
> 2. 换乘需满足：到达时间 + 站级最小换乘时间（mct_minutes）≤ 下一车次发车时间
> 3. 总耗时不超过用户指定的最大时长
>
> **核心要求**：
> 1. 用 Java 实现 RAPTOR 算法变体，Engine 层独立可测试
> 2. 启动时构建站→车次倒排索引（TripIndex），支持二分查找优化
> 3. 优先队列 + 剪枝（时间剪枝 + 最早到达剪枝）
> 4. REST API 输出可达车站列表
>
> **数据模型**（表已建好，用 MyBatis-Plus 实体）：
> ```sql
> station(id, name, mct_minutes)
> trip_stop(id, trip_id, station_id, stop_index, arrive_time, depart_time)
> ```
>
> **输出格式**：
> ```json
> {
>   "stations": [
>     { "stationId": "TJP", "stationName": "天津站", "arriveTime": "08:35",
>       "elapsedMinutes": 35, "transfers": 0 }
>   ],
>   "totalCount": 42,
>   "computeMs": 1234
> }
> ```
>
> **请实现**（先给出包结构和核心类的骨架，再填充关键代码）：
> 1. `model/domain/Trip.java` 和 `Stop.java`
> 2. `TripIndex.java`（索引构建，@PostConstruct）
> 3. `RaptorEngine.java`（核心算法）
> 4. `IsochroneService.java`（算法编排）
> 5. `IsochroneController.java`（REST API）
> 6. `IsochroneRequest.java` / `IsochroneResponse.java`（DTO）
> 7. 关键边界情况处理
>
> **不需要实现**：Python Agent 对接、前端页面、GeoJSON 输出
