from typing import List, Optional, Dict, Any
import asyncio

from client.wrappers.job_wrapper import (
    search_jobs,
    filter_jobs_by_skills,
    get_job_categories,
)
from client.schemas.job import JobSearchResponse, Job

from client.backend_client.user_api import get_user_profile, extract_user_context
from client.llm.job_matching_service import generate_search_queries, rank_and_score_jobs
from client.orchestrator.rule_based_filter import filter_jobs_by_rules


async def get_personalized_recommendations_hybrid(
    user_id: str,
    jwt: str,
    max_results: int = 20,
) -> Dict[str, Any]:
    """
    HYBRID Job Recommendations Pipeline
    
    Flow:
    1. Fetch user profile from backend
    2. LLM generates 3-5 targeted search queries
    3. Execute all searches in parallel (aggregate 50-100 jobs)
    4. Rule-based filtering (fast, deterministic)
    5. LLM ranking (intelligent, semantic)
    6. Return top N with match scores and reasons
    """
    
    try:
        print(f"🚀 Starting HYBRID recommendations for user: {user_id}")
        
        # Step 1: Fetch user profile
        print("📥 Fetching user profile...")
        profile = await get_user_profile(jwt)
        
        if not profile:
            print("⚠️ No user profile found, falling back to generic search")
            return await search_jobs_pipeline(
                keywords="software engineer",
                location="",
                country="in",
                user_id=user_id,
                jwt=jwt,
                max_results=max_results,
            )
        
        user_context = extract_user_context(profile)
        print(f"✅ User context: {len(user_context['skills'])} skills, {user_context['experience_years']} years exp")
        
        # Step 2: Generate search queries using LLM
        print("🤖 Generating personalized search queries with LLM...")
        try:
            search_queries = generate_search_queries(user_context)
        except Exception as e:
            print(f"⚠️ LLM query generation failed: {e}, using fallback")
            skills_str = ", ".join(user_context["skills"][:3])
            location = user_context["location"].get("city", "")
            search_queries = [f"{skills_str} developer {location}"]
        
        # Step 3: Execute all searches in parallel with better error handling
        print(f"🔍 Executing {len(search_queries)} parallel searches...")
        
        country = user_context["preferences"]["country"]
        location = user_context["preferences"].get("city", "")
        
        # Create search tasks
        search_tasks = []
        for query in search_queries:
            task = search_jobs(
                keywords=query,
                country=country,
                where=location or "",
                max_results=20,
                page=1,
            )
            search_tasks.append(task)
        
        # Execute searches with individual error handling
        search_results = []
        for i, task in enumerate(search_tasks):
            try:
                result = await task
                search_results.append(result)
                print(f"✅ Search {i+1}/{len(search_tasks)} completed: {len(result.jobs) if result.success else 0} jobs")
            except Exception as e:
                print(f"⚠️ Search {i+1}/{len(search_tasks)} failed: {type(e).__name__}: {str(e)}")
                import traceback
                traceback.print_exc()
                # Continue with other searches
                continue
        
        # Aggregate all jobs (remove duplicates by ID)
        all_jobs = []
        seen_ids = set()
        
        for result in search_results:
            if hasattr(result, 'success') and result.success:
                for job in result.jobs:
                    if job.id not in seen_ids:
                        all_jobs.append(job.dict())
                        seen_ids.add(job.id)
        
        print(f"✅ Aggregated {len(all_jobs)} unique jobs from {len(search_results)} successful searches")
        
        if not all_jobs:
            return {
                "success": False,
                "error": "No jobs found matching your profile",
                "jobs": [],
                "count": 0,
            }
        
        # Step 4: Rule-based filtering (FAST)
        print("⚡ Applying rule-based filters...")
        filtered_jobs = filter_jobs_by_rules(all_jobs, user_context)
        
        if not filtered_jobs:
            return {
                "success": True,
                "jobs": [],
                "count": 0,
                "message": "No jobs matched your profile criteria"
            }
        
        # Step 5: LLM ranking (INTELLIGENT)
        print("🤖 LLM ranking and scoring jobs...")
        try:
            ranked_jobs = rank_and_score_jobs(user_context, filtered_jobs[:50])
        except Exception as e:
            print(f"⚠️ LLM ranking failed: {e}")
            # Fallback: use rule-based scores only
            for job in filtered_jobs:
                job["match_score"] = job.get("basic_match_score", 50)
                job["match_reason"] = "Match based on skill keywords"
            ranked_jobs = filtered_jobs
        
        # Step 6: Return top N
        final_jobs = ranked_jobs[:max_results]
        
        print(f"✅ Returning top {len(final_jobs)} recommendations")
        
        return {
            "success": True,
            "jobs": final_jobs,
            "count": len(final_jobs),
            "total_found": len(all_jobs),
            "filtered_count": len(filtered_jobs),
            "search_queries_used": search_queries,
            "recommendation_type": "hybrid_llm_powered",
        }
        
    except Exception as e:
        print(f"❌ Hybrid recommendations error: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "error": str(e),
            "jobs": [],
        }


