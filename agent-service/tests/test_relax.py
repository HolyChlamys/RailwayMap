import pytest
from src.nodes.relax import relax
from src.state import AgentState


def make_state(user_input: str = "") -> AgentState:
    return AgentState(
        session_id="t", messages=[], user_input=user_input,
        intent=None, constraints=None, missing=[],
        tool_results=[], reply_text="", instructions=[], suggestions=[], relax_history=[],
    )


@pytest.mark.asyncio
async def test_relax_removes_via_first():
    state = make_state()
    state["intent"] = "route_planning"
    state["constraints"] = {"from": "北京", "to": "广州", "via": "武汉", "maxTransfers": 1}
    result = await relax(state)
    assert "via" not in result["constraints"]
    assert len(result["relax_history"]) == 1


@pytest.mark.asyncio
async def test_relax_exhausted_after_max_rounds():
    state = make_state()
    state["intent"] = "route_planning"
    state["constraints"] = {"from": "北京", "to": "广州"}
    state["relax_history"] = [
        {"round": 1, "original_constraints": {}, "relaxed_constraints": {}, "description": "r1"},
        {"round": 2, "original_constraints": {}, "relaxed_constraints": {}, "description": "r2"},
        {"round": 3, "original_constraints": {}, "relaxed_constraints": {}, "description": "r3"},
    ]
    result = await relax(state)
    assert result.get("relax_exhausted") is True
