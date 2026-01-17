import re
import html
from bs4 import BeautifulSoup


QUOTED_PATTERNS = [
    r"On .* wrote:",
    r"From: .*",
    r"Sent: .*",
    r"To: .*",
    r"Subject: .*"
]

SIGNATURE_MARKERS = [
    "--",
    "Regards,",
    "Best regards,",
    "Thanks,",
    "Sincerely,"
]


def clean_email_body(raw_body: str) -> str:
    """
    Deterministic, rule-based Gmail body cleaner.
    Safe for storage and LLMs.
    """

    if not raw_body:
        return ""

    text = raw_body.strip()

    # HTML safety (in case extract_body got raw HTML)
    if "<" in text and ">" in text:
        soup = BeautifulSoup(text, "html.parser")
        for block in soup.find_all("blockquote"):
            block.decompose()
        text = soup.get_text(separator="\n")

    text = html.unescape(text)

    # Remove quoted replies
    for pattern in QUOTED_PATTERNS:
        text = re.split(pattern, text, flags=re.IGNORECASE)[0]

    # Remove signatures
    for marker in SIGNATURE_MARKERS:
        if marker in text:
            text = text.split(marker)[0]

    # 🔑 Remove invisible Unicode junk (THIS fixes your issue)
    text = re.sub(
    r"[\u0000-\u001f\u007f-\u009f\u2000-\u200f\u202a-\u202e\ufeff\u2060\u034f]",
    "",
    text
)


    # Normalize whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)

    # Optional but recommended length guard
    MAX_CHARS = 3000
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS]

    return text.strip()
