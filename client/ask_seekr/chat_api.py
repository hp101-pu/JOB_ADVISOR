import json

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any

from client.ask_seekr.entrypoint import handle_user_message
from client.ask_seekr.graph import stream_graph
from client.ask_seekr.graph.state import ChatState




app = FastAPI()


@app.middleware("http")
async def jwt_context_middleware(request: Request, call_next):
    auth = request.headers.get("authorization")
    request.state.jwt = None

    if auth and auth.startswith("Bearer "):
        request.state.jwt = auth[7:].strip()

    response = await call_next(request)
    return response



class ChatRequest(BaseModel):
    text: str
    conversation_id: Optional[str] = None
    metadata: Dict[str, Any] = {}
    confirmed: bool = False


@app.post("/ask-seekr")
async def ask_seekr(request: Request, body: ChatRequest):
    """
    Entry point for Ask Seekr chatbot.
    """

    if not request.state.jwt:
        raise HTTPException(status_code=401, detail="Missing JWT")

    print("🟢 /ask-seekr called")
    print("JWT (first 20 chars):", request.state.jwt[:20])
    print(f"🔒 confirmed={body.confirmed}")

    response = await handle_user_message(
        jwt=request.state.jwt,
        user_message=body.text,
        conversation_id=body.conversation_id,
        metadata=body.metadata,
        confirmed=body.confirmed,
    )

    return response


def _extract_user_id(jwt: str) -> str:
    import base64
    try:
        payload_part = jwt.split(".")[1]
        payload_part += "=" * (4 - len(payload_part) % 4)
        decoded = json.loads(base64.b64decode(payload_part).decode("utf-8"))
        return str(decoded.get("_id") or decoded.get("id") or decoded.get("sub") or "")
    except Exception:
        return ""


async def _stream_response(body: ChatRequest, request: Request):
    user_id = _extract_user_id(request.state.jwt)
    conversation_id = body.conversation_id or "default"

    initial_state: ChatState = {
        "user_message": body.text,
        "jwt": request.state.jwt,
        "user_id": user_id,
        "conversation_id": body.conversation_id,
        "confirmed": body.confirmed,
        "metadata": body.metadata or {},
        "conversation_context": [],
        "user_profile": {},
        "intent": "",
        "plan": {},
        "status": "",
        "message": "",
        "pipeline_result": None,
        "response": "",
        "response_metadata": {},
        "stream_tokens": [],
    }

    async for chunk in stream_graph(initial_state, thread_id=conversation_id):
        yield f"data: {json.dumps(chunk)}\n\n"


@app.post("/ask-seekr/stream")
async def ask_seekr_stream(request: Request, body: ChatRequest):
    if not request.state.jwt:
        raise HTTPException(status_code=401, detail="Missing JWT")

    return StreamingResponse(
        _stream_response(body, request),
        media_type="text/event-stream",
    )


@app.get("/health")
async def health():
    return {"status": "ok"}
