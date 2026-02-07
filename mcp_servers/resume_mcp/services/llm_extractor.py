"""
LLM-based resume extraction service.
Sends raw PDF text to Groq and receives structured sections + entities in one shot.
Falls back to None on failure so caller can use the regex pipeline.
"""

import json
import re
import sys
from datetime import datetime
from typing import Dict, Any, Optional

from services.groq_client import GroqClient

CURRENT_YEAR = datetime.now().year
CURRENT_MONTH = datetime.now().month

_SYSTEM_PROMPT = (
    "You are a precise resume parser. "
    "You receive the raw text extracted from a resume PDF. "
    "Your job is to identify sections and extract structured entities. "
    "Return ONLY valid JSON. No markdown, no explanation, no code fences. "
    "The JSON must follow the exact schema provided in the user message."
)

_USER_PROMPT_TEMPLATE = """\
Parse the following resume text and return a JSON object with this exact schema:

{{
  "sections": {{
    "summary": "<text or empty string>",
    "experience": "<text or empty string>",
    "projects": "<text or empty string>",
    "skills": "<text or empty string>",
    "education": "<text or empty string>",
    "certifications": "<text or empty string>",
    "achievements": "<text or empty string>",
    "volunteer": "<text or empty string>",
    "publications": "<text or empty string>",
    "languages": "<text or empty string>",
    "interests": "<text or empty string>",
    "other": "<text or empty string>"
  }},
  "entities": {{
    "is_student": <true or false>,
    "skills": ["<skill1>", "<skill2>", ...],
    "roles": ["<role1>", "<role2>", ...],
    "normalized_roles": ["<canonical role1>", ...],
    "seniority": ["<intern|junior|senior|lead|principal|staff|manager|architect>"],
    "companies": ["<company1>", "<company2>", ...],
    "dates": ["<year1>", "<year2>", ...],
    "experience_years": <integer>,
    "experience_months": <integer>,
    "total_months": <integer>
  }},
  "structured": {{
    "projects": [
      {{ "name": "<project name>", "date": "<date range or empty>", "tech_stack": ["<tech1>", "<tech2>"], "details": ["<detail1>", "<detail2>"] }}
    ],
    "experience": [
      {{ "role": "<job title>", "company": "<company>", "date": "<date range>", "details": ["<detail1>", "<detail2>"] }}
    ],
    "volunteer": [
      {{ "role": "<role>", "organization": "<org>", "date": "<date range>", "details": ["<detail1>", "<detail2>"] }}
    ],
    "education": [
      {{ "degree": "<degree>", "institution": "<school>", "date": "<date range>", "details": "<extra text or empty>" }}
    ],
    "achievements": [
      {{ "title": "<achievement>", "date": "<date or empty>", "details": "<extra text or empty>" }}
    ],
    "certifications": [
      {{ "title": "<cert>", "issuer": "<issuer or empty>", "date": "<date or empty>" }}
    ]
  }}
}}

Rules:
1. SECTIONS: Extract the actual text content for each section. If a section is not present, use an empty string. Clean the text by removing:
   - Page headers, footers, and page numbers
   - Social media handles, GitHub links, LinkedIn links, email addresses
   - Decorative lines, bullets, or repeated separators
   Do NOT paraphrase — keep the original wording but remove the noise above.

2. EXPERIENCE vs ACHIEVEMENTS vs VOLUNTEER vs POR:
   - "experience" must contain ONLY formal paid jobs, internships, or formal work placements.
   - "achievements" must contain ONLY awards, competition results, honors, certifications, hackathons.
   - "volunteer" must contain ONLY volunteer work, community service, or social initiatives.
   - "Positions of Responsibility" (POR), club leadership, event coordination, and student club work go into "volunteer", NOT "experience".
   - If a resume has no formal work experience, "experience" must be an empty string.

3. SKILLS: Extract ALL technical skills, tools, programming languages, frameworks, libraries, databases, cloud platforms, APIs, protocols, and methodologies mentioned ANYWHERE in the resume, including:
   - The skills section
   - The experience section
   - The projects section
   - The education section
   - Certifications
   Use canonical names (e.g. "PostgreSQL" not "postgres", "React" not "reactjs", "GitHub" not "Github"). Include both explicit and implicit technologies. Remove generic words like "Techstack", "Tools", "Languages". Include soft skills ONLY if they are explicitly in a skills section.

4. ROLES: Extract ONLY formal job titles / role names from the EXPERIENCE section. Do NOT extract roles from:
   - Projects (e.g., "built a chatbot" is not a role)
   - Positions of Responsibility (e.g., "Club Coordinator", "Networking Coordinator", "Event Management Team")
   - Volunteer work
   - Achievements
   Use lowercase. If no formal experience exists, return an empty list.

5. NORMALIZED_ROLES: Map each role to its canonical form:
   - "sde" / "sde i/ii/iii" / "software development engineer" → "software engineer"
   - "backend developer" / "api engineer" / "microservices engineer" → "backend engineer"
   - "frontend developer" / "ui developer" / "web developer" → "frontend engineer"
   - "full stack developer" / "full-stack developer" → "full stack engineer"
   - "ml engineer" / "ai engineer" / "machine learning engineer" → "machine learning engineer"
   - "software tester" / "qa engineer" → "qa engineer"
   - "data scientist" / "data analyst" → keep as-is
   Keep other roles as-is (lowercase). If roles is empty, return an empty list.

6. SENIORITY: Extract seniority levels from formal role titles ONLY. Valid values: "intern", "junior", "senior", "lead", "principal", "staff", "manager", "architect". Do NOT include "present", "current", "full-time", "contract", or any date/status words. If no formal roles exist, return an empty list.

7. COMPANIES: Extract ONLY actual employer / company names from the EXPERIENCE section. Do NOT include:
   - Universities, colleges, or institutes (e.g., MNNIT, IIT, NIT, BITS)
   - Clubs, associations, or student bodies (e.g., "Robotics Club", "E-Cell")
   - Location names (India, Remote, USA, etc.)
   - Generic words (Present, Full-time, Contract, Freelance, etc.)
   - Project names or personal ventures
   If no formal experience exists, return an empty list.

8. DATES: Extract ALL years mentioned in the resume (as strings), including:
   - Work experience dates
   - Project dates
   - Education dates
   - Achievement/competition dates
   - Certifications dates
   Return them as a list of 4-digit year strings (e.g., ["2024", "2025", "2026"]).

9. EXPERIENCE CALCULATION:
   - Parse date ranges from the EXPERIENCE section only (NOT projects, NOT achievements, NOT POR).
   - For "Present" or "Current", use {current_year}-{current_month} as the end date.
   - Calculate total_months as the sum of all formal work experience durations.
   - experience_years = total_months // 12
   - experience_months = total_months % 12
   - If the experience section is empty, set all to 0.

10. IS_STUDENT: Set to true if the resume belongs to a current student. Signals:
   - Degree keywords (B.Tech, B.E, B.Sc, BCA, M.Tech, M.Sc, etc.) in education
   - Student phrases (year of study, CGPA, semester, pursuing, enrolled, expected graduation)
   - No significant full-time work experience (internships are OK)
   - Has education + projects as primary sections

11. STRUCTURED DATA (the frontend renders this directly, so it must be accurate and complete):
    - "projects": each project must be a separate object with name, date, tech_stack (array of technologies), and details (array of bullet strings). Do NOT split one project into multiple objects. Do NOT omit any project.
    - "experience": each formal job/internship as a separate object with role, company, date, and details. If none, return an empty array.
    - "volunteer": each POR / volunteer role as a separate object with role, organization, date, and details. If none, return an empty array.
    - "education": each degree/institution as a separate object. If none, return an empty array.
    - "achievements": each award/competition/honor as a separate object. If none, return an empty array.
    - "certifications": each certification as a separate object. If none, return an empty array.

12. Return ONLY the JSON. No other text.

Example for a student resume with no formal experience:
{{
  "sections": {{
    "experience": "",
    "projects": "• AI Chatbot (Jan 2025 - Mar 2025)\nTech: Python, LangChain, OpenAI, FastAPI\n– Built a conversational AI assistant...",
    "skills": "Python, LangChain, OpenAI, FastAPI, React, MongoDB",
    "education": "B.Tech in Computer Science, XYZ University, 2023 - 2027",
    "achievements": "• Winner, Hackathon 2025",
    "volunteer": ""
  }},
  "entities": {{
    "is_student": true,
    "skills": ["Python", "LangChain", "OpenAI", "FastAPI", "React", "MongoDB"],
    "roles": [],
    "normalized_roles": [],
    "seniority": [],
    "companies": [],
    "dates": ["2023", "2025", "2027"],
    "experience_years": 0,
    "experience_months": 0,
    "total_months": 0
  }},
  "structured": {{
    "projects": [
      {{
        "name": "AI Chatbot",
        "date": "Jan 2025 - Mar 2025",
        "tech_stack": ["Python", "LangChain", "OpenAI", "FastAPI"],
        "details": ["Built a conversational AI assistant for customer support.", "Integrated RAG pipeline with vector DB for accurate responses."]
      }}
    ],
    "experience": [],
    "volunteer": [],
    "education": [
      {{
        "degree": "B.Tech in Computer Science",
        "institution": "XYZ University",
        "date": "2023 - 2027",
        "details": ""
      }}
    ],
    "achievements": [
      {{
        "title": "Winner, Hackathon 2025",
        "date": "2025",
        "details": ""
      }}
    ],
    "certifications": []
  }}
}}

Resume text:
---
{raw_text}
---
"""


