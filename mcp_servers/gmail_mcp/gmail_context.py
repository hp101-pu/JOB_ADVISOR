import os
import requests
from gmail_client import build_gmail_service
from dotenv import load_dotenv
load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL")
SERVICE_KEY = os.getenv("SERVICE_KEY")


def get_gmail_service(user_id: str):
    """
    Returns a Gmail API service for a given user by fetching their
    OAuth access token from the Node backend.

    NOTE: We intentionally do NOT cache here. The MCP server runs as
    a fresh subprocess per call (see mcp/client.py), so any in-memory
    cache would be empty on every invocation anyway. Caching would give
    a false sense of security while providing zero benefit.
    """
    if not BACKEND_URL:
        raise RuntimeError("BACKEND_URL env var not set in gmail_mcp")

    # Ask the Node backend for a valid (auto-refreshed) access token
    try:
        res = requests.post(
            f"{BACKEND_URL}/internal/google/gmail/token",
            json={"userId": user_id},
            headers={"X-Service-Key": SERVICE_KEY},
            timeout=10
        )
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(f"Cannot reach backend at {BACKEND_URL}: {e}")

    if res.status_code == 404:
        raise RuntimeError(
            f"Gmail not connected for user {user_id}. "
            "User must authorise Gmail via /sync/google/gmail first."
        )

    if res.status_code == 401:
        raise RuntimeError(
            f"Gmail token expired or revoked for user {user_id}. "
            "User must re-authorise Gmail."
        )

    if not res.ok:
        raise RuntimeError(
            f"Failed to fetch Gmail token for user {user_id}: "
            f"{res.status_code} {res.text}"
        )

    access_token = res.json().get("accessToken")
    if not access_token:
        raise RuntimeError(f"Backend returned no accessToken for user {user_id}")

    return build_gmail_service(access_token)