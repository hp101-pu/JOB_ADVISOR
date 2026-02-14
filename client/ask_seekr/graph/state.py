"""Graph state schema for the AskSeekr chatbot."""

from operator import add
from typing import Annotated, Any, Dict, List, Optional, TypedDict


class ChatState(TypedDict):
    """Full state passed between LangGraph nodes.

    Inputs are populated by the entrypoint wrapper; intermediate keys are
    filled by nodes as the graph executes.
    """

    # Inputs (set by entrypoint wrapper before graph invocation)
    user_message: str
    jwt: str
    user_id: str  # derived from JWT by the wrapper
    conversation_id: Optional[str]
    confirmed: bool
    metadata: Dict[str, Any]

    # Loaded context
    conversation_context: List[Dict[str, Any]]
    user_profile: Dict[str, Any]

    # Planner output
    intent: str  # "CHAT" or "ACTION"
    plan: Dict[str, Any]

    # Validation output
    status: str  # "OK", "BLOCKED", "NEEDS_CONFIRMATION"
    message: str

    # Execution output
    pipeline_result: Optional[Dict[str, Any]]

    # Final output
    response: str
    response_metadata: Dict[str, Any]

    # Streaming
    stream_tokens: Annotated[List[str], add]
