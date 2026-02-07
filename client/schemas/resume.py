from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class ResumeEntities(BaseModel):
    roles:             List[str] = []
    normalized_roles:  List[str] = []
    seniority:         List[str] = []
    skills:            List[str] = []
    companies:         List[str] = []
    dates:             List[str] = []
    experience_years:  int = 0
    experience_months: int = 0
    total_months:      int = 0


class ResumeSections(BaseModel):
    summary:        str = ""
    experience:     str = ""
    projects:       str = ""
    skills:         str = ""
    education:      str = ""
    certifications: str = ""
    achievements:   str = ""
    publications:   str = ""
    volunteer:      str = ""
    languages:      str = ""
    interests:      str = ""
    other:          str = ""


class ProjectItem(BaseModel):
    name:       str = ""
    date:       str = ""
    tech_stack: List[str] = []
    details:    List[str] = []


class ExperienceItem(BaseModel):
    role:    str = ""
    company: str = ""
    date:    str = ""
    details: List[str] = []


class VolunteerItem(BaseModel):
    role:         str = ""
    organization: str = ""
    date:         str = ""
    details:      List[str] = []


class EducationItem(BaseModel):
    degree:      str = ""
    institution: str = ""
    date:        str = ""
    details:     str = ""


class AchievementItem(BaseModel):
    title:   str = ""
    date:    str = ""
    details: str = ""


class CertificationItem(BaseModel):
    title:  str = ""
    issuer: str = ""
    date:   str = ""


class StructuredResume(BaseModel):
    projects:       List[ProjectItem]       = []
    experience:     List[ExperienceItem]    = []
    volunteer:      List[VolunteerItem]      = []
    education:      List[EducationItem]      = []
    achievements:   List[AchievementItem]    = []
    certifications: List[CertificationItem]  = []


class ParsedResume(BaseModel):
    sections:   ResumeSections
    entities:   ResumeEntities
    structured: StructuredResume = StructuredResume()
    parser_version: str = ""


class ATSBreakdown(BaseModel):
    skills:     int = 0
    roles:      int = 0
    experience: int = 0
    structure:  int = 0
    companies:  int = 0


class ATSResult(BaseModel):
    total_score: int
    breakdown:   ATSBreakdown
    flags:       List[str] = []
    meta:        Dict[str, object] = {}


class LLMFeedbackItem(BaseModel):
    text:     str
    severity: str = "yellow"  # green | yellow | red


class ProfileRenderData(BaseModel):
    key:         str = ""
    label:       str = ""
    description: str = ""
    color:       str = ""


class BreakdownRenderItem(BaseModel):
    key:        str   = ""
    label:      str   = ""
    value:      int   = 0
    max:        int   = 0
    percentage: float = 0.0
    color:      str   = ""


class FlagRenderItem(BaseModel):
    severity: str = "yellow"
    text:     str = ""
    type:     str = ""


class DashboardRenderData(BaseModel):
    atsReadiness:   str = "—"
    impact:         str = "—"
    skillAlignment: str = "—"
    lastAnalyzed:   str = "never"


class RenderData(BaseModel):
    profile:      ProfileRenderData        = ProfileRenderData()
    score_label:  str                        = ""
    breakdown:    List[BreakdownRenderItem] = []
    flags:        List[FlagRenderItem]      = []
    llm_feedback: List[LLMFeedbackItem]    = []
    focus_areas:  List[str]                 = []
    dashboard:    DashboardRenderData        = DashboardRenderData()


class ResumeScoreResult(BaseModel):
    final_score:  int
    ats:          ATSResult
    llm_feedback: List[LLMFeedbackItem] = []
    render_data:  RenderData = RenderData()


class ResumePipelineResponse(BaseModel):
    success:       bool
    userId:        Optional[str]        = None
    filename:      Optional[str]        = None
    mimetype:      Optional[str]        = None
    parsed_resume: Optional[ParsedResume] = None
    score:         Optional[ResumeScoreResult] = None
    error:         Optional[str]        = None