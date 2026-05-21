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
