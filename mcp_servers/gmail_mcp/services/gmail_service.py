from datetime import datetime,timedelta
from utils.email_utils import extract_body,extract_headers

def fetch_recent_messages(service,lookback_days=30, max_results=50):
   

    after_date = (datetime.utcnow() - timedelta(days=lookback_days)).strftime("%Y/%m/%d")

    # query = f"(in:inbox OR in:sent) after:{after_date}"
    # query = f"category:primary"
    query = f"in:inbox -category:promotions -category:social -category:updates"

    # google quert requires in this form

    response = service.users().messages().list(
        userId="me",
        q=query,
        maxResults=max_results
    ).execute()

    '''

    {
  "messages": [
    {"id": "18c8a...", "threadId": "18c8a..."},
    {"id": "18c8b...", "threadId": "18c8b..."}
  ]
}

    '''

    return response.get("messages", [])


def get_full_message(service, message_id):
    return service.users().messages().get(
        userId="me",
        id=message_id,
        format="full"
    ).execute()


def parse_email(message):
    payload = message.get("payload", {})
    headers = extract_headers(payload.get("headers", []))
    body = extract_body(payload)

    labels = message.get("labelIds", [])

    is_sent = "SENT" in labels
    is_inbox = "INBOX" in labels


    return {
        "id": message.get("id"),                       # Gmail message ID
        "threadId": message.get("threadId"),           # ✅ added
        "from": headers.get("from"),
        "to": headers.get("to"),                       # ✅ added
        "subject": headers.get("subject"),
        "date": headers.get("date"),                   # human-readable
        "timestamp": int(message.get("internalDate", 0)),  # ✅ reliable
        "labels":labels,
        "isSent":is_sent,
        "isInbox":is_inbox,         
        "body": body.strip()
    }
