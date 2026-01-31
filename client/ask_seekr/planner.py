"""
Planner (GPT-4o-mini)
====================

Uses OpenAI chat.completions with a strict JSON-only prompt to decide:
- CHAT vs ACTION
- Which pipeline from PIPELINE_REGISTRY
- Extract arguments safely
"""

from typing import Dict, Any, List, Optional
import json

from client.ask_seekr.registry.pipeline_registry import PIPELINE_REGISTRY
from client.llm.openai_client import get_openai_client, get_openai_model


# -------------------------------------------------
# Helpers
# -------------------------------------------------

def _build_registry_prompt() -> str:
    blocks = []
    for name, cfg in PIPELINE_REGISTRY.items():
        blocks.append(
            f"""
Pipeline name: {name}
Description: {cfg['description']}
Risk level: {cfg['risk']}
Required arguments: {cfg['required_args']}
Optional arguments: {cfg['optional_args']}
"""
        )
    return "\n".join(blocks)


def _build_context_prompt(context: List[Dict[str, Any]]) -> str:
    if not context:
        return "No prior conversation."
    return "\n".join(f"{t['role']}: {t['content']}" for t in context)


def _find_missing_args(pipeline_name: str, args: Dict[str, Any]) -> List[str]:
    required = PIPELINE_REGISTRY[pipeline_name]["required_args"]
    return [k for k in required if k not in args or args[k] in ("", None)]


# -------------------------------------------------
# Main planner
# -------------------------------------------------

def _build_profile_prompt(metadata: Dict[str, Any]) -> str:
    p = metadata.get("user_profile", {})
    if not p:
        return "No user profile available."

    lines = []
    if p.get("fullname"):       lines.append(f"Name: {p['fullname']}")
    if p.get("age"):            lines.append(f"Age: {p['age']}")
    if p.get("headline"):       lines.append(f"Headline: {p['headline']}")
    if p.get("current_role"):   lines.append(f"Current role: {p['current_role']} at {p.get('current_company', '')}")
    if p.get("latest_degree"): lines.append(f"Education: {p['latest_degree']} — {p.get('latest_institution', '')}")
    if p.get("skills"):         lines.append(f"Skills: {', '.join(p['skills'])}")
    if p.get("location_string"): lines.append(f"Location: {p['location_string']}")
    if p.get("open_to_work"):   lines.append("Status: Open to work")
    if p.get("about"):          lines.append(f"About: {p['about']}")

    return "\n".join(lines) if lines else "No user profile available."


