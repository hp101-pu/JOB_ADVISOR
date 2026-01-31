from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import os

from client.mcp.client import get_mcp_client, close_mcp_client
from client.orchestrator.email_agent import prepare_email_reply_preview,send_email_with_approval,ingest_and_store_emails

from client.orchestrator.job_agent import (
    search_jobs_pipeline,
    get_personalized_recommendations_hybrid,
    fetch_job_categories,
    rank_jobs_by_relevance,
)
# resume pipeline
from client.orchestrator.resume_agent import parse_resume_pipeline, rescore_resume_pipeline
from client.wrappers.resume_wrapper import _get_tool as _warm_resume

from client.orchestrator.calendar_agent import create_calendar_event_pipeline
from client.orchestrator.calendar_email_extractor import extract_calendar_from_email_pipeline
from client.backend_client.email_query_api import query_emails_from_db
from client.backend_client.email_digest_api import fetch_emails_for_digest
from client.backend_client.calendar_query_api import query_calendar_events_from_db
from client.ask_seekr.entrypoint import handle_user_message
from pydantic import BaseModel
from typing import Optional

app = FastAPI()


@app.on_event("startup")
async def on_startup():
    """Pre-warm the resume MCP connection so the first upload isn't slow."""
    try:
        from client.wrappers.resume_wrapper import _get_tool as _warm_resume
        await _warm_resume("ping")
    except Exception:
        pass  # ping tool may not exist — that's fine, connection is still warmed


@app.on_event("shutdown")
async def on_shutdown():
    await close_mcp_client()


SERVICE_KEY = os.getenv("SERVICE_KEY")
if not SERVICE_KEY:
    raise RuntimeError("SERVICE_KEY not set")


# ---------------------------
# JWT middleware (SAFE)
# ---------------------------
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """
    Unified authentication middleware
    - User requests: JWT authentication
    - Cron requests: Service key + user ID in header
    """
    # Always get source (defaults to "user")
    source = request.headers.get("X-Request-Source", "user")
    
    # Verify service key for ALL requests
    service_key = request.headers.get("X-Service-Key")
    if service_key != SERVICE_KEY:
        return JSONResponse(
            {"error": "Invalid service key"}, 
            status_code=401
        )
    
    # Initialize state
    request.state.jwt = None
    request.state.user_id = None
    request.state.source = source
    
    if source == "cron":
        # CRON: Get userId from header (no JWT needed)
        user_id = request.headers.get("X-User-Id")
        if not user_id:
            return JSONResponse(
                {"error": "X-User-Id header missing for cron request"}, 
                status_code=400
            )
        request.state.user_id = user_id
        print(f"🤖 [CRON] Request for user: {user_id}")
        
    elif source == "user":
        # USER: Extract and validate JWT
        auth = request.headers.get("Authorization")
        if auth and auth.startswith("Bearer "):
            jwt_token = auth[7:].strip()
            request.state.jwt = jwt_token
            # Note: Actual JWT validation happens in individual pipelines
            # You could add JWT decode here to set user_id if needed
        else:
            # Some endpoints might not require JWT (like health checks)
            # We'll let individual endpoints enforce JWT requirement
            pass
    
    else:
        return JSONResponse(
            {"error": f"Invalid X-Request-Source: {source}"}, 
            status_code=400
        )
    
    response = await call_next(request)
    return response


# ---------------------------
# MCP executor
# ---------------------------
@app.post("/agent/execute")
async def execute_agent(request: Request):
    if request.headers.get("X-Service-Key") != SERVICE_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized service")

    body = await request.json()
    tool_name = body.get("tool")
    args = body.get("args", {})
    user_id = body.get("userId")
    jwt = request.state.jwt

    if not tool_name or not user_id:
        raise HTTPException(status_code=400, detail="tool and userId required")

    # Tools expect args.userId → already provided by Node
    args.setdefault("userId", user_id)

    mcp = await get_mcp_client()
    tools = await mcp.get_tools()

    tool = next((t for t in tools if t.name == tool_name), None)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    try:
        result = await tool.ainvoke(args)
        return result[0]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Tool execution failed: {str(e)}"
        )

