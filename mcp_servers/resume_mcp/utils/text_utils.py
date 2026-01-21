import re
import unicodedata

ZERO_WIDTH_CHARS = {
    "\u200b",  # zero width space
    "\u200c",  # zero width non-joiner
    "\u200d",  # zero width joiner
    "\ufeff",  # byte order mark
    "\u00ad",  # soft hyphen
}

BULLET_CHARS = {
    "•", "●", "▪", "◦", "‣", "⁃",
    "–", "—", "*"
}

HORIZONTAL_RULE_PATTERN = re.compile(r"^[=\-_]{3,}$")

def normalize_text(text):
    """
    Normalize raw resume text without changing meaning.
    Safe for downstream parsing (sections, entities, ATS).
    """
    if not text:
        return ""

    
    # 1. Unicode normalization (canonical form)
    
    text = unicodedata.normalize("NFKD", text)
    
    # 2. Remove zero-width / invisible characters
    for ch in ZERO_WIDTH_CHARS:
        text = text.replace(ch, "")

    # 3. Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 4. Split into lines for controlled processing
    raw_lines = text.split("\n")
    cleaned_lines = []

    for line in raw_lines:
        line = line.strip()

        if HORIZONTAL_RULE_PATTERN.match(line):
            continue

        # Normalize bullets at line start ONLY
        for bullet in BULLET_CHARS:
            if line.startswith(bullet):
                line = "-" + line[len(bullet):].lstrip()
                break

        # Collapse internal whitespace
        line = re.sub(r"[ \t]+", " ", line)

        cleaned_lines.append(line)

    # 5. Collapse multiple empty lines (max one)
    final_lines = []
    empty_seen = False

    for line in cleaned_lines:
        if line == "":
            if not empty_seen:
                final_lines.append("")
                empty_seen = True
        else:
            final_lines.append(line)
            empty_seen = False

    return "\n".join(final_lines).strip()