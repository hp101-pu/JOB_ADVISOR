from typing import Dict, Any
import os
import httpx

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000")


async def create_calendar_event_pipeline(
    event_type: str,
    company: str,
    date: str,
    start_time: str,
    end_time: str,
    user_id: str,
    jwt: str = None,
    role: str = None,
    timezone: str = "Asia/Kolkata",
    meet_link: str = None,
    description: str = None,
) -> Dict[str, Any]:
    """
    Pipeline to create a calendar event.

    Calls the backend's /api/calendar/events/direct endpoint which:
    1. Saves to MongoDB CalendarEvent collection (always — app calendar)
    2. Pushes to user's Google Calendar if connected (non-fatal)

    Returns success with googleSynced flag so the frontend can show
    whether the event was also synced to Google Calendar.
    """

    try:
        print(f"[calendar_agent] Creating calendar event: {event_type} at {company} for user {user_id}")

        if not jwt:
            raise ValueError("JWT is required to save calendar event to backend")

        summary = f"{company} | {event_type}"
        if role:
            summary += f" ({role})"

        payload = {
            "summary": summary,
            "company": company,
            "role": role or "",
            "date": date,
            "startTime": start_time,
            "endTime": end_time,
            "timezone": timezone,
            "meetLink": meet_link or "",
            "description": description or "",
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {jwt}",
        }

        print(f"[calendar_agent] POST {BACKEND_URL}/api/calendar/events/direct | payload={payload}")

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{BACKEND_URL}/api/calendar/events/direct",
                json=payload,
                headers=headers,
            )

        print(f"[calendar_agent] Backend response: status={resp.status_code} | body={resp.text[:300]}")

        if resp.status_code != 200:
            raise RuntimeError(f"Backend save failed ({resp.status_code}): {resp.text}")

        result = resp.json()
        data = result.get("data", {})

        google_synced = data.get("googleSynced", False)
        google_link = data.get("googleEventLink", "")

        if google_synced:
            print(f"[calendar_agent] Event saved to MongoDB AND Google Calendar: {google_link}")
        else:
            print(f"[calendar_agent] Event saved to MongoDB only (Google Calendar not connected or push failed)")

        return {
            "success": True,
            "message": "Event created successfully",
            "event_id": data.get("eventId", ""),
            "event_link": google_link,
            "google_synced": google_synced,
            "data": data,
        }

    except Exception as e:
        print(f"[calendar_agent] Calendar event creation error: {e}")
        import traceback
        traceback.print_exc()

        return {
            "success": False,
            "error": str(e),
            "message": "Failed to create calendar event",
        }