# Project Flowchart

This document maps the current project structure and runtime flow from the code in this repository.

## 1. High-Level System Flow

```mermaid
flowchart TB
    user["User"]
    browser["Browser"]
    frontend["React + Vite frontend\nfrontend/src"]
    backend["Node/Express backend\nbackend/src"]
    mongo["MongoDB\nMongoose models"]
    cloudinary["Cloudinary\nresume PDF/avatar storage"]
    python["Python FastAPI orchestrator\nclient/orchestrator/client.py"]
    chat["Ask Seekr chat engine\nclient/ask_seekr"]
    mcpClient["LangChain MultiServerMCPClient\nclient/mcp/client.py"]
    gmailMcp["Gmail MCP\nmcp_servers/gmail_mcp"]
    resumeMcp["Resume MCP HTTP server\nmcp_servers/resume_mcp :8001"]
    jobMcp["Job Search MCP\nmcp_servers/job_search_mcp"]
    calendarMcp["Calendar MCP\nmcp_servers/calendar_mcp\ncurrently not enabled in client/mcp/server.py"]
    google["Google APIs\nOAuth, Gmail, Calendar"]
    adzuna["Adzuna Jobs API"]
    llm["LLM providers\nOpenAI + Groq"]
    redis["Redis / memory store\nconversation and orchestration state"]
    sse["SSE channel\n/api/sse"]
    cron["Email sync cron\nbackend/src/jobs/emailSync.job.js"]

    user --> browser --> frontend
    frontend -->|"fetch with credentials include"| backend

    backend -->|"CRUD and user state"| mongo
    backend -->|"resume/avatar files"| cloudinary
    backend -->|"protected pipeline calls\nX-Service-Key + Bearer JWT"| python
    backend -->|"chat proxy\n/api/ai/chat"| chat
    backend -->|"server-sent events"| sse --> frontend
    cron -->|"background sync"| backend

    python --> mcpClient
    python -->|"pipeline summaries, ranking, drafting"| llm
    python -->|"profile/email/calendar API clients"| backend
    chat -->|"planner, validator, executor"| python
    chat -->|"conversation context"| redis
    chat -->|"chat replies and pipeline summaries"| llm

    mcpClient --> gmailMcp --> google
    mcpClient --> resumeMcp
    mcpClient --> jobMcp --> adzuna
    mcpClient -. optional .-> calendarMcp --> google
```

## 2. Repository Ownership Map

```mermaid
flowchart LR
    root["Project root"]

    backend["backend/\nExpress API gateway\nMongoDB models\nOAuth, email, jobs, resume, calendar routes\ncron jobs and SSE"]
    frontend["frontend/\nReact routes, pages, components\nbrowser API calls\nprotected app shell"]
    client["client/\nPython orchestration\nFastAPI pipelines\nMCP wrappers\nLLM, RAG, Ask Seekr, backend clients"]
    mcpServers["mcp_servers/\nstandalone MCP servers\nGmail, resume, job search, calendar"]
    docs["docs/\narchitecture and flow docs"]
    rootFiles["Root files\nREADME.md\nrequirements.txt\npackage.json\nemail.css\nflush_chat_history.py"]

    root --> backend
    root --> frontend
    root --> client
    root --> mcpServers
    root --> docs
    root --> rootFiles

    backend --> backendEntry["src/index.js\nloads env, connects DB, fixes indexes,\nstarts Express and email sync job"]
    backend --> backendApp["src/app.js\nmiddleware, route mounting,\nSSE, 404, global errors"]
    backend --> controllers["controllers/\nHTTP handlers"]
    backend --> services["services/\nbusiness logic and Python pipeline proxy"]
    backend --> models["models/\nUser, Resume, Email, OAuthToken, CalendarEvent"]
    backend --> routes["routes/\n/api/user, /api/auth, /api/jobs,\n/api/emails, /api/calendar, /api/ai,\n/api/resume, /api/profile"]

    frontend --> app["src/App.jsx\nReact Router map"]
    frontend --> pages["pages/\nAuth, Dashboard, Profile, Emails,\nJobs, Settings, AskAI, Resume"]
    frontend --> components["components/\nlayout, common, dashboard, emails,\njobs, profile, resume, auth"]
    frontend --> api["utils/api.js\nall browser-to-backend fetch helpers"]

    client --> fastapi["orchestrator/client.py\nFastAPI endpoints"]
    client --> ask["ask_seekr/\nplanner, validator, executor, memory, RAG"]
    client --> wrappers["wrappers/\nGmail, calendar, resume, job MCP tool wrappers"]
    client --> pyAgents["orchestrator/*_agent.py\nemail, job, resume, calendar pipelines"]
    client --> backendClients["backend_client/\nPython calls back into Express"]
    client --> llmLayer["llm/\nOpenAI, Groq, prompts, job matching"]
    client --> rag["rag/\nembeddings, ingest, retrieve, vector store"]

    mcpServers --> gmail["gmail_mcp\nGmail fetch, parse, draft, send"]
    mcpServers --> resume["resume_mcp\nPDF parse, section extraction, ATS scoring"]
    mcpServers --> job["job_search_mcp\nAdzuna search, categories, skill filter"]
    mcpServers --> calendar["calendar_mcp\nGoogle Calendar event creation"]
```

