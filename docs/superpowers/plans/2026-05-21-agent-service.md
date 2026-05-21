# Agent Service Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python Agent microservice (FastAPI + LangGraph) that replaces the frontend mock with LLM-driven natural language understanding, and wire it to drive map interactions via a frontend instruction system.

**Architecture:** Python FastAPI microservice with LangGraph state machine (understand → clarify/search → format/relax). Agent calls Java backend REST APIs as tools, returns `{ text, instructions, suggestions }` to the Vue 3 frontend. Frontend `useAgentChat.ts` replaced with real HTTP calls; `instructions` dispatch to Pinia stores for map effects.

**Tech Stack:** Python 3.12, FastAPI, LangGraph, langchain-openai, httpx (async), Pydantic; Vue 3 + TypeScript + MapLibre GL JS (existing); Docker Compose.

---

## File Structure Map

```
agent-service/                        # NEW — Python microservice
├── pyproject.toml                    # Dependencies + project metadata
├── Dockerfile                        # Python container
├── src/
│   ├── main.py                       # FastAPI app, POST /api/agent/chat endpoint
│   ├── config.py                     # Pydantic Settings (LLM URL, API key, Java base URL)
│   ├── state.py                      # AgentState TypedDict
│   ├── graph.py                      # LangGraph StateGraph compilation
│   ├── nodes/
│   │   ├── understand.py             # LLM intent + constraint extraction
│   │   ├── clarify.py                # Missing-field clarification question generation
│   │   ├── search.py                 # Parallel tool dispatch to Java API
│   │   ├── relax.py                  # Constraint relaxation strategy
│   │   └── format_reply.py           # Generate {text, instructions, suggestions}
│   └── tools/
│       ├── __init__.py               # Tool registry
│       ├── station_search.py         # GET /api/stations/search?q=
│       ├── train_query.py            # GET /api/trains/{no}/route
│       ├── transfer_search.py        # POST /api/transfer/search
│       ├── isochrone.py              # POST /api/isochrone
│       └── timetable.py              # GET /api/stations/{id}
└── tests/
    ├── test_understand.py
    ├── test_relax.py
    └── test_format_reply.py

railway-frontend/src/
├── types/agent.ts                    # MODIFY — add AgentInstruction, extend AgentMessageContent
├── api/agentApi.ts                   # NEW — POST /api/agent/chat
├── stores/agentStore.ts              # MODIFY — add dispatchInstruction action
├── composables/
│   ├── useAgentChat.ts               # MODIFY — replace mock with real API + instruction dispatch
│   └── useTrainAnimation.ts          # NEW — dashed flowing line + signal pulse animation
└── components/map/
    └── TrainRouteLayer.vue           # NEW — MapLibre GeoJSON layer with animated dash pattern

docker-compose.yml                    # MODIFY — add agent-service container
```

---

### Task 1: Agent Service Project Skeleton

**Files:**
- Create: `agent-service/pyproject.toml`
- Create: `agent-service/src/__init__.py`
- Create: `agent-service/src/config.py`
- Create: `agent-service/src/state.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "railway-agent"
version = "0.1.0"
description = "RailwayMap Agent — LLM-driven natural language railway assistant"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "langgraph>=0.2.0",
    "langchain-openai>=0.2.0",
    "langchain-core>=0.3.0",
    "httpx>=0.27.0",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
]

[project.optional-dependencies]
dev = ["pytest>=8", "pytest-asyncio>=0.24", "httpx>=0.27"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

- [ ] **Step 2: Create agent-service/src/__init__.py**

```python
# railway-agent — RailwayMap natural language assistant
```

- [ ] **Step 3: Create config.py**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "AGENT_", "env_file": ".env", "extra": "ignore"}

    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = "sk-placeholder"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.0

    java_base_url: str = "http://app:8080"

    session_ttl_minutes: int = 30
    max_relax_rounds: int = 3


settings = Settings()
```

- [ ] **Step 4: Create state.py**

```python
from typing import TypedDict, NotRequired


class AgentState(TypedDict):
    session_id: str
    messages: list[dict]          # {role: "user"|"agent", content: str}
    user_input: str
    intent: str | None            # route_planning|isochrone|station_query|train_query|timetable_query|clarify
    constraints: dict | None      # {from, to, via, trainTypes, maxTransfers, dMax, tStart, tEnd, ...}
    missing: list[str]            # required fields not yet provided
    tool_results: list[dict]      # [{tool, params, result, error}]
    reply_text: str
    instructions: list[dict]      # [{action, ...params}]
    suggestions: list[str]
    relax_history: list[dict]     # [{original_constraints, relaxed_constraints, result_count}]
```

- [ ] **Step 5: Commit**

```bash
git add agent-service/
git commit -m "feat: agent service project skeleton — config, state, pyproject.toml"
```

---

### Task 2: Tool Layer — Station & Train Tools

**Files:**
- Create: `agent-service/src/tools/__init__.py`
- Create: `agent-service/src/tools/station_search.py`
- Create: `agent-service/src/tools/train_query.py`

- [ ] **Step 1: Create tools/__init__.py with tool registry**

```python
from .station_search import search_stations, get_station_detail
from .train_query import get_train_route
from .transfer_search import search_transfer
from .isochrone import get_isochrone
from .timetable import get_station_timetable

ALL_TOOLS = {
    "search_stations": search_stations,
    "get_station_detail": get_station_detail,
    "get_train_route": get_train_route,
    "search_transfer": search_transfer,
    "get_isochrone": get_isochrone,
    "get_station_timetable": get_station_timetable,
}
```

- [ ] **Step 2: Create station_search.py**

```python
import httpx
from ..config import settings


async def search_stations(query: str) -> dict:
    """Search stations by name/pinyin. Returns {stations: [...], count: N}."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{settings.java_base_url}/api/stations/search",
            params={"q": query},
        )
        resp.raise_for_status()
        data = resp.json()
        return {"tool": "search_stations", "stations": data if isinstance(data, list) else data.get("data", []), "count": len(data) if isinstance(data, list) else 0}


async def get_station_detail(station_id: str) -> dict:
    """Get station detail including passing trains."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{settings.java_base_url}/api/stations/{station_id}",
        )
        resp.raise_for_status()
        return {"tool": "get_station_detail", "station": resp.json()}
```

- [ ] **Step 3: Create train_query.py**

```python
import httpx
from ..config import settings


async def get_train_route(train_no: str) -> dict:
    """Get train route with stops and schedule."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{settings.java_base_url}/api/trains/{train_no}/route",
        )
        resp.raise_for_status()
        return {"tool": "get_train_route", "train": resp.json()}
```

- [ ] **Step 4: Commit**

```bash
git add agent-service/src/tools/
git commit -m "feat: agent tool layer — station search and train query tools"
```

---

### Task 3: Tool Layer — Transfer, Isochrone & Timetable Tools

**Files:**
- Create: `agent-service/src/tools/transfer_search.py`
- Create: `agent-service/src/tools/isochrone.py`
- Create: `agent-service/src/tools/timetable.py`

- [ ] **Step 1: Create transfer_search.py**

```python
import httpx
from ..config import settings


async def search_transfer(constraints: dict) -> dict:
    """Call POST /api/transfer/search with structured constraints."""
    async with httpx.AsyncClient(timeout=30) as client:
        body = {
            "from": constraints.get("from"),
            "to": constraints.get("to"),
        }
        if constraints.get("via"):
            body["waypoints"] = [constraints["via"]]
        if constraints.get("maxTransfers") is not None:
            body["maxTransfers"] = constraints["maxTransfers"]
        if constraints.get("trainTypes"):
            body["preferTrainTypes"] = constraints["trainTypes"]
        if constraints.get("dMax"):
            body["maxSegmentDuration"] = constraints["dMax"]
        if constraints.get("tStart") or constraints.get("tEnd"):
            body["departAfter"] = _minutes_to_time(constraints.get("tStart"))
            body["arriveBefore"] = _minutes_to_time(constraints.get("tEnd"))

        resp = await client.post(
            f"{settings.java_base_url}/api/transfer/search",
            json=body,
        )
        resp.raise_for_status()
        data = resp.json()
        routes = data if isinstance(data, list) else data.get("data", data.get("routes", []))
        return {"tool": "search_transfer", "params": body, "routes": routes, "count": len(routes)}


def _minutes_to_time(minutes: int | None) -> str | None:
    if minutes is None:
        return None
    h, m = divmod(minutes, 60)
    return f"{h:02d}:{m:02d}"
```

- [ ] **Step 2: Create isochrone.py**

```python
import httpx
from ..config import settings


async def get_isochrone(station_id: str, hours: float) -> dict:
    """Call POST /api/isochrone to get reachable stations within N hours."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{settings.java_base_url}/api/isochrone",
            json={"stationId": station_id, "hours": hours},
        )
        resp.raise_for_status()
        data = resp.json()
        return {"tool": "get_isochrone", "stationId": station_id, "hours": hours, "result": data}
```

- [ ] **Step 3: Create timetable.py**

```python
import httpx
from ..config import settings


async def get_station_timetable(station_id: str) -> dict:
    """Get all trains passing through a station (timetable)."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{settings.java_base_url}/api/stations/{station_id}",
        )
        resp.raise_for_status()
        return {"tool": "get_station_timetable", "station": resp.json()}
```

- [ ] **Step 4: Commit**

```bash
git add agent-service/src/tools/
git commit -m "feat: agent tool layer — transfer, isochrone, timetable tools"
```

---

### Task 4: LangGraph Nodes — Understand

**Files:**
- Create: `agent-service/src/nodes/__init__.py`
- Create: `agent-service/src/nodes/understand.py`

- [ ] **Step 1: Create nodes/__init__.py**

```python
from .understand import understand
from .clarify import clarify
from .search import search
from .relax import relax
from .format_reply import format_reply

__all__ = ["understand", "clarify", "search", "relax", "format_reply"]
```

- [ ] **Step 2: Create understand.py with LLM call for intent + constraint extraction**

```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import json

from ..state import AgentState
from ..config import settings

SYSTEM_PROMPT = """你是中国铁路助手，负责理解用户的自然语言出行需求并提取结构化信息。

输出严格的 JSON，格式如下：
{
  "intent": "route_planning | isochrone | station_query | train_query | timetable_query | clarify",
  "constraints": {
    "from": "出发站名或城市（如北京）",
    "to": "目的站名或城市（如广州南）",
    "via": "中转站名或null",
    "trainTypes": ["G", "D", ...] 或 [],
    "maxTransfers": 数字或null,
    "dMax": 单段最大时长（分钟）或null,
    "tStart": 出发时段起始（分钟，0-1440）或null,
    "tEnd": 到达时段截止（分钟，0-1440）或null,
    "hours": 等时圈时间（小时）或null
  },
  "missing": ["from", "to", ...]  列出尚未提供的必填字段（route_planning 至少需要 from 和 to；isochrone 需要起点站和 hours；train_query 需要车次号）
}

时间量化规则：
- "早上" = tStart: 360, "上午" = tStart: 480, "下午" = tStart: 720, "晚上" = tStart: 1080
- "白天" = tStart: 360, tEnd: 1080
- "不太久" = dMax: 240 (4小时), "短途" = dMax: 180 (3小时)
- "不要太累" = dMax: 240, 降低 maxTransfers

意图分类：
- route_planning: 用户想从A到B（可能带条件）
- isochrone: "从X出发能到哪"、"X周边"、"X小时圈"
- station_query: 查某个车站信息
- train_query: 查特定车次（含字母+数字的车次号）
- timetable_query: 查某站所有经停车次时刻表
- clarify: 意图不明或信息严重不足，需要反问

只输出 JSON，不要多余的文字。"""


def build_llm():
    return ChatOpenAI(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        temperature=settings.llm_temperature,
    )


async def understand(state: AgentState) -> dict:
    llm = build_llm()
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=state["user_input"]),
    ]
    response = await llm.ainvoke(messages)
    raw = response.content.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {
            "intent": "clarify",
            "constraints": None,
            "missing": ["_parse_error"],
            "reply_text": "抱歉，我没能理解你的意思。能换个说法吗？",
            "instructions": [],
            "suggestions": ["查询车次", "查询车站", "路径规划"],
        }

    return {
        "intent": parsed.get("intent", "clarify"),
        "constraints": parsed.get("constraints"),
        "missing": parsed.get("missing", []),
    }
```

- [ ] **Step 3: Commit**

```bash
git add agent-service/src/nodes/
git commit -m "feat: agent node — LLM intent classification and constraint extraction"
```

---

### Task 5: LangGraph Nodes — Clarify & Search

**Files:**
- Create: `agent-service/src/nodes/clarify.py`
- Create: `agent-service/src/nodes/search.py`

