from utils.text_utils import normalize_text
from services.section_splitter import split_sections
from services.entity_extractor import extract_entities


def extract_resume(raw_text: str) -> dict:
    """PDF text → structured sections + entities."""
    if not raw_text or not raw_text.strip():
        return {"sections": {}, "entities": {}}
    sections = split_sections(normalize_text(raw_text))
    return {"sections": sections, "entities": extract_entities(sections)}