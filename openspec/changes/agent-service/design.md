## Context

当前 `railway-frontend/src/composables/useAgentChat.ts` 使用纯客户端 mock（正则匹配 + 硬编码数据 + setTimeout），后端无任何 Agent/AI 基础设施。需要新增 LLM 驱动的 Agent 服务，将 mock 替换为真实自然语言理解 + 工具编排。

约束：Agent 只做理解和编排，所有算法计算（搜索、规划、等时圈）由 Java 后端现有 API 完成。

## Goals / Non-Goals

**Goals:**
- 新增 Python 微服务 `agent-service/`，提供 `POST /api/agent/chat` 入口
- LangGraph 状态图驱动多轮对话（理解 → 反问/搜索 → 格式化 → 松弛）
- LLM 使用 OpenAI 兼容接口，模型可切换
- 前端替换 mock，对接真实 Agent API
- Agent 回复携带 `instructions` 驱动地图交互和面板切换

**Non-Goals:**
- Agent 不实现路线搜索/等时圈算法（复用 Java 后端）
- 不引入消息队列或事件总线（直接 HTTP 通信）
- Phase 初期不实现 `/api/internal/transfer/batch`（后续按需）
- 不引入 WebSocket / SSE 流式推送（先 request-response，流式后续迭代）

## Decisions

### 1. Python + FastAPI + LangGraph（独立微服务）

**选择**：独立 Python 容器，通过 Docker 网络 HTTP 调 Java 后端。

**理由**：LangGraph 状态图天然适配多轮对话 + 条件分支（反问/搜索/松弛）；Python LLM 生态（langchain-openai, instructor）远成熟于 Java；独立演进不污染 railway-api 职责。

**替代方案**：
- Spring AI 内嵌 → Java LLM 框架生态不如 Python，耦合增加
- Node.js 中间层 → 多一层不必要跳转

### 2. 前端指令系统（instructions）而非 Agent 直接返回业务数据

**选择**：Agent 返回 `{ text, instructions: [{action, params}], suggestions }`，前端根据 `instructions` 调 Pinia store actions。

**理由**：地图交互逻辑完全在前端（MapLibre shallowRef、WebGL 动画），Agent 不应感知前端渲染细节。`instructions` 是抽象语义指令（`flyToStation`、`highlightRoutes`），前端自行翻译为具体操作。保持 Agent 和前端解耦。

### 3. LangGraph 状态图而非 if/else 链

**选择**：LangGraph StateGraph 编译为可恢复的状态机。

**理由**：多轮对话的分支逻辑（clarify 后的等待、relax 后的重试）用状态图表达比手写 if/else 更可测试、可观察。LangGraph 内置 checkpointer 机制支持会话状态持久化。

### 4. Async HTTP 并行工具调用

**选择**：用 `asyncio.gather` + `httpx.AsyncClient` 并行调用独立工具。

**理由**：用户查询常需要同时查车站 + 等时圈 + 路线规划，并行可减少延迟。单工具失败不影响其他。

### 5. Request-Response 先于流式

**选择**：Phase 初期使用 JSON request-response，不引入 SSE/WebSocket。

**理由**：流式推送的复杂度主要在：LLM streaming token → 增量 JSON 解析 → 前端渐进渲染。先验证 LangGraph 逻辑正确性，流式作为后续迭代。

## Risks / Trade-offs

- **Agent 独立部署增加运维复杂度** → 通过 docker-compose 一键编排，开发环境透明
- **LLM 输出不确定性** → System prompt 严格约束输出 JSON Schema，understand 节点使用 structured output / tool calling 能力
- **LLM 延迟（1-3s）** → 前端已有 typing indicator 动画，用户可接受；并行工具调用减少串行等待
- **HTTP 调用链增加**（前端 → Agent → Java → DB）→ Java API 已有 Redis 缓存（tiles 1h），数据库有 GIST/B-tree 索引，跟踪延迟瓶颈再针对性优化
- **Python 技术栈被团队不熟悉** → agent-service 代码量小（~20 文件），LangGraph 文档完善，FastAPI 学习曲线低
- **会话状态管理** → 初期用内存 dict，后续可迁 Redis（与 Java 后端共享同一 Redis 实例）