async def rank_jobs_by_relevance(
    jobs: List[Dict],
    user_id: str,
    jwt: str,
) -> Dict[str, Any]:
    """
    Lightweight ranking for search results.
    Uses rule-based filtering + LLM scoring for speed.
    Faster than full recommendations (no multi-query search).
    """
    try:
        print(f"🎯 Ranking {len(jobs)} search results for user: {user_id}")
        
        # Fetch user profile
        profile = await get_user_profile(jwt)
        if not profile:
            print("⚠️ No user profile found, returning unranked")
            return {"success": True, "jobs": jobs}
        
        user_context = extract_user_context(profile)
        print(f"✅ User context: {len(user_context['skills'])} skills")
        
        # Apply rule-based scoring (fast)
        scored_jobs = []
        for job in jobs:
            score = calculate_relevance_score(job, user_context)
            job_copy = job.copy()
            job_copy["relevance_score"] = score
            scored_jobs.append(job_copy)
        
        # Sort by relevance
        scored_jobs.sort(key=lambda j: j["relevance_score"], reverse=True)
        
        print(f"✅ Ranked jobs (top score: {scored_jobs[0]['relevance_score'] if scored_jobs else 0})")
        
        return {
            "success": True,
            "jobs": scored_jobs,
        }
    except Exception as e:
        print(f"❌ Ranking error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": True, "jobs": jobs}  # Fail gracefully


def calculate_relevance_score(job: Dict, user_context: Dict) -> int:
    """
    Calculate a 0-100 relevance score based on rules.
    More comprehensive than basic filter.
    """
    score = 0
    
    job_title = normalize_text(job.get("title", ""))
    job_desc = normalize_text(job.get("description", ""))
    job_location = normalize_text(job.get("location", ""))
    job_content = f"{job_title} {job_desc}"
    
    # 1. Skill matching (0-40 points)
    matched_skills = 0
    for skill in user_context["skills"][:15]:
        if normalize_text(skill) in job_content:
            matched_skills += 1
    score += min(matched_skills * 3, 40)
    
    # 2. Location match (0-15 points)
    preferred_city = normalize_text(user_context["location"].get("city", ""))
    if preferred_city:
        if preferred_city in job_location:
            score += 15
        elif "remote" in job_location:
            score += 12
        elif user_context["preferences"].get("remote"):
            # User wants remote but job isn't remote
            score -= 5
    
    # 3. Experience level match (0-20 points)
    exp_years = user_context["experience_years"]
    
    # Senior level indicators
    if exp_years >= 5:
        if any(word in job_title for word in ["senior", "lead", "principal", "architect"]):
            score += 20
        elif any(word in job_title for word in ["junior", "intern", "entry"]):
            score -= 10  # Penalty for mismatch
    
    # Mid level
    elif 2 <= exp_years < 5:
        if any(word in job_title for word in ["mid", "developer", "engineer"]):
            score += 15
        elif "senior" in job_title:
            score += 8  # Slight bonus for growth opportunity
    
    # Junior level
    else:
        if any(word in job_title for word in ["junior", "entry", "graduate"]):
            score += 15
        elif "senior" in job_title:
            score -= 10  # Too advanced
    
    # 4. Job type preference (0-10 points)
    job_types = user_context["preferences"].get("job_types", [])
    if job_types:
        # Check if any preferred type matches
        for jtype in job_types:
            if normalize_text(jtype) in job_content:
                score += 10
                break
    
    # 5. Salary match (0-10 points)
    min_salary = user_context["preferences"].get("min_salary")
    if min_salary:
        job_min_salary = job.get("salary_min")
        if job_min_salary:
            if job_min_salary >= min_salary:
                score += 10
            elif job_min_salary >= min_salary * 0.8:
                score += 5
    
    # 6. Recent experience match (0-5 points)
    recent_titles = user_context["experience_titles"][:2]
    for title in recent_titles:
        if normalize_text(title) in job_title:
            score += 5
            break
    
    return min(score, 100)  # Cap at 100


def normalize_text(text: str) -> str:
    """Normalize text for matching"""
    import re
    return re.sub(r'[^a-z0-9 ]', ' ', str(text).lower())
# ============================================================
# Pipeline 1: Complete Job Search with Optional Matching
# ============================================================

