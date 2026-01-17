def build_email_prompt(reply_context: dict) -> str:
    required_keys = ["originalEmail", "guidelines"]
    for key in required_keys:
        if key not in reply_context:
            raise ValueError(f"reply_context missing required key: {key}")

    original = reply_context["originalEmail"]
    guidelines = reply_context["guidelines"]

    sender = original.get("from", "Unknown sender")
    subject = original.get("subject", "No subject")
    body = original.get("body", "").strip()

    tone = guidelines.get("tone", "polite and professional")
    length = guidelines.get("length", "short")

    return f"""
You are an assistant that writes polite, respectful, and natural email replies
on behalf of an individual (not a company).

### ORIGINAL EMAIL
From: {sender}
Subject: {subject}

Body:
{body}

### REPLY GUIDELINES
- Write in first person ("I", not "we")
- Be appreciative and respectful
- Use soft, courteous language
- Do NOT sound demanding, final, or authoritative
- Avoid strong words like "however", "we need", "we will"
- Keep the reply calm and non-committal
- Length: {length}

### STRICT RULES
- Write ONLY the email body
- No subject line
- No signature
- No greetings like "Hi" or "Hello"
- No markdown or bullet points

### TASK
Write a natural, polite reply acknowledging the email above.
""".strip()
