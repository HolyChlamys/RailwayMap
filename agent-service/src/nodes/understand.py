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
