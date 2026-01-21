from datetime import datetime
from dateutil import tz


def to_rfc3339(date: str, time: str, timezone: str) -> str:
    """
    Converts date + time + timezone to RFC3339 format
    """
    local_tz = tz.gettz(timezone)
    dt = datetime.strptime(
        f"{date} {time}",
        "%Y-%m-%d %H:%M"
    )
    dt = dt.replace(tzinfo=local_tz)
    return dt.isoformat()