- [ ] **Step 1: Create clarify.py**

```python
import asyncio
import httpx
from ..state import AgentState
from ..config import settings

CLARIFY_TEMPLATES = {
    "from": "请问你想从哪里出发？",
    "to": "请问你的目的地是哪里？",
    "station_query": "你想查询哪个车站的信息？",
    "train_query": "你想查询哪趟车次？请输入车次号（如G1、D301）。",
    "hours": "你想查询几小时内的等时圈？",
    "from_station": "你想从哪个车站出发？",
}

DIRECTION_QUESTIONS = [
    "你可以描述一下想去的大致方向或城市吗？",
    "有没有特别想经过的城市？",
]


async def _resolve_ambiguous_station(name: str) -> dict | None:
    """Check if station name is ambiguous by calling search API."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{settings.java_base_url}/api/stations/search",
            params={"q": name},
        )
        resp.raise_for_status()
        data = resp.json()
        results = data if isinstance(data, list) else data.get("data", [])
        if len(results) > 1:
            return {"query": name, "candidates": [r.get("name") for r in results[:5]]}
        return None


async def clarify(state: AgentState) -> dict:
    missing = state.get("missing", [])
    reply_parts = []

    # Check for ambiguous station names first
    constraints = state.get("constraints") or {}
    ambiguous = []
    for field in ("from", "to", "via"):
        if constraints.get(field) and field not in missing:
            result = await _resolve_ambiguous_station(constraints[field])
            if result:
                ambiguous.append(result)

    if ambiguous:
        for a in ambiguous:
            candidates = "、".join(a["candidates"])
            reply_parts.append(f"「{a['query']}」有多个车站：{candidates}。你指的是哪个？")
    else:
        for field in missing:
            template = CLARIFY_TEMPLATES.get(field)
            if template:
                reply_parts.append(template)

    if not reply_parts:
        reply_parts.append("我没能完全理解你的需求，能再详细说说吗？")

    suggestions = [
        "查询车次",
        "查询车站",
        "路径规划",
    ]

    return {
        "reply_text": "\n\n".join(reply_parts),
        "instructions": [],
        "suggestions": suggestions,
    }
```

- [ ] **Step 2: Create search.py**

```python
import asyncio
from ..state import AgentState
from ..tools import ALL_TOOLS


async def search(state: AgentState) -> dict:
    intent = state.get("intent", "clarify")
    constraints = state.get("constraints") or {}
    tasks = []

    if intent == "station_query" or intent == "timetable_query":
        name = constraints.get("stationName") or constraints.get("from")
        if name:
            tasks.append(("search_stations", ALL_TOOLS["search_stations"](name)))
        elif constraints.get("stationId"):
            tasks.append(("get_station_detail", ALL_TOOLS["get_station_detail"](constraints["stationId"])))

    elif intent == "train_query":
        train_no = constraints.get("trainNo") or constraints.get("from")
        if train_no:
            tasks.append(("get_train_route", ALL_TOOLS["get_train_route"](train_no)))

    elif intent == "isochrone":
        station_id = constraints.get("stationId")
        hours = constraints.get("hours", 4)
        if station_id:
            tasks.append(("get_isochrone", ALL_TOOLS["get_isochrone"](station_id, hours)))
        # Also resolve station if we have name but not ID
        if not station_id and constraints.get("stationName"):
            tasks.append(("search_stations", ALL_TOOLS["search_stations"](constraints["stationName"])))

    elif intent == "route_planning":
        if constraints.get("from") and constraints.get("to"):
            tasks.append(("search_transfer", ALL_TOOLS["search_transfer"](constraints)))

    # Run all tasks in parallel
    tool_results = []
    if tasks:
        names, coros = zip(*tasks)
        results = await asyncio.gather(*coros, return_exceptions=True)
        for name, result in zip(names, results):
            if isinstance(result, Exception):
                tool_results.append({"tool": name, "params": {}, "result": None, "error": str(result)})
            else:
                tool_results.append(result)

    return {"tool_results": tool_results}
```

- [ ] **Step 3: Commit**

```bash
git add agent-service/src/nodes/
git commit -m "feat: agent nodes — clarify (station disambiguation) and search (parallel tool dispatch)"
```

---

### Task 6: LangGraph Nodes — Relax & Format Reply

**Files:**
- Create: `agent-service/src/nodes/relax.py`
- Create: `agent-service/src/nodes/format_reply.py`

- [ ] **Step 1: Create relax.py**

```python
from ..state import AgentState
from ..config import settings

# Relaxation priority: remove via → loosen D_max → increase N_max → loosen T_window
RELAX_STEPS = [
    ("via", "remove", "去掉中转站约束"),
    ("dMax", "loosen", "放宽单段时长限制"),
    ("maxTransfers", "increase", "增加允许的换乘次数"),
    ("tStart_tEnd", "remove", "放宽出发/到达时段限制"),
]


async def relax(state: AgentState) -> dict:
    relax_history = state.get("relax_history", [])
    constraints = state.get("constraints", {})
    original = dict(constraints)

    round_idx = len(relax_history)

    if round_idx >= settings.max_relax_rounds:
        return {
            "relax_history": relax_history,
            "constraints": constraints,
            "relax_exhausted": True,
        }

    step = RELAX_STEPS[min(round_idx, len(RELAX_STEPS) - 1)]
    field, action, description = step

    relaxed = dict(constraints)

    if field == "via":
        relaxed.pop("via", None)
    elif field == "dMax":
        current = relaxed.get("dMax", 240)
        relaxed["dMax"] = min(current * 2, 720)  # double, max 12h
    elif field == "maxTransfers":
        current = relaxed.get("maxTransfers", 2)
        relaxed["maxTransfers"] = current + 1
    elif field == "tStart_tEnd":
        relaxed.pop("tStart", None)
        relaxed.pop("tEnd", None)

    relax_history.append({
        "round": round_idx + 1,
        "original_constraints": original,
        "relaxed_constraints": relaxed,
        "description": description,
    })

    return {
        "constraints": relaxed,
        "relax_history": relax_history,
        "relax_exhausted": False,
    }


def format_relax_diff(relax_history: list[dict]) -> str:
    """Generate human-readable explanation of what was relaxed and why."""
    if not relax_history:
        return ""
    parts = ["\n\n按你的条件没找到结果，我尝试放宽了约束："]
    for entry in relax_history:
        parts.append(f"• {entry['description']}")
    return "\n".join(parts)
```

- [ ] **Step 2: Create format_reply.py**

```python
from ..state import AgentState


async def format_reply(state: AgentState) -> dict:
    intent = state.get("intent", "clarify")
    tool_results = state.get("tool_results", [])
    relax_history = state.get("relax_history", [])
    constraints = state.get("constraints") or {}
    instructions = []
    suggestions = []

    if intent == "station_query" or intent == "timetable_query":
        reply_text, instructions = _format_station_result(tool_results, intent)

    elif intent == "train_query":
        reply_text, instructions = _format_train_result(tool_results)

    elif intent == "route_planning":
        reply_text, instructions = _format_route_result(tool_results, relax_history, constraints)
        suggestions = ["只看高铁", "最少换乘", "尝试其他时间段"]

    elif intent == "isochrone":
        reply_text, instructions = _format_isochrone_result(tool_results, constraints)
        suggestions = ["细看哪个方向？", "从这些城市中选一个目的地规划路线"]

    else:
        reply_text = "有什么我可以帮你的？"

    return {
        "reply_text": reply_text,
        "instructions": instructions,
        "suggestions": suggestions,
    }


def _format_station_result(tool_results: list[dict], intent: str) -> tuple[str, list[dict]]:
    for r in tool_results:
        if r.get("tool") in ("search_stations", "get_station_detail", "get_station_timetable"):
            station = r.get("station") or (r.get("stations", [None])[0] if r.get("stations") else None)
            if not station:
                continue
            name = station.get("name", "未知站")
            city = station.get("city", "")
            sid = station.get("id")
            instructions = [
                {"action": "flyToStation", "stationId": str(sid)},
                {"action": "openPanel", "panel": "station"},
            ]
            if intent == "timetable_query":
                instructions.append({"action": "openModal", "modal": "timetable", "stationId": str(sid)})
            return f"**{name}**，{city}。详细信息已在左侧面板展示。", instructions

    return "抱歉，未找到该车站的信息。", []


def _format_train_result(tool_results: list[dict]) -> tuple[str, list[dict]]:
    for r in tool_results:
        if r.get("tool") == "get_train_route":
            train = r.get("train", {})
            no = train.get("trainNo", "")
            from_s = train.get("fromStation", {}).get("name", "")
            to_s = train.get("toStation", {}).get("name", "")
            stops = train.get("stops", [])
            return (
                f"**{no}** 次列车，{from_s} → {to_s}，共 {len(stops)} 站。\n\n线路已在地图高亮显示。",
                [
                    {"action": "highlightTrain", "trainNo": no},
                    {"action": "openPanel", "panel": "train"},
                ],
            )
    return "抱歉，未找到该车次的信息。", []


def _format_route_result(tool_results: list[dict], relax_history: list[dict], constraints: dict) -> tuple[str, list[dict]]:
    import textwrap
    from .relax import format_relax_diff

    for r in tool_results:
        if r.get("tool") == "search_transfer":
            routes = r.get("routes", [])
            count = r.get("count", len(routes))

            if count == 0:
                return "抱歉，没找到符合条件的中转路线。" + format_relax_diff(relax_history), []

            lines = [f"从 **{constraints.get('from')}** 到 **{constraints.get('to')}**，找到 {count} 条路线：\n"]
            for i, route in enumerate(routes[:5]):
                label = f"方案{i + 1}"
                seg_texts = []
                for seg in route.get("segments", []):
                    if seg.get("trainNo"):
                        seg_texts.append(f"{seg['from']} —{seg['trainNo']}→ {seg['to']}")
                lines.append(f"**{label}**：{' → '.join(seg_texts)}")
                dur = route.get("totalDurationMin", 0)
                transfers = route.get("transfers", 0)
                lines.append(f"⏱ {dur // 60}h{dur % 60}min · 🔄 {transfers} 次换乘\n")

            if count > 5:
                lines.append(f"\n…还有 {count - 5} 条方案，可以进一步筛选。")

            diff_text = format_relax_diff(relax_history)
            route_ids = [r.get("id", f"plan-{i}") for i, r in enumerate(routes[:3])]
            instructions = [{"action": "highlightRoutes", "routeIds": route_ids}]

            return "\n".join(lines) + diff_text, instructions

    return "抱歉，路线规划失败，请稍后重试。", []


def _format_isochrone_result(tool_results: list[dict], constraints: dict) -> tuple[str, list[dict]]:
    for r in tool_results:
        if r.get("tool") == "get_isochrone":
            result = r.get("result", {})
            station_id = r.get("stationId", "")
            hours = r.get("hours", 0)
            groups = result.get("directionGroups", {})  # expected: {"east": [cities], "south": [...], ...}
            total = result.get("totalReachable", 0)

            if not groups:
                return f"从该站出发 {hours} 小时内可达约 {total} 个站点。", [
                    {"action": "highlightIsochrone", "stationId": str(station_id)},
                ]

            dir_names = {"east": "东", "south": "南", "west": "西", "north": "北",
                         "northeast": "东北", "northwest": "西北", "southeast": "东南", "southwest": "西南"}
            parts = []
            for d, cities in groups.items():
                label = dir_names.get(d, d)
                if cities:
                    example = cities[0] if isinstance(cities[0], str) else cities[0].get("name", "")
                    parts.append(f"往**{label}**（{example}方向）{len(cities)} 站")

            return (
                f"从该站出发 **{hours}** 小时内可达 {total} 个站点：\n\n" + "\n".join(parts) + "\n\n你想去哪个方向？我可以帮你规划具体路线。",
                [
                    {"action": "highlightIsochrone", "stationId": str(station_id)},
                ],
            )

    return "等时圈查询暂不可用，请稍后再试。", []
```

- [ ] **Step 3: Commit**

```bash
git add agent-service/src/nodes/
git commit -m "feat: agent nodes — constraint relaxation and reply formatting with frontend instructions"
```

---

### Task 7: LangGraph Compilation & FastAPI Entry Point

**Files:**
- Create: `agent-service/src/graph.py`
- Create: `agent-service/src/main.py`

- [ ] **Step 1: Create graph.py**

