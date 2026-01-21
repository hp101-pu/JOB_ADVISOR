from mcp.server.fastmcp import FastMCP
import base64
from email.message import EmailMessage

from gmail_context import get_gmail_service
from services.gmail_service import (
    fetch_recent_messages,
    get_full_message,
    parse_email
)
from services.job_email_filter import is_job_related

mcp = FastMCP("gmail-mcp")

# ---------------------------
# READ: recent job emails
# ---------------------------
@mcp.tool()
def get_recent_job_emails(
    userId: str,
    lookback_days: int = 7,
    max_results: int = 30
):
    service = get_gmail_service(userId)

    messages = fetch_recent_messages(
        service,
        lookback_days=lookback_days,
        max_results=max_results
    )

    emails = []
    for msg in messages:
        full_msg = get_full_message(service, msg["id"])
        parsed = parse_email(full_msg)

        if is_job_related(parsed):
            emails.append(parsed)

    return {"emails": emails}


# ---------------------------
# READ: email by id
# ---------------------------
@mcp.tool()
def get_email_by_id(userId: str, message_id: str):
    service = get_gmail_service(userId)

    message = service.users().messages().get(
        userId="me",
        id=message_id,
        format="full"
    ).execute()

    parsed = parse_email(message)
    return {"email": parsed}


# ---------------------------
# READ-ONLY: draft reply
# ---------------------------
@mcp.tool()
def draft_reply(
    userId: str,
    message_id: str,
    tone: str = "professional"
):
    service = get_gmail_service(userId)

    message = service.users().messages().get(
        userId="me",
        id=message_id,
        format="full"
    ).execute()

    parsed = parse_email(message)

    return {
        "reply_context": {
            "to": parsed["from"],
            "subject": f"Re: {parsed['subject']}",
            "threadId": message["threadId"],
            "messageId":message_id,
            "originalEmail": {
                "from": parsed["from"],
                "subject": parsed["subject"],
                "date": parsed["date"],
                "body": parsed["body"]
            },
            "guidelines": {
                "tone": tone,
                "length": "short",
                "style": "clear and polite"
            }
        }
    }


# ---------------------------
# WRITE: send email
# ---------------------------
@mcp.tool()
def send_email(
    userId: str,
    to: str,
    subject: str,
    body: str,
    threadId: str,
    in_reply_to: str
):
    service = get_gmail_service(userId)

    msg = EmailMessage()
    msg["To"] = to
    msg["Subject"] = subject
    msg["In-Reply-To"] = in_reply_to
    msg["References"] = in_reply_to
    msg.set_content(body)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    sent = service.users().messages().send(
        userId="me",
        body={
            "raw": raw,
            "threadId": threadId
        }
    ).execute()

    return {
        "status": "sent",
        "messageId": sent["id"],
        "threadId": sent["threadId"]
    }



@mcp.tool()
def ping():
    return "pong"


if __name__ == "__main__":
    mcp.run(transport="stdio")
