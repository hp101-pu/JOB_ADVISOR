import re
from functools import lru_cache
from datetime import datetime

# ---------------------------------------------------------------------------
# Student signal detection
# ---------------------------------------------------------------------------

# Degree keywords that indicate an ongoing/recent undergraduate or postgraduate
STUDENT_DEGREE_RE = re.compile(
    r"\b(b\.?tech|b\.?e\.?|b\.?sc|b\.?s\.?|bca|bba|b\.?com|b\.?a\.?|"
    r"m\.?tech|m\.?e\.?|m\.?sc|m\.?s\.?|mca|mba|"
    r"bachelor|master|undergraduate|postgraduate|"
    r"engineering student|computer science student|"
    r"pursuing|currently enrolled|enrolled in)\b",
    re.IGNORECASE,
)

# Phrases that explicitly signal a current student
STUDENT_SIGNAL_RE = re.compile(
    r"\b("
    r"1st year|2nd year|3rd year|4th year|"
    r"first year|second year|third year|fourth year|"
    r"freshman|sophomore|senior year|"
    r"expected graduation|expected grad|graduating in|"
    r"currently pursuing|currently studying|"
    r"semester|cgpa|gpa|sgpa|"
    r"university|college|institute of technology|iit|nit|bits|"
    r"school of|faculty of"
    r")\b",
    re.IGNORECASE,
)


def _detect_is_student(sections: dict) -> bool:
    """Return True if the resume belongs to a current student, universally."""
    edu_text  = sections.get("education", "") or ""
    proj_text = sections.get("projects", "") or ""
    exp_text  = sections.get("experience", "") or ""
    full_text = edu_text + "\n" + proj_text + "\n" + exp_text

    has_degree_keyword    = bool(STUDENT_DEGREE_RE.search(full_text))
    has_student_signal    = bool(STUDENT_SIGNAL_RE.search(full_text))
    has_education_section = bool(edu_text.strip())

    # Strong: degree keyword + at least one student phrase
    if has_degree_keyword and has_student_signal:
        return True
    # Medium: education section present + student phrase (covers GPA, semester etc.)
    if has_education_section and has_student_signal:
        return True
    # Degree keyword alone inside an education section is enough
    if has_education_section and has_degree_keyword:
        return True
    return False


CURRENT_YEAR  = datetime.now().year
CURRENT_MONTH = datetime.now().month

MONTH_MAP = {
    "jan":1,"january":1,"feb":2,"february":2,"mar":3,"march":3,
    "apr":4,"april":4,"may":5,"jun":6,"june":6,"jul":7,"july":7,
    "aug":8,"august":8,"sep":9,"sept":9,"september":9,
    "oct":10,"october":10,"nov":11,"november":11,"dec":12,"december":12,
}

ROLE_PATTERNS = [
    "engineer","developer","programmer","technologist","technical associate",
    "intern","trainee","graduate engineer trainee",
    "sde","sde i","sde ii","sde iii",
    "software engineer","software developer","application developer",
    "systems engineer","platform engineer","product engineer",
    "backend engineer","backend developer","server-side engineer",
    "api engineer","microservices engineer",
    "frontend engineer","frontend developer","ui engineer","ui developer",
    "web developer","javascript developer",
    "full stack engineer","full-stack engineer","full stack developer","full-stack developer",
    "data scientist","data engineer","data analyst",
    "machine learning engineer","ml engineer","ai engineer","research engineer",
    "applied scientist","business intelligence engineer","bi engineer",
    "devops engineer","site reliability engineer","sre",
    "cloud engineer","infrastructure engineer","platform reliability engineer",
    "security engineer","application security engineer",
    "cyber security engineer","information security engineer",
    "penetration tester","ethical hacker",
    "mobile engineer","android developer","android engineer",
    "ios developer","ios engineer","flutter developer","react native developer",
    "qa engineer","quality assurance engineer","test engineer","software tester",
    "automation engineer","automation test engineer",
    "embedded engineer","firmware engineer","hardware engineer","systems programmer",
    "blockchain developer","blockchain engineer","web3 developer","smart contract developer",
    "technical product manager","product manager","program manager","engineering manager",
    "junior engineer","associate engineer","senior engineer","lead engineer",
    "principal engineer","staff engineer","architect","solutions architect",
]

ROLE_REGEX = re.compile(
    "|".join(rf"\b{re.escape(r)}\b" for r in ROLE_PATTERNS), re.IGNORECASE
)

