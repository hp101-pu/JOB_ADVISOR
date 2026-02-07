# Severity levels returned by the LLM
SEVERITY_GREEN  = "green"   # strength / positive
SEVERITY_YELLOW = "yellow"  # moderate improvement needed
SEVERITY_RED    = "red"     # critical issue


class LLMScorer:
    def __init__(self, client):
        self.client = client

    def evaluate(self, resume: dict, ats_result: dict, job_description=None, profile: str = "student") -> dict:
        """
        Two small Groq calls:
        Call 1: strengths (green)
        Call 2: improvements (yellow) + critical (red)
        Uses structured resume data for specific, resume-aware feedback.
        """
        e          = resume.get("entities", {}) or {}
        s          = resume.get("sections", {}) or {}
        structured = resume.get("structured", {}) or {}
        ctx        = self._PROFILE_CTX.get(profile, self._PROFILE_CTX["student"])

        score     = ats_result.get("total_score", 0)
        breakdown = ats_result.get("breakdown", {})
        flags     = ats_result.get("flags", [])

        skills = e.get("skills", [])[:15]
        projects = structured.get("projects", [])[:5]
        experience = structured.get("experience", [])[:5]
        education = structured.get("education", [])[:3]
        achievements = structured.get("achievements", [])[:5]
        volunteer = structured.get("volunteer", [])[:3]

        context = (
            f"Profile: {ctx}\n"
            f"ATS score: {score}/100\n"
            f"Breakdown: {breakdown}\n"
            f"Flags: {flags}\n"
            f"Skills: {skills}\n"
            f"Projects: {projects}\n"
            f"Experience: {experience}\n"
            f"Education: {education}\n"
            f"Achievements: {achievements}\n"
            f"Volunteer / POR: {volunteer}\n"
        )

        feedback = []

        # ── Call 1: Strengths ────────────────────────────────────────────────────
        prompt1 = (
            "You are an expert ATS resume reviewer.\n"
            + context
            + "\nBased ONLY on the structured resume above, list 1-2 genuine, specific strengths.\n"
            + 'Return ONLY valid JSON: {"strengths":["<one short sentence>"]}\n'
            + "No markdown. No explanation."
        )
        result1 = self.client.complete(prompt1)
        strengths = result1.get("strengths", []) if isinstance(result1, dict) else []
        if isinstance(strengths, list):
            for t in strengths:
                if t and isinstance(t, str):
                    feedback.append({"text": t.strip(), "severity": SEVERITY_GREEN})

        # ── Call 2: Improvements + Critical ──────────────────────────────────────
        prompt2 = (
            "You are an expert ATS resume reviewer.\n"
            f"{context}\n"
            "Based ONLY on the structured resume above, list:\n"
            "  - 1-3 specific improvements (yellow) the candidate should make\n"
            "  - 0-2 critical issues (red) that are likely to hurt shortlisting\n"
            'Return ONLY: {"improvements":["<sentence>"],"critical":["<sentence>"]}\n'
            "Each item must be one short sentence and reference concrete details from the resume."
        )
        result2 = self.client.complete(prompt2)
        result2 = result2 if isinstance(result2, dict) else {}
        improvements = result2.get("improvements", [])
        critical     = result2.get("critical", [])
        if isinstance(improvements, list):
            for t in improvements:
                if t and isinstance(t, str):
                    feedback.append({"text": t.strip(), "severity": SEVERITY_YELLOW})
        if isinstance(critical, list):
            for t in critical:
                if t and isinstance(t, str):
                    feedback.append({"text": t.strip(), "severity": SEVERITY_RED})

        return {
            "feedback":         feedback,
            "score_adjustment": 0,
        }

    # ------------------------------------------------------------------ #
    _PROFILE_CTX = {
        "student":      "STUDENT — no work experience expected. Focus: projects, skills, GPA, achievements.",
        "early_career": "EARLY CAREER — 0-2y experience. Focus: internship quality, quantified impact, skills.",
        "professional": "PROFESSIONAL — 2y+ experience. Focus: quantified impact, career progression, leadership.",
    }