```python
from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import understand, clarify, search, relax, format_reply


def should_clarify(state: AgentState) -> str:
    if state.get("intent") == "clarify" or state.get("missing"):
        return "clarify"
    return "search"


def has_results(state: AgentState) -> str:
    tool_results = state.get("tool_results", [])
    for r in tool_results:
        if r.get("tool") == "search_transfer":
            if r.get("count", 0) == 0:
                return "no_result"
        elif r.get("tool") == "get_isochrone":
            if r.get("result", {}).get("totalReachable", 0) == 0:
                return "no_result"
    if tool_results and not any(r.get("error") for r in tool_results):
        return "format"
    if not tool_results:
        return "format"
    return "format"


def should_relax(state: AgentState) -> str:
    if state.get("intent") != "route_planning":
        return "format"
    if state.get("relax_exhausted"):
        return "format"
    return "relax"


def build_graph() -> StateGraph:
    workflow = StateGraph(AgentState)

    workflow.add_node("understand", understand)
    workflow.add_node("clarify", clarify)
    workflow.add_node("search", search)
    workflow.add_node("relax", relax)
    workflow.add_node("format_reply", format_reply)

    workflow.set_entry_point("understand")

    workflow.add_conditional_edges(
        "understand",
        should_clarify,
        {"clarify": "clarify", "search": "search"},
    )
    workflow.add_edge("clarify", END)

    workflow.add_conditional_edges(
        "search",
        has_results,
        {"format": "format_reply", "no_result": "relax"},
    )
    workflow.add_conditional_edges(
        "relax",
        should_relax,
        {"relax": "search", "format": "format_reply"},
    )
    workflow.add_edge("format_reply", END)

    return workflow.compile()


graph = build_graph()
```

- [ ] **Step 2: Create main.py**

```python
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .state import AgentState
from .graph import graph
from .config import settings


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str


class ChatResponse(BaseModel):
    session_id: str
    text: str
    instructions: list[dict]
    suggestions: list[str]


sessions: dict[str, AgentState] = {}


def get_or_create_session(session_id: str | None) -> tuple[str, AgentState]:
    sid = session_id or str(uuid.uuid4())
    if sid not in sessions:
        sessions[sid] = AgentState(
            session_id=sid,
            messages=[],
            user_input="",
            intent=None,
            constraints=None,
            missing=[],
            tool_results=[],
            reply_text="",
            instructions=[],
            suggestions=[],
            relax_history=[],
        )
    return sid, sessions[sid]


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Cleanup expired sessions on shutdown
    sessions.clear()


app = FastAPI(title="RailwayMap Agent", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/agent/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(400, "message is required")

    sid, state = get_or_create_session(req.session_id)

    # Update state for this turn
    state["user_input"] = req.message.strip()
    state["messages"].append({"role": "user", "content": req.message.strip()})
    state["tool_results"] = []
    state["instructions"] = []
    state["suggestions"] = []
    state["reply_text"] = ""

    # Run the graph
    result = await graph.ainvoke(state)

    # Merge results back into state
    sessions[sid] = {**state, **result}

    reply = sessions[sid].get("reply_text", "")
    instructions = sessions[sid].get("instructions", [])
    suggestions = sessions[sid].get("suggestions", [])

    sessions[sid]["messages"].append({"role": "agent", "content": reply})

    return ChatResponse(
        session_id=sid,
        text=reply,
        instructions=instructions,
        suggestions=suggestions,
    )


@app.get("/api/agent/health")
async def health():
    return {"status": "ok", "model": settings.llm_model}
```

- [ ] **Step 3: Commit**

```bash
git add agent-service/src/main.py agent-service/src/graph.py
git commit -m "feat: agent graph compilation and FastAPI entry point"
```

---

### Task 8: Docker & Docker Compose

**Files:**
- Create: `agent-service/Dockerfile`
- Modify: `docker-compose.yml`

- [ ] **Step 1: Create agent-service/Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY src/ ./src/

ENV AGENT_LLM_BASE_URL=https://api.openai.com/v1
ENV AGENT_JAVA_BASE_URL=http://app:8080

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Add agent-service to docker-compose.yml**

Add this new service block after the `app` service and before `frontend`:

```yaml
  agent:
    build:
      context: ./agent-service
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      AGENT_LLM_BASE_URL: ${AGENT_LLM_BASE_URL:-https://api.openai.com/v1}
      AGENT_LLM_API_KEY: ${AGENT_LLM_API_KEY}
      AGENT_LLM_MODEL: ${AGENT_LLM_MODEL:-gpt-4o-mini}
      AGENT_JAVA_BASE_URL: http://app:8080
    depends_on:
      - app
    restart: unless-stopped
```

Also update the `frontend` service — add `agent` to depends_on and proxy `/api/agent` to the agent service. Update `nginx.conf` later if needed (task for frontend configuration).

- [ ] **Step 3: Update frontend nginx config (if exists)**

Check if `nginx.conf` exists and add agent proxy:

```nginx
location /api/agent {
    proxy_pass http://agent:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

- [ ] **Step 4: Commit**

```bash
git add agent-service/Dockerfile docker-compose.yml
git commit -m "feat: docker deployment for agent-service"
```

---

### Task 9: Frontend — Types and API Client

**Files:**
- Modify: `railway-frontend/src/types/agent.ts`
- Create: `railway-frontend/src/api/agentApi.ts`

- [ ] **Step 1: Extend types/agent.ts with instruction types**

Add after the existing `QuickSuggestion` interface (at end of file):

```typescript
/** Frontend instruction dispatched from agent response */
export interface AgentInstruction {
  action: 'flyToStation' | 'highlightTrain' | 'highlightRoutes' | 'highlightIsochrone'
    | 'openPanel' | 'openModal' | 'clearHighlights'
  [key: string]: unknown
}

export interface FlyToStationInstruction extends AgentInstruction {
  action: 'flyToStation'
  stationId: string
}

export interface HighlightTrainInstruction extends AgentInstruction {
  action: 'highlightTrain'
  trainNo: string
}

export interface HighlightRoutesInstruction extends AgentInstruction {
  action: 'highlightRoutes'
  routeIds: string[]
}

export interface HighlightIsochroneInstruction extends AgentInstruction {
  action: 'highlightIsochrone'
  stationId: string
}

export interface OpenPanelInstruction extends AgentInstruction {
  action: 'openPanel'
  panel: 'station' | 'train' | 'routePlan'
}

export interface OpenModalInstruction extends AgentInstruction {
  action: 'openModal'
  modal: 'timetable'
  stationId: string
}
```

Also add `instructions` and `suggestions` to `AgentMessageContent`:

```typescript
export interface AgentMessageContent {
  text: string
  routePlans?: RoutePlan[]
  stationId?: string
  trainNo?: string
  city?: string
  instructions?: AgentInstruction[]
  suggestions?: string[]
}
```

- [ ] **Step 2: Create api/agentApi.ts**

```typescript
import apiClient from './client'
import type { AgentInstruction } from '../types/agent'

export interface AgentChatRequest {
  session_id?: string
  message: string
}

export interface AgentChatResponse {
  session_id: string
  text: string
  instructions: AgentInstruction[]
  suggestions: string[]
}

export const agentApi = {
  chat(req: AgentChatRequest) {
    return apiClient.post<unknown, AgentChatResponse>('/agent/chat', req)
  },
}
```

Note: The Vite dev server needs to proxy `/api/agent` to the agent service. This will be done in the vite config update step.

- [ ] **Step 3: Commit**

```bash
git add railway-frontend/src/types/agent.ts railway-frontend/src/api/agentApi.ts
git commit -m "feat: frontend agent types and API client for real agent service"
```

---

### Task 10: Frontend — Rewrite useAgentChat.ts

**Files:**
- Modify: `railway-frontend/src/composables/useAgentChat.ts`
- Modify: `railway-frontend/src/stores/agentStore.ts`

- [ ] **Step 1: Add dispatchInstruction action to agentStore.ts**

Add this action inside `useAgentStore` (before `return`):

```typescript
  function dispatchInstruction(instruction: AgentInstruction) {
    const mapStore = useMapStore()
    const stationStore = useStationStore()
    const trainStore = useTrainStore()
    const routePlanStore = useRoutePlanStore()

    switch (instruction.action) {
      case 'flyToStation': {
        const { stationId } = instruction as FlyToStationInstruction
        mapStore.setFocusStation(stationId)
        stationStore.setCurrentStation(stationId)
        break
      }
      case 'highlightTrain': {
        const { trainNo } = instruction as HighlightTrainInstruction
        mapStore.setFocusTrain(trainNo)
        trainStore.setCurrentTrain(trainNo)
        break
      }
      case 'highlightRoutes': {
        const { routeIds } = instruction as HighlightRoutesInstruction
        routePlanStore.setActivePlanIds(routeIds)
        break
      }
      case 'highlightIsochrone': {
        const { stationId } = instruction as HighlightIsochroneInstruction
        mapStore.setFocusStation(stationId)
        break
      }
      case 'openPanel': {
        // Panel opening handled by App.vue watch on stores
        break
      }
      case 'openModal': {
        // Modal opening handled by component
        break
      }
      case 'clearHighlights': {
        mapStore.clearAllFocus()
        routePlanStore.clear()
        break
      }
    }
  }
```

Add `dispatchInstruction` to the return object of `useAgentStore()`.

Add this import at the top of agentStore.ts:
```typescript
import type { AgentInstruction, FlyToStationInstruction, HighlightTrainInstruction, HighlightRoutesInstruction, HighlightIsochroneInstruction } from '../types/agent'
import { useMapStore } from './mapStore'
import { useStationStore } from './stationStore'
import { useTrainStore } from './trainStore'
import { useRoutePlanStore } from './routePlanStore'
```

Also add `setActivePlanIds` to routePlanStore (currently it only has `filterByConstraint`):

Add to `railway-frontend/src/stores/routePlanStore.ts`:
```typescript
  function setActivePlanIds(ids: string[]) {
    activePlanIndices.value = ids
      .map(id => plans.value.findIndex(p => p.id === id))
      .filter(i => i !== -1)
  }
```

And add to its return object.

- [ ] **Step 2: Rewrite useAgentChat.ts**

Replace the entire file:

```typescript
import { useAgentStore } from '../stores/agentStore'
import { agentApi } from '../api/agentApi'

let sessionId: string | null = null

export function useAgentChat() {
  const agentStore = useAgentStore()

  async function sendMessage(text: string) {
    agentStore.addMessage('user', { text })
    agentStore.setProcessing(true)

    try {
      const response = await agentApi.chat({
        session_id: sessionId,
        message: text,
      })

      sessionId = response.session_id

      agentStore.addMessage('agent', {
        text: response.text,
        instructions: response.instructions,
        suggestions: response.suggestions,
      })

      // Dispatch instructions to drive map interactions
      for (const instruction of response.instructions) {
        agentStore.dispatchInstruction(instruction)
      }

      // Update quick suggestions for follow-up
      if (response.suggestions.length > 0) {
        agentStore.setQuickSuggestions(
          response.suggestions.map(s => ({ label: s, prompt: s }))
        )
      }
    } catch (err) {
      agentStore.addMessage('agent', {
        text: `抱歉，请求失败：${err instanceof Error ? err.message : '未知错误'}。请稍后重试。`,
      })
    } finally {
      agentStore.setProcessing(false)
    }
  }

  return { sendMessage }
}
```

- [ ] **Step 3: Add setQuickSuggestions to agentStore.ts**

```typescript
  const quickSuggestions = ref<QuickSuggestion[]>(defaultQuickSuggestions)

  function setQuickSuggestions(sugs: QuickSuggestion[]) {
    quickSuggestions.value = sugs
  }
```

Update the AgentPanel to use `agentStore.quickSuggestions` instead of `agentStore.defaultQuickSuggestions`. Also add `quickSuggestions` and `setQuickSuggestions` to the return object.

- [ ] **Step 4: Update vite.config.ts to proxy agent requests**

Read the existing vite config and add the proxy rule:

```typescript
// In proxy section, add:
'/api/agent': {
  target: 'http://localhost:8000',
  changeOrigin: true,
},
```

- [ ] **Step 5: Commit**

```bash
git add railway-frontend/src/composables/useAgentChat.ts \
        railway-frontend/src/stores/agentStore.ts \
        railway-frontend/src/stores/routePlanStore.ts \
        railway-frontend/vite.config.ts
git commit -m "feat: replace agent mock with real API calls + instruction dispatch"
```

---

### Task 11: Frontend — Train Route Map Animation

**Files:**
- Create: `railway-frontend/src/composables/useTrainAnimation.ts`
- Create: `railway-frontend/src/components/map/TrainRouteLayer.vue`

- [ ] **Step 1: Create useTrainAnimation.ts**

```typescript
import { ref, watch, onUnmounted } from 'vue'
import type { Map } from 'maplibre-gl'
import type { RoutePlan, RouteSegment } from '../types/route'