def _parse_json_response(text: str) -> Optional[dict]:
    """Parse JSON from LLM response, handling markdown code fences and partial output."""
    if not text:
        return None

    text = text.strip()

    # Strip markdown code fences
    text = re.sub(r'^```[a-z]*\n?', '', text).rstrip('`').strip()

    # Try direct parse
    try:
        return json.loads(text)
    except Exception:
        pass

    # Try to extract JSON object from the text
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass

    return None


def _deduplicate_skills(entities: dict) -> None:
    """Remove case-insensitive duplicate skills, keeping the first casing seen."""
    skills = entities.get("skills", [])
    if not isinstance(skills, list):
        entities["skills"] = []
        return

    seen = set()
    deduped = []
    for skill in skills:
        key = skill.lower()
        if key and key not in seen:
            seen.add(key)
            deduped.append(skill)
    entities["skills"] = deduped


def _validate_and_normalize(result: dict) -> Optional[dict]:
    """Ensure the parsed result has the expected schema with correct types."""
    if not isinstance(result, dict):
        return None

    sections = result.get("sections", {})
    entities = result.get("entities", {})

    if not isinstance(sections, dict) or not isinstance(entities, dict):
        return None

    # Ensure all section keys exist with string values
    section_keys = [
        "summary", "experience", "projects", "skills", "education",
        "certifications", "achievements", "volunteer", "publications",
        "languages", "interests", "other"
    ]
    for key in section_keys:
        val = sections.get(key, "")
        if val is None:
            val = ""
        sections[key] = str(val) if not isinstance(val, str) else val

    # Ensure all entity keys exist with correct types
    list_keys = ["skills", "roles", "normalized_roles", "seniority", "companies", "dates"]
    for key in list_keys:
        val = entities.get(key, [])
        if not isinstance(val, list):
            entities[key] = []
        else:
            entities[key] = [str(v).strip() for v in val if v and isinstance(v, (str, int, float))]

    # Deduplicate skills case-insensitively, preferring the first-cased occurrence
    _deduplicate_skills(entities)

    # Filter seniority to valid levels only
    valid_seniority = {"intern", "junior", "senior", "lead", "principal", "staff", "manager", "architect"}
    entities["seniority"] = [s for s in entities.get("seniority", []) if s.lower() in valid_seniority]

    # Filter out common false-positive company names (universities, locations, status words)
    bad_company_words = {
        "present", "current", "full-time", "part-time", "contract", "freelance", "remote",
        "india", "usa", "uk", "canada", "germany", "singapore",
        "mnnit", "iit", "nit", "bits", "iiit", "university", "college", "institute",
    }
    entities["companies"] = [
        c for c in entities.get("companies", [])
        if c.lower() not in bad_company_words and len(c) > 1
    ]
    # Remove exact duplicate companies
    entities["companies"] = list(dict.fromkeys(entities["companies"]))

    # Filter dates to valid 4-digit years in a reasonable range
    entities["dates"] = [
        d for d in entities.get("dates", [])
        if re.fullmatch(r"\d{4}", d) and 1950 <= int(d) <= CURRENT_YEAR + 1
    ]
    entities["dates"] = sorted(set(entities["dates"]))

    # Ensure numeric fields
    for key in ["experience_years", "experience_months", "total_months"]:
        val = entities.get(key, 0)
        try:
            entities[key] = int(val)
        except (TypeError, ValueError):
            entities[key] = 0

    # Ensure is_student is bool
    is_student = entities.get("is_student", False)
    entities["is_student"] = bool(is_student)

    # Validate and normalize structured data for the frontend
    result["structured"] = _validate_structured(result.get("structured", {}))

    result["sections"] = sections
    result["entities"] = entities
    return result


