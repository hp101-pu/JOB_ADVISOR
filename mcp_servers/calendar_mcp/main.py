from mcp.server.fastmcp import FastMCP
from calendar_mcp.schemas import CalendarEventInput
from calendar_mcp.calendar_service import create_calendar_event

mcp = FastMCP("calendar-mcp")

@mcp.tool()
def schedule_event(event: CalendarEventInput):
    """
    Schedule interview / assessment in Google Calendar
    """
    return create_calendar_event(event)

if __name__ == "__main__":
    mcp.run()