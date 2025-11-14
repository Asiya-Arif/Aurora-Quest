from fastapi import APIRouter, HTTPException
import os
import httpx
from pydantic import BaseModel

router = APIRouter()

AGORA_LANGUAGE_URL = os.getenv("AGORA_LANGUAGE_URL", "https://api.agora.ai/v1/language")
AGORA_API_KEY = os.getenv("AGORA_API_KEY", "")

class TutorRequest(BaseModel):
    input: str
    target_language: str = "en"
    session_id: str | None = None

@router.post("/agora/language/tutor")
async def agora_language_tutor(req: TutorRequest):
    if not AGORA_API_KEY:
        raise HTTPException(status_code=500, detail="AGORA_API_KEY not configured on server")
    payload = {
        "input": req.input,
        "target_language": req.target_language,
        "session": req.session_id or "anonymous"
        # Add additional parameters or model selection as required
    }
    headers = {"Authorization": f"Bearer {AGORA_API_KEY}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            r = await client.post(AGORA_LANGUAGE_URL, json=payload, headers=headers)
        except Exception as e:
            raise HTTPException(status_code=502, detail=str(e))
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Agora Language API returned {r.status_code}: {r.text}")
    data = r.json()
    # Map response to a simple { reply: "..." } format
    reply_text = data.get("reply") or data.get("output") or str(data)
    return {"reply": reply_text}