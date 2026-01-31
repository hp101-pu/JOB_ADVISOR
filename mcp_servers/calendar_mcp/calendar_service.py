# My calendar tool called in main.py.
from googleapiclient.discovery import build
from auth import get_calendar_credentials
from utils import to_rfc3339
from schemas import CalendarEventInput




def create_calendar_event(event: CalendarEventInput):
    creds = get_calendar_credentials()
    service = build("calendar", "v3", credentials=creds)

    start_dt = to_rfc3339(event.date, event.start_time, event.timezone)
    end_dt = to_rfc3339(event.date, event.end_time, event.timezone)

    summary = f"{event.company} | {event.event_type}"
    if event.role:
        summary += f" ({event.role})"

    event_body = {
        "summary": summary,
        "description": event.description,
        "start": {
            "dateTime": start_dt,
            "timeZone": event.timezone,
        },
        "end": {
            "dateTime": end_dt,
            "timeZone": event.timezone,
        },
    }

    if event.meet_link:
        event_body["location"] = event.meet_link

    created_event = service.events().insert(
        calendarId="primary",
        body=event_body
    ).execute()

    return {
        "status": "success",
        "event_link": created_event.get("htmlLink")
    }