ROLE_CANONICAL = {
    "sde":"software engineer","sde i":"software engineer",
    "sde ii":"software engineer","sde iii":"software engineer",
    "backend developer":"backend engineer","api engineer":"backend engineer",
    "microservices engineer":"backend engineer",
    "frontend developer":"frontend engineer","ui developer":"frontend engineer",
    "web developer":"frontend engineer",
    "full stack developer":"full stack engineer","full-stack developer":"full stack engineer",
    "ml engineer":"machine learning engineer","ai engineer":"machine learning engineer",
    "software tester":"qa engineer",
}

SENIORITY = {
    "intern":"intern","trainee":"intern","junior":"junior","associate":"junior",
    "senior":"senior","lead":"lead","principal":"principal",
    "staff":"staff","manager":"manager","architect":"architect",
}

MONTH_RANGE_RE = re.compile(r"""
    (jan|january|feb|february|mar|march|apr|april|may|
     jun|june|jul|july|aug|august|sep|sept|september|
     oct|october|nov|november|dec|december)
    [\s,\-'']*  ((?:19|20)\d{2})
    \s*(?:-|–|to)\s*
    (jan|january|feb|february|mar|march|apr|april|may|
     jun|june|jul|july|aug|august|sep|sept|september|
     oct|october|nov|november|dec|december|present)
    [\s,\-'']* ((?:19|20)\d{2})?
""", re.IGNORECASE | re.VERBOSE)

YEAR_RANGE_RE = re.compile(
    r"\b((?:19|20)\d{2})\s*(?:-|–|to)\s*((?:19|20)\d{2}|present)\b", re.IGNORECASE
)

YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")

TECH_RE = re.compile(
    r"\b(python|java(?:script)?|typescript|golang?|rust|c\+\+|c#|ruby|php|swift|kotlin|"
    r"react|angular|vue|next\.?js|node\.?js|django|flask|fastapi|spring|express|"
    r"postgresql|mysql|mongodb|redis|sqlite|cassandra|dynamodb|elasticsearch|"
    r"docker|kubernetes|k8s|aws|gcp|azure|git|linux|nginx|terraform|ansible|"
    r"tensorflow|pytorch|pandas|numpy|scikit[\-. ]learn|"
    r"rest(?:ful)?|graphql|grpc|kafka|rabbitmq|celery|"
    r"html5?|css3?|tailwind|bootstrap|sass|"
    # Modern tools commonly missing from base list
    r"langchain|openai|groq|spacy|pymupdf|pdfplumber|"
    r"firebase|supabase|prisma|mongoose|sequelize|"
    r"jwt|oauth|mcp|rag|llm|nlp|"
    r"postman|vscode|vercel|netlify)\b", re.IGNORECASE
)

COMPANY_PATTERNS = [
    re.compile(r"\bat\s+([A-Z][A-Za-z0-9&.\- ]{2,30})(?:\s*[,|]|$)"),
    re.compile(r"[-–|]\s*([A-Z][A-Za-z0-9&.\- ]{2,30})$"),
    re.compile(
        r"^([A-Z][A-Za-z0-9&.\- ]{2,30})\s*[|–-]\s*(?:" +
        "|".join(re.escape(r) for r in ROLE_PATTERNS[:25]) + r")", re.IGNORECASE
    ),
    re.compile(r"^([A-Z][A-Za-z0-9&.\- ]{2,30}),\s*[A-Z][a-z]"),
]


@lru_cache(maxsize=1)
def _spacy():
    try:
        import spacy
        return spacy.load("en_core_web_sm")
    except Exception:
        return None


def _parse_skills(text):
    """
    Parse skills section — handles label:value format (e.g. "Languages:Python,JS")
    and protects parenthetical groups (e.g. "Django (ORM, REST)").
    """
    if not text:
        return set()
    skills = set()
    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        # strip "Label:" prefix common in student resumes
        m = re.match(r'^[A-Za-z][A-Za-z\s&/]{0,35}:\s*(.*)', line)
        if m:
            line = m.group(1).strip()
            if not line:
                continue
        # protect commas inside parentheses
        line = re.sub(r"\(([^)]*)\)", lambda x: "(" + x.group(1).replace(",", "§") + ")", line)
        for part in re.split(r"[,|]", line):
            skill = part.replace("§", ",").strip()
            if 1 < len(skill) <= 60:
                skills.add(skill)
    return skills


def _walk_months(sy, sm, ey, em, worked):
    """Add every (year, month) tuple in range to worked set."""
    y, mo = sy, sm
    while (y, mo) <= (ey, em):
        worked.add((y, mo))
        mo += 1
        if mo > 12:
            mo, y = 1, y + 1


