import sys
from utils.text_utils import normalize_text
from services.section_splitter import split_sections
from services.entity_extractor import extract_entities


def extract_resume(raw_text: str, use_llm: bool = True) -> dict:
    """
    PDF text → structured sections + entities.
    Tries LLM extraction first (if enabled), falls back to regex pipeline.
    Returns dict with keys: sections, entities, parser_version.
    """
    if not raw_text or not raw_text.strip():
        return {
            "sections": {},
            "entities": {},
            "parser_version": "none",
            "structured": {
                "projects": [], "experience": [], "volunteer": [],
                "education": [], "achievements": [], "certifications": [],
            },
        }

    # --- LLM extraction (primary) ---
    if use_llm:
        try:
            from services.llm_extractor import LLMExtractor
            extractor = LLMExtractor()
            result = extractor.extract(raw_text)
            if result is not None:
                result["parser_version"] = "llm_v1"
                print("[EXTRACT] LLM extraction succeeded", flush=True, file=sys.stderr)
                return result
            print("[EXTRACT] LLM extraction returned None, falling back to regex", flush=True, file=sys.stderr)
        except Exception as e:
            print(f"[EXTRACT] LLM extraction failed with error: {e}", flush=True, file=sys.stderr)

    # --- Regex extraction (fallback) ---
    print("[EXTRACT] Using regex pipeline", flush=True, file=sys.stderr)
    sections = split_sections(normalize_text(raw_text))
    return {
        "sections": sections,
        "entities": extract_entities(sections),
        "parser_version": "regex_v1",
        "structured": {
            "projects": [], "experience": [], "volunteer": [],
            "education": [], "achievements": [], "certifications": [],
        },
    }