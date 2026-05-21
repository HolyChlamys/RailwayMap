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
        current = relaxed.get("dMax") or 240
        relaxed["dMax"] = min(current * 2, 720)
    elif field == "maxTransfers":
        current = relaxed.get("maxTransfers") or 2
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
