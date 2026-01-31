import httpx

BASE_URL = "http://localhost:5000"


async def query_calendar_events_from_db(jwt: str) -> dict:
    """
    Fetch all calendar events for the user from MongoDB via the Node backend.
    Returns events from the CalendarEvent collection (created by cron or chatbot).
    """
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            f"{BASE_URL}/api/calendar/events/all",
            headers={
                "Authorization": f"Bearer {jwt}",
            },
        )

    if response.status_code != 200:
        raise RuntimeError(
            f"Calendar query failed ({response.status_code}): {response.text}"
        )

    return response.json()
