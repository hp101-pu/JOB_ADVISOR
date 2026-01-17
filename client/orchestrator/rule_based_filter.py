"""
Rule-Based Job Filtering
Fast deterministic filtering before LLM ranking
"""

from typing import List, Dict, Any
import re


def normalize_text(text: str) -> str:
    """Normalize text for matching"""
    return re.sub(r'[^a-z0-9 ]', ' ', text.lower())


def filter_jobs_by_rules(
    jobs: List[Dict[str, Any]],
    user_context: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Apply rule-based filtering to jobs.
    
    Filters:
    1. Required skills (at least 1 must match)
    2. Location preference (if specified)
    3. Salary range (if specified)
    4. Experience level (avoid junior roles for seniors, etc.)
    
    Returns filtered list with basic_match_score
    """
    
    skills = [normalize_text(s) for s in user_context["skills"]]
    experience_years = user_context["experience_years"]
    preferences = user_context["preferences"]
    
    filtered_jobs = []
    
    for job in jobs:
        job_title = normalize_text(job.get("title", ""))
        job_desc = normalize_text(job.get("description", ""))
        job_content = f"{job_title} {job_desc}"
        
        # Rule 1: Skills matching
        matched_skills = []
        for skill in skills[:15]:  # Check top 15 skills
            if skill in job_content:
                matched_skills.append(skill)
        
        if not matched_skills:
            continue  # Skip if no skills match
        
        # Rule 2: Location filtering (if preferred city specified)
        preferred_city = (preferences.get("city") or "").lower()
        if preferred_city:
            job_location = normalize_text(job.get("location", ""))
            # Allow remote jobs or matching city
            if "remote" not in job_location and preferred_city not in job_location:
                # Still include but with lower score
                pass
        
        # Rule 3: Salary filtering (if min salary specified)
        min_salary = preferences.get("min_salary")
        if min_salary:
            job_min_salary = job.get("salary_min")
            if job_min_salary and job_min_salary < min_salary * 0.8:  # 20% tolerance
                continue  # Skip if salary too low
        
        # Rule 4: Experience level filtering
        # Junior roles should not appear for 5+ years exp
        if experience_years >= 5:
            if any(word in job_title for word in ["intern", "trainee", "junior", "entry level"]):
                continue
        
        # Calculate basic match score (0-50 range)
        # LLM will add 0-50 more points based on semantic matching
        basic_score = min(len(matched_skills) * 5, 50)  # Max 50 from rules
        
        job_copy = job.copy()
        job_copy["basic_match_score"] = basic_score
        job_copy["matched_skills"] = matched_skills[:5]  # Top 5 for display
        
        filtered_jobs.append(job_copy)
    
    print(f"✅ Rule-based filter: {len(jobs)} → {len(filtered_jobs)} jobs")
    
    # Sort by basic score (will be re-sorted after LLM ranking)
    filtered_jobs.sort(key=lambda j: j["basic_match_score"], reverse=True)
    
    return filtered_jobs