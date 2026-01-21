from auth.gmail_auth import get_gmail_service

_gmail_service = None

def get_cached_gmail_service():
    global _gmail_service
    if _gmail_service is None:
        _gmail_service = get_gmail_service()
    return _gmail_service