## 3. Backend Startup And Request Routing

```mermaid
flowchart TB
    start["npm run dev\nnodemon src/index.js"]
    dotenv["Load backend/.env"]
    appImport["Import Express app from src/app.js"]
    db["connectDB()"]
    indexRepair["Startup CalendarEvent maintenance\nread indexes, drop stale index,\nde-duplicate null emailId rows,\nsync schema indexes"]
    listen["app.listen(PORT or 5000)"]
    emailCron["startEmailSyncJob()"]
    shutdown["SIGINT/SIGTERM\nstop cron jobs and close mongoose"]

    appSetup["app.js setup"]
    cors["CORS\norigin CORS_ORIGIN or localhost:5173\ncredentials enabled"]
    middleware["cookieParser\njson parser\nurlencoded parser\nstatic public + uploads"]
    mount["Mount routers"]
    sseRoute["GET /api/sse\nverifyJWT, register browser SSE client"]
    health["GET /\nhealth text"]
    notFound["404 handler"]
    errorHandler["global error handler"]

    start --> dotenv --> appImport --> appSetup
    appSetup --> cors --> middleware --> mount --> sseRoute --> health --> notFound --> errorHandler
    appImport --> db --> indexRepair --> listen --> emailCron
    listen --> shutdown

    mount --> user["/api/user\nregister, login, me, logout, Gmail status"]
    mount --> auth["/api/auth\nGoogle OAuth"]
    mount --> profile["/api/profile\nprofile, avatar, skills,\nexperience, education"]
    mount --> jobs["/api/jobs\nsearch, categories,\nrecommended, save, rank"]
    mount --> emails["/api/emails\nfetch, sync, draft, send,\nquery, digest, star, delete"]
    mount --> calendar["/api/calendar\nOAuth, status, events, disconnect"]
    mount --> ai["/api/ai\nexecute pipeline, chat proxy"]
    mount --> resume["/api/resume\nupload, get, recalculate,\ndelete, open PDF"]
    mount --> internal["/internal/google\nservice-only backend endpoints"]
    mount --> sync["/sync/google\nGoogle OAuth and sync entry points"]
    mount --> notifications["/api/notifications\npreferences"]
```

## 4. Frontend Navigation And API Flow

```mermaid
flowchart TB
    vite["frontend/src/main.jsx\nmounts React app"]
    app["App.jsx\nReact Router"]
    protected["ProtectedRoute\ncalls getCurrentUser()"]
    api["utils/api.js\nBASE_URL=http://localhost:5000/api\ncredentials: include"]

    app --> auth["/auth\nAuth page\nLogin/Signin components"]
    app --> protected
    protected -->|"unauthorized"| auth
    protected -->|"authorized"| dashboard["/dashboard\nDashboard widgets"]
    protected --> profile["/profile\nProfile CRUD"]
    protected --> emails["/emails\nEmail list/detail/sidebar\nAI reply preview modal"]
    protected --> jobs["/jobs\nJob feed, filters, details, save/rank"]
    protected --> settings["/settings\nnotification and integrations"]
    protected --> askai["/ask-ai\nAsk Seekr chat UI"]
    protected --> resume["/resume\nResume upload, ATS score, metadata"]

    auth --> api
    dashboard --> api
    profile --> api
    emails --> api
    jobs --> api
    settings --> api
    askai -->|"POST /api/ai/chat"| api
    resume --> api

    api --> backend["Express backend :5000"]

    askai --> conv["conversation_id in localStorage\nmessages only in React state"]
    resume --> resumeUi["ResumeUpload + ATSScore + ResumeMetadata"]
    emails --> emailUi["EmailSidebar + EmailList + EmailDetail\nComposeModal + AiReplyPreviewModal"]
    jobs --> jobUi["JobFilters + JobFeed + JobDetails + JobCard"]
```

