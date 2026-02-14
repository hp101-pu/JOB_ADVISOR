"""LangGraph node implementations for the AskSeekr chatbot."""

from client.ask_seekr.graph.state import ChatState
from client.ask_seekr.memory import get_conversation_context
from client.ask_seekr.planner import planner_decide
from client.ask_seekr.profile_fetcher import fetch_user_profile


async def load_context_node(state: ChatState) -> dict:
    """Load conversation history and user profile.

    Reads ``conversation_id``, ``user_id``, and ``jwt`` from the state and
    returns ``conversation_context`` and ``user_profile``.
    """
    conversation_id = state.get("conversation_id")
    user_id = state.get("user_id", "")
    jwt = state.get("jwt", "")

    conversation_context = get_conversation_context(conversation_id, user_id)
    user_profile = await fetch_user_profile(jwt)

    return {
        "conversation_context": conversation_context,
        "user_profile": user_profile,
    }


async def planner_node(state: ChatState) -> dict:
    """Decide CHAT vs ACTION and choose a pipeline.

    Builds the metadata dict expected by ``planner_decide``, injecting the
    loaded ``user_profile`` and the current ``confirmed`` flag.
    """
    metadata = dict(state.get("metadata") or {})
    user_profile = state.get("user_profile", {})
    if user_profile:
        metadata["user_profile"] = user_profile

    plan = await planner_decide(
        user_message=state["user_message"],
        conversation_context=state.get("conversation_context", []),
        metadata=metadata,
    )

    # Preserve the confirmation flag for downstream validation
    plan["confirmed"] = state.get("confirmed", False)

    return {
        "intent": plan.get("type", "CHAT"),
        "plan": plan,
    }


async def chat_node(state: ChatState) -> dict:
    """Generate a conversational reply for CHAT intent.

    Mirrors the original ``entrypoint.py`` CHAT branch; memory persistence is
    handled separately by ``save_memory_node``.
    """
    from client.llm.openai_client import get_openai_client, get_openai_model

    client = get_openai_client()
    model = get_openai_model()

    user_message = state["user_message"]
    conversation_context = state.get("conversation_context", [])
    user_profile = state.get("user_profile", {})

    context_messages = [
        {"role": t["role"], "content": t["content"]}
        for t in conversation_context
    ]

    if user_profile:
        name = user_profile.get("fullname", "there")
        first_name = name.split()[0] if name else "there"
        age_str = f", {user_profile['age']} years old" if user_profile.get("age") else ""
        role_str = f" Currently working as {user_profile['current_role']} at {user_profile['current_company']}." if user_profile.get("current_role") else ""
        edu_str = f" Studied {user_profile['latest_degree']} at {user_profile['latest_institution']}." if user_profile.get("latest_degree") else ""
        skills_str = f" Skills: {', '.join(user_profile['skills'][:6])}." if user_profile.get("skills") else ""
        location_str = f" Based in {user_profile['location_string']}." if user_profile.get("location_string") else ""
        otw_str = " They are currently open to work." if user_profile.get("open_to_work") else ""
        about_str = f" About them: {user_profile['about']}." if user_profile.get("about") else ""

        personal_context = (
            f"You are talking to {name}{age_str}.{location_str}{role_str}"
            f"{edu_str}{skills_str}{otw_str}{about_str}\n"
            f"Address them by their first name ({first_name}) naturally when appropriate. "
            f"Use their background to give personalised, relevant advice."
        )
    else:
        personal_context = "You don't have the user's profile yet — be helpful and friendly."

    chat_response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are Seekr AI, a friendly and knowledgeable job search assistant. "
                    "Help the user with their job search, career advice, interview tips, "
                    "resume guidance, and anything related to finding a job. "
                    "Be concise, warm, and helpful.\n\n"
                    f"USER CONTEXT:\n{personal_context}"
                ),
            },
            *context_messages,
            {"role": "user", "content": user_message},
        ],
        temperature=0.7,
        max_tokens=500,
    )

    reply = chat_response.choices[0].message.content.strip()
    return {"response": reply}


async def resolve_email_message_id_node(state: ChatState) -> dict:
    """Resolve a missing ``messageId`` for the ``email_reply_preview`` pipeline.

    This node mirrors the original ``entrypoint.py`` behavior: it runs **after**
    validation, so when validation blocks on a missing required argument this code
    is effectively unreachable. It is kept as a drop-in refactor for parity and can
    be reordered in a future fix.
    """
    plan = state.get("plan", {})
    if plan.get("pipeline") != "email_reply_preview" or plan["args"].get("messageId"):
        return {}

    from client.ask_seekr.entrypoint import _resolve_message_id

    resolved_id = await _resolve_message_id(
        user_message=state["user_message"],
        jwt=state["jwt"],
    )

    if resolved_id:
        plan["args"]["messageId"] = resolved_id
        return {"plan": plan}

    reply = (
        "I couldn't find that email in your inbox. "
        "Could you be more specific — e.g. the subject line or sender's name?"
    )
    return {
        "response": reply,
        "response_metadata": {"plan": plan},
    }


async def validate_node(state: ChatState) -> dict:
    """Validate the planner's ACTION decision.

    Delegates to ``client.ask_seekr.validator.validate_plan`` and writes the
    resulting ``status`` and ``message`` into the graph state.
    """
    from client.ask_seekr.validator import validate_plan

    validation = validate_plan(state.get("plan", {}))
    status = validation["status"]
    message = validation.get("message", "")

    updates: dict = {"status": status, "message": message}
    if status in ("BLOCKED", "NEEDS_CONFIRMATION"):
        updates["response"] = message

    return updates


