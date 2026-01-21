# Email decoding + parsing

'''decode_base64()
extract_headers()
extract_body()'''

# utils/email_utils.py
import base64
from bs4 import BeautifulSoup

def decode_base64(data: str) -> str:
    if not data:
        return ""
    return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")


def extract_headers(headers):
    result = {}
    for h in headers:
        if h["name"] in ["From", "To", "Subject", "Date"]:
            result[h["name"].lower()] = h["value"]
    return result


def extract_body(payload: dict) -> str:
    """
    Extract best possible email body from Gmail payload.
    Preference: text/plain > text/html > raw body.
    """

    # Case 1: multipart email
    if "parts" in payload:
        # 1️⃣ Prefer text/plain
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain":
                return decode_base64(part.get("body", {}).get("data"))

        # 2️⃣ Fallback to text/html
        for part in payload["parts"]:
            if part.get("mimeType") == "text/html":
                html = decode_base64(part.get("body", {}).get("data"))
                return BeautifulSoup(html, "html.parser").get_text(separator="\n")

    # Case 2: single-part email
    if payload.get("body", {}).get("data"):
        return decode_base64(payload["body"]["data"])

    return ""
