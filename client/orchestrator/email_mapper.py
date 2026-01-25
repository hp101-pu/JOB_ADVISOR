from client.llm.llm_service import classify_email_semantic
from datetime import datetime

ALLOWED_TYPES = {
    "JOB", "INTERVIEW", "OFFER", "REJECTION", "OTHER"
}


def map_to_backend(email):
    """
    Maps parsed Gmail email → backend Email model
    """

    # -----------------------------
    # Date handling (REQUIRED)
    # -----------------------------
    timestamp = email.get("timestamp")

    if timestamp:
        date = datetime.utcfromtimestamp(timestamp / 1000)
    else:
        date = email.get("date")

    if not date:
        # 🔥 HARD FAIL (better than silent corruption)
        raise ValueError(f"Missing date for email {email.get('id')}")

    # -----------------------------
    # Classification (LLM)
    # -----------------------------
    result = classify_email_semantic(
        email.get("subject", ""),
        email.get("body", "")
    )

    is_relevant = bool(result.get("is_relevant", False))
    email_type = result.get("type", "OTHER").upper()
    if email_type not in ALLOWED_TYPES:
        print(f"[email_mapper] Unknown type '{email_type}', defaulting to OTHER for email: {email.get('id')}")
        email_type = "OTHER"

    if not is_relevant:
        print(f"[email_mapper] Marking email as non-relevant: {email.get('id')}")
        email_type = "OTHER"

    # -----------------------------
    # Final payload
    # -----------------------------
    folder = "SENT" if email.get("isSent") else "INBOX"

    return {
        "emailId": email["id"],
        "type": email_type,
        "threadId": email["threadId"],
        "from": email.get("from", ""),
        "subject": email.get("subject", ""),
        "text": email.get("body", ""),
        "date": date.isoformat(),
        "folder": folder,
        "isRelevant": is_relevant,
    }
