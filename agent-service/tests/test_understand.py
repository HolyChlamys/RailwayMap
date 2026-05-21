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
async def test_understand_parses_valid_json():
    state = make_state("从北京到广州，高铁，换乘不超过1次")
    mock_resp = AsyncMock()
    mock_resp.content = '{"intent":"route_planning","constraints":{"from":"北京","to":"广州","trainTypes":["G"],"maxTransfers":1},"missing":[]}'
    with patch("src.nodes.understand.build_llm") as mock_llm:
        mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_resp)
        result = await understand(state)
    assert result["intent"] == "route_planning"
    assert result["constraints"]["from"] == "北京"


@pytest.mark.asyncio
async def test_understand_handles_malformed_json():
    state = make_state("...")
    mock_resp = AsyncMock()
    mock_resp.content = "not valid json at all"
    with patch("src.nodes.understand.build_llm") as mock_llm:
        mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_resp)
        result = await understand(state)
    assert result["intent"] == "clarify"
