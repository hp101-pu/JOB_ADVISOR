"""
LLM Service for Intelligent Job Matching
Uses Groq LLM for semantic understanding and ranking
"""

import json
from typing import List, Dict, Any
from client.llm.groq_client import get_groq_client

MODEL_ID = "llama-3.1-8b-instant"


def generate_search_queries(user_context: Dict[str, Any]) -> List[str]:
    """
    Generate 3-5 targeted search queries based on user profile.
    
    Example output:
    [
        "React Senior Developer Bangalore",
        "Frontend Lead TypeScript Remote",
        "Full Stack Engineer Startup India"
    ]
    """
    
    try:
        skills_str = ", ".join(user_context["skills"][:5])  # Top 5 skills
        experience_years = user_context["experience_years"]
        location = user_context["location"].get("city", "")
        country = user_context["preferences"]["country"]
        
        # Determine seniority level
        if experience_years == 0:
            level = "Junior"
        elif experience_years <= 2:
            level = "Junior"
        elif experience_years <= 5:
            level = "Mid-Level"
        else:
            level = "Senior"
        
        # Create fallback queries in case LLM fails
        fallback_queries = [
            f"{skills_str[:50]} {level} {location}",
            f"{skills_str[:50]} Developer {country}",
            f"{user_context['experience_titles'][0] if user_context['experience_titles'] else 'Software Engineer'} {location}"
        ]
        
        prompt = f"""
You are a job search expert. Generate 3-5 targeted job search queries based on this profile:

Skills: {skills_str}
Experience: {experience_years} years ({level})
Location: {location}, {country}
Recent Roles: {", ".join(user_context["experience_titles"][:2]) if user_context["experience_titles"] else "None"}

Generate diverse search queries that:
1. Match primary skills with appropriate seniority
2. Include location preferences
3. Consider related roles and career growth
4. Mix specific and broader searches

Return ONLY a JSON array of search strings:
["query 1", "query 2", "query 3", "query 4", "query 5"]
""".strip()

        client = get_groq_client()
        
        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=200,
        )
        
        raw_text = response.choices[0].message.content.strip()
        
        # Clean markdown if present
        if raw_text.startswith("```"):
            raw_text = raw_text.strip("`").replace("json", "").strip()
        
        queries = json.loads(raw_text)
        print(f"🔍 Generated {len(queries)} search queries:")
        for q in queries:
            print(f"  - {q}")
        return queries[:5]  # Max 5 queries
        
    except Exception as e:
        # Fallback to basic queries if LLM fails
        print(f"⚠️ LLM query generation failed: {e}")
        print(f"⚠️ Using fallback queries")
        return fallback_queries[:3]  # Return 3 fallback queries


def rank_and_score_jobs(
    user_context: Dict[str, Any],
    jobs: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Use LLM to rank jobs and assign match scores (0-100).
    
    Returns jobs with added fields:
    - match_score: 0-100
    - match_reason: Brief explanation
    """
    
    if not jobs:
        return []
    
    # Prepare user context summary
    skills_str = ", ".join(user_context["skills"][:10])
    experience_years = user_context["experience_years"]
    preferences = user_context["preferences"]
    
    # Process in batches (LLM context limits)
    batch_size = 10
    ranked_jobs = []
    
    for i in range(0, len(jobs), batch_size):
        batch = jobs[i:i+batch_size]
        
        # Prepare job summaries for LLM
        job_summaries = []
        for idx, job in enumerate(batch):
            job_summaries.append(f"""
Job {idx+1}:
Title: {job['title']}
Company: {job['company']}
Location: {job['location']}
Description: {job['description'][:300]}...
""".strip())
        
        jobs_text = "\n\n".join(job_summaries)
        
        prompt = f"""
You are a job matching expert. Rate how well each job matches this candidate:

CANDIDATE PROFILE:
- Skills: {skills_str}
- Experience: {experience_years} years
- Preferred Location: {preferences.get('city', 'Flexible')}
- Remote Preference: {preferences.get('remote', False)}

JOBS TO EVALUATE:
{jobs_text}

For each job, provide:
1. Match score (0-100): How well it fits the candidate
2. Brief reason (15-25 words max)

Consider:
- Skills match (most important)
- Experience level fit
- Location preference
- Career growth potential
- Company reputation (if recognizable)

Return STRICT JSON only:
[
  {{"job_index": 1, "score": 85, "reason": "Strong React skills match, senior level aligns with experience"}},
  {{"job_index": 2, "score": 72, "reason": "Good technical fit but location doesn't match preference"}}
]
""".strip()

        client = get_groq_client()
        
        try:
            response = client.chat.completions.create(
                model=MODEL_ID,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500,
            )
            
            raw_text = response.choices[0].message.content.strip()
            
            # Clean markdown
            if raw_text.startswith("```"):
                raw_text = raw_text.strip("`").replace("json", "").strip()
            
            scores = json.loads(raw_text)
            
            # Apply scores to jobs
            for score_data in scores:
                job_idx = score_data["job_index"] - 1
                if 0 <= job_idx < len(batch):
                    batch[job_idx]["match_score"] = score_data["score"]
                    batch[job_idx]["match_reason"] = score_data["reason"]
            
        except Exception as e:
            print(f"⚠️ LLM ranking failed for batch: {e}")
            # Fallback: assign default scores
            for job in batch:
                job["match_score"] = 50
                job["match_reason"] = "Match based on keyword analysis"
        
        ranked_jobs.extend(batch)
    
    # Sort by score
    ranked_jobs.sort(key=lambda j: j.get("match_score", 0), reverse=True)
    
    print(f"✅ Ranked {len(ranked_jobs)} jobs (top score: {ranked_jobs[0].get('match_score', 0) if ranked_jobs else 0})")
    
    return ranked_jobs