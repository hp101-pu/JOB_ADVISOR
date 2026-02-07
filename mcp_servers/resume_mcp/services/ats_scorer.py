import re
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Profile detection constants
# ---------------------------------------------------------------------------

PROFILE_STUDENT      = "student"
PROFILE_EARLY_CAREER = "early_career"
PROFILE_PROFESSIONAL = "professional"


# ---------------------------------------------------------------------------
# Frontend-render data — single source of truth for the UI
# ---------------------------------------------------------------------------
# Profile labels, colors, and descriptions
PROFILE_RENDER_DATA = {
    PROFILE_STUDENT: {
        "label":       "Student Profile",
        "color":       "#6366f1",
        "description": "Scored on skills, projects & education — not work experience.",
    },
    PROFILE_EARLY_CAREER: {
        "label":       "Early Career",
        "color":       "#f59e0b",
        "description": "Scored with lighter experience requirements for junior candidates.",
    },
    PROFILE_PROFESSIONAL: {
        "label":       "Professional",
        "color":       "#10b981",
        "description": "Full scoring across all categories.",
    },
}

# Per-profile breakdown labels and max weights
# These are the canonical values the frontend should render.
PROFILE_BREAKDOWN = {
    PROFILE_STUDENT: {
        "skills":     {"label": "Technical Skills", "max": 35},
        "roles":      {"label": "Project Depth",    "max": 10},
        "experience": {"label": "Activity Score",   "max": 10},
        "structure":  {"label": "Resume Structure", "max": 25},
        "companies":  {"label": "Internship Credit", "max": 20},
    },
    PROFILE_EARLY_CAREER: {
        "skills":     {"label": "Technical Skills", "max": 38},
        "roles":      {"label": "Role Experience",  "max": 15},
        "experience": {"label": "Work Duration",    "max": 15},
        "structure":  {"label": "Resume Structure", "max": 17},
        "companies":  {"label": "Companies",        "max": 15},
    },
    PROFILE_PROFESSIONAL: {
        "skills":     {"label": "Technical Skills", "max": 40},
        "roles":      {"label": "Roles Detected",   "max": 20},
        "experience": {"label": "Experience",       "max": 20},
        "structure":  {"label": "Resume Structure", "max": 10},
        "companies":  {"label": "Companies",        "max": 10},
    },
}

# Human-readable flag labels (profile-aware)
FLAG_LABELS = {
    "missing_education_section":       "Add an Education section with your degree & institution",
    "missing_experience_and_projects": "Add at least a Projects section to showcase your work",
    "no_experience_signal":            "Add projects or internships to show real-world experience",
    "missing_experience_section":      "Add a Work Experience section to strengthen your resume",
    "low_experience":                  "Limited work experience — add internships or projects",
    "intern_only_profile":             "Only intern-level roles found — consider adding projects or freelance work",
    "no_company_signal":               "No company names detected — make sure employers are clearly listed",
    "low_skill_count":                 "List more technical skills — aim for at least 8-10 technologies",
    "no_quantified_impact":            "Add numbers to your project bullets (e.g. '3 modules', '50% faster') to show impact",
    "missing_skills":                  "Add a Skills section listing your technical & soft skills",
}


def _score_color(percentage: float, profile: str, key: str) -> str:
    """Return a color for a breakdown bar based on percentage and profile context."""
    # Low-weight categories for students are expected to be low — render neutrally
    if profile == PROFILE_STUDENT and key in {"roles", "experience", "companies"}:
        return "#10b981" if percentage >= 60 else "#94a3b8"
    if percentage >= 75:
        return "#10b981"
    if percentage >= 50:
        return "#f59e0b"
    return "#ef4444"


def _score_label(final_score: int) -> str:
    if final_score >= 80:
        return "Excellent"
    if final_score >= 60:
        return "Good"
    return "Needs Improvement"