## 5. Authentication And Authorization Flow

```mermaid
sequenceDiagram
    participant Browser
    participant React as React frontend
    participant Express as Express backend
    participant JWT as verifyJWT middleware
    participant Mongo as MongoDB
    participant Google as Google OAuth
    participant Python as Python orchestrator

    Browser->>React: Open protected route
    React->>Express: GET /api/user/me with cookies
    Express->>JWT: verify accessToken cookie or Bearer token
    JWT->>Mongo: Load user
    Mongo-->>JWT: User document
    JWT-->>Express: req.user
    Express-->>React: success true + user

    Browser->>React: Login/Register or Google login
    React->>Express: POST /api/user/login or /api/auth/google
    Express->>Google: Verify Google id token when using Google
    Express->>Mongo: Create/update user and OAuth token state
    Express-->>Browser: Set httpOnly accessToken cookie

    React->>Express: Protected API request
    Express->>JWT: Validate cookie
    Express->>Python: Pipeline request with X-Service-Key + Authorization Bearer JWT
    Python->>Python: Validate X-Service-Key in middleware
    Python->>Python: Save JWT in request.state.jwt
```

## 6. AI Pipeline Gateway Flow

```mermaid
flowchart TB
    browser["Browser action"]
    expressRoute["Express route/controller"]
    verify["verifyJWT\nreq.user + cookie token"]
    aiService["backend/src/services/ai.service.js\nexecutePipeline()"]
    mcpService["backend/src/services/mcp.service.js\ncallMCP()"]
    serviceHeaders["Headers\nX-Service-Key\nX-Request-Source=user|cron\nAuthorization: Bearer JWT"]
    fastapi["client/orchestrator/client.py\nFastAPI middleware"]
    decision{"endpoint or tool?"}
    pipeline["Pipeline endpoint\n/pipelines/*"]
    agentExec["/agent/execute\nfind MCP tool by name"]
    mcpClient["get_mcp_client()\nMultiServerMCPClient"]
    tool["MCP tool invocation"]
    result["JSON result"]

    browser --> expressRoute --> verify --> aiService --> mcpService --> serviceHeaders --> fastapi
    fastapi --> decision
    decision -->|"endpoint provided"| pipeline
    decision -->|"tool provided"| agentExec --> mcpClient --> tool
    pipeline --> result
    tool --> result
    result --> fastapi --> mcpService --> expressRoute --> browser
```

## 7. Ask Seekr Chat Flow

```mermaid
sequenceDiagram
    participant UI as AskAI.jsx
    participant Express as /api/ai/chat
    participant Chat as Python /ask-seekr
    participant Memory as conversation memory
    participant Profile as profile_fetcher/backend API
    participant Planner as planner_decide
    participant Validator as validate_plan
    participant Executor as run_pipeline
    participant LLM as OpenAI/Groq
    participant Pipelines as Python pipeline endpoints

    UI->>UI: Create or reuse conversation_id
    UI->>Express: POST /api/ai/chat with text and cookie
    Express->>Express: verifyJWT
    Express->>Chat: POST /ask-seekr with Bearer JWT
    Chat->>Memory: Load user-scoped conversation context
    Chat->>Profile: Fetch user profile
    Chat->>Planner: Decide CHAT or actionable pipeline

    alt CHAT plan
        Planner-->>Chat: type=CHAT
        Chat->>LLM: Generate personalized conversational response
        Chat->>Memory: Save user turn and assistant reply
        Chat-->>Express: response text
    else Pipeline plan
        Planner-->>Chat: pipeline + endpoint + args
        Chat->>Validator: Validate required fields and confirmation needs
        alt blocked or needs confirmation
            Validator-->>Chat: User-facing clarification
            Chat->>Memory: Save neutral turn
            Chat-->>Express: clarification
        else executable
            Chat->>Executor: Run pipeline
            Executor->>Pipelines: Call selected backend/Python pipeline
            Pipelines-->>Executor: Raw result
            Executor-->>Chat: Raw result
            Chat->>LLM: Summarize using only result data
            Chat->>Memory: Save neutral action note, not raw private data
            Chat-->>Express: human-readable response
        end
    end

    Express-->>UI: JSON response
    UI->>UI: Render markdown assistant message
```

