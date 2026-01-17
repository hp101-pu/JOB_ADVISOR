from typing import Dict, Any
from client.llm.llm_service import extract_calendar_details_from_email


async def extract_calendar_from_email_pipeline(
    subject: str,
    text: str,
) -> Dict[str, Any]:
    """
    Pipeline to extract calendar event details from an interview email.
    
    Args:
        subject: Email subject line
        text: Email body text
        
    Returns:
        Dictionary with calendar event details
    """
    
    try:
        print(f"🔍 Extracting calendar details from email: {subject[:50]}...")
        
        # Use LLM to extract calendar details
        calendar_details = extract_calendar_details_from_email(subject, text)
        
        print(f"✅ Successfully extracted calendar details for {calendar_details.get('company')}")
        
        return {
            "success": True,
            "data": calendar_details,
        }
        
    except Exception as e:
        print(f"❌ Calendar extraction error: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to extract calendar details from email",
        }