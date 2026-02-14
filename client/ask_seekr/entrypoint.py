from typing import Optional, Dict, Any
import base64
import json as _jwt_json

from langgraph.types import Command


NODE_API_URL_ENV = __import__("os").getenv("NODE_API_URL", "http://localhost:5000")


# -------------------------------------------------
# Helper: resolve messageId from sender keyword
# -------------------------------------------------

async def _resolve_message_id(user_message: str, jwt: str) -> str | None:
    """
    Uses Groq to extract the sender/company keyword from the user message,
    then queries the inbox to find the matching email's Gmail emailId.
    """
    from client.backend_client.email_query_api import query_emails_from_db
    from client.llm.groq_client import get_groq_client
    import asyncio

    # Step 1: Use Groq to extract just the sender/company name
    try:
        groq = get_groq_client()
        extraction = await asyncio.to_thread(
            groq.chat.completions.create,
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract only the company or sender name from the user's message. "
                        "Return ONLY the name, nothing else. No punctuation, no explanation. "
                        "Examples:\n"
                        "'draft reply for amazon email' -> 'amazon'\n"
                        "'reply to desmus and co' -> 'desmus'\n"
                        "'respond to shona labs interview' -> 'shona labs'\n"
                        "'draft a reply for my desmus and co gmail' -> 'desmus'"
                    )
                },
                {"role": "user", "content": user_message}
            ],
            temperature=0,
            max_tokens=20,
        )
        keyword = extraction.choices[0].message.content.strip().lower()
        print(f"🔵 Groq extracted sender keyword: '{keyword}'")
    except Exception as e:
        print(f"⚠️ Groq keyword extraction failed: {e}, falling back to raw message")
        keyword = user_message

    # Step 2: Query inbox using the clean keyword
    for attempt in [
        {"sender": keyword, "folder": "INBOX", "limit": 5},
        {"keyword": keyword, "folder": "INBOX", "limit": 5},
        {"keyword": keyword, "limit": 10},
    ]:
        try:
            result = await query_emails_from_db(jwt=jwt, **attempt)
            emails = result.get("emails", [])
            if emails:
                email_id = emails[0].get("emailId")
                print(f"🟢 Resolved emailId: '{email_id}' from sender '{emails[0].get('from')}'")
                return email_id
        except Exception:
            continue

    print(f"🔴 Could not resolve messageId for keyword: '{keyword}'")
    return None


# -------------------------------------------------
# Main Entrypoint
# -------------------------------------------------

async def handle_user_message(
    jwt: str,
    user_message: str,
    conversation_id: Optional[str],
    metadata: Optional[Dict[str, Any]] = None,
    confirmed: bool = False,
) -> Dict[str, Any]:
    """
    Core brain of Ask Seekr.

    Delegates to the LangGraph state machine implemented under
    client.ask_seekr.graph.
    """

    metadata = metadata or {}

    # Extract user_id from JWT so memory is scoped per user
    user_id = ""
    try:
        payload_part = jwt.split(".")[1]
        payload_part += "=" * (4 - len(payload_part) % 4)
        decoded = _jwt_json.loads(base64.b64decode(payload_part).decode("utf-8"))
        user_id = str(decoded.get("_id") or decoded.get("id") or decoded.get("sub") or "")
    except Exception:
        pass

    from client.ask_seekr.graph.state import ChatState
    from client.ask_seekr.graph.workflow import compiled_graph

    graph = compiled_graph()

    # Use the conversation_id as the thread_id so interrupts/checkpoints are
    # scoped per conversation.
    config = {"configurable": {"thread_id": conversation_id or "default"}}

    if confirmed:
        # Resume an interrupted confirmation. If the thread is not waiting on
        # an interrupt, LangGraph treats this as a fresh run and the confirmed
        # flag flows through validation normally.
        final_state = await graph.ainvoke(
            Command(resume={"confirmed": True}),
            config=config,
        )
    else:
        final_state = await _run_fresh(graph, user_message, jwt, user_id, conversation_id, metadata)

    # LangGraph surfaces interrupts as a state key rather than raising.
    if final_state.get("__interrupt__"):
        return {
            "response": final_state.get("response", "Please confirm this action."),
            "conversation_id": final_state.get("conversation_id"),
            "metadata": {
                "plan": final_state.get("plan", {}),
                "status": "NEEDS_CONFIRMATION",
            },
        }

    return {
        "response": final_state.get("response", ""),
        "conversation_id": final_state.get("conversation_id"),
        "metadata": final_state.get("response_metadata", {}),
    }


async def _run_fresh(
    graph,
    user_message: str,
    jwt: str,
    user_id: str,
    conversation_id: Optional[str],
    metadata: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Start a fresh graph run and surface NEEDS_CONFIRMATION interrupts."""
    from client.ask_seekr.graph.state import ChatState

    initial_state: ChatState = {
        "user_message": user_message,
        "jwt": jwt,
        "user_id": user_id,
        "conversation_id": conversation_id,
        "confirmed": False,
        "metadata": metadata or {},
        "conversation_context": [],
        "user_profile": {},
        "intent": "",
        "plan": {},
        "status": "",
        "message": "",
        "pipeline_result": None,
        "response": "",
        "response_metadata": {},
        "stream_tokens": [],
    }

    config = {"configurable": {"thread_id": conversation_id or "default"}}

    return await graph.ainvoke(initial_state, config=config)