def _validate_structured(structured: dict) -> dict:
    """
    Ensure the structured output has the expected shape with default values.
    Returns a fully populated dict so the frontend can render without null checks.
    """
    if not isinstance(structured, dict):
        structured = {}

    def _ensure_list(val, item_shape: dict) -> list:
        if not isinstance(val, list):
            return []
        result = []
        for item in val:
            if not isinstance(item, dict):
                continue
            normalized = {}
            for key, default in item_shape.items():
                v = item.get(key, default)
                if isinstance(default, list):
                    if not isinstance(v, list):
                        v = []
                    normalized[key] = [str(x).strip() for x in v if x is not None]
                else:
                    normalized[key] = str(v).strip() if v is not None else ""
            result.append(normalized)
        return result

    return {
        "projects": _ensure_list(structured.get("projects"), {
            "name": "", "date": "", "tech_stack": [], "details": []
        }),
        "experience": _ensure_list(structured.get("experience"), {
            "role": "", "company": "", "date": "", "details": []
        }),
        "volunteer": _ensure_list(structured.get("volunteer"), {
            "role": "", "organization": "", "date": "", "details": []
        }),
        "education": _ensure_list(structured.get("education"), {
            "degree": "", "institution": "", "date": "", "details": ""
        }),
        "achievements": _ensure_list(structured.get("achievements"), {
            "title": "", "date": "", "details": ""
        }),
        "certifications": _ensure_list(structured.get("certifications"), {
            "title": "", "issuer": "", "date": ""
        }),
    }


