# RailwayMap 健康检查修复实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复健康检查报告中的 P0 安全问题、P1 架构违规和核心性能瓶颈

**Architecture:** 修复遵循现有分层架构 (api→service→data→common)，新增 Service 和 Mapper 保持与现有模式（@RequiredArgsConstructor + final field）一致

**Tech Stack:** Java 21, Spring Boot 3.5, MyBatis-Plus, Python 3.12, Vue 3 + TypeScript

---

## Phase 1: 紧急安全修复 (P0)

### Task 1: 撤销已泄露的 API Key 并清理 .env

**Files:**
- Modify: `agent-service/.env`
- Modify: `.gitignore` (already has `.env` rule, verify)
- Modify: `agent-service/src/config.py:8`

**说明:** `.env` 已在 `.gitignore` 第 32 行，且 `git ls-files agent-service/.env` 返回空 — 该文件未被 git 跟踪。但文件系统上存在含真实 API Key 的文件，需要清理并确保即使误提交也不会生效。

- [ ] **Step 1: 将 .env 中的 API Key 改为占位符**

```bash
# 编辑 agent-service/.env，将真实的 API Key 替换为占位符
```

修改 `agent-service/.env`:

```ini
AGENT_LLM_BASE_URL=https://api.deepseek.com
AGENT_LLM_API_KEY=sk-your-key-here
AGENT_LLM_MODEL=deepseek-v4-flash
AGENT_JAVA_BASE_URL=http://localhost:10010
```

- [ ] **Step 2: 创建 .env.example 作为配置模板**

创建 `agent-service/.env.example`:

```ini
AGENT_LLM_BASE_URL=https://api.deepseek.com
AGENT_LLM_API_KEY=sk-your-key-here
AGENT_LLM_MODEL=deepseek-v4-flash
AGENT_JAVA_BASE_URL=http://localhost:10010
```

- [ ] **Step 3: 移除 config.py 中的占位默认值**

修改 `agent-service/src/config.py` 第 8 行:

```python
# 原:
llm_api_key: str = "sk-placeholder"

# 改为:
llm_api_key: str = ""
```

- [ ] **Step 4: 添加 agent-service 的 .gitignore**

创建 `agent-service/.gitignore`:

```
.env
__pycache__/
*.pyc
.venv/
```

- [ ] **Step 5: 验证 .env 未被 git 跟踪**

```bash
git ls-files agent-service/.env
# 预期: 空输出
git status agent-service/.env
# 预期: 文件出现在 "Untracked files" 或不在 git 视野内
```

- [ ] **Step 6: Commit**

```bash
git add agent-service/.env.example agent-service/.gitignore agent-service/src/config.py
git commit -m "fix: 移除 agent-service 中的敏感 API Key 占位符，添加 .env.example 模板"
```

### Task 2: JWT 密钥移除硬编码默认值

**Files:**
- Modify: `railway-api/src/main/java/com/railwaymap/api/config/JwtUtil.java:19`
- Modify: `railway-api/src/main/resources/application.yml:49`

- [ ] **Step 1: JwtUtil 移除硬编码默认密钥**

修改 `JwtUtil.java` 第 19 行构造函数参数:

```java
// 原:
public JwtUtil(@Value("${railway.jwt.secret:railwaymap-default-jwt-secret-key-2026}") String secret,
               @Value("${railway.jwt.expiration:86400000}") long expirationMs) {

// 改为 (无默认值，启动即报错提醒配置):
public JwtUtil(@Value("${railway.jwt.secret}") String secret,
               @Value("${railway.jwt.expiration:86400000}") long expirationMs) {
    if (secret == null || secret.isBlank() || secret.length() < 32) {
        throw new IllegalArgumentException("JWT secret must be at least 32 characters. Set JWT_SECRET environment variable.");
    }
```

- [ ] **Step 2: application.yml 移除 JWT 默认值**

修改 `application.yml` 第 49 行:

