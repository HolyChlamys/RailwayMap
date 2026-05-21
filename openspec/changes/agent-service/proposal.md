## Why

当前前端 Agent UI 使用纯客户端 mock（正则匹配 + 硬编码数据），无法处理模糊自然语言查询（"武汉周边4小时内能去哪"）、多条件约束路径规划（"中途停武汉，每段不超过4小时"）、以及反问澄清等真实对话场景。需要引入 LLM 驱动的 Agent 服务，将现有的 mock 大脑替换为真正的自然语言理解 + 工具编排能力。

## What Changes

- 新增 `agent-service/` Python 微服务（FastAPI + LangGraph），独立部署
- LangGraph 状态图驱动多轮对话：意图分类 → 约束提取 → 工具调用 → 格式化回复 → 约束松弛
- 前端 `useAgentChat.ts` 替换 mock 为真实 `POST /api/agent/chat` 调用
- Agent 回复携带前端指令（`instructions`），驱动地图高亮、面板打开、路线动画等视觉效果
- Agent 通过 HTTP 调用 Java 后端现有 API（station/train/transfer/isochrone），不做算法计算
- 支持 OpenAI 兼容接口，模型可切换

## Capabilities

### New Capabilities
- `agent-chat-api`: Agent 对话 API — FastAPI 入口、LangGraph 状态图、LLM 意图理解与多轮对话管理
- `agent-tool-orchestration`: 工具编排 — Java API 调用、并行执行、约束松弛、冲突检测
- `agent-frontend-integration`: 前端集成 — instruction 驱动的地图交互、路线动画、搜索联动

### Modified Capabilities
- None（现有 API 不变，Agent 作为新消费者调用现有接口）

## Impact

- **新增代码**：`agent-service/` Python 模块（FastAPI + LangGraph + httpx）
- **新增依赖**：langgraph, fastapi, uvicorn, httpx, openai（兼容 SDK）
- **修改前端**：`useAgentChat.ts` 替换 mock 为 HTTP 调用；`AgentMessageContent` 扩展 `instructions` 字段
- **修改部署**：`docker-compose.yml` 新增 `agent-service` 容器
- **Java 后端**：不变（Phase 后续可能新增 `/api/internal/transfer/batch`）
