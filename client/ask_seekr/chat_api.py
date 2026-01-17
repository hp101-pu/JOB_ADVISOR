from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from client.ask_seekr.entrypoint import handle_user_message




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


@app.post("/ask-seekr")
async def ask_seekr(request: Request, body: ChatRequest):
    """
    Entry point for Ask Seekr chatbot.
    """

    if not request.state.jwt:
        raise HTTPException(status_code=401, detail="Missing JWT")

    print("🟢 /ask-seekr called")
    print("JWT (first 20 chars):", request.state.jwt[:20])

    response = await handle_user_message(
        jwt=request.state.jwt,
        user_message=body.text,
        conversation_id=body.conversation_id,
        metadata=body.metadata,
    )

    return response


@app.get("/health")
async def health():
    return {"status": "ok"}