```yaml
# 原:
    secret: ${JWT_SECRET:railwaymap-production-secret-change-in-env}

# 改为:
    secret: ${JWT_SECRET}
```

- [ ] **Step 3: docker-compose.yml 添加 JWT_SECRET 环境变量占位**

修改 `docker-compose.yml`，在 app 服务的 environment 中添加:

```yaml
    environment:
      DB_HOST: db
      DB_USER: railway
      DB_PASSWORD: ${DB_PASSWORD}
      REDIS_HOST: redis
      REDIS_PORT: 6379
      JWT_SECRET: ${JWT_SECRET}
```

- [ ] **Step 4: Commit**

```bash
git add railway-api/src/main/java/com/railwaymap/api/config/JwtUtil.java \
        railway-api/src/main/resources/application.yml \
        docker-compose.yml
git commit -m "fix: 移除 JWT 密钥硬编码默认值，改为必填环境变量启动校验"
```

### Task 3: 移除数据库密码明文硬编码

**Files:**
- Modify: `docker-compose.yml:7,41`
- Modify: `railway-api/src/main/resources/application.yml:10`
- Modify: `railway-api/src/main/resources/application-dev.yml:5`

- [ ] **Step 1: docker-compose.yml 密码改用环境变量**

修改 `docker-compose.yml`:

```yaml
# 原:
      POSTGRES_PASSWORD: railway123
      # ...
      DB_PASSWORD: railway123

# 改为:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      # ...
      DB_PASSWORD: ${DB_PASSWORD}
```

- [ ] **Step 2: application.yml 移除默认密码**

修改 `application.yml` 第 10 行:

```yaml
# 原:
    password: ${DB_PASSWORD:railway123}

# 改为:
    password: ${DB_PASSWORD}
```

- [ ] **Step 3: application-dev.yml 改用环境变量**

修改 `application-dev.yml`:

```yaml
# 原:
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/railwaymap
    username: railway
    password: railway123

# 改为:
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/railwaymap
    username: ${DB_USER:railway}
    password: ${DB_PASSWORD}
```

- [ ] **Step 4: 创建 .env.example 用于项目根目录**

创建 `.env.example`:

```
DB_PASSWORD=change-me
JWT_SECRET=change-me-use-openssl-rand-base64-32
AGENT_LLM_API_KEY=sk-your-key-here
AGENT_LLM_BASE_URL=https://api.deepseek.com
AGENT_LLM_MODEL=deepseek-v4-flash
```

- [ ] **Step 5: Commit**

```bash
git add docker-compose.yml \
        railway-api/src/main/resources/application.yml \
        railway-api/src/main/resources/application-dev.yml \
        .env.example
git commit -m "fix: 移除数据库密码明文硬编码，全部改用环境变量注入"
```

### Task 4: 修复 nginx 代理端口 + 添加安全响应头

**Files:**
- Modify: `nginx.conf`

- [ ] **Step 1: 修复 API 代理端口并添加安全头**

修改 `nginx.conf`:

```nginx
server {
    listen 80;
    server_name localhost;

    # 安全响应头
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Content-Security-Policy "default-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; connect-src 'self' https://api.maptiler.com; img-src 'self' data: https://api.maptiler.com; worker-src 'self' blob:; child-src 'self' blob:" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Vue 前端静态文件
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # API 反向代理
    location /api/ {
        proxy_pass http://app:10010;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/agent {
        proxy_pass http://agent:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

- [ ] **Step 2: Commit**

```bash
git add nginx.conf
git commit -m "fix: 修复 nginx proxy_pass 端口 8080→10010，添加安全响应头"
```

---

## Phase 2: 架构分层修复 (P1)

### Task 5: 创建 UserMapper

**Files:**
- Create: `railway-data/src/main/java/com/railwaymap/data/mapper/UserMapper.java`

User entity 已存在于 `railway-common/src/main/java/com/railwaymap/common/entity/User.java`，但缺少对应的 MyBatis-Plus Mapper。

- [ ] **Step 1: 创建 UserMapper**

```java
package com.railwaymap.data.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.railwaymap.common.entity.User;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface UserMapper extends BaseMapper<User> {
}
```

- [ ] **Step 2: Commit**

```bash
git add railway-data/src/main/java/com/railwaymap/data/mapper/UserMapper.java
git commit -m "feat: 添加 UserMapper，为 Auth/User Service 分层修复做准备"
```

### Task 6: 创建 AuthService

**Files:**
- Create: `railway-service/src/main/java/com/railwaymap/service/auth/AuthService.java`
- Modify: `railway-api/src/main/java/com/railwaymap/api/controller/AuthController.java`

将 AuthController 中的 JdbcTemplate SQL 操作迁移到新的 AuthService。

- [ ] **Step 1: 创建 AuthService**

```java
package com.railwaymap.service.auth;

