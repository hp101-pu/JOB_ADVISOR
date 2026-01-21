from mcp.server.fastmcp import FastMCP
import httpx  # Use httpx instead of requests for async
import os
import re
import time
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("job-search-mcp")

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_API_KEY = os.getenv("ADZUNA_API_KEY")

BASE_URL = "https://api.adzuna.com/v1/api/jobs"

CACHE: Dict[str, Dict] = {}
CACHE_TTL = 300  # 5 minutes


def _cache_key(*args) -> str:
    return ":".join(str(a) for a in args)


def _is_cache_valid(entry: Dict) -> bool:
    return time.time() - entry["time"] < CACHE_TTL


# -------------------------------------------------
# Utility Helpers
# -------------------------------------------------

def normalize(text: str) -> str:
    """
    Normalize text for reliable matching:
    - lowercase
    - remove punctuation
    """
    return re.sub(r"[^a-z0-9 ]", " ", text.lower())


# -------------------------------------------------
# MCP TOOLS (NOW ASYNC)
# -------------------------------------------------

@mcp.tool()
async def search_jobs(
    keywords: str,
    country: str = "in",
    where: str = "",
    max_results: int = 10,
    page: int = 1
):
    """
    Search for jobs using Adzuna API.
    """

    if not ADZUNA_APP_ID or not ADZUNA_API_KEY:
        return {
            "success": False,
            "error": "Adzuna API credentials not configured",
            "jobs": []
        }

    cache_key = _cache_key("search", keywords, country, where, max_results, page)
    cached = CACHE.get(cache_key)

    if cached and _is_cache_valid(cached):
        return cached["data"]

    url = f"{BASE_URL}/{country}/search/{page}"

    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_API_KEY,
        "what": keywords,
        "results_per_page": min(max_results, 50),
        "content-type": "application/json"
    }

    if where:
        params["where"] = where

    try:
        # Use httpx async client
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()

        jobs = []
        for job in payload.get("results", []):
            jobs.append({
                "id": str(job.get("id")),
                "title": job.get("title"),
                "company": job.get("company", {}).get("display_name", "Unknown"),
                "location": job.get("location", {}).get("display_name", ""),
                "description": job.get("description", "")[:1000],
                "apply_url": job.get("redirect_url"),
                "salary_min": job.get("salary_min"),
                "salary_max": job.get("salary_max"),
                "contract_type": job.get("contract_type"),
                "contract_time": job.get("contract_time"),
                "category": job.get("category", {}).get("label"),
                "created": job.get("created"),
                "source": "adzuna"
            })

        result = {
            "success": True,
            "jobs": jobs,
            "count": len(jobs),
            "total_results": payload.get("count", 0),
            "page": page,
            "country": country
        }

        CACHE[cache_key] = {
            "time": time.time(),
            "data": result
        }

        return result

    except httpx.HTTPError as e:
        return {
            "success": False,
            "error": f"Adzuna request failed: {str(e)}",
            "jobs": []
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "jobs": []
        }


@mcp.tool()
async def get_job_categories(country: str = "in"):
    """
    Fetch available job categories from Adzuna.
    """

    if not ADZUNA_APP_ID or not ADZUNA_API_KEY:
        return {"success": False, "error": "Missing Adzuna credentials"}

    url = f"{BASE_URL}/{country}/categories"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                url,
                params={"app_id": ADZUNA_APP_ID, "app_key": ADZUNA_API_KEY}
            )
            response.raise_for_status()

        return {
            "success": True,
            "categories": response.json().get("results", [])
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def filter_jobs_by_skills(
    jobs: List[Dict],
    required_skills: List[str],
    preferred_skills: List[str]
):
    """
    Filter and rank jobs based on resume skills.
    This is CPU-bound, so it stays synchronous.
    """

    matched_jobs = []

    for job in jobs:
        title = normalize(job.get("title", ""))
        description = normalize(job.get("description", ""))
        content = f"{title} {description}"

        score = 0
        matched_required = False

        # Required skills (high weight)
        for skill in required_skills:
            skill_norm = normalize(skill)
            if skill_norm and skill_norm in content:
                score += 3
                matched_required = True

        # Preferred skills (low weight)
        for skill in preferred_skills:
            skill_norm = normalize(skill)
            if skill_norm and skill_norm in content:
                score += 1

        if matched_required or score >= 3:
            job_copy = job.copy()
            job_copy["match_score"] = score
            matched_jobs.append(job_copy)

    matched_jobs.sort(
        key=lambda j: j.get("match_score", 0),
        reverse=True
    )

    return {
        "success": True,
        "matched_jobs": matched_jobs,
        "total_matches": len(matched_jobs)
    }


@mcp.tool()
def ping():
    """
    Health check for Job Search MCP.
    """

    return {
        "status": "active",
        "service": "Job Search MCP",
        "provider": "Adzuna",
        "api_configured": bool(ADZUNA_APP_ID and ADZUNA_API_KEY)
    }


# -------------------------------------------------
# MCP Runner
# -------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="stdio")