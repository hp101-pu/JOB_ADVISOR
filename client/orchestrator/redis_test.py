from client.orchestrator.redis_client import redis_client
from client.ask_seekr.memory import (
    get_conversation_context,
    save_conversation_turn,
)

USER_ID = "test_user"
CONVERSATION_ID = "12345"

if redis_client is None:
    print("[REDIS TEST] Redis is not available. Skipping direct Redis test.")
else:
    save_conversation_turn(
        CONVERSATION_ID,
        "Hey tell me about my amazon interview",
        "I can help with that.",
        USER_ID,
    )
    context = get_conversation_context(CONVERSATION_ID, USER_ID)
    print(f"[REDIS TEST] Saved context: {context}")