const TRAIN_TYPE_COLORS: Record<string, string> = {
  'G': '#E53E3E',  // high-speed red
  'D': '#ED8936',  // bullet orange
  'C': '#38A169',  // intercity green
  'Z': '#3182CE',  // direct express blue
  'T': '#3182CE',  // express blue
  'K': '#3182CE',  // fast blue
}

const DASH_ARRAY = [8, 6]  // 8px solid, 6px gap

export function useTrainAnimation(mapRef: { value: Map | null }) {
  const activeRoutes = ref<RoutePlan[]>([])
  const animating = ref(false)
  let animationFrameId: number | null = null
  let dashOffsets: number[] = []
  const speeds: number[] = [] // offset per frame per route

  function getTrainColor(trainNo: string | null): string {
    if (!trainNo) return '#A0AEC0'
    const prefix = trainNo.charAt(0).toUpperCase()
    return TRAIN_TYPE_COLORS[prefix] || '#A0AEC0'
  }

  function getSpeed(trainNo: string | null): number {
    if (!trainNo) return 0.3
    const prefix = trainNo.charAt(0).toUpperCase()
    if (prefix === 'G') return 1.2   // fastest
    if (prefix === 'D' || prefix === 'C') return 0.8
    return 0.4  // conventional
  }

  function startAnimation(routes: RoutePlan[]) {
    stopAnimation()
    activeRoutes.value = routes
    dashOffsets = routes.map(() => 0)
    speeds.length = 0
    routes.forEach(r => {
      const firstTrain = r.segments.find(s => s.trainNo)
      speeds.push(getSpeed(firstTrain?.trainNo ?? null))
    })
    animate()
  }

  function animate() {
    const map = mapRef.value
    if (!map || activeRoutes.value.length === 0) return

    for (let i = 0; i < activeRoutes.value.length; i++) {
      dashOffsets[i] = (dashOffsets[i] + speeds[i]) % (DASH_ARRAY[0] + DASH_ARRAY[1])
    }

    // Update paint properties via map.setPaintProperty
    // Each route gets a GeoJSON source with dasharray animation via line-dasharray offset
    // We use a custom property driven by JS since MapLibre native dash-offset is limited
    activeRoutes.value.forEach((route, i) => {
      const sourceId = `route-${route.id}`
      if (map.getLayer(`${sourceId}-line`)) {
        // Toggle between two dash arrays shifted by offset to simulate flow
        const offset = dashOffsets[i]
        const a = DASH_ARRAY[0]
        const b = DASH_ARRAY[1]
        map.setPaintProperty(`${sourceId}-line`, 'line-dasharray', [
          a, b, a, b + offset, a, b,
        ])
      }
    })

    animationFrameId = requestAnimationFrame(animate)
  }

  function stopAnimation() {
    if (animationFrameId !== null) {
      cancelAnimationFrame(animationFrameId)
      animationFrameId = null
    }
    activeRoutes.value = []
    dashOffsets = []
  }

  function getPulsePhase(): number {
    // Returns 0..1 cycling every 1.5 seconds
    return (Date.now() % 1500) / 1500
  }

  onUnmounted(() => stopAnimation())

  return {
    activeRoutes,
    animating,
    startAnimation,
    stopAnimation,
    getTrainColor,
    getSpeed,
    getPulsePhase,
    TRAIN_TYPE_COLORS,
  }
}
```

- [ ] **Step 2: Create TrainRouteLayer.vue**

```vue
<script setup lang="ts">
import { watch } from 'vue'
import type { RoutePlan } from '../../types/route'
import { useTrainAnimation } from '../../composables/useTrainAnimation'

const props = defineProps<{
  mapRef: { value: maplibregl.Map | null }
  routes: RoutePlan[]
}>()

const { startAnimation, stopAnimation, getTrainColor } = useTrainAnimation(props.mapRef)

watch(
  () => props.routes,
  (routes) => {
    stopAnimation()
    if (routes.length > 0) {
      addRouteSources(routes)
      startAnimation(routes)
    }
  },
  { deep: true },
)

function addRouteSources(routes: RoutePlan[]) {
  const map = props.mapRef.value
  if (!map) return

  routes.forEach((route, i) => {
    const sourceId = `route-${route.id}`
    const color = route.color || getTrainColor(route.segments[0]?.trainNo)

    // Collect all non-transfer segment coordinates
    const coords: [number, number][] = []
    route.segments.forEach(seg => {
      if (seg.coordinates) {
        coords.push(...seg.coordinates)
      }
    })

    if (coords.length < 2) return

    if (map.getSource(sourceId)) {
      (map.getSource(sourceId) as maplibregl.GeoJSONSource).setData({
        type: 'Feature',
        properties: {},
        geometry: { type: 'LineString', coordinates: coords },
      })
    } else {
      map.addSource(sourceId, {
        type: 'geojson',
        data: {
          type: 'Feature',
          properties: {},
          geometry: { type: 'LineString', coordinates: coords },
        },
      })

      map.addLayer({
        id: `${sourceId}-line`,
        type: 'line',
        source: sourceId,
        paint: {
          'line-color': color,
          'line-width': 3,
          'line-dasharray': [8, 6],
          'line-opacity': 0.9,
        },
      })

      // Station dots layer
      const stationCoords: maplibregl.GeoJSON.Feature[] = []
      route.segments.forEach((seg, idx) => {
        if (seg.coordinates && seg.coordinates.length > 0) {
          const firstCoord = seg.coordinates[0]
          stationCoords.push({
            type: 'Feature',
            properties: { isTerminal: idx === 0 || idx === route.segments.length - 1 },
            geometry: { type: 'Point', coordinates: firstCoord },
          })
        }
      })

      map.addSource(`${sourceId}-stops`, {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: stationCoords },
      })

      map.addLayer({
        id: `${sourceId}-stops`,
        type: 'circle',
        source: `${sourceId}-stops`,
        paint: {
          'circle-color': color,
          'circle-radius': [
            'case',
            ['get', 'isTerminal'], 8,
            5,
          ],
          'circle-stroke-width': [
            'case',
            ['get', 'isTerminal'], 2,
            0,
          ],
          'circle-stroke-color': '#fff',
          'circle-opacity': 0.9,
        },
      })
    }
  })
}
</script>

<template>
  <div />
</template>
```

- [ ] **Step 3: Commit**

```bash
git add railway-frontend/src/composables/useTrainAnimation.ts \
        railway-frontend/src/components/map/TrainRouteLayer.vue
git commit -m "feat: train route dash-flow animation and signal pulse effect"
```

---

### Task 12: Integration — Wire Everything Together

**Files:**
- Modify: `railway-frontend/src/App.vue`
- Modify: `railway-frontend/src/components/agent/AgentBubble.vue`
- Modify: `railway-frontend/src/App.vue` (watch agent instructions to trigger map effects)

- [ ] **Step 1: Add instruction rendering to AgentBubble.vue**

In AgentBubble's template, after the text rendering, add rendering for `suggestions` from the message content:

```vue
<!-- After the text content div, before timestamp -->
<div v-if="message.role === 'agent' && message.content.suggestions?.length" class="bubble-suggestions">
  <button
    v-for="sug in message.content.suggestions"
    :key="sug"
    class="bubble-suggestion-chip"
    @click="emit('quickReply', sug)"
  >
    {{ sug }}
  </button>
</div>
```

Add the `quickReply` emit to the component.

- [ ] **Step 2: Handle instructions in App.vue**

Add a watcher in App.vue (or in AgentPanel.vue) to handle `openModal` instructions:

```typescript
// In App.vue, watch the last agent message for instructions
watch(
  () => agentStore.messages[agentStore.messages.length - 1]?.content?.instructions,
  (instructions) => {
    if (!instructions) return
    for (const inst of instructions) {
      if (inst.action === 'openModal' && inst.modal === 'timetable') {
        // Open timetable modal
        showTimetableModal.value = true
        timetableStationId.value = inst.stationId as string
      }
    }
  },
  { deep: true },
)
```

- [ ] **Step 3: Verify build**

Run:
```bash
cd railway-frontend && npm run build
```
Expected: Build succeeds without TypeScript errors.

- [ ] **Step 4: Commit**

```bash
git add railway-frontend/src/App.vue \
        railway-frontend/src/components/agent/AgentBubble.vue
git commit -m "feat: wire agent instructions to frontend map and panel interactions"
```

---

### Task 13: Basic Tests for Agent Service

**Files:**
- Create: `agent-service/tests/__init__.py`
- Create: `agent-service/tests/test_understand.py`
- Create: `agent-service/tests/test_relax.py`
- Create: `agent-service/tests/test_format_reply.py`

- [ ] **Step 1: Create tests/test_understand.py**

```python
import pytest
from unittest.mock import AsyncMock, patch
from src.nodes.understand import understand
from src.state import AgentState


@pytest.mark.asyncio
async def test_understand_parses_valid_json():
    state = AgentState(
        session_id="test-1",
        messages=[],
        user_input="从北京到广州，高铁，换乘不超过1次",
        intent=None,
        constraints=None,
        missing=[],
        tool_results=[],
        reply_text="",
        instructions=[],
        suggestions=[],
        relax_history=[],
    )

    mock_response = AsyncMock()
    mock_response.content = '{"intent":"route_planning","constraints":{"from":"北京","to":"广州","trainTypes":["G"],"maxTransfers":1},"missing":[]}'

    with patch("src.nodes.understand.build_llm") as mock_llm:
        mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
        result = await understand(state)

    assert result["intent"] == "route_planning"
    assert result["constraints"]["from"] == "北京"
    assert result["constraints"]["to"] == "广州"


@pytest.mark.asyncio
async def test_understand_handles_malformed_json():
    state = AgentState(
        session_id="test-2", messages=[], user_input="...",
        intent=None, constraints=None, missing=[],
        tool_results=[], reply_text="", instructions=[], suggestions=[], relax_history=[],
    )

    mock_response = AsyncMock()
    mock_response.content = "not valid json at all"

    with patch("src.nodes.understand.build_llm") as mock_llm:
        mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
        result = await understand(state)

    assert result["intent"] == "clarify"
```

- [ ] **Step 2: Create tests/test_relax.py**

```python
import pytest
from src.nodes.relax import relax
from src.state import AgentState


@pytest.mark.asyncio
async def test_relax_removes_via_first():
    state = AgentState(
        session_id="t", messages=[], user_input="",
        intent="route_planning",
        constraints={"from": "北京", "to": "广州", "via": "武汉", "maxTransfers": 1},
        missing=[], tool_results=[], reply_text="", instructions=[], suggestions=[],
        relax_history=[],
    )

    result = await relax(state)
    assert "via" not in result["constraints"]
    assert len(result["relax_history"]) == 1
    assert "去掉中转站约束" in result["relax_history"][0]["description"]


@pytest.mark.asyncio
async def test_relax_exhausted_after_max_rounds():
    state = AgentState(
        session_id="t", messages=[], user_input="",
        intent="route_planning",
        constraints={"from": "北京", "to": "广州"},
        missing=[], tool_results=[], reply_text="", instructions=[], suggestions=[],
        relax_history=[
            {"round": 1, "original_constraints": {}, "relaxed_constraints": {}, "description": "r1"},
            {"round": 2, "original_constraints": {}, "relaxed_constraints": {}, "description": "r2"},
            {"round": 3, "original_constraints": {}, "relaxed_constraints": {}, "description": "r3"},
        ],
    )

    result = await relax(state)
    assert result.get("relax_exhausted") is True
```

- [ ] **Step 3: Create tests/test_format_reply.py**

```python
import pytest
from src.nodes.format_reply import format_reply, _format_route_result, _format_train_result
from src.state import AgentState


@pytest.mark.asyncio
async def test_format_route_result_empty():
    state = AgentState(
        session_id="t", messages=[], user_input="",
        intent="route_planning", constraints={"from": "北京", "to": "广州"},
        missing=[], instructions=[], suggestions=[],
        tool_results=[{"tool": "search_transfer", "params": {}, "routes": [], "count": 0}],
        reply_text="", relax_history=[],
    )

    result = await format_reply(state)
    assert "没找到" in result["reply_text"]


@pytest.mark.asyncio
async def test_format_route_result_with_routes():
    state = AgentState(
        session_id="t", messages=[], user_input="",
        intent="route_planning", constraints={"from": "北京", "to": "广州"},
        missing=[], instructions=[], suggestions=[],
        tool_results=[{
            "tool": "search_transfer",
            "params": {},
            "routes": [
                {
                    "id": "r1", "label": "方案一",
                    "segments": [
                        {"trainNo": "G1", "from": "北京南", "to": "广州南"}
                    ],
                    "totalDurationMin": 480, "transfers": 1,
                },
            ],
            "count": 1,
        }],
        reply_text="", relax_history=[],
    )

    result = await format_reply(state)
    assert "G1" in result["reply_text"]
    assert len(result["instructions"]) > 0
    assert result["instructions"][0]["action"] == "highlightRoutes"
