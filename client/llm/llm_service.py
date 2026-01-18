import json

from client.llm.groq_client import get_groq_client, groq_chat_with_fallback


MODEL_ID = "llama-3.1-8b-instant"


def generate_email_reply(prompt: str) -> str:
    """
    Generates a polite, professional email reply.
    Returns ONLY the email body.
    """

    response = groq_chat_with_fallback(
        model=MODEL_ID,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional assistant that writes concise, "
                    "polite, business-appropriate email replies."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.4,
        max_tokens=300,
    )

    return response.choices[0].message.content.strip()


def classify_email_semantic(subject: str, body: str) -> dict:
    """
    Determines whether an email is job-related and classifies it.
    Includes DEBUG logs.
    """

    prompt = f"""
You classify emails related to job applications.

Decide:
1. Is this a REAL job-related email?
2. If yes, classify into ONE category:
   OFFER, INTERVIEW, REJECTION, JOB, OTHER

Return STRICT JSON only (no markdown, no explanation):
{{
  "is_relevant": true | false,
  "type": "OFFER | INTERVIEW | REJECTION | JOB | OTHER"
}}

Subject:
{subject}

Body:
{body}
""".strip()

    response = groq_chat_with_fallback(
        model=MODEL_ID,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=120,
    )

    raw_text = response.choices[0].message.content.strip()

    # 🔍 DEBUG LOG
    print("\n[LLM RAW RESPONSE]")
    print(raw_text)

    # 🔧 Strip markdown if present
    cleaned = raw_text
    if raw_text.startswith("```"):
        cleaned = raw_text.strip("`").replace("json", "").strip()

    try:
        result = json.loads(cleaned)
    except Exception as e:
        print("[LLM PARSE ERROR]", e)
        return {"is_relevant": False, "type": "OTHER"}

    # 🔍 DEBUG LOG
    print("[LLM PARSED RESULT]", result)

    return {
        "is_relevant": bool(result.get("is_relevant", False)),
        "type": result.get("type", "OTHER").upper(),
    }


def classify_request_requirements(
    user_message: str,
    conversation_context: list | None = None,
) -> dict:
    """
    Classifies whether a request requires:
    - RAG (knowledge lookup)
    - TOOL / ACTION execution

    Returns STRICT JSON-compatible dict.
    """

    prompt = f"""
You are an intent classification system.

Decide:
1. Does the user need knowledge lookup or explanation? (requires_rag)
2. Does the user want an action or tool execution? (requires_tools)

Rules:
- RAG: explanations, definitions, debugging, errors, "why", "how"
- ACTION: run, execute, trigger, start, deploy, schedule

Respond ONLY in valid JSON:
{{
  "requires_rag": true | false,
  "requires_tools": true | false,
  "intent": "KNOWLEDGE" | "ACTION" | "BOTH"
}}

User message:
{user_message}

Conversation context:
{conversation_context}
""".strip()

    response = groq_chat_with_fallback(
        model=MODEL_ID,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=120,
    )

    raw_text = response.choices[0].message.content.strip()


    print("\n[LLM RAW RESPONSE]")
    print(raw_text)

    print("\n[CALENDAR EXTRACTION RAW RESPONSE]")
    print(raw_text)

    # Strip markdown if present
    cleaned = raw_text
    if raw_text.startswith("```"):
        cleaned = raw_text.strip("`").replace("json", "").strip()

    try:
        result = json.loads(cleaned)
    except Exception as e:
        print("[LLM PARSE ERROR]", e)
        return {
            "requires_rag": False,
            "requires_tools": False,
            "intent": "KNOWLEDGE",
        }


    print("[LLM PARSED RESULT]", result)

    return {
        "requires_rag": bool(result.get("requires_rag", False)),
        "requires_tools": bool(result.get("requires_tools", False)),
        "intent": result.get("intent", "KNOWLEDGE").upper(),
    }
    

def extract_calendar_details_from_email(subject: str, text: str) -> dict:
    """
    Extracts calendar event details from an interview email.
    Uses LLM to parse unstructured email text into structured calendar data.
    """
    
    prompt = f"""
You are an AI assistant that extracts calendar event details from interview invitation emails.

Extract the following information from the email:
1. Company name
2. Job role/position  
3. Interview date (format: YYYY-MM-DD)
4. Interview start time (format: HH:MM in 24-hour format)
5. Interview end time (format: HH:MM in 24-hour format, estimate 1 hour if not specified)
6. Meeting link (Google Meet, Zoom, Teams, etc.)
7. Timezone (default to "Asia/Kolkata" if not specified)
8. Brief description/summary

Return STRICT JSON only (no markdown, no explanation):
{{
  "company": "Company Name",
  "role": "Job Title",
  "date": "YYYY-MM-DD",
  "startTime": "HH:MM",
  "endTime": "HH:MM",
  "meetLink": "https://...",
  "timezone": "Asia/Kolkata",
  "description": "Brief summary"
}}

If any field cannot be extracted, use these defaults:
- role: "Interview"
- endTime: 1 hour after startTime
- timezone: "Asia/Kolkata"
- description: subject line
- meetLink: "" (empty string if not found)

Email Subject:
{subject}

Email Body:
{text}
""".strip()

    response = groq_chat_with_fallback(
        model=MODEL_ID,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=400,
    )

    raw_text = response.choices[0].message.content.strip()

    print("\n[CALENDAR EXTRACTION RAW RESPONSE]")
    print(raw_text)

    # Strip markdown if present
    cleaned = raw_text
    if raw_text.startswith("```"):
        cleaned = raw_text.strip("`").replace("json", "").strip()

    try:
        result = json.loads(cleaned)
    except Exception as e:
        print("[CALENDAR EXTRACTION PARSE ERROR]", e)
        raise ValueError(f"Failed to parse LLM response: {e}")

    print("[CALENDAR EXTRACTION PARSED RESULT]", result)

    # Validate required fields
    required_fields = ["company", "date", "startTime", "endTime"]
    for field in required_fields:
        if not result.get(field):
            raise ValueError(f"Missing required field: {field}")

    # Set defaults for optional fields
    result.setdefault("role", "Interview")
    result.setdefault("timezone", "Asia/Kolkata")
    result.setdefault("description", subject)
    result.setdefault("meetLink", "")

    return result