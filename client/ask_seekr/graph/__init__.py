"""LangGraph chatbot state machine."""

from typing import Any, AsyncIterator, Dict, Optional

from client.ask_seekr.graph.state import ChatState
from client.ask_seekr.graph.workflow import compiled_graph

__all__ = ["compiled_graph", "stream_graph"]


async def stream_graph(
    state: ChatState,
    thread_id: Optional[str] = None,
) -> AsyncIterator[Dict[str, Any]]:
    """Async generator that yields progress and the final response from the graph.

    Yields:
        - ``{"type": "node", "node": <node_name>}`` for each completed node.
        - ``{"type": "final", "response": ..., "conversation_id": ..., "metadata": ...}`` at the end.
        - ``{"type": "interrupt", "message": ..., "plan": ..., "conversation_id": ...}`` when confirmation is needed.
    """
    graph = compiled_graph()
    config = {"configurable": {"thread_id": thread_id or "default"}}

    async for chunk in graph.astream(
        state,
        config=config,
        stream_mode=["updates", "values"],
    ):
        if isinstance(chunk, tuple):
            stream_mode, payload = chunk
        else:
            # Some versions return dict-like objects
            stream_mode = getattr(chunk, "stream_mode", "updates")
            payload = chunk

        if stream_mode == "updates" and isinstance(payload, dict):
            for node_name in payload.keys():
                if node_name != "__start__":
                    yield {"type": "node", "node": node_name}

        if stream_mode == "values" and isinstance(payload, dict):
            if payload.get("__interrupt__"):
                yield {
                    "type": "interrupt",
                    "message": payload.get("response", "Please confirm this action."),
                    "plan": payload.get("plan", {}),
                    "conversation_id": payload.get("conversation_id"),
                }
                return

            if payload.get("response") and payload.get("response_metadata") is not None:
                yield {
                    "type": "final",
                    "response": payload["response"],
                    "conversation_id": payload.get("conversation_id"),
                    "metadata": payload.get("response_metadata", {}),
                }
                return