import com.railwaymap.api.config.JwtUtil;
import com.railwaymap.common.entity.User;
import com.railwaymap.data.mapper.UserMapper;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.Map;

@Service
@RequiredArgsConstructor
@Slf4j
public class AuthService {

    private final UserMapper userMapper;
    private final PasswordEncoder passwordEncoder;
    private final JwtUtil jwtUtil;

    public Map<String, Object> register(String username, String password) {
        if (username == null || password == null || username.length() < 3 || password.length() < 6) {
            return Map.of("success", false, "message", "用户名≥3字符, 密码≥6字符");
        }

        // 检查用户名是否已存在
        Long count = userMapper.selectCount(
                new LambdaQueryWrapper<User>().eq(User::getUsername, username));
        if (count > 0) {
            return Map.of("success", false, "message", "用户名已存在");
        }

        User user = new User();
        user.setUsername(username);
        user.setPasswordHash(passwordEncoder.encode(password));
        userMapper.insert(user);

        String token = jwtUtil.generateToken(username);
        return Map.of("success", true, "token", token);
    }

    public Map<String, Object> login(String username, String password) {
        try {
            User user = userMapper.selectOne(
                    new LambdaQueryWrapper<User>().eq(User::getUsername, username));
            if (user != null && passwordEncoder.matches(password, user.getPasswordHash())) {
                String token = jwtUtil.generateToken(username);
                return Map.of("success", true, "token", token);
            }
        } catch (Exception e) {
            log.error("登录查询失败: username={}", username, e);
            return Map.of("success", false, "message", "系统错误，请稍后重试");
        }

        return Map.of("success", false, "message", "用户名或密码错误");
    }
}
```

- [ ] **Step 2: 重构 AuthController 使用 AuthService**

```java
package com.railwaymap.api.controller;

import com.railwaymap.service.auth.AuthService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    @PostMapping("/register")
    public Map<String, Object> register(@RequestBody Map<String, String> body) {
        return authService.register(body.get("username"), body.get("password"));
    }

    @PostMapping("/login")
    public Map<String, Object> login(@RequestBody Map<String, String> body) {
        return authService.login(body.get("username"), body.get("password"));
    }
}
```

- [ ] **Step 3: Commit**

```bash
git add railway-service/src/main/java/com/railwaymap/service/auth/AuthService.java \
        railway-api/src/main/java/com/railwaymap/api/controller/AuthController.java
git commit -m "refactor: 将 AuthController JdbcTemplate 操作迁移至 AuthService 分层修复"
```

### Task 7: 创建 UserService + FavoriteService

**Files:**
- Create: `railway-service/src/main/java/com/railwaymap/service/user/UserService.java`
- Create: `railway-service/src/main/java/com/railwaymap/service/user/FavoriteService.java`
- Modify: `railway-api/src/main/java/com/railwaymap/api/controller/UserController.java`

注意: `user_favorites` 和 `user_search_history` 没有对应的 Entity。为最小化变更范围，UserService 使用 JdbcTemplate（迁出现有逻辑即可），FavoriteService 负责序列化/校验。

- [ ] **Step 1: 创建 UserService**

```java
package com.railwaymap.service.user;

