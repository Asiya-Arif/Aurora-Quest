from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import google.generativeai as genai
import PyPDF2
import io
import os
from typing import Dict, List
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ONLY use Gemini - no Groq to avoid errors
genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))
model = genai.GenerativeModel('gemini-1.5-flash')

# Pydantic models
class ChatRequest(BaseModel):
    user_question: str
    subject: str

class QuizRequest(BaseModel):
    subject: str
    num_questions: int = 5

class LanguageRequest(BaseModel):
    language: str
    level: str
    user_input: str

# Storage
notes_storage: Dict[str, str] = {}
quiz_history: List[dict] = []
user_stats = {"total_xp": 0, "quizzes_taken": 0, "accuracy": 0}

def extract_pdf_text(pdf_bytes: bytes) -> str:
    pdf_file = io.BytesIO(pdf_bytes)
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def get_context(subject: str, query: str = "") -> str:
    parts = []
    for filename, content in notes_storage.items():
        if subject.lower() in filename.lower() or subject.lower() in content.lower():
            parts.append(content)
    return "\n\n".join(parts[:3]) if parts else "No notes found"

@app.get("/favicon.ico")
async def favicon():
    """Handle favicon requests to prevent 404 errors."""
    return Response(content=b"", media_type="image/x-icon")

@app.get("/api/")
async def root():
    return {"message": "Aurora Quest API ✨", "status": "healthy", "version": "2.0"}

@app.get("/api/health")
async def health():
    return {"status": "ok", "notes": len(notes_storage)}

@app.post("/api/upload-notes")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    text = extract_pdf_text(content) if file.filename.endswith('.pdf') else content.decode('utf-8')
    notes_storage[file.filename] = text
    return {"message": "Uploaded", "filename": file.filename, "chars": len(text)}

@app.post("/api/generate-quiz")
async def quiz(request: QuizRequest):
    context = get_context(request.subject)
    if context == "No notes found":
        return {"error": "Upload notes first"}

    prompt = f"Create {request.num_questions} quiz questions from: {context[:2000]}"
    response = model.generate_content(prompt)
    return {"quiz": response.text, "subject": request.subject}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    context = get_context(request.subject, request.user_question)
    prompt = f"Context: {context[:2000]}\n\nQuestion: {request.user_question}\n\nAnswer:"
    response = model.generate_content(prompt)
    return {"response": response.text, "subject": request.subject}

@app.post("/api/language-tutor")
async def tutor(request: LanguageRequest):
    prompt = f"You are a {request.language} tutor. Student said: {request.user_input}. Give feedback."
    response = model.generate_content(prompt)
    return {"tutor_response": response.text, "language": request.language}

@app.post("/api/generate-flashcards")
async def flashcards(subject: str, num_cards: int = 10):
    context = get_context(subject)
    if context == "No notes found":
        return {"error": "Upload notes first"}

    prompt = f"Create {num_cards} flashcards from: {context[:2000]}"
    response = model.generate_content(prompt)
    return {"flashcards": response.text, "subject": subject}

@app.get("/api/performance-dashboard")
async def dashboard():
    return {
        "total_xp": user_stats["total_xp"],
        "quizzes_taken": user_stats["quizzes_taken"],
        "accuracy": user_stats["accuracy"],
        "total_notes": len(notes_storage)
    }

@app.get("/api/history")
async def history():
    return {"quiz_history": quiz_history[-20:]}

@app.post("/api/submit-quiz")
async def submit(score: int, total: int, subject: str):
    xp = score * 10
    quiz_history.append({"subject": subject, "score": score, "total": total, "xp": xp})
    user_stats["total_xp"] += xp
    user_stats["quizzes_taken"] += 1
    return {"message": "Submitted", "xp_earned": xp, "total_xp": user_stats["total_xp"]}

handler = app