## 8. Resume Upload, Parse, Score, Store Flow

```mermaid
sequenceDiagram
    participant UI as Resume.jsx
    participant API as frontend/utils/api.js
    participant Express as /api/resume
    participant Multer as multer memory upload
    participant Controller as resume.controller.js
    participant Service as resume.services.js
    participant Python as /pipelines/resume-parse
    participant Wrapper as resume_wrapper.py
    participant MCP as resume_mcp :8001
    participant Parser as pdf_loader/extract_pipeline
    participant Scorer as ScorePipeline/ats_scorer/llm_scorer
    participant Cloud as Cloudinary
    participant Mongo as Resume model

    UI->>API: uploadResume(file)
    API->>Express: POST /api/resume multipart form-data
    Express->>Express: verifyJWT
    Express->>Multer: Validate PDF and keep buffer in memory
    Multer->>Controller: req.file
    Controller->>Controller: Convert buffer to base64
    Controller->>Service: parseResumePdf(userId, jwt, file_b64)
    Service->>Python: POST /pipelines/resume-parse
    Python->>Python: Validate userId, JWT, file type
    Python->>Wrapper: parse_resume_pdf(file_b64)
    Wrapper->>MCP: parse_resume tool
    MCP->>Parser: Base64 decode, PDF header check, text extraction, section/entity extraction
    Parser-->>MCP: parsed_resume
    MCP-->>Wrapper: status ok + result
    Python->>Wrapper: score_resume_ats(parsed_resume)
    Wrapper->>MCP: ats_score tool
    MCP->>Scorer: Profile-aware ATS scoring and optional Groq feedback
    Scorer-->>MCP: score_result
    MCP-->>Python: score result
    Python-->>Service: success, parsed_resume, score
    Service-->>Controller: parsed and scored result
    Controller->>Cloud: Upload original PDF
    Cloud-->>Controller: cloudinaryUrl + public_id
    Controller->>Mongo: findOneAndUpdate upsert Resume document
    Mongo-->>Controller: resumeDoc
    Controller-->>API: ApiResponse with metadata, parsed_resume, score, openUrl
    API-->>UI: Render ATSScore and ResumeMetadata
```

## 9. Resume Recalculation Flow

```mermaid
flowchart TB
    openPage["Resume page opens"]
    fetchResume["GET /api/resume"]
    readStored["Read stored parsed_resume and score from MongoDB"]
    stale{"score.ats.meta.scorer != ats_v4?"}
    render["Render cached score and metadata"]
    recalc["POST /api/resume/recalculate"]
    py["Python /pipelines/resume-recalculate"]
    score["score_resume_ats(parsed_resume)\nno PDF parse, no Cloudinary upload"]
    update["Update only Resume.score in MongoDB"]
    renderNew["Render refreshed score"]

    openPage --> fetchResume --> readStored --> stale
    stale -->|"no"| render
    stale -->|"yes and parsed entities exist"| recalc --> py --> score --> update --> renderNew
```

## 10. Job Search And Recommendation Flow

```mermaid
flowchart TB
    jobsPage["Jobs page"]
    searchApi["GET /api/jobs/search"]
    recommendedApi["GET /api/jobs/recommended"]
    rankApi["POST /api/jobs/rank"]
    jobsController["backend/src/controllers/jobs.controller.js"]
    callMcp["callMCP()\nPython pipeline proxy"]

    searchPipeline["/pipelines/job-search"]
    recPipeline["/pipelines/job-recommendations"]
    rankPipeline["/pipelines/rank-jobs"]

    jobAgent["client/orchestrator/job_agent.py"]
    profile["get_user_profile(jwt)\nextract_user_context()"]
    queries["generate_search_queries(user_context)\nLLM generated targeted searches"]
    jobWrapper["client/wrappers/job_wrapper.py"]
    jobMcp["job_search_mcp search_jobs"]
    adzuna["Adzuna API"]
    rules["filter_jobs_by_rules()\ncalculate_relevance_score()"]
    llmRank["rank_and_score_jobs()\nLLM semantic ranking"]
    result["jobs, scores, counts, query metadata"]
    savedJobs["Save/unsave jobs\nMongoDB user/job data"]

    jobsPage --> searchApi --> jobsController --> callMcp --> searchPipeline --> jobAgent
    jobsPage --> recommendedApi --> jobsController --> callMcp --> recPipeline --> jobAgent
    jobsPage --> rankApi --> jobsController --> callMcp --> rankPipeline --> jobAgent

    jobAgent --> profile
    recPipeline --> queries
    jobAgent --> jobWrapper --> jobMcp --> adzuna
    jobAgent --> rules
    recPipeline --> llmRank
    rankPipeline --> rules
    searchPipeline --> result
    recPipeline --> result
    rankPipeline --> result
    result --> jobsPage
    jobsPage --> savedJobs
```