async def planner_decide(
    user_message: str,
    conversation_context: Optional[List[Dict[str, Any]]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:

    conversation_context = conversation_context or []
    metadata = metadata or {}

    client = get_openai_client()
    model = get_openai_model()  # should be gpt-4o-mini

    registry_prompt = _build_registry_prompt()
    context_prompt = _build_context_prompt(conversation_context)
    profile_prompt = _build_profile_prompt(metadata)

    system_prompt = f"""
You are Seekr Planner, a strict routing agent.

Your job is to decide whether the user intent is:
- CHAT (pure conversation, no system action)
- ACTION (execute exactly one pipeline)

--------------------------------------------------
RULES (DO NOT BREAK)
--------------------------------------------------
1. You MUST output VALID JSON ONLY.
2. Do NOT include explanations outside JSON.
3. NEVER invent pipelines or arguments.
4. If intent matches a pipeline, return ACTION
   EVEN IF required arguments are missing.
5. Choose EXACTLY ONE pipeline for ACTION.
6. "show me", "give me", "what did X send", "contents of", "read my email"
   → ALWAYS use email_query pipeline, NEVER CHAT.
7. "summary", "overview", "briefing", "what happened"
   → ALWAYS use email_digest pipeline.
8. "draft a reply", "write a reply", "respond to"
   → ALWAYS use email_reply_preview pipeline.
9. For email_query, extract the sender company name into args.sender
   (e.g. "desmus and co" → sender: "desmus", "amazon" → sender: "amazon").
10. ANY query about interviews, assessments, or events — with OR without dates
    → ALWAYS use calendar_query pipeline (queries CalendarEvent collection).
    This includes: "list all interviews", "show my interviews", "all my interviews",
    "what interviews do I have", "interviews in July 2026", "events on 2025-07-15",
    "what's on my calendar", "upcoming interviews", "interviews available in the calendar".
    "interview emails", "show me interview emails", "what interview emails did I receive"
    → use email_query with args.type = "INTERVIEW" (queries Email collection).
    CRITICAL: If the user asks about interviews/assessments/events in any form,
    use calendar_query UNLESS they explicitly say "emails".
11. "how is my job search", "application status", "track my applications"
    → use application_stats pipeline.
12. NEVER use application_stats for questions about specific email types like interviews.

--------------------------------------------------
AVAILABLE PIPELINES
--------------------------------------------------
{registry_prompt}

--------------------------------------------------
USER PROFILE (use this to auto-fill args when user says "for me", "based on my profile", or doesn't specify keywords/location)
--------------------------------------------------
{profile_prompt}

--------------------------------------------------
CONVERSATION CONTEXT
--------------------------------------------------
{context_prompt}

--------------------------------------------------
RESPONSE FORMAT (JSON ONLY)
--------------------------------------------------
{{
  "type": "CHAT | ACTION",
  "pipeline": "<pipeline_name or null>",
  "args": {{}},
  "confidence": 0.0,
  "reasoning": "Short explanation"
}}

--------------------------------------------------
EXAMPLES
--------------------------------------------------

User: hi
{{
  "type": "CHAT",
  "pipeline": null,
  "args": {{}},
  "confidence": 0.9,
  "reasoning": "User is greeting."
}}

User: Find me Python jobs in Bangalore
{{
  "type": "ACTION",
  "pipeline": "job_search",
  "args": {{
    "keywords": "Python",
    "location": "Bangalore"
  }},
  "confidence": 0.95,
  "reasoning": "User wants Python jobs in Bangalore."
}}

User: Reply to the recruiter email
{{
  "type": "ACTION",
  "pipeline": "email_reply_preview",
  "args": {{}},
  "confidence": 0.7,
  "reasoning": "User wants to reply to an email but did not specify message ID."
}}

User: Show me my desmus&co email / give me the contents of my desmus and co email / what did amazon send me
{{
  "type": "ACTION",
  "pipeline": "email_query",
  "args": {{"sender": "desmus"}},
  "confidence": 0.92,
  "reasoning": "User wants to read/view an email from a specific sender. Use email_query with the sender keyword."
}}

User: Show me my offer emails / list my interview emails / any rejection emails?
{{
  "type": "ACTION",
  "pipeline": "email_query",
  "args": {{"type": "OFFER"}},
  "confidence": 0.92,
  "reasoning": "User wants to see emails filtered by type. Use email_query with the type field."
}}

User: What interviews do I have scheduled? / Show my scheduled interviews / any upcoming interviews? / Do I have any interviews coming up?
{{
  "type": "ACTION",
  "pipeline": "calendar_query",
  "args": {{}},
  "confidence": 0.95,
  "reasoning": "User wants to see scheduled calendar events (interviews, assessments). Use calendar_query to fetch from CalendarEvent collection, NOT email_query."
}}

User: List all interviews / show my interviews / all my interviews / what are all the interviews
{{
  "type": "ACTION",
  "pipeline": "calendar_query",
  "args": {{}},
  "confidence": 0.95,
  "reasoning": "User asks about all interviews. Use calendar_query to fetch from CalendarEvent collection. NOT email_query — email_query would only show INTERVIEW emails, not the actual scheduled calendar events."
}}

User: Mention all interviews in July 2026 / what interviews are on my calendar this month / events in 2026
{{
  "type": "ACTION",
  "pipeline": "calendar_query",
  "args": {{}},
  "confidence": 0.95,
  "reasoning": "User asks about interviews/events during a specific time period. Use calendar_query to fetch from CalendarEvent collection. NEVER email_query — email_query searches emails, not calendar events."
}}

User: Show me my interview emails / Any interview emails? / What interview emails did I receive?
{{
  "type": "ACTION",
  "pipeline": "email_query",
  "args": {{"type": "INTERVIEW"}},
  "confidence": 0.92,
  "reasoning": "User wants to see emails classified as INTERVIEW type. Use email_query with type=INTERVIEW."
}}

User: What emails did I receive this week? / Show me all my emails
{{
  "type": "ACTION",
  "pipeline": "email_digest",
  "args": {{"period": "week"}},
  "confidence": 0.9,
  "reasoning": "User wants a summary/overview of emails. Use email_digest."
}}

User: Create a calendar event for my Google interview on 2025-07-15 from 14:00 to 15:00
{{
  "type": "ACTION",
  "pipeline": "calendar_create_event",
  "args": {{
    "eventType": "interview",
    "company": "Google",
    "date": "2025-07-15",
    "startTime": "14:00",
    "endTime": "15:00"
  }},
  "confidence": 0.95,
  "reasoning": "User wants to create a calendar event. Use calendar_create_event."
}}

User: Schedule my Amazon assessment on 2025-08-01 at 10:00
{{
  "type": "ACTION",
  "pipeline": "calendar_create_event",
  "args": {{
    "eventType": "assessment",
    "company": "Amazon",
    "date": "2025-08-01",
    "startTime": "10:00",
    "endTime": "11:00"
  }},
  "confidence": 0.94,
  "reasoning": "User wants to schedule a calendar event. Use calendar_create_event."
}}

User: Find jobs for me (profile has skills: ["React", "Node.js"], location: "Bangalore, India")
{{
  "type": "ACTION",
  "pipeline": "job_search",
  "args": {{
    "keywords": "React Node.js",
    "location": "Bangalore",
    "country": "in"
  }},
  "confidence": 0.92,
  "reasoning": "User wants jobs matched to their profile. Used skills as keywords and profile location."
}}

Respond with JSON ONLY.
"""

    # -------------------------------------------------
    # OpenAI call (stable + deterministic)
    # -------------------------------------------------
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0,
        max_tokens=300,
    )

    raw_text = response.choices[0].message.content.strip()

    # -------------------------------------------------
    # Parse JSON safely
    # -------------------------------------------------
    try:
        decision = json.loads(raw_text)
    except json.JSONDecodeError:
        return {
            "type": "CHAT",
            "pipeline": None,
            "endpoint": None,
            "args": {},
            "missing": [],
            "risk": None,
            "requires_confirmation": False,
            "confidence": 0.4,
            "reasoning": "Planner could not parse model output",
        }

    # -------------------------------------------------
    # CHAT intent
    # -------------------------------------------------
    if decision.get("type") == "CHAT":
        return {
            "type": "CHAT",
            "pipeline": None,
            "endpoint": None,
            "args": {},
            "missing": [],
            "risk": None,
            "requires_confirmation": False,
            "confidence": decision.get("confidence", 0.6),
            "reasoning": decision.get("reasoning", "Conversational intent"),
        }

    # -------------------------------------------------
    # ACTION intent
    # -------------------------------------------------
    pipeline_name = decision.get("pipeline")

    if pipeline_name not in PIPELINE_REGISTRY:
        return {
            "type": "CHAT",
            "pipeline": None,
            "endpoint": None,
            "args": {},
            "missing": [],
            "risk": None,
            "requires_confirmation": False,
            "confidence": 0.3,
            "reasoning": "Invalid or unknown pipeline selected",
        }

    pipeline_cfg = PIPELINE_REGISTRY[pipeline_name]
    args = decision.get("args", {}) or {}

    missing_args = _find_missing_args(pipeline_name, args)

    return {
        "type": "ACTION",
        "pipeline": pipeline_name,
        "endpoint": pipeline_cfg["endpoint"],
        "args": args,
        "missing": missing_args,
        "risk": pipeline_cfg["risk"],
        "requires_confirmation": pipeline_cfg.get("requires_confirmation", False),
        "confidence": decision.get("confidence", 0.8),
        "reasoning": decision.get("reasoning", f"Matched pipeline '{pipeline_name}'"),
    }