```

- [ ] **Step 4: Run tests**

```bash
cd agent-service && pip install -e ".[dev]" && python -m pytest tests/ -v
```
Expected: 5 tests pass.

- [ ] **Step 5: Commit**

```bash
git add agent-service/tests/
git commit -m "test: agent understand, relax, and format_reply unit tests"
```

---

### Task 14: Final Verification

- [ ] **Step 1: Verify all files exist**

```bash
echo "=== Agent service ==="
find agent-service/src -name '*.py' | sort
echo ""
echo "=== Agent tests ==="
find agent-service/tests -name '*.py' | sort
echo ""
echo "=== Frontend changes ==="
ls railway-frontend/src/api/agentApi.ts
ls railway-frontend/src/composables/useTrainAnimation.ts
ls railway-frontend/src/components/map/TrainRouteLayer.vue
```
Expected: All paths exist without errors.

- [ ] **Step 2: Verify frontend TypeScript compilation**

```bash
cd railway-frontend && npx vue-tsc --noEmit 2>&1 | head -20
```
Expected: No type errors (or only pre-existing ones unrelated to our changes).

- [ ] **Step 3: Verify OpenSpec change is valid**

```bash
openspec validate agent-service
```
Expected: "Change 'agent-service' is valid"

- [ ] **Step 4: Final commit (if any fixes)**

```bash
git status
git add <any-fix-files>
git commit -m "chore: final integration verification and fixes"
```

---
```

<｜｜DSML｜｜parameter name="content" string="true"># Agent Service Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python Agent microservice (FastAPI + LangGraph) that replaces the frontend mock with LLM-driven natural language understanding, and wire it to drive map interactions via a frontend instruction system.

**Architecture:** Python FastAPI microservice with LangGraph state machine (understand → clarify/search → format/relax). Agent calls Java backend REST APIs as tools, returns `{ text, instructions, suggestions }` to the Vue 3 frontend. Frontend `useAgentChat.ts` replaced with real HTTP calls; `instructions` dispatch to Pinia stores for map effects.

**Tech Stack:** Python 3.12, FastAPI, LangGraph, langchain-openai, httpx (async), Pydantic; Vue 3 + TypeScript + MapLibre GL JS (existing); Docker Compose.

---

## File Structure Map

```
agent-service/                        # NEW — Python microservice
├── pyproject.toml                    # Dependencies + project metadata
├── Dockerfile                        # Python container
├── src/
│   ├── main.py                       # FastAPI app, POST /api/agent/chat endpoint
│   ├── config.py                     # Pydantic Settings (LLM URL, API key, Java base URL)
│   ├── state.py                      # AgentState TypedDict
│   ├── graph.py                      # LangGraph StateGraph compilation
│   ├── nodes/
│   │   ├── understand.py             # LLM intent + constraint extraction
│   │   ├── clarify.py                # Missing-field clarification question generation
│   │   ├── search.py                 # Parallel tool dispatch to Java API
│   │   ├── relax.py                  # Constraint relaxation strategy
│   │   └── format_reply.py           # Generate {text, instructions, suggestions}
│   └── tools/
│       ├── __init__.py               # Tool registry
│       ├── station_search.py         # GET /api/stations/search?q=
│       ├── train_query.py            # GET /api/trains/{no}/route
│       ├── transfer_search.py        # POST /api/transfer/search
│       ├── isochrone.py              # POST /api/isochrone
│       └── timetable.py              # GET /api/stations/{id}
└── tests/
    ├── test_understand.py
    ├── test_relax.py
    └── test_format_reply.py

railway-frontend/src/
├── types/agent.ts                    # MODIFY — add AgentInstruction, extend AgentMessageContent
├── api/agentApi.ts                   # NEW — POST /api/agent/chat
├── stores/agentStore.ts              # MODIFY — add dispatchInstruction action
├── composables/
│   ├── useAgentChat.ts               # MODIFY — replace mock with real API + instruction dispatch
│   └── useTrainAnimation.ts          # NEW — dashed flowing line + signal pulse animation
└── components/map/
    └── TrainRouteLayer.vue           # NEW — MapLibre GeoJSON layer with animated dash pattern

docker-compose.yml                    # MODIFY — add agent-service container
```

---

### Task 1: Agent Service Project Skeleton

**Files:**
- Create: `agent-service/pyproject.toml`
- Create: `agent-service/src/__init__.py`
- Create: `agent-service/src/config.py`
- Create: `agent-service/src/state.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "railway-agent"
version = "0.1.0"
description = "RailwayMap Agent — LLM-driven natural language railway assistant"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "langgraph>=0.2.0",
    "langchain-openai>=0.2.0",
    "langchain-core>=0.3.0",
    "httpx>=0.27.0",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
]

[project.optional-dependencies]
dev = ["pytest>=8", "pytest-asyncio>=0.24", "httpx>=0.27"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

- [ ] **Step 2: Create agent-service/src/__init__.py**

```python
# railway-agent — RailwayMap natural language assistant
```

- [ ] **Step 3: Create config.py**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "AGENT_", "env_file": ".env", "extra": "ignore"}

    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = "sk-placeholder"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.0

    java_base_url: str = "http://app:8080"

    session_ttl_minutes: int = 30
    max_relax_rounds: int = 3


settings = Settings()
```

- [ ] **Step 4: Create state.py**

```python
from typing import TypedDict, NotRequired


class AgentState(TypedDict):
    session_id: str
    messages: list[dict]          # {role: "user"|"agent", content: str}
    user_input: str
    intent: str | None            # route_planning|isochrone|station_query|train_query|timetable_query|clarify
    constraints: dict | None      # {from, to, via, trainTypes, maxTransfers, dMax, tStart, tEnd, ...}
    missing: list[str]            # required fields not yet provided
    tool_results: list[dict]      # [{tool, params, result, error}]
    reply_text: str
    instructions: list[dict]      # [{action, ...params}]
    suggestions: list[str]
    relax_history: list[dict]     # [{original_constraints, relaxed_constraints, result_count}]
```

- [ ] **Step 5: Commit**

```bash
git add agent-service/
git commit -m "feat: agent service project skeleton — config, state, pyproject.toml"
```

---

### Task 2: Tool Layer — Station & Train Tools

**Files:**
- Create: `agent-service/src/tools/__init__.py`
- Create: `agent-service/src/tools/station_search.py`
- Create: `agent-service/src/tools/train_query.py`

- [ ] **Step 1: Create tools/__init__.py with tool registry**

```python
from .station_search import search_stations, get_station_detail
from .train_query import get_train_route
from .transfer_search import search_transfer
from .isochrone import get_isochrone
from .timetable import get_station_timetable

ALL_TOOLS = {
    "search_stations": search_stations,
    "get_station_detail": get_station_detail,
    "get_train_route": get_train_route,
    "search_transfer": search_transfer,
    "get_isochrone": get_isochrone,
    "get_station_timetable": get_station_timetable,
}
```

- [ ] **Step 2: Create station_search.py**

```python
import httpx
from ..config import settings


async def search_stations(query: str) -> dict:
    """Search stations by name/pinyin. Returns {stations: [...], count: N}."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{settings.java_base_url}/api/stations/search",
            params={"q": query},
        )
        resp.raise_for_status()
        data = resp.json()
        return {"tool": "search_stations", "stations": data if isinstance(data, list) else data.get("data", []), "count": len(data) if isinstance(data, list) else 0}


async def get_station_detail(station_id: str) -> dict:
    """Get station detail including passing trains."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{settings.java_base_url}/api/stations/{station_id}",
        )
        resp.raise_for_status()
        return {"tool": "get_station_detail", "station": resp.json()}
```

- [ ] **Step 3: Create train_query.py**

```python
import httpx
from ..config import settings


async def get_train_route(train_no: str) -> dict:
    """Get train route with stops and schedule."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{settings.java_base_url}/api/trains/{train_no}/route",
        )
        resp.raise_for_status()
        return {"tool": "get_train_route", "train": resp.json()}
```

- [ ] **Step 4: Commit**

```bash
git add agent-service/src/tools/
git commit -m "feat: agent tool layer — station search and train query tools"
```

---

### Task 3: Tool Layer — Transfer, Isochrone & Timetable Tools

**Files:**
- Create: `agent-service/src/tools/transfer_search.py`
- Create: `agent-service/src/tools/isochrone.py`
- Create: `agent-service/src/tools/timetable.py`

- [ ] **Step 1: Create transfer_search.py**

```python
import httpx
from ..config import settings


async def search_transfer(constraints: dict) -> dict:
    """Call POST /api/transfer/search with structured constraints."""
    async with httpx.AsyncClient(timeout=30) as client:
        body = {
            "from": constraints.get("from"),
            "to": constraints.get("to"),
        }
        if constraints.get("via"):
            body["waypoints"] = [constraints["via"]]
        if constraints.get("maxTransfers") is not None:
            body["maxTransfers"] = constraints["maxTransfers"]
        if constraints.get("trainTypes"):
            body["preferTrainTypes"] = constraints["trainTypes"]
        if constraints.get("dMax"):
            body["maxSegmentDuration"] = constraints["dMax"]
        if constraints.get("tStart") or constraints.get("tEnd"):
            body["departAfter"] = _minutes_to_time(constraints.get("tStart"))
            body["arriveBefore"] = _minutes_to_time(constraints.get("tEnd"))

        resp = await client.post(
            f"{settings.java_base_url}/api/transfer/search",
            json=body,
        )
        resp.raise_for_status()
        data = resp.json()
        routes = data if isinstance(data, list) else data.get("data", data.get("routes", []))
        return {"tool": "search_transfer", "params": body, "routes": routes, "count": len(routes)}


def _minutes_to_time(minutes: int | None) -> str | None:
    if minutes is None:
        return None
    h, m = divmod(minutes, 60)
    return f"{h:02d}:{m:02d}"
```

- [ ] **Step 2: Create isochrone.py**

```python
import httpx
from ..config import settings


async def get_isochrone(station_id: str, hours: float) -> dict:
    """Call POST /api/isochrone to get reachable stations within N hours."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{settings.java_base_url}/api/isochrone",
            json={"stationId": station_id, "hours": hours},
        )
        resp.raise_for_status()
        data = resp.json()
        return {"tool": "get_isochrone", "stationId": station_id, "hours": hours, "result": data}
```

- [ ] **Step 3: Create timetable.py**

```python
import httpx
from ..config import settings


async def get_station_timetable(station_id: str) -> dict:
    """Get all trains passing through a station (timetable)."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{settings.java_base_url}/api/stations/{station_id}",
        )
        resp.raise_for_status()
        return {"tool": "get_station_timetable", "station": resp.json()}
```

- [ ] **Step 4: Commit**

```bash
git add agent-service/src/tools/
git commit -m "feat: agent tool layer — transfer, isochrone, timetable tools"
```

---

### Task 4: LangGraph Nodes — Understand

**Files:**
- Create: `agent-service/src/nodes/__init__.py`
- Create: `agent-service/src/nodes/understand.py`

- [ ] **Step 1: Create nodes/__init__.py**

```python
from .understand import understand
from .clarify import clarify
from .search import search
from .relax import relax
from .format_reply import format_reply

__all__ = ["understand", "clarify", "search", "relax", "format_reply"]
```

- [ ] **Step 2: Create understand.py with LLM call for intent + constraint extraction**

```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import json

from ..state import AgentState
from ..config import settings

SYSTEM_PROMPT = """你是中国铁路助手，负责理解用户的自然语言出行需求并提取结构化信息。

输出严格的 JSON，格式如下：
{
  "intent": "route_planning | isochrone | station_query | train_query | timetable_query | clarify",
  "constraints": {
    "from": "出发站名或城市（如北京）",
    "to": "目的站名或城市（如广州南）",
    "via": "中转站名或null",
    "trainTypes": ["G", "D", ...] 或 [],
    "maxTransfers": 数字或null,
    "dMax": 单段最大时长（分钟）或null,
    "tStart": 出发时段起始（分钟，0-1440）或null,
    "tEnd": 到达时段截止（分钟，0-1440）或null,
    "hours": 等时圈时间（小时）或null
  },
  "missing": ["from", "to", ...]  列出尚未提供的必填字段（route_planning 至少需要 from 和 to；isochrone 需要起点站和 hours；train_query 需要车次号）
}

时间量化规则：
- "早上" = tStart: 360, "上午" = tStart: 480, "下午" = tStart: 720, "晚上" = tStart: 1080
- "白天" = tStart: 360, tEnd: 1080
- "不太久" = dMax: 240 (4小时), "短途" = dMax: 180 (3小时)
- "不要太累" = dMax: 240, 降低 maxTransfers

意图分类：
- route_planning: 用户想从A到B（可能带条件）
- isochrone: "从X出发能到哪"、"X周边"、"X小时圈"
- station_query: 查某个车站信息
- train_query: 查特定车次（含字母+数字的车次号）
- timetable_query: 查某站所有经停车次时刻表
- clarify: 意图不明或信息严重不足，需要反问

只输出 JSON，不要多余的文字。"""


def build_llm():
    return ChatOpenAI(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        temperature=settings.llm_temperature,
    )


async def understand(state: AgentState) -> dict:
    llm = build_llm()
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=state["user_input"]),
    ]
    response = await llm.ainvoke(messages)
    raw = response.content.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {
            "intent": "clarify",
            "constraints": None,
            "missing": ["_parse_error"],
            "reply_text": "抱歉，我没能理解你的意思。能换个说法吗？",
            "instructions": [],
            "suggestions": ["查询车次", "查询车站", "路径规划"],
        }

    return {
        "intent": parsed.get("intent", "clarify"),
        "constraints": parsed.get("constraints"),
        "missing": parsed.get("missing", []),
    }
```

