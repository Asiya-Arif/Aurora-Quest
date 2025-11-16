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

# HTML content for the homepage (served directly to avoid file system issues)
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aurora Quest ✨ - Your AI-Powered Learning Companion</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='0.9em' font-size='90'>✨</text></svg>"</link>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Inter', sans-serif;
        }

        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            overflow-x: hidden;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }

        nav {
            padding: 20px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .logo {
            font-size: 24px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .hero {
            text-align: center;
            padding: 80px 0;
            margin-bottom: 60px;
        }

        .hero h1 {
            font-size: 48px;
            font-weight: 700;
            margin-bottom: 20px;
            line-height: 1.2;
        }

        .hero p {
            font-size: 20px;
            margin-bottom: 40px;
            opacity: 0.9;
        }

        .btn {
            background: white;
            color: #667eea;
            padding: 15px 30px;
            border-radius: 25px;
            text-decoration: none;
            font-weight: 600;
            display: inline-block;
            transition: all 0.3s ease;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        }

        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin-bottom: 80px;
        }

        .feature-card {
            background: rgba(255, 255, 255, 0.1);
            padding: 30px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .feature-card h3 {
            font-size: 24px;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .feature-card p {
            opacity: 0.9;
        }

        .footer {
            text-align: center;
            padding: 40px 0;
            border-top: 1px solid rgba(255, 255, 255, 0.2);
            margin-top: 80px;
        }

        @media (max-width: 768px) {
            .hero h1 {
                font-size: 36px;
            }

            .hero p {
                font-size: 18px;
            }

            .features {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <nav>
        <div class="container">
            <div class="logo">
                ✨ Aurora Quest
            </div>
        </div>
    </nav>

    <main class="container">
        <section class="hero">
            <h1>Welcome to Aurora Quest</h1>
            <p>Your AI-powered learning companion that turns study sessions into adventures</p>
            <a href="#start" class="btn" id="startBtn">Begin Your Journey</a>
        </section>

        <section class="features" id="features">
            <div class="feature-card">
                <h3>📚 Smart Learning</h3>
                <p>AI-generated quizzes and flashcards tailored to your study materials</p>
            </div>
            <div class="feature-card">
                <h3>🎯 Progress Tracking</h3>
                <p>Earn XP, track your achievements, and watch your knowledge grow</p>
            </div>
            <div class="feature-card">
                <h3>🌍 Language Learning</h3>
                <p>Practice languages with AI-powered conversation tutors</p>
            </div>
        </section>

        <section class="hero" id="app">
            <h2>Welcome to Aurora Quest - Deployed Successfully! 🎉</h2>
            <p>The app is now running on Vercel platform.</p>
            <p>API endpoints: /api/upload-notes, /api/chat, /api/generate-quiz, etc.</p>
        </section>
    </main>

    <footer class="footer">
        <div class="container">
            <p>&copy; 2025 Aurora Quest. Built with FastAPI and Vercel.</p>
        </div>
    </footer>

    <script>
        document.getElementById('startBtn').addEventListener('click', function() {
            fetch('/api/health')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('app').innerHTML = '<h2>API Status: ' + data.message + '</h2><p>Server is healthy! 🎯</p>';
                })
                .catch(err => {
                    document.getElementById('app').innerHTML = '<h2>API Error - Check Logs</h2><p>Error: ' + err.message + '</p>';
                });
        });
    </script>
</body>
</html>
"""

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
