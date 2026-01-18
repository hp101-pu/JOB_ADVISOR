from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# =====================================================
# Core Job Model
# =====================================================

class Job(BaseModel):
    id: str
    title: str
    company: str
    location: str
    description: str
    apply_url: str

    salary_min: Optional[float] = None
    salary_max: Optional[float] = None

    contract_type: Optional[str] = None
    contract_time: Optional[str] = None

    category: Optional[str] = None
    created: Optional[datetime] = None

    source: str = "adzuna"
    match_score: Optional[int] = None


# =====================================================
# Search
# =====================================================

class JobSearchRequest(BaseModel):
    keywords: str
    country: str = "in"
    where: str = ""
    max_results: int = 10
    page: int = 1


class JobSearchResponse(BaseModel):
    success: bool
    jobs: List[Job]
    count: int
    total_results: int
    page: int
    country: str
    error: Optional[str] = None


# =====================================================
# Filtering
# =====================================================

class JobFilterRequest(BaseModel):
    jobs: List[Job]
    required_skills: List[str]
    preferred_skills: List[str]


class JobFilterResponse(BaseModel):
    success: bool
    matched_jobs: List[Job]
    total_matches: int
    error: Optional[str] = None