- [ ] **Step 3: Commit**

```bash
git add agent-service/src/nodes/
git commit -m "feat: agent node — LLM intent classification and constraint extraction"
```

---

### Task 5: LangGraph Nodes — Clarify & Search

**Files:**
- Create: `agent-service/src/nodes/clarify.py`
- Create: `agent-service/src/nodes/search.py`

- [ ] **Step 1: Create clarify.py**

```python
import httpx
from ..state import AgentState
from ..config import settings

CLARIFY_TEMPLATES = {
    "from": "请问你想从哪里出发？",
    "to": "请问你的目的地是哪里？",
    "station_query": "你想查询哪个车站的信息？",
    "train_query": "你想查询哪趟车次？请输入车次号（如G1、D301）。",
    "hours": "你想查询几小时内的等时圈？",
}


async def _resolve_ambiguous_station(name: str) -> dict | None:
    """Check if station name is ambiguous by calling search API."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{settings.java_base_url}/api/stations/search",
            params={"q": name},
        )
        resp.raise_for_status()
        data = resp.json()
        results = data if isinstance(data, list) else data.get("data", [])
        if len(results) > 1:
            return {"query": name, "candidates": [r.get("name") for r in results[:5]]}
        return None


async def clarify(state: AgentState) -> dict:
    missing = state.get("missing", [])
    reply_parts = []

    # Check for ambiguous station names first
    constraints = state.get("constraints") or {}
    ambiguous = []
    for field in ("from", "to", "via"):
        if constraints.get(field) and field not in missing:
            result = await _resolve_ambiguous_station(constraints[field])
            if result:
                ambiguous.append(result)

    if ambiguous:
        for a in ambiguous:
            candidates = "、".join(a["candidates"])
            reply_parts.append(f"「{a['query']}」有多个车站：{candidates}。你指的是哪个？")
    else:
        for field in missing:
            template = CLARIFY_TEMPLATES.get(field)
            if template:
                reply_parts.append(template)

    if not reply_parts:
        reply_parts.append("我没能完全理解你的需求，能再详细说说吗？")

    return {
        "reply_text": "\n\n".join(reply_parts),
        "instructions": [],
        "suggestions": ["查询车次", "查询车站", "路径规划"],
    }
```

- [ ] **Step 2: Create search.py**

```python
import asyncio
from ..state import AgentState
from ..tools import ALL_TOOLS


async def search(state: AgentState) -> dict:
    intent = state.get("intent", "clarify")
    constraints = state.get("constraints") or {}
    tasks = []

    if intent == "station_query" or intent == "timetable_query":
        name = constraints.get("stationName") or constraints.get("from")
        if name:
            tasks.append(("search_stations", ALL_TOOLS["search_stations"](name)))
        elif constraints.get("stationId"):
            tasks.append(("get_station_detail", ALL_TOOLS["get_station_detail"](constraints["stationId"])))

    elif intent == "train_query":
        train_no = constraints.get("trainNo") or constraints.get("from")
        if train_no:
            tasks.append(("get_train_route", ALL_TOOLS["get_train_route"](train_no)))

    elif intent == "isochrone":
        station_id = constraints.get("stationId")
        hours = constraints.get("hours", 4)
        if station_id:
            tasks.append(("get_isochrone", ALL_TOOLS["get_isochrone"](station_id, hours)))
        if not station_id and constraints.get("stationName"):
            tasks.append(("search_stations", ALL_TOOLS["search_stations"](constraints["stationName"])))

    elif intent == "route_planning":
        if constraints.get("from") and constraints.get("to"):
            tasks.append(("search_transfer", ALL_TOOLS["search_transfer"](constraints)))

    # Run all tasks in parallel
    tool_results = []
    if tasks:
        names, coros = zip(*tasks)
        results = await asyncio.gather(*coros, return_exceptions=True)
        for name, result in zip(names, results):
            if isinstance(result, Exception):
                tool_results.append({"tool": name, "params": {}, "result": None, "error": str(result)})
            else:
                tool_results.append(result)

    return {"tool_results": tool_results}
```

- [ ] **Step 3: Commit**

```bash
git add agent-service/src/nodes/
git commit -m "feat: agent nodes — clarify (station disambiguation) and search (parallel tool dispatch)"
```

---

### Task 6: LangGraph Nodes — Relax & Format Reply

**Files:**
- Create: `agent-service/src/nodes/relax.py`
- Create: `agent-service/src/nodes/format_reply.py`

- [ ] **Step 1: Create relax.py**

```python
from ..state import AgentState
from ..config import settings

RELAX_STEPS = [
    ("via", "remove", "去掉中转站约束"),
    ("dMax", "loosen", "放宽单段时长限制"),
    ("maxTransfers", "increase", "增加允许的换乘次数"),
    ("tStart_tEnd", "remove", "放宽出发/到达时段限制"),
]


async def relax(state: AgentState) -> dict:
    relax_history = state.get("relax_history", [])
    constraints = state.get("constraints", {})
    original = dict(constraints)

    round_idx = len(relax_history)

    if round_idx >= settings.max_relax_rounds:
        return {
            "relax_history": relax_history,
            "constraints": constraints,
            "relax_exhausted": True,
        }

    step = RELAX_STEPS[min(round_idx, len(RELAX_STEPS) - 1)]
    field, action, description = step

    relaxed = dict(constraints)

    if field == "via":
        relaxed.pop("via", None)
    elif field == "dMax":
        current = relaxed.get("dMax", 240)
        relaxed["dMax"] = min(current * 2, 720)
    elif field == "maxTransfers":
        current = relaxed.get("maxTransfers", 2)
        relaxed["maxTransfers"] = current + 1
    elif field == "tStart_tEnd":
        relaxed.pop("tStart", None)
        relaxed.pop("tEnd", None)

    relax_history.append({
        "round": round_idx + 1,
        "original_constraints": original,
        "relaxed_constraints": relaxed,
        "description": description,
    })

    return {
        "constraints": relaxed,
        "relax_history": relax_history,
        "relax_exhausted": False,
    }


def format_relax_diff(relax_history: list[dict]) -> str:
    if not relax_history:
        return ""
    parts = ["\n\n按你的条件没找到结果，我尝试放宽了约束："]
    for entry in relax_history:
        parts.append(f"• {entry['description']}")
    return "\n".join(parts)
```

- [ ] **Step 2: Create format_reply.py**

```python
from ..state import AgentState


async def format_reply(state: AgentState) -> dict:
    intent = state.get("intent", "clarify")
    tool_results = state.get("tool_results", [])
    relax_history = state.get("relax_history", [])
    constraints = state.get("constraints") or {}
    instructions = []
    suggestions = []

    if intent == "station_query" or intent == "timetable_query":
        reply_text, instructions = _format_station_result(tool_results, intent)
    elif intent == "train_query":
        reply_text, instructions = _format_train_result(tool_results)
    elif intent == "route_planning":
        reply_text, instructions = _format_route_result(tool_results, relax_history, constraints)
        suggestions = ["只看高铁", "最少换乘", "尝试其他时间段"]
    elif intent == "isochrone":
        reply_text, instructions = _format_isochrone_result(tool_results, constraints)
        suggestions = ["细看哪个方向？", "从这些城市中选一个目的地规划路线"]
    else:
        reply_text = "有什么我可以帮你的？"

    return {
        "reply_text": reply_text,
        "instructions": instructions,
        "suggestions": suggestions,
    }


def _format_station_result(tool_results: list[dict], intent: str) -> tuple[str, list[dict]]:
    for r in tool_results:
        if r.get("tool") in ("search_stations", "get_station_detail", "get_station_timetable"):
            station = r.get("station") or (r.get("stations", [None])[0] if r.get("stations") else None)
            if not station:
                continue
            name = station.get("name", "未知站")
            city = station.get("city", "")
            sid = station.get("id")
            instructions = [
                {"action": "flyToStation", "stationId": str(sid)},
                {"action": "openPanel", "panel": "station"},
            ]
            if intent == "timetable_query":
                instructions.append({"action": "openModal", "modal": "timetable", "stationId": str(sid)})
            return f"**{name}**，{city}。详细信息已在左侧面板展示。", instructions
    return "抱歉，未找到该车站的信息。", []


def _format_train_result(tool_results: list[dict]) -> tuple[str, list[dict]]:
    for r in tool_results:
        if r.get("tool") == "get_train_route":
            train = r.get("train", {})
            no = train.get("trainNo", "")
            from_s = train.get("fromStation", {}).get("name", "")
            to_s = train.get("toStation", {}).get("name", "")
            stops = train.get("stops", [])
            return (
                f"**{no}** 次列车，{from_s} → {to_s}，共 {len(stops)} 站。\n\n线路已在地图高亮显示。",
                [
                    {"action": "highlightTrain", "trainNo": no},
                    {"action": "openPanel", "panel": "train"},
                ],
            )
    return "抱歉，未找到该车次的信息。", []


def _format_route_result(tool_results: list[dict], relax_history: list[dict], constraints: dict) -> tuple[str, list[dict]]:
    from .relax import format_relax_diff

    for r in tool_results:
        if r.get("tool") == "search_transfer":
            routes = r.get("routes", [])
            count = r.get("count", len(routes))

            if count == 0:
                return "抱歉，没找到符合条件的中转路线。" + format_relax_diff(relax_history), []

            lines = [f"从 **{constraints.get('from')}** 到 **{constraints.get('to')}**，找到 {count} 条路线：\n"]
            for i, route in enumerate(routes[:5]):
                label = f"方案{i + 1}"
                seg_texts = []
                for seg in route.get("segments", []):
                    if seg.get("trainNo"):
                        seg_texts.append(f"{seg['from']} —{seg['trainNo']}→ {seg['to']}")
                lines.append(f"**{label}**：{' → '.join(seg_texts)}")
                dur = route.get("totalDurationMin", 0)
                transfers = route.get("transfers", 0)
                lines.append(f"⏱ {dur // 60}h{dur % 60}min · 🔄 {transfers} 次换乘\n")

            if count > 5:
                lines.append(f"\n…还有 {count - 5} 条方案，可以进一步筛选。")

            diff_text = format_relax_diff(relax_history)
            route_ids = [r.get("id", f"plan-{i}") for i, r in enumerate(routes[:3])]
            instructions = [{"action": "highlightRoutes", "routeIds": route_ids}]

            return "\n".join(lines) + diff_text, instructions

    return "抱歉，路线规划失败，请稍后重试。", []


def _format_isochrone_result(tool_results: list[dict], constraints: dict) -> tuple[str, list[dict]]:
    for r in tool_results:
        if r.get("tool") == "get_isochrone":
            result = r.get("result", {})
            station_id = r.get("stationId", "")
            hours = r.get("hours", 0)
            groups = result.get("directionGroups", {})
            total = result.get("totalReachable", 0)

            if not groups:
                return f"从该站出发 {hours} 小时内可达约 {total} 个站点。", [
                    {"action": "highlightIsochrone", "stationId": str(station_id)},
                ]

            dir_names = {"east": "东", "south": "南", "west": "西", "north": "北",
                         "northeast": "东北", "northwest": "西北", "southeast": "东南", "southwest": "西南"}
            parts = []
            for d, cities in groups.items():
                label = dir_names.get(d, d)
                if cities:
                    example = cities[0] if isinstance(cities[0], str) else cities[0].get("name", "")
                    parts.append(f"往**{label}**（{example}方向）{len(cities)} 站")

            return (
                f"从该站出发 **{hours}** 小时内可达 {total} 个站点：\n\n" + "\n".join(parts) + "\n\n你想去哪个方向？我可以帮你规划具体路线。",
                [{"action": "highlightIsochrone", "stationId": str(station_id)}],
            )

    return "等时圈查询暂不可用，请稍后再试。", []
```

