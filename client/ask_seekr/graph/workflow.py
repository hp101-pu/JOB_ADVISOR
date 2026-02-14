"""LangGraph state machine assembly for AskSeekr."""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from client.ask_seekr.graph.nodes import (
    chat_node,
    confirm_node,
    execute_node,
    load_context_node,
    planner_node,
    resolve_email_message_id_node,
    respond_node,
    save_memory_node,
    summarize_node,
    validate_node,
)
from client.ask_seekr.graph.state import ChatState


def _route_after_planner(state: ChatState) -> str:
    return state.get("intent", "CHAT")


def _route_after_resolve(state: ChatState) -> str:
    """If resolution failed, respond immediately; otherwise validate."""
    if state.get("response"):
        return "respond"
    return "validate"


def _route_after_validate(state: ChatState) -> str:
    status = state.get("status", "OK")
    if status == "OK":
        return "execute"
    if status == "NEEDS_CONFIRMATION":
        return "confirm"
    return "respond"


def _route_after_confirm(state: ChatState) -> str:
    """After resuming from interrupt, re-validate if confirmed, otherwise respond."""
    if state.get("confirmed", False):
        return "validate"
    return "respond"


def build_graph():
    """Build and return the compiled Phase 1 graph."""
    builder = StateGraph(ChatState)

    # Nodes
    builder.add_node("load_context", load_context_node)
    builder.add_node("planner", planner_node)
    builder.add_node("chat", chat_node)
    builder.add_node("resolve_email", resolve_email_message_id_node)
    builder.add_node("validate", validate_node)
    builder.add_node("confirm", confirm_node)
    builder.add_node("execute", execute_node)
    builder.add_node("summarize", summarize_node)
    builder.add_node("save_memory", save_memory_node)
    builder.add_node("respond", respond_node)

    # Edges
    builder.set_entry_point("load_context")
    builder.add_edge("load_context", "planner")

    builder.add_conditional_edges(
        "planner",
        _route_after_planner,
        {"CHAT": "chat", "ACTION": "resolve_email"},
    )

    builder.add_conditional_edges(
        "resolve_email",
        _route_after_resolve,
        {"respond": "save_memory", "validate": "validate"},
    )

    builder.add_conditional_edges(
        "validate",
        _route_after_validate,
        {"execute": "execute", "confirm": "confirm", "respond": "save_memory"},
    )

    builder.add_conditional_edges(
        "confirm",
        _route_after_confirm,
        {"validate": "validate", "respond": "save_memory"},
    )

    builder.add_edge("chat", "save_memory")
    builder.add_edge("execute", "summarize")
    builder.add_edge("summarize", "save_memory")
    builder.add_edge("save_memory", "respond")
    builder.add_edge("respond", END)

    # Dev checkpointer. Swap for a persistent SQLite/Postgres checkpointer
    # (e.g. AsyncSqliteSaver) for production.
    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)


_COMPILED_GRAPH = None


def compiled_graph():
    """Singleton compiled graph instance."""
    global _COMPILED_GRAPH
    if _COMPILED_GRAPH is None:
        _COMPILED_GRAPH = build_graph()
    return _COMPILED_GRAPH