# ---------------------------
# Email reply preview pipeline
# ---------------------------
@app.post("/pipelines/email-reply-preview")
async def email_reply_preview(request: Request):
    if request.headers.get("X-Service-Key") != SERVICE_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized service")

    body = await request.json()

    message_id = body.get("messageId")
    tone = body.get("tone", "professional")
    user_id = body.get("userId")
    jwt = request.state.jwt
    if not jwt:
        raise HTTPException(status_code=401, detail="JWT missing")

    print(jwt,"APP>POST/PIPELINE")

    if not message_id or not user_id:
        raise HTTPException(
            status_code=400,
            detail="messageId and userId required"
        )

    if not jwt:
        raise HTTPException(status_code=401, detail="JWT missing")

    try:
        result = await prepare_email_reply_preview(
            message_id=message_id,
            tone=tone,
            jwt=jwt
        )
        return result
    except Exception as e:
        import traceback
        print(f"❌ email-reply-preview FULL ERROR:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pipelines/email-reply-send")
async def email_reply_send(request: Request):
    if request.headers.get("X-Service-Key") != SERVICE_KEY:
        raise HTTPException(status_code=401)

    body = await request.json()
    draft = body.get("draft")
    jwt = request.state.jwt

    if not jwt or not draft:
        raise HTTPException(status_code=400)

    result = await send_email_with_approval(draft, jwt)
    return result


@app.post("/pipelines/email-sync")
async def email_sync(request: Request):
    if request.headers.get("X-Service-Key") != SERVICE_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized service")

    source = request.state.source
    
    if source == "user":
        # USER flow: requires JWT
        jwt = request.state.jwt
        if not jwt:
            raise HTTPException(status_code=401, detail="JWT missing")
        
        print(f"👤 [USER] Email sync with JWT")
        result = await ingest_and_store_emails(jwt=jwt)
    
    elif source == "cron":
        # CRON flow: no JWT, uses user_id from header
        user_id = request.state.user_id
        print(f"🤖 [CRON] Email sync for user: {user_id}")
        
        # Pass None for JWT, user_id separately - MCP handles OAuth fetch
        result = await ingest_and_store_emails(jwt=None, user_id=user_id)
    
    else:
        raise HTTPException(status_code=400, detail="Invalid source")

    return {
        "status": "ok",
        "synced": len(result)
    }

# ============================================================
# JOB PIPELINES
# ============================================================

@app.post("/pipelines/job-search")
async def job_search_pipeline_endpoint(request: Request):
    if request.headers.get("X-Service-Key") != SERVICE_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized service")

    body = await request.json()
    jwt = request.state.jwt

    if not jwt:
        raise HTTPException(status_code=401, detail="JWT missing")

    user_id = body.get("userId")
    if not user_id:
        raise HTTPException(status_code=400, detail="userId required")

    keywords = body.get("keywords", "")
    if not keywords:
        raise HTTPException(status_code=400, detail="keywords required")

    print(f"📥 Job search request: keywords='{keywords}', user={user_id}")

    result = await search_jobs_pipeline(
        keywords=keywords,
        location=body.get("location", ""),
        country=body.get("country", "in"),
        user_id=user_id,
        jwt=jwt,
        use_resume_matching=body.get("useResumeMatching", False),
        max_results=body.get("maxResults", 20),
        page=body.get("page", 1),
    )

    print(f"📤 Job search response: success={result.get('success')}, count={result.get('count', 0)}")

    return result



