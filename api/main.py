from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, HTMLResponse
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

# Gemini model initialization (lazy loading)
model = None
genai = None

def get_gemini_model():
    """Get or initialize Gemini model safely."""
    global model, genai

    if model is not None:
        return model

    if genai is None:
        try:
            import google.generativeai as genai_module
            genai = genai_module
        except ImportError:
            return None

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
    if GEMINI_API_KEY and GEMINI_API_KEY != "your_new_gemini_key_here":
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-1.5-flash')
            return model
        except Exception as e:
            print(f"Error configuring Gemini: {e}")
    return None

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

# Simple HTML template (kept minimal to avoid deployment issues)
HTML_CONTENT = """<!DOCTYPE html>
<html><head><title>Aurora Quest ✨</title>
<style>body{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;text-align:center;padding:40px;font-family:sans-serif;}
h1{font-size:48px;margin-bottom:20px;}p{font-size:20px;margin-bottom:30px;}.btn{background:white;color:#667eea;padding:15px 30px;border-radius:25px;text-decoration:none;font-weight:600;display:inline-block;}
footer{margin-top:80px;padding:20px;border-top:1px solid rgba(255,255,255,0.2);}#status{margin-top:30px;}
</style></head><body><h1>Aurora Quest ✨</h1><p>Your AI-powered learning companion is deployed successfully!</p>
<p>API Status: <span id="api-status">Checking...</span></p><a href="#api-test" class="btn" onclick="checkAPI()">Test API</a>
<footer><p>Built with FastAPI and Vercel</p></footer>
<script>async function checkAPI(){try{const r=await fetch('/api/health');const d=await r.json();document.getElementById('api-status').textContent=d.message}catch(e){document.getElementById('api-status').textContent='Error: '+e.message}}</script></body></html>"""

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
    current_model = get_gemini_model()
    if current_model is None:
        return {"error": "AI model not configured"}
    context = get_context(request.subject)
    if context == "No notes found":
        return {"error": "Upload notes first"}

    prompt = f"Create {request.num_questions} quiz questions from: {context[:2000]}"
    response = current_model.generate_content(prompt)
    return {"quiz": response.text, "subject": request.subject}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    current_model = get_gemini_model()
    if current_model is None:
        return {"error": "AI model not configured"}
    context = get_context(request.subject, request.user_question)
    prompt = f"Context: {context[:2000]}\n\nQuestion: {request.user_question}\n\nAnswer:"
    response = current_model.generate_content(prompt)
    return {"response": response.text, "subject": request.subject}

@app.post("/api/language-tutor")
async def tutor(request: LanguageRequest):
    current_model = get_gemini_model()
    if current_model is None:
        return {"error": "AI model not configured"}
    prompt = f"You are a {request.language} tutor. Student said: {request.user_input}. Give feedback."
    response = current_model.generate_content(prompt)
    return {"tutor_response": response.text, "language": request.language}

@app.post("/api/generate-flashcards")
async def flashcards(subject: str, num_cards: int = 10):
    current_model = get_gemini_model()
    if current_model is None:
        return {"error": "AI model not configured"}
    context = get_context(subject)
    if context == "No notes found":
        return {"error": "Upload notes first"}

    prompt = f"Create {num_cards} flashcards from: {context[:2000]}"
    response = current_model.generate_content(prompt)
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

# Catch-all route for serving static content (HTML, favicon, etc.)
@app.get("/{path:path}")
async def catch_all(path: str):
    """Serve static content like favicon.ico and index.html directly from FastAPI."""
    if path == "favicon.ico":
        return Response(content=b"", media_type="image/x-icon")
    elif path == "index.html" or path == "":
        # Serve the HTML page directly (no filesystem access needed)
        return HTMLResponse(content=HTML_CONTENT, status_code=200)
    # For any other path, return a 404
    raise HTTPException(status_code=404, detail="Page not found")

handler = app
