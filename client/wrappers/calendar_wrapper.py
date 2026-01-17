from typing import Dict
from client.mcp.client import get_mcp_client

async def schedule_calendar_event(
    event_type: str,
    company: str,
    date: str,
    start_time: str,
    end_time: str,
    role: str = None,
    timezone: str = "Asia/Kolkata",
    meet_link: str = None,
    description: str = None,
) -> Dict:
    """
    Schedule an event in Google Calendar via MCP.
    
    Args:
        event_type: "Online Assessment" or "Interview"
        company: Company name (e.g., "Amazon")
        date: Date in YYYY-MM-DD format
        start_time: Start time in HH:MM format
        end_time: End time in HH:MM format
        role: Job role (optional)
        timezone: Timezone (default: Asia/Kolkata)
        meet_link: Google Meet link (optional)
        description: Event description (optional)
    """
    
    print(f"[calendar_wrapper] Scheduling event: {event_type} at {company}")
    
    mcp = await get_mcp_client()
    
    async with mcp.session("calendar") as session:
        from langchain_mcp_adapters.client import load_mcp_tools
        tools = await load_mcp_tools(session)
        
        print(f"[calendar_wrapper] Available tools: {[t.name for t in tools]}")
        
        # Find the schedule_event tool
        tool = next((t for t in tools if t.name == "schedule_event"), None)
        if not tool:
            raise ValueError(f"schedule_event tool not found. Available: {[t.name for t in tools]}")
        
        # Prepare event data
        event_data = {
            "event_type": event_type,
            "company": company,
            "date": date,
            "start_time": start_time,
            "end_time": end_time,
            "timezone": timezone,
        }
        
        if role:
            event_data["role"] = role
        if meet_link:
            event_data["meet_link"] = meet_link
        if description:
            event_data["description"] = description
        
        print(f"[calendar_wrapper] Invoking schedule_event with: {event_data}")
        
        result = await tool.ainvoke({"event": event_data})
        
        print(f"[calendar_wrapper] Result: {result}")
        
        # Parse result (MCP returns dict directly for calendar)
        if isinstance(result, dict):
            return result
        
        # Handle list response
        if isinstance(result, list) and len(result) > 0:
            return result[0]
        
        raise ValueError(f"Unexpected result format: {result}")