async def search_jobs_pipeline(
    keywords: str,
    location: str,
    country: str,
    user_id: str,
    jwt: str,
    use_resume_matching: bool = False,
    max_results: int = 20,
    page: int = 1,
) -> Dict[str, Any]:
    """
    Full job search pipeline with optional skill matching.
    
    Steps:
    1. Search jobs via MCP
    2. If use_resume_matching, fetch user skills and filter
    3. Return formatted results
    """
    
    try:
        # Step 1: Search jobs via MCP
        print(f"🔍 Searching jobs: keywords='{keywords}', location='{location}', country='{country}'")
        
        try:
            search_result = await search_jobs(
                keywords=keywords,
                country=country,
                where=location,
                max_results=max_results,
                page=page,
            )
        except Exception as search_error:
            print(f"❌ Search jobs wrapper error: {type(search_error).__name__}: {search_error}")
            import traceback
            traceback.print_exc()
            raise
        
        if not search_result.success:
            return {
                "success": False,
                "error": search_result.error or "Job search failed",
                "jobs": [],
            }
        
        jobs = search_result.jobs
        print(f"✅ Found {len(jobs)} jobs")
        
        # Step 2: Resume matching (placeholder for now)
        if use_resume_matching:
            print("⚠️ Resume matching requested but not yet implemented (Phase 2)")
            # Will implement in Phase 2:
            # - Fetch user profile from MongoDB
            # - Extract skills from resume
            # - Filter jobs using filter_jobs_by_skills
            # - Add match scores
        
        # Step 3: Format response
        return {
            "success": True,
            "jobs": [job.dict() for job in jobs],
            "count": len(jobs),
            "total_results": search_result.total_results,
            "page": search_result.page,
            "country": search_result.country,
            "matched_to_resume": use_resume_matching,
        }
        
    except Exception as e:
        print(f"❌ Job search pipeline error: {e}")
        return {
            "success": False,
            "error": str(e),
            "jobs": [],
        }


# ============================================================
# Pipeline 2: Personalized Recommendations
# ============================================================

async def get_personalized_recommendations(
    user_id: str,
    jwt: str,
    max_results: int = 20,
) -> Dict[str, Any]:
    """
    Get personalized job recommendations based on user profile.
    
    Phase 1: Basic implementation (generic search)
    Phase 2: Will add:
    - Fetch user profile from MongoDB
    - Extract skills and preferences
    - Build personalized query
    - Match and rank by relevance
    """
    
    try:
        print(f"🔍 Getting recommendations for user: {user_id}")
        
        # Phase 1: Generic search as placeholder
        # Phase 2: Will fetch user profile and build personalized query
        result = await search_jobs_pipeline(
            keywords="software engineer",
            location="",
            country="in",
            user_id=user_id,
            jwt=jwt,
            use_resume_matching=False,  # Phase 2: Set to True
            max_results=max_results,
        )
        
        return result
        
    except Exception as e:
        print(f"❌ Recommendations pipeline error: {e}")
        return {
            "success": False,
            "error": str(e),
            "jobs": [],
        }


# ============================================================
# Helper: Get Job Categories
# ============================================================

async def fetch_job_categories(country: str = "in") -> Dict[str, Any]:
    """
    Fetch job categories from job_search_mcp.
    """
    try:
        print(f"📋 Fetching job categories for country: {country}")
        return await get_job_categories(country=country)
    except Exception as e:
        print(f"❌ Categories fetch error: {e}")
        return {
            "success": False,
            "error": str(e),
            "categories": [],
        }


# ============================================================
# Legacy Functions (Keep for backward compatibility)
# ============================================================

async def search_and_filter_jobs(
    keywords: str,
    country: str = "in",
    where: str = "",
    required_skills: Optional[List[str]] = None,
    preferred_skills: Optional[List[str]] = None,
    max_results: int = 20,
    page: int = 1,
) -> Dict[str, Any]:
    """
    DEPRECATED: Use search_jobs_pipeline instead.
    Kept for backward compatibility.
    """
    
    search_response: JobSearchResponse = await search_jobs(
        keywords=keywords,
        country=country,
        where=where,
        max_results=max_results,
        page=page,
    )

    if not search_response.success:
        return {
            "success": False,
            "error": "Job search failed",
            "jobs": [],
        }

    if not required_skills and not preferred_skills:
        return {
            "success": True,
            "jobs": [job.dict() for job in search_response.jobs],
            "count": search_response.count,
            "total_results": search_response.total_results,
            "page": search_response.page,
            "country": search_response.country,
            "filtered": False,
        }

    filter_result = await filter_jobs_by_skills(
        jobs=search_response.jobs,
        required_skills=required_skills or [],
        preferred_skills=preferred_skills or [],
    )

    return {
        "success": filter_result.success,
        "jobs": filter_result.matched_jobs,
        "total_matches": filter_result.total_matches,
        "filtered": True,
    }


async def get_recommended_jobs_for_user(user_id: str) -> Dict[str, Any]:
    """
    DEPRECATED: Use get_personalized_recommendations instead.
    """
    return await search_and_filter_jobs(
        keywords="software engineer",
        country="in",
        where="bangalore",
        max_results=10,
    )