async def execute_node(state: ChatState) -> dict:
    """Execute the validated ACTION plan against the orchestrator."""
    from client.ask_seekr.executor import run_pipeline

    plan = state.get("plan", {})
    pipeline_name = plan.get("pipeline", "")
    endpoint = plan.get("endpoint", "")
    args = dict(plan.get("args", {}))
    jwt = state.get("jwt", "")

    result = await run_pipeline(
        pipeline_name=pipeline_name,
        endpoint=endpoint,
        args=args,
        jwt=jwt,
    )

    return {"pipeline_result": result}


async def summarize_node(state: ChatState) -> dict:
    """Summarize the raw pipeline result into a human-readable response."""
    import json as _json

    from client.llm.openai_client import get_openai_client, get_openai_model

    client = get_openai_client()
    model = get_openai_model()

    user_message = state["user_message"]
    result = state.get("pipeline_result", {})

    try:
        result_text = _json.dumps(result, indent=2) if isinstance(result, dict) else str(result)
    except Exception:
        result_text = str(result)

    summary_response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are Seekr AI, a precise and friendly job search assistant. "
                    "You will be given raw pipeline result data and must summarize it for the user. "
                    "\n\n"
                    "STRICT ACCURACY RULES — YOU MUST FOLLOW THESE:\n"
                    "1. NEVER invent, infer, or assume any information not explicitly present in the data.\n"
                    "2. Use EXACT values from the data: sender names, company names, email subjects, counts, dates.\n"
                    "3. If the data says 'from' is 'Ritvik Rai <rai.ritvik2005@gmail.com>', the sender is 'Ritvik Rai', NOT 'Gmail'.\n"
                    "4. Only mention things that are ACTUALLY in the data. If there are 0 rejections, do not mention rejections.\n"
                    "5. If a count is 0, do not say 'no X yet' — simply omit that category entirely.\n"
                    "6. Do NOT infer application status from email types unless explicitly stated in the data.\n"
                    "7. For emails: use the 'subject', 'from', and 'type' fields exactly as given.\n"
                    "8. For jobs: use the exact title, company, salary, and URL from the data.\n"
                    "\n"
                    "FORMAT RULES:\n"
                    "- Be concise, warm, and friendly.\n"
                    "- Use markdown: bold for names/companies, bullet points for lists.\n"
                    "- Keep it under 250 words.\n"
                    "- Never show raw JSON or field names like 'emailId', '_id', 'lastSubject', 'emailCount', 'lastContact'.\n"
                    "- For interview emails: show the subject, sender, date naturally. E.g. '**Flipkart** — Interview Scheduled for March 30 at 10:30 AM'.\n"
                    "- Never use technical grouping fields. Present each email as a human-readable item.\n"
                    "- If data has a meeting link, show it as a clickable link."
                ),
            },
            {"role": "user", "content": f"User asked: {user_message}"},
            {"role": "assistant", "content": f"Pipeline result data (use ONLY this data, nothing else):\n{result_text}"},
            {"role": "user", "content": "Summarize this accurately using only the data above. Do not invent anything."},
        ],
        temperature=0.1,
        max_tokens=600,
    )

    human_reply = summary_response.choices[0].message.content.strip()
    return {"response": human_reply}


async def save_memory_node(state: ChatState) -> dict:
    """Persist the conversation turn to Redis.

    - CHAT replies: save the full assistant reply.
    - ACTION results: save only a neutral note, never raw pipeline data or
      generated summaries that contain real email/job content.
    """
    from client.ask_seekr.memory import save_conversation_turn

    conversation_id = state.get("conversation_id")
    user_id = state.get("user_id", "")
    user_message = state["user_message"]
    intent = state.get("intent", "CHAT")
    response = state.get("response", "")
    plan = state.get("plan", {})

    status = state.get("status", "OK")

    if intent == "CHAT":
        assistant_message = response
    elif status in ("BLOCKED", "NEEDS_CONFIRMATION"):
        assistant_message = state.get("message") or response
    else:
        pipeline_name = plan.get("pipeline", "action")
        assistant_message = f"Ran pipeline '{pipeline_name}' successfully."

    save_conversation_turn(
        conversation_id=conversation_id,
        user_message=user_message,
        assistant_message=assistant_message,
        user_id=user_id,
    )

    return {}


async def confirm_node(state: ChatState) -> dict:
    """Pause the graph and ask the user to confirm a high-risk action.

    The value returned by ``interrupt`` is supplied by the caller when the
    graph is resumed (e.g. ``{"confirmed": True}``). A ``False`` value
    cancels the action.
    """
    from langgraph.types import interrupt

    resume_value = interrupt(
        {
            "message": state.get("message", ""),
            "plan": state.get("plan", {}),
        }
    )

    confirmed = bool(resume_value.get("confirmed", False)) if isinstance(resume_value, dict) else False
    updates = {"confirmed": confirmed}
    if confirmed:
        # Mirror the confirmed flag into the plan so the validator sees it.
        plan = dict(state.get("plan", {}))
        plan["confirmed"] = True
        updates["plan"] = plan
    else:
        updates["response"] = "Action cancelled."

    return updates


async def respond_node(state: ChatState) -> dict:
    """Assemble the final JSON returned to the API caller."""
    plan = state.get("plan", {})
    pipeline_result = state.get("pipeline_result") or {}

    response_metadata = {"plan": plan}

    # Pass through calendar event sync info for frontend display
    if plan.get("pipeline") == "calendar_create_event" and isinstance(pipeline_result, dict):
        response_metadata["event_created"] = pipeline_result.get("success", False)
        response_metadata["google_synced"] = pipeline_result.get("google_synced", False)

    return {
        "response": state.get("response", ""),
        "conversation_id": state.get("conversation_id"),
        "response_metadata": response_metadata,
    }
