"""
User Profile API Client
Fetches user data from Node.js backend for personalized recommendations
"""

import httpx
import os
from typing import Optional, Dict, Any

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000")


async def get_user_profile(jwt: str) -> Optional[Dict[str, Any]]:
    """Fetch complete user profile from Node backend"""
    
    url = f"{BACKEND_URL}/api/profile/me"
    headers = {
        "Authorization": f"Bearer {jwt}",
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("profile"):
                    return data["profile"]
            return None
                
    except Exception as e:
        print(f"❌ Failed to fetch user profile: {e}")
        raise


def extract_user_context(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Extract relevant fields from user profile for job matching"""
    
    skills = profile.get("skills", [])
    experience_items = profile.get("experience", [])
    experience_years = len(experience_items)
    experience_titles = [exp.get("title", "") for exp in experience_items]
    
    education_items = profile.get("education", [])
    education = [
        f"{edu.get('degree', '')} {edu.get('fieldOfStudy', '')}".strip()
        for edu in education_items
    ]
    
    location = profile.get("location", {})
    job_prefs = profile.get("jobPreferences", {})
    
    return {
        "skills": skills,
        "experience_years": experience_years,
        "experience_titles": experience_titles,
        "education": education,
        "location": location,
        "preferences": {
            "remote": job_prefs.get("remoteOnly", False),
            "job_types": job_prefs.get("jobTypes", []),
            "min_salary": job_prefs.get("minSalary"),
            "city": job_prefs.get("city"),
            "country": job_prefs.get("country", "in")
        },
        "open_to_work": profile.get("openToWork", False),
        "headline": profile.get("headline", "")
    }