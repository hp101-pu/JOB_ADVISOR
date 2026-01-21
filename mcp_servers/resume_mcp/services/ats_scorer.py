import re
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Profile detection constants
# ---------------------------------------------------------------------------
# A resume is treated as a STUDENT profile when:
#   - total work experience < 12 months  AND
#   - has an education section            AND
#   - has a projects section  (their primary signal)
#
# EARLY_CAREER: has some experience (internship / <24 months) but no degree
#   signal or clearly junior.
#
# PROFESSIONAL: everything else (>= 24 months experience).
# ---------------------------------------------------------------------------

PROFILE_STUDENT      = "student"
PROFILE_EARLY_CAREER = "early_career"
PROFILE_PROFESSIONAL = "professional"


class ATSScorer:
    # -----------------------------------------------------------------------
    # Weights per profile type
    # Keys must stay identical to ATSBreakdown schema:
    #   skills | roles | experience | structure | companies
    # -----------------------------------------------------------------------
    WEIGHTS = {
        PROFILE_STUDENT: {
            # Skills still matter most — fair for everyone
            "skills":     35,
            # Having ANY role title (intern / trainee counts fully)
            "roles":      10,
            # Experience expected to be low → low weight, generous buckets
            "experience": 10,
            # Structure: education + projects replace experience section
            "structure":  25,
            # Companies: even 1 internship = full marks
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
            # Original weights — unchanged for experienced candidates
            "skills":     40,
            "roles":      20,
            "experience": 20,
            "structure":  10,
            "companies":  10,
        },
    }

    # Experience buckets per profile: (min_total_months, score)
    # Student: 0 months → 6 pts baseline so they're not immediately penalised
    # Early career: gentler ramp
    # Professional: original strict buckets
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

    # -----------------------------------------------------------------------
    # Public API — identical signature, identical return shape
    # -----------------------------------------------------------------------
    def score(self, resume: Dict, jd: Optional[Dict] = None) -> Dict:
        e = dict(resume.get("entities", {}) or {})  # shallow copy so we can inject _proj_text
        s = resume.get("sections", {}) or {}

        # Inject project text so _roles can use it for student activity detection
        e["_proj_text"] = s.get("projects", "") or ""

        profile = self._detect_profile(e, s)
        w       = self.WEIGHTS[profile]

        breakdown = {
            "skills":     self._skills(e, jd, w),
            "roles":      self._roles(e, jd, w, profile),
            "experience": self._experience(e, profile, w),
            "structure":  self._structure(s, profile, w),
            "companies":  self._companies(e, w, profile),
        }
        return {
            "total_score": min(100, sum(breakdown.values())),
            "breakdown":   breakdown,
            "flags":       self._flags(e, s, profile),
            "meta": {
                "scorer":   "ats_v4",
                "profile":  profile,
                "jd_used":  bool(jd),
            },
        }

    # -----------------------------------------------------------------------
    # Profile detection
    # -----------------------------------------------------------------------
    def _detect_profile(self, e: Dict, s: Dict) -> str:
        total_months  = self._total_months(e)
        has_education = bool(s.get("education", "").strip())
        has_projects  = bool(s.get("projects",  "").strip())
        seniority     = e.get("seniority", [])

        # --- Primary override: entity extractor detected student signals ---
        # is_student=True means the resume contains degree keywords + student
        # phrases (GPA, semester, university, pursuing, year of study, etc.)
        # This fires BEFORE month-counting so students with internships are
        # never mis-classified as early_career.
        if e.get("is_student") and total_months < 24:
            return PROFILE_STUDENT

        # --- Legacy checks (kept as safety net) ---
        # Student: very low experience + education present + projects as primary
        if total_months < 12 and has_education and has_projects:
            return PROFILE_STUDENT

        # Student without explicit education section but pure intern/trainee
        if total_months < 6 and ("intern" in seniority or "trainee" in seniority):
            return PROFILE_STUDENT

        # Early career: some experience but not yet professional level
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

    def _skills(self, e: Dict, jd: Optional[Dict], w: Dict) -> int:
        skills = set(e.get("skills", []))
        if not skills:
            return 0
        max_w = w["skills"]
        if jd and jd.get("skills"):
            ratio = len(skills & set(jd["skills"])) / max(len(jd["skills"]), 1)
            return int(max_w * min(ratio, 1.0))
        # Full marks at 12+ skills (was 16 — too hard for students with focused stacks)
        # Score scales linearly up to 12, capped at max_w
        return min(max_w, int(len(skills) * (max_w / 12)))

    # Keywords in project bullets that signal active developer role for students
    _PROJECT_ROLE_RE = re.compile(
        r"\b(building|built|developing|developed|designing|designed|"
        r"implementing|implemented|integrating|integrated|creating|created|"
        r"architecting|architected|deploying|deployed|engineering|engineered)"
        r"\b",
        re.IGNORECASE,
    )

    def _roles(self, e: Dict, jd: Optional[Dict], w: Dict, profile: str) -> int:
        roles = set(e.get("normalized_roles", []))
        max_w    = w["roles"]
        seniority = e.get("seniority", [])

        if not roles:
            # For students with no formal role titles, check if project section
            # shows active developer work — award up to 60% of role weight
            if profile == PROFILE_STUDENT:
                proj_text = e.get("_proj_text", "")  # injected by score() below
                if proj_text and self._PROJECT_ROLE_RE.search(proj_text):
                    return int(max_w * 0.6)
            return 0

        # JD mismatch penalty — same for all profiles
        if jd and jd.get("roles") and not (roles & set(jd["roles"])):
            max_w = int(max_w * 0.5)

        # Intern/trainee seniority:
        #   Student  → no penalty (expected)
        #   Early    → mild penalty (0.8)
        #   Pro      → steeper (0.5) — an intern title on a senior resume is a red flag
        if "intern" in seniority or "trainee" in seniority:
            if profile == PROFILE_EARLY_CAREER:
                max_w = int(max_w * 0.8)
            elif profile == PROFILE_PROFESSIONAL:
                max_w = int(max_w * 0.5)
            # PROFILE_STUDENT: no penalty at all

        return max_w

    def _experience(self, e: Dict, profile: str, w: Dict) -> int:
        total   = self._total_months(e)
        buckets = self.EXP_BUCKETS[profile]
        max_w   = w["experience"]
        for min_m, frac_score in reversed(buckets):
            if total >= min_m:
                # frac_score is already an absolute value relative to the
                # old weight=20 scale — rescale to current profile weight
                return min(max_w, frac_score)
        return 0

    # Quantified impact markers in bullets (numbers/metrics signal stronger work)
    _QUANT_RE = re.compile(
        r"("
        r"\d+\s*%|"                                                          # percentages: 50%
        r"\d+\+\s*(problems?|questions?|users?|requests?|endpoints?|modules?|features?|pages?|clients?|contributions?)|"  # 380+ problems
        r"\d+\+?\s*(users?|requests?|api|endpoints?|modules?|features?|pages?|clients?)|"  # numbers with units
        r"\d+x\b|"                                                           # 3x faster
        r"\d+\s*(ms|seconds?|hrs?|hours?)"                                   # time metrics
        r")",
        re.IGNORECASE,
    )

    def _structure(self, s: Dict, profile: str, w: Dict) -> int:
        """
        Professional: reward experience + skills + projects
        Student/Early: richness-based scoring
          - section presence (base)
          - project depth: number of projects + bullet count
          - education quality: has GPA/CGPA?
          - quantified impact in bullets
          - achievements + certifications bonus
        """
        max_w = w["structure"]

        if profile == PROFILE_PROFESSIONAL:
            present = sum(
                bool(s.get(k, "").strip())
                for k in ["experience", "skills", "projects"]
            )
            if present == 3: return max_w
            if present == 2: return int(max_w * 0.7)
            if s.get("projects", "").strip(): return int(max_w * 0.4)
            return int(max_w * 0.2) if present else 0

        # ---------------------------------------------------------------
        # Student / Early career: richness-based
        # ---------------------------------------------------------------
        score = 0.0

        # 1. Section presence (base) — same weights as before but scaled to 0.70 of max
        section_weights = {
            "skills":       0.25,
            "projects":     0.25,
            "education":    0.20,
            "experience":   0.05,
            "achievements": 0.05,
        }
        for section, weight in section_weights.items():
            if s.get(section, "").strip():
                score += max_w * weight

        # 2. Project depth bonus (up to 10% of max_w)
        proj_text = s.get("projects", "") or ""
        if proj_text.strip():
            # count non-empty lines as a proxy for bullet richness
            proj_lines = [l for l in proj_text.split("\n") if l.strip()]
            proj_line_count = len(proj_lines)
            # 5+ lines = full depth bonus, scale linearly below that
            depth_ratio = min(proj_line_count / 5.0, 1.0)
            score += max_w * 0.10 * depth_ratio

        # 3. Education quality bonus (up to 5% of max_w)
        # Covers CGPA, CPI (MNNIT), GPA, SGPA, percentage — all common formats
        edu_text = s.get("education", "") or ""
        if re.search(r"(cgpa|cpi|gpa|sgpa|percentage)\s*[:/]?\s*[\d.]+", edu_text, re.IGNORECASE):
            score += max_w * 0.05

        # 4. Quantified impact bonus (up to 5% of max_w)
        # Scan projects + experience + achievements for numbers/metrics
        combined_text = proj_text + "\n" + (s.get("experience", "") or "") + "\n" + (s.get("achievements", "") or "")
        if self._QUANT_RE.search(combined_text):
            score += max_w * 0.05

        # 5. Certifications or volunteer show initiative
        bonus_sections = ["certifications", "volunteer"]
        if any(s.get(sec, "").strip() for sec in bonus_sections):
            score += max_w * 0.05

        return int(min(max_w, score))

    def _companies(self, e: Dict, w: Dict, profile: str) -> int:
        companies    = e.get("companies", [])
        total_months = self._total_months(e)
        max_w        = w["companies"]

        if not companies:
            if profile == PROFILE_STUDENT:
                # No company but active projects = partial credit (30%)
                proj_text = e.get("_proj_text", "")
                if proj_text and proj_text.strip():
                    return int(max_w * 0.30)
            return 0

        if profile == PROFILE_STUDENT:
            # Companies list is non-empty, but we must verify the student has
            # REAL work experience (not just volunteer/responsibility orgs that
            # leaked through the entity extractor).
            # Gate: require at least 1 month of real experience to award full marks.
            # Without that gate a student with 0 internships but extracted
            # volunteer org names ("SMP Mentor") incorrectly scores 20/20.
            if total_months >= 1:
                return max_w          # confirmed real internship → full marks
            else:
                # Companies detected but no actual work duration → likely
                # volunteer/org names. Give same partial credit as projects-only.
                proj_text = e.get("_proj_text", "")
                return int(max_w * 0.30) if proj_text and proj_text.strip() else int(max_w * 0.15)

        if profile == PROFILE_EARLY_CAREER:
            return max_w if len(companies) >= 2 else int(max_w * 0.7)

        # Professional: original logic
        return max_w if len(companies) >= 2 else int(max_w * 0.6)

    # -----------------------------------------------------------------------
    # Flags — profile-aware, no false alarms for students
    # -----------------------------------------------------------------------
    def _flags(self, e: Dict, s: Dict, profile: str) -> List[str]:
        flags   = []
        total   = self._total_months(e)
        has_exp = bool(s.get("experience", "").strip())
        has_proj = bool(s.get("projects",  "").strip())

        # Skills missing — relevant for ALL profiles
        if not e.get("skills"):
            flags.append("missing_skills")

        if profile == PROFILE_STUDENT:
            # Students are not expected to have an experience section
            # Only flag if they have NEITHER experience NOR projects
            if not has_exp and not has_proj:
                flags.append("missing_experience_and_projects")
            if not s.get("education", "").strip():
                flags.append("missing_education_section")
            # No company flag only if they have zero internships AND no projects
            if not e.get("companies") and not has_proj:
                flags.append("no_experience_signal")
            # Flag if skill count is low — students should list technologies prominently
            if len(e.get("skills", [])) < 6:
                flags.append("low_skill_count")
            # Flag if no quantified impact found in projects, experience, or achievements
            proj_text  = s.get("projects", "") or ""
            exp_text   = s.get("experience", "") or ""
            achiev_text = s.get("achievements", "") or ""
            if has_proj and not self._QUANT_RE.search(proj_text + "\n" + exp_text + "\n" + achiev_text):
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