## 11. Gmail Email Sync, Draft, And Send Flow

```mermaid
flowchart TB
    emailsPage["Emails page"]
    syncButton["Manual sync\nPOST /api/emails/email-sync"]
    cron["Backend email sync cron"]
    emailController["email.controller.js"]
    callMcp["callMCP()\nX-Service-Key + source user/cron"]
    pySync["/pipelines/email-sync or /pipelines/ingest-emails"]
    emailAgent["client/orchestrator/email_agent.py"]
    gmailTool["Gmail MCP get_recent_job_emails"]
    gmailApi["Google Gmail API"]
    filter["job_email_filter.is_job_related"]
    dedupe["get_existing_email_ids()\nskip already stored emails"]
    map["email_mapper.map_to_backend()"]
    save["save_email()\nbackend_client/email_api.py"]
    mongo["MongoDB Email model"]
    sse["sseService notifies browser of new synced emails"]

    emailsPage --> syncButton --> emailController --> callMcp --> pySync --> emailAgent
    cron --> emailController
    emailAgent --> gmailTool --> gmailApi
    gmailTool --> filter --> emailAgent
    emailAgent --> dedupe --> map --> save --> mongo
    mongo --> sse --> emailsPage

    emailsPage --> preview["AI reply preview\nPOST /api/emails/email-reply-preview"]
    preview --> pyPreview["/pipelines/email-reply-preview"]
    pyPreview --> draftTool["Gmail MCP draft_reply"]
    draftTool --> gmailApi
    pyPreview --> prompt["build_email_prompt()"]
    prompt --> llm["generate_email_reply()\nLLM"]
    llm --> draft["Draft returned to UI for user approval"]

    emailsPage --> send["Send approved draft\nPOST /api/emails/email-reply-send"]
    send --> pySend["/pipelines/email-reply-send"]
    pySend --> sendTool["Gmail MCP send_email"]
    sendTool --> gmailApi
```

## 12. Calendar Flow

```mermaid
flowchart TB
    calendarUi["Dashboard calendar widgets / calendar APIs"]
    expressCalendar["/api/calendar routes"]
    calendarServices["backend calendar services\ncalendar.service.js\ngoogleCalendar.service.js"]
    oauth["Google Calendar OAuth/status/disconnect"]
    mongo["CalendarEvent model"]
    googleCalendar["Google Calendar API"]
    pyCreate["/pipelines/calendar-create-event"]
    pyExtract["/pipelines/extract-calendar-from-email"]
    calendarAgent["client/orchestrator/calendar_agent.py"]
    extractor["calendar_email_extractor.py\nLLM extracts event fields from email text"]
    calendarMcp["calendar_mcp schedule_event\npresent but disabled in client/mcp/server.py"]

    calendarUi --> expressCalendar
    expressCalendar --> calendarServices
    calendarServices --> oauth
    calendarServices --> mongo
    calendarServices --> googleCalendar

    calendarUi -->|"AI/extraction workflows"| pyExtract --> extractor
    calendarUi -->|"event creation pipeline"| pyCreate --> calendarAgent
    calendarAgent -. optional MCP route .-> calendarMcp -.-> googleCalendar
```

## 13. Data Persistence Flow

