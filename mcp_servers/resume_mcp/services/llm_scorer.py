# Severity levels returned by the LLM
SEVERITY_GREEN  = "green"   # strength / positive
SEVERITY_YELLOW = "yellow"  # moderate improvement needed
SEVERITY_RED    = "red"     # critical issue


class LLMScorer:
    def __init__(self, client):
        self.client = client

    def evaluate(self, resume: dict, ats_result: dict, job_description=None, profile: str = "student") -> dict:
        """
        Two small Groq calls instead of one large one.
        Call 1: strengths (green)
        Call 2: improvements (yellow) + critical (red)
        score_adjustment removed - final score = pure ATS math only.
        """
        e   = resume.get("entities", {}) or {}
        s   = resume.get("sections",  {}) or {}
        ctx = self._PROFILE_CTX.get(profile, self._PROFILE_CTX["student"])
        skills_preview  = e.get("skills", [])[:10]
        projects_text   = (s.get("projects",     "") or "")[:300]
        experience_text = (s.get("experience",   "") or "")[:200]
        education_text  = (s.get("education",    "") or "")[:150]
        achieve_text    = (s.get("achievements", "") or "")[:150]
        score           = ats_result.get("total_score", 0)
        breakdown       = ats_result.get("breakdown", {})

        # Shared context block reused in both prompts
        context = (
            f"Profile: {ctx}\n"
            f"ATS: {score}/100  breakdown: {breakdown}\n"
            f"Skills: {skills_preview}\n"
            f"Projects: {projects_text}\n"
            f"Experience: {experience_text}\n"
            f"Education: {education_text}\n"
            f"Achievements: {achieve_text}\n"
        )

        feedback = []

        # ── Call 1: Strengths only (no score_adjustment) ────────────────────────────────────────────────────
        # score_adjustment intentionally removed — final score = pure ATS math only.
        prompt1 = (
            "You are an ATS resume reviewer.\n"
            + context
            + "List 1-2 genuine strengths of this resume.\n"
            + 'Return ONLY valid JSON: {"strengths":["<one short sentence>"]}\n'
            + "No markdown. No explanation."
        )
        result1 = self.client.complete(prompt1)
        strengths = result1.get("strengths", [])
        if isinstance(strengths, list):
            for t in strengths:
                if t and isinstance(t, str):
                    feedback.append({"text": t.strip(), "severity": SEVERITY_GREEN})
        adj = 0  # always 0 - ATS score is authoritative — ATS score is authoritative

        # ── Call 2: Improvements + Critical ─────────────────────────────────────────
        prompt2 = (
            f"You are an ATS resume reviewer.\n"
            f"{context}\n"
            f"List 1-3 improvements needed (yellow) and 0-2 critical issues (red).\n"
            f'Return ONLY: {{"improvements":["<sentence>"],"critical":["<sentence>"]}}\n'
            f"improvements = things to improve, critical = must-fix issues. One short sentence each."
        )
        result2 = self.client.complete(prompt2)
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
            "score_adjustment": adj,
        }

    # ------------------------------------------------------------------ #
    _PROFILE_CTX = {
        "student":      "STUDENT — no work experience expected. Focus: projects, skills, GPA, achievements.",
        "early_career": "EARLY CAREER — 0-2y experience. Focus: internship quality, quantified impact, skills.",
        "professional": "PROFESSIONAL — 2y+ experience. Focus: quantified impact, career progression, leadership.",
    }