@app.post("/pipelines/job-recommendations")
async def job_recommendations_pipeline_endpoint(request: Request):
    """
    Personalized job recommendations pipeline - HYBRID APPROACH
    """
    if request.headers.get("X-Service-Key") != SERVICE_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    body = await request.json()
    jwt = request.state.jwt

    if not jwt:
        raise HTTPException(status_code=401, detail="JWT missing")

    user_id = body.get("userId")
    if not user_id:
        raise HTTPException(status_code=400, detail="userId required")
    
    print(f"📥 HYBRID Recommendations request: user={user_id}")
    
    # Use the new hybrid function
    result = await get_personalized_recommendations_hybrid(
        user_id=user_id,
        jwt=jwt,
        max_results=body.get("maxResults", 20),
    )

    print(f"📤 Recommendations response: success={result.get('success')}, count={result.get('count', 0)}")

    return result

@app.post("/pipelines/rank-jobs")
async def rank_jobs_pipeline_endpoint(request: Request):
    """
    Rank search results by relevance for logged-in users.
    Lightweight ranking (rule-based only for speed).
    """
    if request.headers.get("X-Service-Key") != SERVICE_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    body = await request.json()
    jwt = request.state.jwt

    if not jwt:
        raise HTTPException(status_code=401, detail="JWT missing")

    user_id = body.get("userId")
    jobs = body.get("jobs", [])
    
    if not user_id:
        raise HTTPException(status_code=400, detail="userId required")
    
    if not jobs:
        return {"success": True, "jobs": []}

    print(f"📥 Rank jobs request: {len(jobs)} jobs for user={user_id}")

    result = await rank_jobs_by_relevance(
        jobs=jobs,
        user_id=user_id,
        jwt=jwt,
    )

    print(f"📤 Rank jobs response: success={result.get('success')}")

    return result

@app.get("/pipelines/job-categories")
async def job_categories_pipeline_endpoint(request: Request):
    if request.headers.get("X-Service-Key") != SERVICE_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    country = request.query_params.get("country", "in")

    print(f"📥 Categories request: country={country}")

    result = await fetch_job_categories(country=country)

    return result
# ============================================================
# CALENDAR PIPELINES
# ============================================================

@app.post("/pipelines/calendar-create-event")
async def calendar_create_event_endpoint(request: Request):
    """
    Create a calendar event for interviews/assessments.
    """
    if request.headers.get("X-Service-Key") != SERVICE_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized service")
    
    body = await request.json()
    jwt = request.state.jwt
    
    if not jwt:
        raise HTTPException(status_code=401, detail="JWT missing")
    
    user_id = body.get("userId")
    if not user_id:
        raise HTTPException(status_code=400, detail="userId required")
    
    # Required fields
    event_type = body.get("eventType")
    company = body.get("company")
    date = body.get("date")
    start_time = body.get("startTime")
    end_time = body.get("endTime")
    
    if not all([event_type, company, date, start_time, end_time]):
        raise HTTPException(
            status_code=400,
            detail="eventType, company, date, startTime, and endTime are required"
        )
    
    print(f"📥 Calendar event request: {event_type} at {company} on {date}")
    
    result = await create_calendar_event_pipeline(
        event_type=event_type,
        company=company,
        date=date,
        start_time=start_time,
        end_time=end_time,
        user_id=user_id,
        jwt=jwt,
        role=body.get("role"),
        timezone=body.get("timezone", "Asia/Kolkata"),
        meet_link=body.get("meetLink"),
        description=body.get("description"),
    )
    
    print(f"📤 Calendar event response: success={result.get('success')}")
    
    return result



@app.post("/pipelines/calendar-query")
async def calendar_query_pipeline(request: Request):
    """
    Query all calendar events for the user from MongoDB.
    Returns events from the CalendarEvent collection (created by cron or chatbot).
    """
    if request.headers.get("X-Service-Key") != SERVICE_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized service")

    jwt = request.state.jwt

    if not jwt:
        raise HTTPException(status_code=401, detail="JWT missing")

    print(f"[calendar_query] Fetching all calendar events")

    result = await query_calendar_events_from_db(jwt=jwt)

    data = result.get("data", {})
    events = data.get("events", [])
    print(f"[calendar_query] Found {len(events)} calendar events")

    return {
        "total": len(events),
        "events": events,
    }