import com.railwaymap.common.entity.User;
import com.railwaymap.data.mapper.UserMapper;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class UserService {

    private final UserMapper userMapper;

    public Long getUserId(String username) {
        User user = userMapper.selectOne(
                new LambdaQueryWrapper<User>().eq(User::getUsername, username));
        return user != null ? user.getId() : null;
    }
}
```

- [ ] **Step 2: 创建 FavoriteService**

```java
package com.railwaymap.service.user;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
@Slf4j
public class FavoriteService {

    private final JdbcTemplate jdbc;
    private final UserService userService;
    private final ObjectMapper objectMapper;

    public List<Map<String, Object>> getFavorites(String username) {
        Long userId = userService.getUserId(username);
        return jdbc.queryForList(
                "SELECT id, type, target_id, label, data, created_at FROM user_favorites WHERE user_id = ?",
                userId);
    }

    public Map<String, Object> addFavorite(String username, Map<String, Object> body) {
        Long userId = userService.getUserId(username);
        String type = (String) body.get("type");
        String targetId = (String) body.get("target_id");
        String label = (String) body.get("label");

        String dataJson;
        try {
            dataJson = objectMapper.writeValueAsString(body.getOrDefault("data", Map.of()));
        } catch (JsonProcessingException e) {
            log.warn("Failed to serialize favorite data", e);
            dataJson = "{}";
        }

        jdbc.update(
                "INSERT INTO user_favorites (user_id, type, target_id, label, data) " +
                "VALUES (?, ?, ?, ?, ?::jsonb) ON CONFLICT (user_id, type, target_id) DO NOTHING",
                userId, type, targetId, label, dataJson);
        return Map.of("success", true);
    }

    public Map<String, Object> removeFavorite(String username, Long id) {
        Long userId = userService.getUserId(username);
        jdbc.update("DELETE FROM user_favorites WHERE id = ? AND user_id = ?", id, userId);
        return Map.of("success", true);
    }

    public List<Map<String, Object>> getHistory(String username) {
        Long userId = userService.getUserId(username);
        return jdbc.queryForList(
                "SELECT id, search_type, query_text, created_at FROM user_search_history " +
                "WHERE user_id = ? ORDER BY created_at DESC LIMIT 50", userId);
    }

    public Map<String, Object> addHistory(String username, String searchType, String queryText) {
        Long userId = userService.getUserId(username);
        jdbc.update(
                "INSERT INTO user_search_history (user_id, search_type, query_text) VALUES (?, ?, ?)",
                userId, searchType, queryText);
        return Map.of("success", true);
    }
}
```

- [ ] **Step 3: 重构 UserController**

```java
package com.railwaymap.api.controller;

import com.railwaymap.service.user.FavoriteService;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class UserController {

    private final FavoriteService favoriteService;

    @GetMapping("/favorites")
    public List<Map<String, Object>> getFavorites(@AuthenticationPrincipal String username) {
        return favoriteService.getFavorites(username);
    }

    @PostMapping("/favorites")
    public Map<String, Object> addFavorite(@AuthenticationPrincipal String username,
                                            @RequestBody Map<String, Object> body) {
        return favoriteService.addFavorite(username, body);
    }

    @DeleteMapping("/favorites/{id}")
    public Map<String, Object> removeFavorite(@AuthenticationPrincipal String username,
                                               @PathVariable Long id) {
        return favoriteService.removeFavorite(username, id);
    }

    @GetMapping("/history")
    public List<Map<String, Object>> getHistory(@AuthenticationPrincipal String username) {
        return favoriteService.getHistory(username);
    }

    @PostMapping("/history")
    public Map<String, Object> addHistory(@AuthenticationPrincipal String username,
                                           @RequestBody Map<String, String> body) {
        return favoriteService.addHistory(username, body.get("search_type"), body.get("query_text"));
    }
}
```

- [ ] **Step 4: Commit**

```bash
git add railway-service/src/main/java/com/railwaymap/service/user/UserService.java \
        railway-service/src/main/java/com/railwaymap/service/user/FavoriteService.java \
        railway-api/src/main/java/com/railwaymap/api/controller/UserController.java
