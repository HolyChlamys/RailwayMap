from typing import TypedDict


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
