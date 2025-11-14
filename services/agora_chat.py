from fastapi import APIRouter, HTTPException, Request
import os
import httpx
from pydantic import BaseModel

router = APIRouter()

AGORA_CHAT_URL = os.getenv("AGORA_CHAT_URL", "https://api.agora.ai/v1/chat")  # set correct base URL for your use
AGORA_API_KEY = os.getenv("AGORA_API_KEY", "")

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None

@router.post("/agora/chat")
async def agora_chat(req: ChatRequest):
    if not AGORA_API_KEY:
        raise HTTPException(status_code=500, detail="AGORA_API_KEY not configured on server")
    payload = {
        "input": req.message,
        "session": req.session_id or "anonymous",
        # Add other parameters per the Agora Chat API spec (model, temperature, etc.)
    }
    headers = {"Authorization": f"Bearer {AGORA_API_KEY}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            r = await client.post(AGORA_CHAT_URL, json=payload, headers=headers)
        except Exception as e:
            raise HTTPException(status_code=502, detail=str(e))
    if r.status_code != 200:
        # propagate message for debugging (don't leak secrets)
        raise HTTPException(status_code=502, detail=f"Agora API returned {r.status_code}: {r.text}")
    data = r.json()
    # Map Agora response to { reply: "..." } — adapt to Agora's response shape
    reply_text = data.get("reply") or data.get("output") or data.get("message") or str(data)
    return {"reply": reply_text}