git commit -m "refactor: 将 UserController JdbcTemplate 操作迁移至 UserService/FavoriteService"
```

### Task 8: 创建 TrainRouteService

**Files:**
- Create: `railway-service/src/main/java/com/railwaymap/service/search/TrainRouteService.java`
- Modify: `railway-api/src/main/java/com/railwaymap/api/controller/TrainController.java`

- [ ] **Step 1: 创建 TrainRouteService**

```java
package com.railwaymap.service.search;

import com.railwaymap.common.dto.TrainRouteDetail;
import com.railwaymap.common.entity.*;
import com.railwaymap.data.mapper.*;
import com.railwaymap.service.route.RouteGeoJsonService;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class TrainRouteService {

    private final TrainRouteMapper trainRouteMapper;
    private final TrainStopMapper trainStopMapper;
    private final TrainSegmentMappingMapper mappingMapper;
    private final TrainFareMapper fareMapper;
    private final StationMapper stationMapper;
    private final RouteGeoJsonService geoJsonService;

    public TrainRouteDetail getRouteDetail(String no) {
        TrainRoute route = trainRouteMapper.selectOne(
                new LambdaQueryWrapper<TrainRoute>().eq(TrainRoute::getTrainNo, no));
        if (route == null) return null;

        List<TrainStop> stops = trainStopMapper.selectList(
                new LambdaQueryWrapper<TrainStop>()
                        .eq(TrainStop::getTrainNo, no)
                        .orderByAsc(TrainStop::getSeq));

        List<TrainSegmentMapping> mappings = mappingMapper.selectList(
                new LambdaQueryWrapper<TrainSegmentMapping>()
                        .eq(TrainSegmentMapping::getTrainNo, no));

        List<TrainFare> fares = fareMapper.selectList(
                new LambdaQueryWrapper<TrainFare>()
                        .eq(TrainFare::getTrainNo, no));

        TrainRouteDetail detail = new TrainRouteDetail();
        detail.setTrainNo(route.getTrainNo());
        detail.setTrainType(route.getTrainType());
        detail.setDepartStation(route.getDepartStation());
        detail.setArriveStation(route.getArriveStation());
        detail.setDepartTime(route.getDepartTime());
        detail.setArriveTime(route.getArriveTime());
        detail.setDurationMin(route.getDurationMin());

        detail.setStops(stops.stream().map(s -> {
            TrainRouteDetail.StopInfo si = new TrainRouteDetail.StopInfo();
            si.setSeq(s.getSeq());
            si.setStationName(s.getStationName());
            si.setStationId(s.getStationId());
            si.setArriveTime(s.getArriveTime());
            si.setDepartTime(s.getDepartTime());
            si.setStayMin(s.getStayMin());
            return si;
        }).collect(Collectors.toList()));

        if (!mappings.isEmpty()) {
            detail.setSegmentsGeoJson(geoJsonService.toGeoJson(mappings));
        }

        detail.setFares(fares.stream().map(f -> {
            TrainRouteDetail.FareInfo fi = new TrainRouteDetail.FareInfo();
            fi.setFromStation(f.getFromStation());
            fi.setToStation(f.getToStation());
            fi.setPriceSecond(f.getPriceSecond());
            fi.setPriceFirst(f.getPriceFirst());
            fi.setPriceBusiness(f.getPriceBusiness());
            fi.setPriceSoftSleeperDown(f.getPriceSoftSleeperDown());
            fi.setPriceHardSleeperDown(f.getPriceHardSleeperDown());
            fi.setPriceHardSeat(f.getPriceHardSeat());
            return fi;
        }).collect(Collectors.toList()));

        return detail;
    }
}
```

- [ ] **Step 2: 重构 TrainController**

```java
package com.railwaymap.api.controller;