def extract_entities(sections):
    roles, norm_roles, seniority, skills, companies = set(), set(), set(), set(), set()
    dates, worked_months = set(), set()

    skills.update(_parse_skills(sections.get("skills", "") or ""))

    exp_text  = sections.get("experience", "") or ""
    proj_text = sections.get("projects", "") or ""
    combined  = exp_text + "\n" + proj_text
    exp_lines = exp_text.split("\n")

    # inline tech skills from bullets — scan both experience AND projects
    for m in TECH_RE.finditer(combined):
        skills.add(m.group().strip())

    # roles + companies — experience section only
    role_lines = []
    for line in exp_lines:
        m = ROLE_REGEX.search(line)
        if m:
            role = m.group().lower()
            role_lines.append(line.strip())
            roles.add(role)
            norm_roles.add(ROLE_CANONICAL.get(role, role))
            level = next((v for k, v in SENIORITY.items() if k in role), None)
            if level:
                seniority.add(level)

    for line in exp_lines:
        s = line.strip()
        if not s:
            continue
        for p in COMPANY_PATTERNS:
            m = p.search(s)
            if m:
                companies.add(m.group(1).strip())
                break

    nlp = _spacy()
    if nlp and role_lines:
        for ent in nlp("\n".join(role_lines)).ents:
            if ent.label_ == "ORG" and "\n" not in ent.text and len(ent.text) > 2:
                companies.add(ent.text.strip())

    # Dates for metadata — scan combined (experience + projects)
    for y in YEAR_RE.findall(combined):
        dates.add(y)

    # Work duration — EXPERIENCE SECTION ONLY.
    # Project dates (e.g. "Dec 2025 – Present") must NOT inflate total_months
    # or a student with side-projects looks like a 1yr+ professional.
    exp_lower = exp_text.lower()

    # month ranges: "Jan 2022 – Dec 2023"
    # Track which years are already covered by a month-range match so
    # YEAR_RANGE_RE does not double-count them on the same line.
    month_range_years: set = set()
    for g in MONTH_RANGE_RE.findall(exp_lower):
        sy, sm = int(g[1]), MONTH_MAP[g[0]]
        if g[2] == "present":
            ey, em = CURRENT_YEAR, CURRENT_MONTH
        else:
            em = MONTH_MAP.get(g[2], 1)
            ey = int(g[3]) if g[3] else CURRENT_YEAR
        _walk_months(sy, sm, ey, em, worked_months)
        month_range_years.add(sy)
        month_range_years.add(ey)

    # year-only ranges: "2022 – 2024"
    # Skip any year already covered by a more-precise month-range above.
    # This prevents "July 2025 – Present" from ALSO matching as "2025 – Present"
    # (which would add all of Jan-Jun 2025, inflating months by ~6).
    for g in YEAR_RANGE_RE.findall(exp_text):
        sy = int(g[0])
        ey = CURRENT_YEAR if g[1].lower() == "present" else int(g[1])
        # Skip if this range overlaps with an already-processed month-range
        if sy in month_range_years or ey in month_range_years:
            continue
        for y in range(sy, min(ey + 1, CURRENT_YEAR + 1)):
            for mo in range(1, 13):
                if y == CURRENT_YEAR and mo > CURRENT_MONTH:
                    break
                worked_months.add((y, mo))

    # Strip false positives from company set:
    # 1. "Present" / date words captured by the trailing "- Present" pattern
    # 2. Single-word generic terms that are never real company names
    # 3. Pure location words (India, Remote, etc.)
    _NOT_COMPANY = re.compile(
        r"^(present|remote|full[\s-]?time|part[\s-]?time|contract|freelance|"
        r"india|usa|us|uk|canada|hybrid|onsite|on-site|online|virtual|"
        r"duration|period|current|ongoing|now|till|since)$",
        re.IGNORECASE,
    )
    companies = {c for c in companies if c and len(c) > 2 and not _NOT_COMPANY.match(c.strip())}

    total   = len(worked_months)
    return {
        "is_student":        _detect_is_student(sections),
        "roles":             sorted(roles),
        "normalized_roles":  sorted(norm_roles),
        "seniority":         sorted(seniority),
        "skills":            sorted(s for s in skills if s),
        "companies":         sorted(companies),
        "dates":             sorted(dates),
        "experience_years":  total // 12,
        "experience_months": total % 12,
        "total_months":      total,
    }