- [ ] **Step 3: Commit**

```bash
git add agent-service/src/nodes/
git commit -m "feat: agent nodes — constraint relaxation and reply formatting with frontend instructions"
```

---

### Task 7: LangGraph Compilation & FastAPI Entry Point

**Files:**
- Create: `agent-service/src/graph.py`
- Create: `agent-service/src/main.py`

- [ ] **Step 1: Create graph.py**

```python
from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import understand, clarify, search, relax, format_reply


def should_clarify(state: AgentState) -> str:
    if state.get("intent") == "clarify" or state.get("missing"):
        return "clarify"
    return "search"


def has_results(state: AgentState) -> str:
    tool_results = state.get("tool_results", [])
    for r in tool_results:
        if r.get("tool") == "search_transfer":
            if r.get("count", 0) == 0:
                return "no_result"
    if tool_results and not any(r.get("error") for r in tool_results):
        return "format"
    return "format"


def should_relax(state: AgentState) -> str:
    if state.get("intent") != "route_planning":
        return "format"
    if state.get("relax_exhausted"):
        return "format"
    return "relax"


def build_graph() -> StateGraph:
    workflow = StateGraph(AgentState)

    workflow.add_node("understand", understand)
    workflow.add_node("clarify", clarify)
    workflow.add_node("search", search)
    workflow.add_node("relax", relax)
    workflow.add_node("format_reply", format_reply)

    workflow.set_entry_point("understand")

    workflow.add_conditional_edges(
        "understand",
        should_clarify,
        {"clarify": "clarify", "search": "search"},
    )
    workflow.add_edge("clarify", END)

    workflow.add_conditional_edges(
        "search",
        has_results,
        {"format": "format_reply", "no_result": "relax"},
    )
    workflow.add_conditional_edges(
        "relax",
        should_relax,
        {"relax": "search", "format": "format_reply"},
    )
    workflow.add_edge("format_reply", END)

    return workflow.compile()


graph = build_graph()
```

- [ ] **Step 2: Create main.py**

```python
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .state import AgentState
from .graph import graph
from .config import settings


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str


class ChatResponse(BaseModel):
    session_id: str
    text: str
    instructions: list[dict]
    suggestions: list[str]


sessions: dict[str, AgentState] = {}


def get_or_create_session(session_id: str | None) -> tuple[str, AgentState]:
    sid = session_id or str(uuid.uuid4())
    if sid not in sessions:
        sessions[sid] = AgentState(
            session_id=sid,
            messages=[],
            user_input="",
            intent=None,
            constraints=None,
            missing=[],
            tool_results=[],
            reply_text="",
            instructions=[],
            suggestions=[],
            relax_history=[],
        )
    return sid, sessions[sid]


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    sessions.clear()


app = FastAPI(title="RailwayMap Agent", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/agent/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(400, "message is required")

    sid, state = get_or_create_session(req.session_id)

    state["user_input"] = req.message.strip()
    state["messages"].append({"role": "user", "content": req.message.strip()})
    state["tool_results"] = []
    state["instructions"] = []
    state["suggestions"] = []
    state["reply_text"] = ""

    result = await graph.ainvoke(state)

    sessions[sid] = {**state, **result}

    reply = sessions[sid].get("reply_text", "")
    instructions = sessions[sid].get("instructions", [])
    suggestions = sessions[sid].get("suggestions", [])

    sessions[sid]["messages"].append({"role": "agent", "content": reply})

    return ChatResponse(
        session_id=sid,
        text=reply,
        instructions=instructions,
        suggestions=suggestions,
    )


@app.get("/api/agent/health")
async def health():
    return {"status": "ok", "model": settings.llm_model}
```

- [ ] **Step 3: Commit**

```bash
git add agent-service/src/main.py agent-service/src/graph.py
git commit -m "feat: agent graph compilation and FastAPI entry point"
```

---

### Task 8: Docker & Docker Compose

**Files:**
- Create: `agent-service/Dockerfile`
- Modify: `docker-compose.yml`

- [ ] **Step 1: Create agent-service/Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY src/ ./src/

ENV AGENT_LLM_BASE_URL=https://api.openai.com/v1
ENV AGENT_JAVA_BASE_URL=http://app:8080

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Add agent-service to docker-compose.yml**

Add this service block after the `app` service (after line 49, before `frontend`):

```yaml
  agent:
    build:
      context: ./agent-service
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      AGENT_LLM_BASE_URL: ${AGENT_LLM_BASE_URL:-https://api.openai.com/v1}
      AGENT_LLM_API_KEY: ${AGENT_LLM_API_KEY}
      AGENT_LLM_MODEL: ${AGENT_LLM_MODEL:-gpt-4o-mini}
      AGENT_JAVA_BASE_URL: http://app:8080
    depends_on:
      - app
    restart: unless-stopped
```

Also add `agent` to the frontend service's `depends_on`.

- [ ] **Step 3: Commit**

```bash
git add agent-service/Dockerfile docker-compose.yml
git commit -m "feat: docker deployment for agent-service"
```

---

### Task 9: Frontend — Types and API Client

**Files:**
- Modify: `railway-frontend/src/types/agent.ts`
- Create: `railway-frontend/src/api/agentApi.ts`

- [ ] **Step 1: Extend types/agent.ts with instruction types**

Add after the existing `QuickSuggestion` interface:

```typescript
export interface AgentInstruction {
  action: 'flyToStation' | 'highlightTrain' | 'highlightRoutes' | 'highlightIsochrone'
    | 'openPanel' | 'openModal' | 'clearHighlights'
  [key: string]: unknown
}

export interface FlyToStationInstruction extends AgentInstruction {
  action: 'flyToStation'
  stationId: string
}

export interface HighlightTrainInstruction extends AgentInstruction {
  action: 'highlightTrain'
  trainNo: string
}

export interface HighlightRoutesInstruction extends AgentInstruction {
  action: 'highlightRoutes'
  routeIds: string[]
}

export interface HighlightIsochroneInstruction extends AgentInstruction {
  action: 'highlightIsochrone'
  stationId: string
}

export interface OpenPanelInstruction extends AgentInstruction {
  action: 'openPanel'
  panel: 'station' | 'train' | 'routePlan'
}

export interface OpenModalInstruction extends AgentInstruction {
  action: 'openModal'
  modal: 'timetable'
  stationId: string
}
```

Also add `instructions` and `suggestions` to `AgentMessageContent`:

```typescript
export interface AgentMessageContent {
  text: string
  routePlans?: RoutePlan[]
  stationId?: string
  trainNo?: string
  city?: string
  instructions?: AgentInstruction[]
  suggestions?: string[]
}
```

- [ ] **Step 2: Create api/agentApi.ts**

```typescript
import apiClient from './client'
import type { AgentInstruction } from '../types/agent'

export interface AgentChatRequest {
  session_id?: string
  message: string
}

export interface AgentChatResponse {
  session_id: string
  text: string
  instructions: AgentInstruction[]
  suggestions: string[]
}

export const agentApi = {
  chat(req: AgentChatRequest) {
    return apiClient.post<unknown, AgentChatResponse>('/agent/chat', req)
  },
}
```

- [ ] **Step 3: Commit**

```bash
git add railway-frontend/src/types/agent.ts railway-frontend/src/api/agentApi.ts
git commit -m "feat: frontend agent types and API client for real agent service"
```

---

### Task 10: Frontend — Rewrite useAgentChat.ts

**Files:**
- Modify: `railway-frontend/src/composables/useAgentChat.ts`
- Modify: `railway-frontend/src/stores/agentStore.ts`
- Modify: `railway-frontend/src/stores/routePlanStore.ts`

- [ ] **Step 1: Add setActivePlanIds to routePlanStore.ts**

Add this action inside `useRoutePlanStore`:

```typescript
  function setActivePlanIds(ids: string[]) {
    activePlanIndices.value = ids
      .map(id => plans.value.findIndex(p => p.id === id))
      .filter(i => i !== -1)
  }
```

Add `setActivePlanIds` to the return object.

- [ ] **Step 2: Add dispatchInstruction and setQuickSuggestions to agentStore.ts**

Add imports at top:
```typescript
import type { AgentInstruction, FlyToStationInstruction, HighlightTrainInstruction, HighlightRoutesInstruction, HighlightIsochroneInstruction } from '../types/agent'
import { useMapStore } from './mapStore'
import { useStationStore } from './stationStore'
import { useTrainStore } from './trainStore'
import { useRoutePlanStore } from './routePlanStore'
import type { QuickSuggestion } from '../types/agent'
```

Add state:
```typescript
const quickSuggestions = ref<QuickSuggestion[]>(defaultQuickSuggestions)
```

Add actions:
```typescript
  function dispatchInstruction(instruction: AgentInstruction) {
    const mapStore = useMapStore()
    const stationStore = useStationStore()
    const trainStore = useTrainStore()
    const routePlanStore = useRoutePlanStore()

    switch (instruction.action) {
      case 'flyToStation': {
        const { stationId } = instruction as FlyToStationInstruction
        mapStore.setFocusStation(stationId)
        stationStore.setCurrentStation(stationId)
        break
      }
      case 'highlightTrain': {
        const { trainNo } = instruction as HighlightTrainInstruction
        mapStore.setFocusTrain(trainNo)
        trainStore.setCurrentTrain(trainNo)
        break
      }
      case 'highlightRoutes': {
        const { routeIds } = instruction as HighlightRoutesInstruction
        routePlanStore.setActivePlanIds(routeIds)
        break
      }
      case 'highlightIsochrone': {
        const { stationId } = instruction as HighlightIsochroneInstruction
        mapStore.setFocusStation(stationId)
        break
      }
      case 'clearHighlights': {
        mapStore.clearAllFocus()
        routePlanStore.clear()
        break
      }
    }
  }

  function setQuickSuggestions(sugs: QuickSuggestion[]) {
    quickSuggestions.value = sugs
  }
```

Add `quickSuggestions`, `dispatchInstruction`, `setQuickSuggestions` to return object.

- [ ] **Step 3: Rewrite useAgentChat.ts**

```typescript
import { useAgentStore } from '../stores/agentStore'
import { agentApi } from '../api/agentApi'

let sessionId: string | null = null

export function useAgentChat() {
  const agentStore = useAgentStore()

  async function sendMessage(text: string) {
    agentStore.addMessage('user', { text })
    agentStore.setProcessing(true)

    try {
      const response = await agentApi.chat({
        session_id: sessionId,
        message: text,
      })

      sessionId = response.session_id

      agentStore.addMessage('agent', {
        text: response.text,
        instructions: response.instructions,
        suggestions: response.suggestions,
      })

      for (const instruction of response.instructions) {
        agentStore.dispatchInstruction(instruction)
      }

      if (response.suggestions.length > 0) {
        agentStore.setQuickSuggestions(
          response.suggestions.map(s => ({ label: s, prompt: s }))
        )
      }
    } catch (err) {
      agentStore.addMessage('agent', {
        text: `抱歉，请求失败：${err instanceof Error ? err.message : '未知错误'}。请稍后重试。`,
      })
    } finally {
      agentStore.setProcessing(false)
    }
  }

  return { sendMessage }
}
```

- [ ] **Step 4: Update vite.config.ts proxy**

Read the existing vite.config.ts to find the proxy section, then add:
```typescript
'/api/agent': {
  target: 'http://localhost:8000',
  changeOrigin: true,
},
```

- [ ] **Step 5: Commit**

```bash
git add railway-frontend/src/composables/useAgentChat.ts \
        railway-frontend/src/stores/agentStore.ts \
        railway-frontend/src/stores/routePlanStore.ts \
        railway-frontend/vite.config.ts
git commit -m "feat: replace agent mock with real API calls + instruction dispatch"
```

---

### Task 11: Frontend — Train Route Map Animation

**Files:**
- Create: `railway-frontend/src/composables/useTrainAnimation.ts`
- Create: `railway-frontend/src/components/map/TrainRouteLayer.vue`

- [ ] **Step 1: Create useTrainAnimation.ts**