class LLMExtractor:
    """Extracts resume sections and entities using Groq LLM."""

    def __init__(self, client: GroqClient = None):
        self.client = client
        if self.client is None:
            try:
                self.client = GroqClient()
            except Exception as e:
                print(f"[LLM_EXTRACT] Failed to init GroqClient: {e}", flush=True, file=sys.stderr)
                self.client = None

    def extract(self, raw_text: str) -> Optional[Dict[str, Any]]:
        """
        Send raw resume text to Groq and return structured sections + entities.
        Returns None on failure (caller should fall back to regex).
        """
        if not self.client:
            print("[LLM_EXTRACT] No GroqClient available", flush=True, file=sys.stderr)
            return None

        if not raw_text or not raw_text.strip():
            print("[LLM_EXTRACT] Empty raw text", flush=True, file=sys.stderr)
            return None

        # Truncate very long resumes to avoid token limits.
        # ~12000 chars is roughly 3000 tokens; output JSON can be ~2000 tokens.
        max_chars = 12000
        truncated = False
        text_to_send = raw_text
        if len(raw_text) > max_chars:
            text_to_send = raw_text[:max_chars]
            truncated = True
            print(f"[LLM_EXTRACT] Resume text truncated from {len(raw_text)} to {max_chars} chars", flush=True, file=sys.stderr)

        prompt = _USER_PROMPT_TEMPLATE.format(
            raw_text=text_to_send,
            current_year=CURRENT_YEAR,
            current_month=CURRENT_MONTH,
        )

        print(f"[LLM_EXTRACT] Sending to Groq (text length={len(text_to_send)}, truncated={truncated})", flush=True, file=sys.stderr)

        try:
            raw_response = self.client.complete_raw(
                prompt=prompt,
                system=_SYSTEM_PROMPT,
                max_tokens=6000,
                temperature=0.1,
            )
        except Exception as e:
            print(f"[LLM_EXTRACT] Groq call failed: {e}", flush=True, file=sys.stderr)
            return None

        if not raw_response:
            print("[LLM_EXTRACT] Groq returned empty response", flush=True, file=sys.stderr)
            return None

        print(f"[LLM_EXTRACT] Groq response received (length={len(raw_response)})", flush=True, file=sys.stderr)

        result = _parse_json_response(raw_response)
        if result is None:
            print("[LLM_EXTRACT] Failed to parse JSON from Groq response", flush=True, file=sys.stderr)
            return None

        result = _validate_and_normalize(result)
        if result is None:
            print("[LLM_EXTRACT] Parsed result failed validation", flush=True, file=sys.stderr)
            return None

        # Log extraction summary
        entities = result.get("entities", {})
        print(
            f"[LLM_EXTRACT] Success — skills={len(entities.get('skills', []))}, "
            f"roles={len(entities.get('roles', []))}, "
            f"companies={len(entities.get('companies', []))}, "
            f"total_months={entities.get('total_months', 0)}, "
            f"is_student={entities.get('is_student', False)}",
            flush=True, file=sys.stderr
        )

        return result
