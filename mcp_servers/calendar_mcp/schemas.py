from pydantic import BaseModel
from typing import Optional


class CalendarEventInput(BaseModel):
    event_type: str              # "Online Assessment", "Interview"
    company: str                 # Amazon, Google
    role: Optional[str] = None   # SDE Intern
    date: str                    # YYYY-MM-DD
    start_time: str              # HH:MM
    end_time: str                # HH:MM
    timezone: str = "Asia/Kolkata"
    meet_link: Optional[str] = None
    description: Optional[str] = None