```typescript
import { ref, onUnmounted } from 'vue'
import type { RoutePlan } from '../types/route'

const TRAIN_TYPE_COLORS: Record<string, string> = {
  'G': '#E53E3E',
  'D': '#ED8936',
  'C': '#38A169',
  'Z': '#3182CE',
  'T': '#3182CE',
  'K': '#3182CE',
}

const DASH_ARRAY = [8, 6]

export function useTrainAnimation(mapRef: { value: maplibregl.Map | null }) {
  const activeRoutes = ref<RoutePlan[]>([])
  let animationFrameId: number | null = null
  const dashOffsets: number[] = []
  const speeds: number[] = []

  function getTrainColor(trainNo: string | null): string {
    if (!trainNo) return '#A0AEC0'
    const prefix = trainNo.charAt(0).toUpperCase()
    return TRAIN_TYPE_COLORS[prefix] || '#A0AEC0'
  }

  function getSpeed(trainNo: string | null): number {
    if (!trainNo) return 0.3
    const prefix = trainNo.charAt(0).toUpperCase()
    if (prefix === 'G') return 1.2
    if (prefix === 'D' || prefix === 'C') return 0.8
    return 0.4
  }

  function startAnimation(routes: RoutePlan[]) {
    stopAnimation()
    activeRoutes.value = routes
    dashOffsets.length = 0
    speeds.length = 0
    routes.forEach(r => {
      const firstTrain = r.segments.find(s => s.trainNo)
      dashOffsets.push(0)
      speeds.push(getSpeed(firstTrain?.trainNo ?? null))
    })
    animate()
  }

  function animate() {
    const map = mapRef.value
    if (!map || activeRoutes.value.length === 0) return

    for (let i = 0; i < activeRoutes.value.length; i++) {
      dashOffsets[i] = (dashOffsets[i] + speeds[i]) % (DASH_ARRAY[0] + DASH_ARRAY[1])
    }

    activeRoutes.value.forEach((route, i) => {
      const sourceId = `route-${route.id}`
      if (map.getLayer(`${sourceId}-line`)) {
        const [a, b] = DASH_ARRAY
        const offset = dashOffsets[i]
        map.setPaintProperty(`${sourceId}-line`, 'line-dasharray', [a, b, a, b + offset, a, b])
      }
    })

    animationFrameId = requestAnimationFrame(animate)
  }

  function stopAnimation() {
    if (animationFrameId !== null) {
      cancelAnimationFrame(animationFrameId)
      animationFrameId = null
    }
    activeRoutes.value = []
    dashOffsets.length = 0
  }

  function getPulsePhase(): number {
    return (Date.now() % 1500) / 1500
  }

  onUnmounted(() => stopAnimation())

  return {
    activeRoutes,
    startAnimation,
    stopAnimation,
    getTrainColor,
    getSpeed,
    getPulsePhase,
    TRAIN_TYPE_COLORS,
  }
}
```

- [ ] **Step 2: Create TrainRouteLayer.vue**

```vue
<script setup lang="ts">
import { watch } from 'vue'
import type { RoutePlan } from '../../types/route'
import { useTrainAnimation } from '../../composables/useTrainAnimation'

const props = defineProps<{
  mapRef: { value: maplibregl.Map | null }
  routes: RoutePlan[]
}>()

const { startAnimation, stopAnimation, getTrainColor } = useTrainAnimation(props.mapRef)

watch(
  () => props.routes,
  (routes) => {
    stopAnimation()
    if (routes.length > 0) {
      addRouteSources(routes)
      startAnimation(routes)
    }
  },
  { deep: true },
)

function addRouteSources(routes: RoutePlan[]) {
  const map = props.mapRef.value
  if (!map) return

  const displayRoutes = routes.length > 3 ? routes.slice(0, 3) : routes
  const simplified = routes.length > 3

  displayRoutes.forEach((route) => {
    const sourceId = `route-${route.id}`
    const color = route.color || getTrainColor(route.segments[0]?.trainNo)

    const coords: [number, number][] = []
    route.segments.forEach(seg => {
      if (seg.coordinates) coords.push(...seg.coordinates)
    })

    if (coords.length < 2) return

    const geojson: GeoJSON.Feature = {
      type: 'Feature',
      properties: {},
      geometry: { type: 'LineString', coordinates: coords },
    }

    if (map.getSource(sourceId)) {
      (map.getSource(sourceId) as maplibregl.GeoJSONSource).setData(geojson)
    } else {
      map.addSource(sourceId, { type: 'geojson', data: geojson })

      map.addLayer({
        id: `${sourceId}-line`,
        type: 'line',
        source: sourceId,
        paint: {
          'line-color': color,
          'line-width': simplified ? 2 : 3,
          'line-dasharray': simplified ? [4, 2] : [8, 6],
          'line-opacity': 0.9,
        },
      })

      const stationFeatures: GeoJSON.Feature[] = []
      route.segments.forEach((seg, idx) => {
        if (seg.coordinates && seg.coordinates.length > 0) {
          stationFeatures.push({
            type: 'Feature',
            properties: { isTerminal: idx === 0 || idx === route.segments.length - 1 },
            geometry: { type: 'Point', coordinates: seg.coordinates[0] },
          })
        }
      })

      map.addSource(`${sourceId}-stops`, {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: stationFeatures },
      })

      map.addLayer({
        id: `${sourceId}-stops-layer`,
        type: 'circle',
        source: `${sourceId}-stops`,
        paint: {
          'circle-color': color,
          'circle-radius': ['case', ['get', 'isTerminal'], 8, 5],
          'circle-stroke-width': ['case', ['get', 'isTerminal'], 2, 0],
          'circle-stroke-color': '#fff',
          'circle-opacity': 0.9,
        },
      })
    }
  })
}
</script>

<template>
  <div />
</template>
```

- [ ] **Step 3: Commit**

```bash
git add railway-frontend/src/composables/useTrainAnimation.ts \
        railway-frontend/src/components/map/TrainRouteLayer.vue
git commit -m "feat: train route dash-flow animation with signal pulse effect"
```

---

### Task 12: Integration — Wire Map Interactions

**Files:**
- Modify: `railway-frontend/src/App.vue`
- Modify: `railway-frontend/src/components/agent/AgentBubble.vue`
- Modify: `railway-frontend/src/components/agent/AgentPanel.vue`

- [ ] **Step 1: Update AgentPanel.vue to use dynamic quick suggestions**

Change the `quick-suggestions` section to use `agentStore.quickSuggestions`:

```vue
<div
  v-if="agentStore.messageCount === 1"
  class="quick-suggestions"
>
  <button
    v-for="chip in agentStore.quickSuggestions"
    :key="chip.prompt"
    class="quick-chip"
    @click="handleQuickChip(chip.prompt)"
  >
    {{ chip.label }}
  </button>
</div>
```

- [ ] **Step 2: Add suggestion chips to AgentBubble for agent messages**

After the markdown text div and before the timestamp div, add:

```vue
<div
  v-if="message.role === 'agent' && message.content.suggestions?.length"
  class="bubble-suggestions"
>
  <button
    v-for="sug in message.content.suggestions"
    :key="sug"
    class="bubble-suggestion-chip"
    @click="emit('quickReply', sug)"
  >
    {{ sug }}
  </button>
</div>
```

Add to the script section:
```typescript
const emit = defineEmits<{
  navigate: [type: string, action: string]
  quickReply: [prompt: string]
}>()
```

Add scoped styles:
```css
.bubble-suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 8px;
}
.bubble-suggestion-chip {
  padding: 4px 10px;
  border-radius: var(--radius-full);
  border: 1px solid var(--border-medium);
  background: var(--glass-bg-active);
  font-size: var(--text-xs);
  color: var(--text-secondary);
  cursor: pointer;
  font-family: inherit;
  transition: all var(--duration-fast);
}
.bubble-suggestion-chip:hover {
  background: var(--border-light);
  color: var(--text-primary);
}
```

- [ ] **Step 3: Handle quickReply in AgentPanel.vue**

Add to `AgentBubble` usage:
```vue
<AgentBubble
  v-for="msg in agentStore.messages"
  :key="msg.id"
  :message="msg"
  @navigate="(t, a) => emit('navigate', t, a)"
  @quick-reply="handleQuickChip"
/>
```

- [ ] **Step 4: Verify frontend builds**

```bash
cd railway-frontend && npm run build
```
Expected: Build succeeds.

- [ ] **Step 5: Commit**

```bash
git add railway-frontend/src/
git commit -m "feat: wire agent instructions to frontend map and UI interactions"
```

---

### Task 13: Agent Service Tests

**Files:**
- Create: `agent-service/tests/__init__.py`
- Create: `agent-service/tests/test_understand.py`
- Create: `agent-service/tests/test_relax.py`
- Create: `agent-service/tests/test_format_reply.py`

- [ ] **Step 1: Create tests/test_understand.py**

```python
import pytest
from unittest.mock import AsyncMock, patch
from src.nodes.understand import understand
from src.state import AgentState


def make_state(user_input: str) -> AgentState:
    return AgentState(
        session_id="test", messages=[], user_input=user_input,
        intent=None, constraints=None, missing=[],
        tool_results=[], reply_text="", instructions=[], suggestions=[], relax_history=[],
    )


@pytest.mark.asyncio
async def test_understand_route_planning():
    state = make_state("从北京到广州，高铁，换乘不超过1次")
    mock_resp = AsyncMock()
    mock_resp.content = '{"intent":"route_planning","constraints":{"from":"北京","to":"广州","trainTypes":["G"],"maxTransfers":1},"missing":[]}'
    with patch("src.nodes.understand.build_llm") as mock_llm:
        mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_resp)
        result = await understand(state)
    assert result["intent"] == "route_planning"
    assert result["constraints"]["from"] == "北京"


@pytest.mark.asyncio
async def test_understand_malformed_json():
    state = make_state("...")
    mock_resp = AsyncMock()
    mock_resp.content = "not json"
    with patch("src.nodes.understand.build_llm") as mock_llm:
        mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_resp)
        result = await understand(state)
    assert result["intent"] == "clarify"
```

- [ ] **Step 2: Create tests/test_relax.py**

```python
import pytest
from src.nodes.relax import relax
from ..test_understand import make_state


@pytest.mark.asyncio
async def test_relax_removes_via():
    state = make_state("")
    state["intent"] = "route_planning"
    state["constraints"] = {"from": "北京", "to": "广州", "via": "武汉", "maxTransfers": 1}
    result = await relax(state)
    assert "via" not in result["constraints"]
    assert len(result["relax_history"]) == 1


@pytest.mark.asyncio
async def test_relax_exhausted():
    state = make_state("")
    state["intent"] = "route_planning"
    state["relax_history"] = [{"round": i, "description": f"r{i}"} for i in range(1, 4)]
    result = await relax(state)
    assert result.get("relax_exhausted") is True
```

- [ ] **Step 3: Create tests/test_format_reply.py**

```python
import pytest
from src.nodes.format_reply import format_reply
from ..test_understand import make_state


@pytest.mark.asyncio
async def test_format_empty_route():
    state = make_state("")
    state["intent"] = "route_planning"
    state["constraints"] = {"from": "北京", "to": "广州"}
    state["tool_results"] = [{"tool": "search_transfer", "params": {}, "routes": [], "count": 0}]
    result = await format_reply(state)
    assert "没找到" in result["reply_text"]


@pytest.mark.asyncio
async def test_format_with_routes():
    state = make_state("")
    state["intent"] = "route_planning"
    state["constraints"] = {"from": "北京", "to": "广州"}
    state["tool_results"] = [{
        "tool": "search_transfer",
        "routes": [{"id": "r1", "segments": [{"trainNo": "G1", "from": "北京南", "to": "广州南"}], "totalDurationMin": 480, "transfers": 1}],
        "count": 1,
    }]
    result = await format_reply(state)
    assert "G1" in result["reply_text"]
    assert result["instructions"][0]["action"] == "highlightRoutes"
```

- [ ] **Step 4: Run tests**

```bash
cd agent-service && pip install -e ".[dev]" && python -m pytest tests/ -v
```
Expected: 5 tests pass.

- [ ] **Step 5: Commit**

```bash
git add agent-service/tests/
git commit -m "test: agent understand, relax, and format_reply unit tests"
```

---

### Task 14: Final Verification

- [ ] **Step 1: Verify all files exist**

```bash
echo "=== Agent service ===" && find agent-service/src -name '*.py' | sort
echo "=== Agent tests ===" && find agent-service/tests -name '*.py' | sort
echo "=== Frontend new files ===" && ls railway-frontend/src/api/agentApi.ts railway-frontend/src/composables/useTrainAnimation.ts railway-frontend/src/components/map/TrainRouteLayer.vue
```
Expected: All paths exist.

- [ ] **Step 2: Verify frontend TypeScript compilation**

```bash
cd railway-frontend && npx vue-tsc --noEmit 2>&1 | head -20
```
Expected: No new type errors.

- [ ] **Step 3: Verify OpenSpec change is valid**

```bash
openspec validate agent-service
```
Expected: "Change 'agent-service' is valid"

- [ ] **Step 4: Final commit**

```bash
git status
git add <any-remaining-files>
git commit -m "chore: final integration verification for agent service"
```