def _dashboard_metrics(final_score: int, breakdown: Dict, profile: str) -> Dict:
    max_map = PROFILE_BREAKDOWN.get(profile, PROFILE_BREAKDOWN[PROFILE_PROFESSIONAL])

    ats_readiness = (
        "Excellent" if final_score >= 80 else
        "Good"      if final_score >= 60 else
        "Needs Work"
    )

    structure = breakdown.get("structure", 0)
    structure_max = max_map.get("structure", {}).get("max", 1)
    structure_pct = min((structure / structure_max) * 100, 100) if structure_max else 0
    impact = (
        "Strong"   if structure_pct >= 75 else
        "Moderate" if structure_pct >= 50 else
        "Low"
    )

    skills = breakdown.get("skills", 0)
    skills_max = max_map.get("skills", {}).get("max", 1)
    skills_pct = min((skills / skills_max) * 100, 100) if skills_max else 0
    skill_alignment = (
        "High"   if skills_pct >= 85 else
        "Medium" if skills_pct >= 60 else
        "Low"
    )

    return {
        "atsReadiness":   ats_readiness,
        "impact":         impact,
        "skillAlignment": skill_alignment,
    }


class ATSScorer:
    # -----------------------------------------------------------------------
    # Weights per profile type
    # Keys must stay identical to ATSBreakdown schema:
    #   skills | roles | experience | structure | companies
    # -----------------------------------------------------------------------
    WEIGHTS = {
        PROFILE_STUDENT: {
            "skills":     35,
            "roles":      10,
            "experience": 10,
            "structure":  25,
            "companies":  20,
        },
        PROFILE_EARLY_CAREER: {
            "skills":     38,
            "roles":      15,
            "experience": 15,
            "structure":  17,
            "companies":  15,
        },
        PROFILE_PROFESSIONAL: {
            "skills":     40,
            "roles":      20,
            "experience": 20,
            "structure":  10,
            "companies":  10,
        },
    }

    # Experience buckets per profile: (min_total_months, absolute_score)
    # These absolute scores are pre-calibrated to the profile weight above.
    EXP_BUCKETS = {
        PROFILE_STUDENT: [
            (0, 6), (3, 7), (6, 8), (12, 9), (18, 10),
        ],
        PROFILE_EARLY_CAREER: [
            (0, 3), (6, 7), (12, 11), (18, 13), (24, 15),
        ],
        PROFILE_PROFESSIONAL: [
            (0, 0), (6, 5), (12, 10), (24, 15), (36, 17), (60, 20),
        ],
    }

    # Keywords in project bullets that signal active developer role for students
    _PROJECT_ROLE_RE = re.compile(
        r"\b(building|built|developing|developed|designing|designed|"
        r"implementing|implemented|integrating|integrated|creating|created|"
        r"architecting|architected|deploying|deployed|engineering|engineered)"
        r"\b",
        re.IGNORECASE,
    )

    # Quantified impact markers in bullets (numbers/metrics signal stronger work)
    _QUANT_RE = re.compile(
        r"("
        r"\d+\s*%|"
        r"\d+\+\s*(problems?|questions?|users?|requests?|endpoints?|modules?|features?|pages?|clients?|contributions?)|"
        r"\d+\+?\s*(users?|requests?|api|endpoints?|modules?|features?|pages?|clients?)|"
        r"\d+x\b|"
        r"\d+\s*(ms|seconds?|hrs?|hours?)"
        r")",
        re.IGNORECASE,
    )

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------
    def score(self, resume: Dict, jd: Optional[Dict] = None) -> Dict:
        structured = resume.get("structured", {}) or {}
        e = resume.get("entities", {}) or {}
        s = resume.get("sections", {}) or {}

        profile = self._detect_profile(e, structured, s)
        w = self.WEIGHTS[profile]

        breakdown = {
            "skills":     self._skills(e, jd, w),
            "roles":      self._roles(e, structured, jd, w, profile),
            "experience": self._experience(e, profile, w),
            "structure":  self._structure(structured, s, profile, w),
            "companies":  self._companies(e, structured, w, profile),
        }
        flags = self._flags(e, structured, s, profile)
        total_score = min(100, sum(breakdown.values()))

        return {
            "total_score": total_score,
            "breakdown":   breakdown,
            "flags":       flags,
            "meta": {
                "scorer":   "ats_v4",
                "profile":  profile,
                "jd_used":  bool(jd),
            },
            "render_data": self._build_render_data(profile, breakdown, flags, resume),
        }

    # -----------------------------------------------------------------------
    # Profile detection
    # -----------------------------------------------------------------------
    def _detect_profile(self, e: Dict, structured: Dict, s: Dict) -> str:
        total_months = self._total_months(e)
        seniority = e.get("seniority", [])

        # Prefer structured data; fall back to raw text sections for legacy resumes
        has_education = bool(
            (structured.get("education") and len(structured["education"]) > 0)
            or s.get("education", "").strip()
        )
        has_projects = bool(
            (structured.get("projects") and len(structured["projects"]) > 0)
            or s.get("projects", "").strip()
        )

        # Primary override: entity extractor detected student signals
        if e.get("is_student") and total_months < 24:
            return PROFILE_STUDENT

        # Student: low experience + education + projects
        if total_months < 12 and has_education and has_projects:
            return PROFILE_STUDENT

        # Student without explicit education but intern/trainee
        if total_months < 6 and ("intern" in seniority or "trainee" in seniority):
            return PROFILE_STUDENT

        # Early career
        if total_months < 24:
            return PROFILE_EARLY_CAREER

        return PROFILE_PROFESSIONAL

    # -----------------------------------------------------------------------
    # Scoring helpers
    # -----------------------------------------------------------------------
    def _total_months(self, e: Dict) -> int:
        return (
            e.get("total_months")
            or e.get("experience_years", 0) * 12 + e.get("experience_months", 0)
        )

    def _text_from_details(self, items: List[Dict]) -> str:
        """Concatenate detail arrays from structured items for regex scanning."""
        parts = []
        for item in items:
            details = item.get("details", [])
            if isinstance(details, list):
                parts.extend(str(d) for d in details if d)
            else:
                parts.append(str(details))
        return "\n".join(parts)

    def _all_detail_text(self, structured: Dict) -> str:
        """All detail text across projects, experience, volunteer, achievements."""
        parts = []
        for key in ["projects", "experience", "volunteer", "achievements"]:
            items = structured.get(key, [])
            if isinstance(items, list):
                parts.append(self._text_from_details(items))
        return "\n".join(parts)

    def _has_section(self, key: str, structured: Dict, s: Dict) -> bool:
        """Check section presence using structured data first, then raw sections."""
        items = structured.get(key)
        if isinstance(items, list) and len(items) > 0:
            return True
        return bool(s.get(key, "").strip())

    def _skills(self, e: Dict, jd: Optional[Dict], w: Dict) -> int:
        skills = set(e.get("skills", []))
        if not skills:
            return 0
        max_w = w["skills"]
        if jd and jd.get("skills"):
            ratio = len(skills & set(jd["skills"])) / max(len(jd["skills"]), 1)
            return int(max_w * min(ratio, 1.0))
        return min(max_w, int(len(skills) * (max_w / 12)))

    def _roles(self, e: Dict, structured: Dict, jd: Optional[Dict], w: Dict, profile: str) -> int:
        roles = set(e.get("normalized_roles", []))
        max_w = w["roles"]
        seniority = e.get("seniority", [])

        if not roles:
            # For students with no formal role titles, check project details for active verbs
            if profile == PROFILE_STUDENT:
                proj_text = self._text_from_details(structured.get("projects", []))
                if proj_text and self._PROJECT_ROLE_RE.search(proj_text):
                    return int(max_w * 0.6)
            return 0

        # JD mismatch penalty
        if jd and jd.get("roles") and not (roles & set(jd["roles"])):
            max_w = int(max_w * 0.5)

        # Intern/trainee seniority penalty
        if "intern" in seniority or "trainee" in seniority:
            if profile == PROFILE_EARLY_CAREER:
                max_w = int(max_w * 0.8)
            elif profile == PROFILE_PROFESSIONAL:
                max_w = int(max_w * 0.5)

        return max_w

    def _experience(self, e: Dict, profile: str, w: Dict) -> int:
        total = self._total_months(e)
        buckets = self.EXP_BUCKETS[profile]
        max_w = w["experience"]
        for min_m, absolute_score in reversed(buckets):
            if total >= min_m:
                # absolute_score is pre-calibrated for this profile's weight
                return min(max_w, absolute_score)
        return 0

    def _structure(self, structured: Dict, s: Dict, profile: str, w: Dict) -> int:
        max_w = w["structure"]

        if profile == PROFILE_PROFESSIONAL:
            present = sum(
                self._has_section(k, structured, s)
                for k in ["experience", "skills", "projects"]
            )
            if present == 3:
                return max_w
            if present == 2:
                return int(max_w * 0.7)
            if self._has_section("projects", structured, s):
                return int(max_w * 0.4)
            return int(max_w * 0.2) if present else 0

        # Student / Early career: richness-based scoring
        score = 0.0

        section_weights = {
            "skills":       0.25,
            "projects":     0.25,
            "education":    0.20,
            "experience":   0.05,
            "achievements": 0.05,
        }
        for section, weight in section_weights.items():
            if self._has_section(section, structured, s):
                score += max_w * weight

        # Project depth bonus
        projects = structured.get("projects", []) if isinstance(structured.get("projects"), list) else []
        if projects:
            bullet_count = sum(len(p.get("details", [])) for p in projects if isinstance(p, dict))
            depth_ratio = min(bullet_count / 5.0, 1.0)
            score += max_w * 0.10 * depth_ratio
        elif s.get("projects", "").strip():
            # Legacy fallback: count non-empty lines
            proj_lines = [l for l in s.get("projects", "").split("\n") if l.strip()]
            depth_ratio = min(len(proj_lines) / 5.0, 1.0)
            score += max_w * 0.10 * depth_ratio

        # Education quality bonus
        edu_items = structured.get("education", []) if isinstance(structured.get("education"), list) else []
        edu_text = "\n".join(
            f"{item.get('degree', '')} {item.get('details', '')}" for item in edu_items if isinstance(item, dict)
        )
        if not edu_text.strip():
            edu_text = s.get("education", "") or ""
        if re.search(r"(cgpa|cpi|gpa|sgpa|percentage)\s*[:/]?\s*[\d.]+", edu_text, re.IGNORECASE):
            score += max_w * 0.05

        # Quantified impact bonus
        detail_text = self._all_detail_text(structured)
        if not detail_text.strip():
            detail_text = (
                (s.get("projects", "") or "") + "\n" +
                (s.get("experience", "") or "") + "\n" +
                (s.get("achievements", "") or "")
            )
        if self._QUANT_RE.search(detail_text):
            score += max_w * 0.05

        # Certifications or volunteer show initiative
        has_cert = self._has_section("certifications", structured, s)
        has_vol = self._has_section("volunteer", structured, s)
        if has_cert or has_vol:
            score += max_w * 0.05

        return int(min(max_w, score))

    def _companies(self, e: Dict, structured: Dict, w: Dict, profile: str) -> int:
        total_months = self._total_months(e)
        max_w = w["companies"]

        # Prefer real companies from structured experience
        exp_items = structured.get("experience", []) if isinstance(structured.get("experience"), list) else []
        real_companies = [
            item.get("company", "").strip()
            for item in exp_items
            if isinstance(item, dict) and item.get("company", "").strip()
        ]
        # Fallback to entity-extracted companies
        companies = real_companies or e.get("companies", [])
        has_projects = self._has_section("projects", structured, e)

        if not companies:
            if profile == PROFILE_STUDENT and has_projects:
                return int(max_w * 0.30)
            return 0

        if profile == PROFILE_STUDENT:
            # Gate on real work duration to avoid volunteer orgs being treated as internships
            if total_months >= 1:
                return max_w
            return int(max_w * 0.30) if has_projects else int(max_w * 0.15)

        if profile == PROFILE_EARLY_CAREER:
            return max_w if len(companies) >= 2 else int(max_w * 0.7)

        return max_w if len(companies) >= 2 else int(max_w * 0.6)

    # -----------------------------------------------------------------------
    # Flags
    # -----------------------------------------------------------------------
    def _flags(self, e: Dict, structured: Dict, s: Dict, profile: str) -> List[str]:
        flags = []
        total = self._total_months(e)
        has_exp = self._has_section("experience", structured, s)
        has_proj = self._has_section("projects", structured, s)
        skills = e.get("skills", [])

        if not skills:
            flags.append("missing_skills")

        if profile == PROFILE_STUDENT:
            if not has_exp and not has_proj:
                flags.append("missing_experience_and_projects")
            if not self._has_section("education", structured, s):
                flags.append("missing_education_section")
            if not e.get("companies") and not has_proj:
                flags.append("no_experience_signal")
            if len(skills) < 6:
                flags.append("low_skill_count")
            if has_proj and not self._QUANT_RE.search(self._all_detail_text(structured)):
                flags.append("no_quantified_impact")

        elif profile == PROFILE_EARLY_CAREER:
            if not has_exp and not has_proj:
                flags.append("missing_experience_and_projects")
            if total < 6:
                flags.append("low_experience")
            if not e.get("companies"):
                flags.append("no_company_signal")

        else:  # PROFESSIONAL
            if not has_exp:
                flags.append("missing_experience_section")
            if total < 6:
                flags.append("low_experience")
            if "intern" in e.get("seniority", []):
                flags.append("intern_only_profile")
            if not e.get("companies"):
                flags.append("no_company_signal")

        return flags

    # -----------------------------------------------------------------------
    # Render data builder — frontend consumes this directly
    # -----------------------------------------------------------------------
    def _build_render_data(self, profile: str, breakdown: Dict, flags: List[str], resume: Dict) -> Dict:
        profile_conf = PROFILE_RENDER_DATA.get(profile, PROFILE_RENDER_DATA[PROFILE_PROFESSIONAL])
        max_map = PROFILE_BREAKDOWN.get(profile, PROFILE_BREAKDOWN[PROFILE_PROFESSIONAL])
        final_score = min(100, sum(breakdown.values()))

        render_breakdown = []
        for key, value in breakdown.items():
            meta = max_map.get(key, {"label": key.capitalize(), "max": 20})
            max_val = meta["max"]
            percentage = min((value / max_val) * 100, 100) if max_val else 0
            render_breakdown.append({
                "key":        key,
                "label":      meta["label"],
                "value":      value,
                "max":        max_val,
                "percentage": round(percentage, 1),
                "color":      _score_color(percentage, profile, key),
            })

        render_flags = []
        for flag in flags:
            render_flags.append({
                "severity": "yellow",
                "text":     FLAG_LABELS.get(flag, flag.replace("_", " ").title()),
                "type":     flag,
            })

        dashboard = _dashboard_metrics(final_score, breakdown, profile)
        dashboard["lastAnalyzed"] = "just now"

        return {
            "profile": {
                "key":         profile,
                "label":       profile_conf["label"],
                "description": profile_conf["description"],
                "color":       profile_conf["color"],
            },
            "score_label":  _score_label(final_score),
            "breakdown":    render_breakdown,
            "flags":        render_flags,
            "llm_feedback": [],  # populated by ScorePipeline after LLM call
            "focus_areas":  [f["text"] for f in render_flags[:3]],
            "dashboard":    dashboard,
        }