@app.post("/pipelines/extract-calendar-from-email")
async def extract_calendar_from_email_endpoint(request: Request):
    """
    Extract calendar event details from an interview email.
    Uses LLM to parse email content into structured calendar data.
    """
    if request.headers.get("X-Service-Key") != SERVICE_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized service")
    
    body = await request.json()
    
    # No JWT needed for this operation - it's just LLM parsing
    subject = body.get("subject")
    text = body.get("text")
    
    if not subject or not text:
        raise HTTPException(
            status_code=400,
            detail="subject and text are required"
        )
    
    print(f"📥 Calendar extraction request: {subject[:50]}...")
    
    result = await extract_calendar_from_email_pipeline(
        subject=subject,
        text=text,
    )
    
    print(f"📤 Calendar extraction response: success={result.get('success')}")
    
    return result



@app.post("/pipelines/email-query")
async def email_query_pipeline(request: Request):
    if request.headers.get("X-Service-Key") != SERVICE_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized service")

    body = await request.json()
    jwt = request.state.jwt

    if not jwt:
        raise HTTPException(status_code=401, detail="JWT missing")

    result = await query_emails_from_db(
        jwt=jwt,
        sender=body.get("sender"),
        type=body.get("type"),
        folder=body.get("folder"),
        keyword=body.get("keyword"),
        limit=body.get("limit", 20),
    )

    return result


# ============================================================
# EMAIL DIGEST PIPELINE
# ============================================================

@app.post("/pipelines/email-digest")
async def email_digest_pipeline(request: Request):
    """
    Fetch emails grouped by type for a given period.
    period: today | week | month | all
    """
    if request.headers.get("X-Service-Key") != SERVICE_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized service")

    body = await request.json()
    jwt = request.state.jwt

    if not jwt:
        raise HTTPException(status_code=401, detail="JWT missing")

    period = body.get("period", "week")
    print(f"📥 Email digest request: period={period}")

    result = await fetch_emails_for_digest(jwt=jwt, period=period)

    print(f"📤 Email digest: total={result['total']}, counts={result['counts']}")

    return result






# ============================================================
# EMAIL INGEST PIPELINE
# ============================================================

@app.post("/pipelines/ingest-emails")
async def ingest_emails_endpoint(request: Request):
    body = await request.json()
    source = request.state.source
    jwt = request.state.jwt
    user_id = body.get("userId") or request.state.user_id

    if not user_id:
        raise HTTPException(status_code=400, detail="userId required")

    if source == "cron":
        print(f"🤖 [CRON] Ingest emails for user: {user_id}")
        result = await ingest_and_store_emails(jwt=None, user_id=user_id)
    else:
        if not jwt:
            raise HTTPException(status_code=401, detail="JWT missing")
        print(f"👤 [USER] Ingest emails for user: {user_id}")
        result = await ingest_and_store_emails(jwt=jwt, user_id=user_id)

    print(f"📤 Ingest complete: stored {len(result)} emails for user {user_id}")
    return {"success": True, "stored": len(result), "userId": user_id}


# ============================================================
# APPLICATION TRACKER PIPELINES
# ============================================================

@app.post("/pipelines/application-stats")
async def application_stats_pipeline(request: Request):
    """
    Get job application stats — counts per status inferred from email types.
    """
    if request.headers.get("X-Service-Key") != SERVICE_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized service")

    body = await request.json()
    jwt = request.state.jwt

    if not jwt:
        raise HTTPException(status_code=401, detail="JWT missing")

    from client.backend_client.application_tracker_api import get_application_stats
    result = await get_application_stats(jwt=jwt, period=body.get("period", "all"))

    print(f"📤 Application stats: {result.get('summary')}")
    return result


