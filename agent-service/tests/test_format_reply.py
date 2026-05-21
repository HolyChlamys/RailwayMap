import pytest
from src.nodes.format_reply import format_reply
from src.state import AgentState


def make_state() -> AgentState:
    return AgentState(
        session_id="t", messages=[], user_input="",
        intent=None, constraints=None, missing=[],
        tool_results=[], reply_text="", instructions=[], suggestions=[], relax_history=[],
    )


@pytest.mark.asyncio
async def test_format_empty_route():
    state = make_state()
    state["intent"] = "route_planning"
    state["constraints"] = {"from": "北京", "to": "广州"}
    state["tool_results"] = [{"tool": "search_transfer", "params": {}, "routes": [], "count": 0}]
    result = await format_reply(state)
    assert "没找到" in result["reply_text"]


@pytest.mark.asyncio
async def test_format_with_routes():
    state = make_state()
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
