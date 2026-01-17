from client.ask_seekr.memory import (
    get_conversation_context,
    save_conversation_turn,
)

def test_memory():
    conversation_id = "test-convo-2"

    save_conversation_turn(
        conversation_id,
        user_message="Hi Seekr",
        assistant_message="Hello! How can I help you?"
    )

    save_conversation_turn(
        conversation_id,
        user_message="Find me Python jobs",
        assistant_message="Sure, looking for Python roles."
    )

    context = get_conversation_context(conversation_id)

    print("🧠 Conversation context:")
    for turn in context:
        print(turn)


if __name__ == "__main__":
    test_memory()
