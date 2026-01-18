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


class ParsedResume(BaseModel):
    sections: ResumeSections
    entities: ResumeEntities


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


class ResumeScoreResult(BaseModel):
    final_score:  int
    ats:          ATSResult
    llm_feedback: List[LLMFeedbackItem] = []


class ResumePipelineResponse(BaseModel):
    success:       bool
    userId:        Optional[str]        = None
    filename:      Optional[str]        = None
    mimetype:      Optional[str]        = None
    parsed_resume: Optional[ParsedResume] = None
    score:         Optional[ResumeScoreResult] = None
    error:         Optional[str]        = None