import asyncio
import uuid

from client.ask_seekr.planner import planner_decide
from client.ask_seekr.memory import (
    get_conversation_context,
    save_conversation_turn,
)


async def test_planner():
    # Use fresh conversation every run
    conversation_id = f"test-{uuid.uuid4().hex[:8]}"
    print("🧠 Conversation ID:", conversation_id)
    print("-" * 50)

    # -----------------------------
    # Turn 1 — Job search
    # -----------------------------
    user_message = "I am looking for remote Python backend developer jobs in India."

    context = get_conversation_context(conversation_id)

    decision = await planner_decide(
        user_message=user_message,
        conversation_context=context,
    )

    print("USER:", user_message)
    print("PLANNER DECISION:")
    print(decision)

    save_conversation_turn(
        conversation_id=conversation_id,
        user_message=user_message,
        assistant_message=decision["reasoning"],
    )

    print("-" * 50)

    # -----------------------------
    # Turn 2 — Calendar event
    # -----------------------------
    user_message = """Schedule an interview with Google for the Software Engineer role.

Date: 2026-02-05
Start Time: 10:00
End Time: 11:00
Timezone: Asia/Kolkata
Meeting link: https://meet.google.com/xyz-abcd
"""

    context = get_conversation_context(conversation_id)

    decision = await planner_decide(
        user_message=user_message,
        conversation_context=context,
    )

    print("USER:", user_message)
    print("PLANNER DECISION:")
    print(decision)

    save_conversation_turn(
        conversation_id=conversation_id,
        user_message=user_message,
        assistant_message=decision["reasoning"],
    )

    print("-" * 50)

    # -----------------------------
    # Turn 3 — Email reply preview
    # -----------------------------
    user_message = """Please draft a professional reply to this recruiter email.

Message ID: 18c2f9ab
Subject: Interview Opportunity at Microsoft
"""

    context = get_conversation_context(conversation_id)

    decision = await planner_decide(
        user_message=user_message,
        conversation_context=context,
    )

    print("USER:", user_message)
    print("PLANNER DECISION:")
    print(decision)

    save_conversation_turn(
        conversation_id=conversation_id,
        user_message=user_message,
        assistant_message=decision["reasoning"],
    )


if __name__ == "__main__":
    asyncio.run(test_planner())
