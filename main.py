from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import google.generativeai as genai
import PyPDF2
import io
import os
from typing import Dict, List, Optional
from pydantic import BaseModel

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))

# Don't initialize Groq at module level - use lazy loading
_groq_client = None

def get_groq_client():
    """Lazy load Groq client only when needed"""
    global _groq_client
    if _groq_client is None:
        try:
            from groq import Groq
            _groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        except Exception as e:
            print(f"Warning: Could not initialize Groq client: {e}")
            _groq_client = None
    return _groq_client

# Rest of your code stays the same...
# In endpoints that use Groq, replace groq_client with get_groq_client()

@app.post("/chat")
async def chat_with_notes(request: ChatRequest):
    try:
        context = get_relevant_context(request.subject, request.user_question)
        
        groq = get_groq_client()
        if not groq:
            raise HTTPException(status_code=500, detail="Groq client not available")
        
        chat_completion = groq.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"Answer based on these notes: {context[:2000]}"
                },
                {
                    "role": "user",
                    "content": request.user_question
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=500
        )
        
        return {
            "response": chat_completion.choices[0].message.content,
            "subject": request.subject
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