@app.post("/pipelines/application-followup")
async def application_followup_pipeline(request: Request):
    """
    Find companies that haven't replied in N days.
    """
    if request.headers.get("X-Service-Key") != SERVICE_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized service")

    body = await request.json()
    jwt = request.state.jwt

    if not jwt:
        raise HTTPException(status_code=401, detail="JWT missing")

    from client.backend_client.application_tracker_api import get_followup_needed
    result = await get_followup_needed(jwt=jwt, days=body.get("days", 7))

    print(f"📤 Follow-up needed: {result.get('count')} companies")
    return result


# ============================================================
# ASK SEEKR CHAT
# ============================================================

class ChatRequest(BaseModel):
    text: str
    conversation_id: Optional[str] = None
    metadata: dict = {}
    confirmed: bool = False


@app.post("/ask-seekr")
async def ask_seekr(request: Request, body: ChatRequest):
    """
    Chat endpoint — proxied from Node /api/ai/chat.
    JWT arrives as Authorization: Bearer from Node after cookie verification.
    """
    jwt = request.state.jwt
    if not jwt:
        raise HTTPException(status_code=401, detail="Missing JWT")

    print("🟢 /ask-seekr called")
    print(f"🔒 confirmed={body.confirmed}")

    response = await handle_user_message(
        jwt=jwt,
        user_message=body.text,
        conversation_id=body.conversation_id,
        metadata=body.metadata,
        confirmed=body.confirmed,
    )

    return response

# RESUME PIPELINE

@app.post("/pipelines/resume-parse")
async def resume_parse_pipeline_endpoint(request: Request):
    """
    Resume parsing pipeline endpoint.

    Input JSON:
      {
        "userId": "...",
        "file_b64": "...",
        "filename": "resume.pdf" (optional),
        "mimetype": "application/pdf" (optional)
      }
    """
    if request.headers.get("X-Service-Key") != SERVICE_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized service")

    body = await request.json()
    jwt = request.state.jwt

    if not jwt:
        raise HTTPException(status_code=401, detail="JWT missing")

    user_id = body.get("userId")
    if not user_id:
        raise HTTPException(status_code=400, detail="userId required")

    file_b64 = body.get("file_b64")
    if not file_b64:
        raise HTTPException(status_code=400, detail="file_b64 required")

    print(f"📥 Resume parse request: user={user_id}")

    result = await parse_resume_pipeline(
        user_id=user_id,
        jwt=jwt,
        file_b64=file_b64,
        filename=body.get("filename", "resume.pdf"),
        mimetype=body.get("mimetype", "application/pdf"),
        use_llm=body.get("use_llm", True),
        job_description=body.get("job_description", None),
    )

    print(f"📤 Resume parse response: success={result.get('success')}")
    return result


@app.post("/pipelines/resume-recalculate")
async def resume_recalculate_pipeline_endpoint(request: Request):
    """
    Re-score an already-parsed resume using the latest ATS scorer.
    Skips the PDF parse step — uses the stored parsed_resume from MongoDB.

    Input JSON:
      {
        "userId": "...",
        "parsed_resume": { sections: {...}, entities: {...} }
      }
    """
    if request.headers.get("X-Service-Key") != SERVICE_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized service")

    body = await request.json()
    jwt  = request.state.jwt

    if not jwt:
        raise HTTPException(status_code=401, detail="JWT missing")

    user_id = body.get("userId")
    if not user_id:
        raise HTTPException(status_code=400, detail="userId required")

    parsed_resume = body.get("parsed_resume")
    if not parsed_resume:
        raise HTTPException(status_code=400, detail="parsed_resume required")

    print(f"📥 Resume recalculate request: user={user_id}")

    result = await rescore_resume_pipeline(
        user_id=user_id,
        parsed_resume=parsed_resume,
        use_llm=body.get("use_llm", True),
        job_description=body.get("job_description", None),
    )

    print(f"📤 Resume recalculate response: success={result.get('success')}")
    return result