```mermaid
flowchart LR
    frontend["React frontend"]
    backend["Express backend"]
    python["Python orchestrator"]

    userModel["User\nidentity, profile reference,\nGmail/Calendar status"]
    profileData["Profile data\nskills, education, experience,\npreferences"]
    oauthModel["OAuthToken\nGoogle access/refresh tokens"]
    emailModel["Email\njob-related messages,\ntype, folder, star, sender"]
    resumeModel["Resume\nCloudinary URL, parsed_resume,\nATS score"]
    calendarModel["CalendarEvent\nlocal event cache and Google IDs"]
    redis["Redis/conversation memory\nAsk Seekr context"]
    cloud["Cloudinary\nPDFs and avatars"]

    frontend --> backend
    python -->|"backend_client APIs"| backend
    backend --> userModel
    backend --> profileData
    backend --> oauthModel
    backend --> emailModel
    backend --> resumeModel
    backend --> calendarModel
    backend --> cloud
    python --> redis
```

## 14. Active MCP Server Topology

```mermaid
flowchart TB
    config["client/mcp/server.py\nSERVERS config"]
    multi["MultiServerMCPClient"]

    config --> multi

    multi --> gmail["gmail\nstdio\npython main.py\ncwd mcp_servers/gmail_mcp"]
    multi --> resume["resume\nstreamable_http\nhttp://127.0.0.1:8001/mcp"]
    multi --> job["job_search\nstdio\npython main.py\ncwd mcp_servers/job_search_mcp"]
    multi -. commented out .-> calendar["calendar\nstdio\nmcp_servers/calendar_mcp"]

    gmail --> gmailTools["Tools\nget_recent_job_emails\nget_email_by_id\ndraft_reply\nsend_email\nping"]
    resume --> resumeTools["Tools\nparse_resume\nats_score\nping"]
    job --> jobTools["Tools\nsearch_jobs\nget_job_categories\nfilter_jobs_by_skills\nping"]
    calendar --> calendarTools["Tool\nschedule_event"]
```

## 15. Main User Journeys

```mermaid
flowchart TB
    start["User logs in"]
    protected["Protected dashboard"]

    start --> protected

    protected --> resumeJourney["Resume journey"]
    resumeJourney --> upload["Upload PDF"]
    upload --> parse["Parse via Resume MCP"]
    parse --> score["ATS score + LLM feedback"]
    score --> storeResume["Store metadata in MongoDB\nfile in Cloudinary"]

    protected --> jobsJourney["Jobs journey"]
    jobsJourney --> search["Search jobs or request recommendations"]
    search --> adzuna["Fetch Adzuna jobs via Job MCP"]
    adzuna --> rank["Rule and LLM ranking"]
    rank --> saveJob["Save selected jobs"]

    protected --> emailJourney["Email journey"]
    emailJourney --> connectGmail["Connect Gmail OAuth"]
    connectGmail --> sync["Sync job-related emails"]
    sync --> classify["Filter/map/store emails"]
    classify --> reply["Generate AI reply preview"]
    reply --> approve["User approves send"]

    protected --> calendarJourney["Calendar journey"]
    calendarJourney --> connectCal["Connect Calendar OAuth"]
    connectCal --> listEvents["List/cache events"]
    listEvents --> extractEvent["Extract interview event from email"]
    extractEvent --> createEvent["Create event"]

    protected --> chatJourney["Ask Seekr journey"]
    chatJourney --> plan["Planner decides chat vs action"]
    plan --> action["Run pipeline if needed"]
    action --> summarize["Summarize result safely"]
    summarize --> memory["Save neutral memory note"]
```

## 16. Important Implementation Notes

- The frontend talks to the backend at `http://localhost:5000/api` with `credentials: "include"`, so auth is cookie-centered in the browser.
- Express validates user requests with `verifyJWT`, then forwards JWTs to Python as Bearer tokens for user-scoped pipelines.
- Python pipeline endpoints require `X-Service-Key`; cron calls also use `X-Request-Source: cron` and `X-User-Id`.
- `client/mcp/server.py` currently enables Gmail, resume, and job search MCP servers. Calendar MCP exists but is commented out there.
- Resume MCP runs as a separate HTTP MCP server on `127.0.0.1:8001/mcp`; Gmail and job search run as stdio subprocess MCP servers.
- Ask Seekr stores conversation context by user/conversation, but after tool execution it stores only a neutral action note, not raw private email/job data.
- `docs/architecture.md`, `docs/agent_flow.md`, and `docs/mcp_contracts.md` are currently empty in this checkout, so this file is the detailed architecture reference generated from source.