import com.railwaymap.common.dto.TrainRouteDetail;
import com.railwaymap.common.dto.TrainSearchRequest;
import com.railwaymap.common.dto.TrainSearchResult;
import com.railwaymap.service.search.TrainRouteService;
import com.railwaymap.service.search.TrainSearchService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/trains")
@RequiredArgsConstructor
public class TrainController {

    private final TrainSearchService trainSearchService;
    private final TrainRouteService trainRouteService;

    @GetMapping("/search")
    public List<TrainSearchResult> search(@ModelAttribute TrainSearchRequest request) {
        return trainSearchService.search(request.getQ(), request.getType(), request.getLimit());
    }

    @GetMapping("/{no}/route")
    public TrainRouteDetail getRoute(@PathVariable String no) {
        return trainRouteService.getRouteDetail(no);
    }
}
```

- [ ] **Step 3: Commit**

```bash
git add railway-service/src/main/java/com/railwaymap/service/search/TrainRouteService.java \
        railway-api/src/main/java/com/railwaymap/api/controller/TrainController.java
git commit -m "refactor: 将 TrainController Mapper 操作迁移至 TrainRouteService 分层修复"
```

---

## Phase 3: 前端修复 (P1)

### Task 9: 解除 agentStore 跨 store 引用

**Files:**
- Create: `railway-frontend/src/composables/useAgentDispatch.ts`
- Modify: `railway-frontend/src/stores/agentStore.ts`
- Modify: `railway-frontend/src/components/agent/AgentPanel.vue`

将 `dispatchInstruction` 从 agentStore 移出到独立的 composable。agentStore 不再导入其他 store，只发出指令事件；composable 在组件层订阅并驱动其他 store。

- [ ] **Step 1: 创建 useAgentDispatch composable**

```typescript
// useAgentDispatch.ts
import { watch } from 'vue'
import type { AgentInstruction } from '../types/agent'
import type { FlyToStationInstruction, HighlightTrainInstruction, HighlightRoutesInstruction, HighlightIsochroneInstruction } from '../types/agent'
import { useMapStore } from '../stores/mapStore'
import { useStationStore } from '../stores/stationStore'
import { useTrainStore } from '../stores/trainStore'
import { useRoutePlanStore } from '../stores/routePlanStore'

export function useAgentDispatch(instruction: Ref<AgentInstruction | null>) {
  const mapStore = useMapStore()
  const stationStore = useStationStore()
  const trainStore = useTrainStore()
  const routePlanStore = useRoutePlanStore()

  watch(instruction, (inst) => {
    if (!inst) return
    switch (inst.action) {
      case 'flyToStation': {
        const { stationId } = inst as FlyToStationInstruction
        const id = parseInt(stationId, 10)
        mapStore.setFocusStation(stationId)
        stationStore.setCurrentStation(isNaN(id) ? null : id)
        break
      }
      case 'highlightTrain': {
        const { trainNo } = inst as HighlightTrainInstruction
        mapStore.setFocusTrain(trainNo)
        trainStore.setCurrentTrain(trainNo)
        break
      }
      case 'highlightRoutes': {
        const { routeIds } = inst as HighlightRoutesInstruction
        routePlanStore.setActivePlanIds(routeIds)
        break
      }
      case 'highlightIsochrone': {
        const { stationId } = inst as HighlightIsochroneInstruction
        mapStore.setFocusStation(stationId)
        break
      }
      case 'openPanel':
      case 'openModal':
        break
      case 'clearHighlights': {
        mapStore.clearAllFocus()
        routePlanStore.clear()
        break
      }
    }
  })
}
```

- [ ] **Step 2: 重构 agentStore 移除 store 交叉引用**

```typescript
// agentStore.ts — 移除 import useMapStore/useStationStore/useTrainStore/useRoutePlanStore
// 移除 dispatchInstruction 方法
// 将 defaultQuickSuggestions 加入 return

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ChatMessage, AgentMessageContent, AgentPanelState, QuickSuggestion } from '../types/agent'

