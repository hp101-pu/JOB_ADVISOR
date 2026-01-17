from typing import Dict, Any
from client.wrappers.calendar_wrapper import schedule_calendar_event

async def create_calendar_event_pipeline(
    event_type: str,
    company: str,
    date: str,
    start_time: str,
    end_time: str,
    user_id: str,
    role: str = None,
    timezone: str = "Asia/Kolkata",
    meet_link: str = None,
    description: str = None,
) -> Dict[str, Any]:
    """
    Pipeline to create a calendar event.
    
    Handles:
    - Input validation
    - Event creation via Calendar MCP
    - Error handling and response formatting
    """
    
    try:
        print(f"📅 Creating calendar event: {event_type} at {company} for user {user_id}")
        
        # Call the calendar wrapper
        result = await schedule_calendar_event(
            event_type=event_type,
            company=company,
            date=date,
            start_time=start_time,
            end_time=end_time,
            role=role,
            timezone=timezone,
            meet_link=meet_link,
            description=description,
        )
        
        print(f"✅ Calendar event created successfully")
        
        return {
            "success": True,
            "message": "Event created successfully",
            "event_link": result.get("event_link"),
            "data": result,
        }
        
    except Exception as e:
        print(f"❌ Calendar event creation error: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to create calendar event",
        }