export const useAgentStore = defineStore('agent', () => {
  const messages = ref<ChatMessage[]>([])
  const panelState = ref<AgentPanelState>('closed')
  const isProcessing = ref(false)

  const isOpen = computed(() => panelState.value === 'open')
  const messageCount = computed(() => messages.value.length)

  const defaultQuickSuggestions: QuickSuggestion[] = [
    { label: '北京到广州怎么走', prompt: '北京到广州怎么走' },
    { label: '查询G1车次', prompt: '查询G1车次' },
    { label: '上海虹桥有哪些车', prompt: '上海虹桥有哪些车' },
  ]

  const quickSuggestions = ref<QuickSuggestion[]>([...defaultQuickSuggestions])

  function loadHistory() {
    try {
      const saved = localStorage.getItem('railwaymap_agent_history')
      if (saved) {
        const parsed = JSON.parse(saved)
        if (Array.isArray(parsed) && parsed.length > 0) {
          messages.value = parsed.map(m => ({
            ...m,
            timestamp: new Date(m.timestamp)
          }))
          return
        }
      }
    } catch (e) {
      console.warn('Failed to load agent history', e)
    }
    if (messages.value.length === 0) {
      addWelcomeMessage()
    }
  }

  function saveHistory() {
    try {
      localStorage.setItem('railwaymap_agent_history', JSON.stringify(messages.value))
    } catch (e) {
      console.warn('Failed to save agent history', e)
    }
  }

  function openPanel() {
    panelState.value = 'open'
    if (messages.value.length === 0) loadHistory()
  }

  function closePanel() { panelState.value = 'closed' }

  function togglePanel() {
    if (panelState.value === 'open') closePanel()
    else openPanel()
  }

  function addMessage(role: 'user' | 'agent', content: AgentMessageContent) {
    messages.value.push({
      id: `msg-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      role,
      content,
      timestamp: new Date(),
    })
    saveHistory()
  }

  function addWelcomeMessage() {
    messages.value.push({
      id: 'welcome',
      role: 'agent',
      content: {
        text: '你好！我是铁路助手，可以帮你：\n\n🔍 **查询信息** — 车站详情、车次信息、城市车站\n🗺️ **路径规划** — 输入起点、终点和偏好，我帮你规划中转路线\n\n直接告诉我你的需求。',
      },
      timestamp: new Date(),
    })
    saveHistory()
  }

  function setProcessing(p: boolean) { isProcessing.value = p }

  function setQuickSuggestions(sugs: QuickSuggestion[]) {
    quickSuggestions.value = sugs
  }

  function clearMessages() {
    messages.value = []
    localStorage.removeItem('railwaymap_agent_history')
    addWelcomeMessage()
  }

  return {
    messages, panelState, isProcessing, isOpen, messageCount,
    defaultQuickSuggestions, quickSuggestions,
    openPanel, closePanel, togglePanel, addMessage,
    setProcessing, clearMessages, setQuickSuggestions,
  }
})
```

- [ ] **Step 3: 修改 AgentPanel.vue 使用 composable**

在 `AgentPanel.vue` 的 `<script setup>` 中添加:

```typescript
import { ref } from 'vue'
import { useAgentDispatch } from '../../composables/useAgentDispatch'
import type { AgentInstruction } from '../../types/agent'

// 替换原有对 agentStore.dispatchInstruction 的调用
const lastInstruction = ref<AgentInstruction | null>(null)
useAgentDispatch(lastInstruction)

// 在原调用 agentStore.dispatchInstruction(inst) 的地方改为:
// lastInstruction.value = inst
```

同时修复 `agentStore.defaultQuickSuggestions` 的引用（当前 diff 中第 131 行 `agentStore.defaultQuickSuggestions` — 现在 store 已暴露此属性）。

- [ ] **Step 4: Commit**

```bash
git add railway-frontend/src/composables/useAgentDispatch.ts \
        railway-frontend/src/stores/agentStore.ts \
        railway-frontend/src/components/agent/AgentPanel.vue
git commit -m "refactor: 解除 agentStore 跨 store 引用，dispatchInstruction 移至 composable"
```

---

## Phase 4: 性能优化 (P2)

### Task 10: 为 TileService 和关键查询启用 Redis 缓存

**Files:**
- Modify: `railway-service/src/main/java/com/railwaymap/service/map/TileService.java`
- Modify: `railway-service/src/main/java/com/railwaymap/service/search/StationSearchService.java`
- Modify: `railway-service/src/main/java/com/railwaymap/service/search/TrainRouteService.java`

- [ ] **Step 1: 为 TileService.getTile 添加 @Cacheable**

修改 `TileService.java`，在 `getTile` 方法上添加:

```java
import org.springframework.cache.annotation.Cacheable;

@Cacheable(value = "tiles", key = "#layer + ':' + #z + '/' + #x + '/' + #y")
public byte[] getTile(String layer, int z, int x, int y) {
    // 现有逻辑不变
}
```

- [ ] **Step 2: 为 StationSearchService.search 添加缓存**

```java
@Cacheable(value = "stationSearch", key = "#q + ':' + #limit")
public List<StationSearchResult> search(String q, String type, int limit) {
    // 现有逻辑不变
}
```

- [ ] **Step 3: 为 TrainRouteService.getRouteDetail 添加缓存**

```java
@Cacheable(value = "trainRoutes", key = "#no")
public TrainRouteDetail getRouteDetail(String no) {
    // 现有逻辑不变
}
```

- [ ] **Step 4: Commit**

```bash
git add railway-service/src/main/java/com/railwaymap/service/map/TileService.java \
        railway-service/src/main/java/com/railwaymap/service/search/StationSearchService.java \
        railway-service/src/main/java/com/railwaymap/service/search/TrainRouteService.java
git commit -m "feat: 为 Tile/StationSearch/TrainRoute 启用 Redis @Cacheable 缓存"
```

### Task 11: 批量查询优化 — RouteGeoJsonService

**Files:**
- Modify: `railway-service/src/main/java/com/railwaymap/service/route/RouteGeoJsonService.java`

将 for 循环中的 `selectById` 改为 `selectBatchIds` 批量查询。

- [ ] **Step 1: 批量查询替代逐条查询**

修改 `RouteGeoJsonService.java` 的 `toGeoJson` 方法:

```java
// 原: 第25行 segmentMapper.selectById(m.getSegId()) 在 for 循环
// 改为:
List<Long> segIds = mappings.stream()
        .map(TrainSegmentMapping::getSegId)
        .distinct()
        .collect(Collectors.toList());
List<RailwaySegment> segments = segmentMapper.selectBatchIds(segIds);
Map<Long, RailwaySegment> segMap = segments.stream()
        .collect(Collectors.toMap(RailwaySegment::getId, s -> s));

for (TrainSegmentMapping m : mappings) {
    RailwaySegment seg = segMap.get(m.getSegId());
    if (seg == null) continue;
    // ... 后续 WKT 解析逻辑不变
}
```

- [ ] **Step 2: Commit**

```bash
git add railway-service/src/main/java/com/railwaymap/service/route/RouteGeoJsonService.java
git commit -m "perf: RouteGeoJsonService 用 selectBatchIds 替代逐条查询，消除 N+1"
```

---

## Phase 5: 验证与收尾

### Task 12: 编译验证 + 前端类型检查

- [ ] **Step 1: 编译 Java 后端**

```bash
cd railway-api && mvn compile -q
# 预期: BUILD SUCCESS
```

- [ ] **Step 2: 检查前端 TypeScript**

```bash
cd railway-frontend && npx vue-tsc --noEmit 2>&1 | head -30
# 检查是否有类型错误
```

- [ ] **Step 3: 最终 git status 检查**

```bash
git status
# 预期: 所有变更已提交，工作区干净
git log --oneline -15
# 确认提交记录清晰
```
