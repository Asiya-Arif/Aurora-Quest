from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import PyPDF2
import io
import os
from typing import Dict, List
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

# ==================== PYDANTIC MODELS ====================
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

# ==================== GLOBAL STORAGE ====================
notes_storage: Dict[str, str] = {}
quiz_history: List[dict] = []
user_stats: Dict[str, int] = {"total_xp": 0, "quizzes_taken": 0, "accuracy": 0}

# ==================== GROQ CLIENT (LAZY LOADING) ====================
_groq_client = None

def get_groq_client():
    global _groq_client
    if _groq_client is None:
        try:
            from groq import Groq
            _groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        except Exception as e:
            print(f"Warning: Groq client initialization failed: {e}")
    return _groq_client

# ==================== HELPER FUNCTIONS ====================
def extract_pdf_text(pdf_bytes: bytes) -> str:
    try:
        pdf_file = io.BytesIO(pdf_bytes)
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to extract PDF: {str(e)}")

def get_relevant_context(subject: str, query: str = "") -> str:
    context_parts = []
    for filename, content in notes_storage.items():
        if subject.lower() in filename.lower() or subject.lower() in content.lower():
            if query:
                paragraphs = content.split('\n\n')
                query_words = set(query.lower().split())
                for para in paragraphs:
                    para_words = set(para.lower().split())
                    if len(query_words & para_words) >= 2:
                        context_parts.append(para)
            else:
                context_parts.append(content)

    return "\n\n".join(context_parts[:5]) if context_parts else "No notes found for this subject."

# ==================== API ENDPOINTS ====================

@app.get("/")
async def root():
    return {
        "message": "Aurora Quest API is running! 🌈✨",
        "status": "healthy",
        "version": "1.0"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "api": "Aurora Quest",
        "notes_count": len(notes_storage),
        "quiz_history_count": len(quiz_history)
    }

@app.post("/upload-notes")
async def upload_notes(file: UploadFile = File(...)):
    try:
        content = await file.read()

        # Extract text based on file type
        if file.filename.endswith('.pdf'):
            text = extract_pdf_text(content)
        else:
            text = content.decode('utf-8')

        # Store in memory
        notes_storage[file.filename] = text

        return {
            "message": "Notes uploaded successfully",
            "filename": file.filename,
            "characters": len(text),
            "total_notes": len(notes_storage)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-quiz")
async def generate_quiz(request: QuizRequest):
    try:
        context = get_relevant_context(request.subject)

        if context == "No notes found for this subject.":
            return {"error": "Please upload notes for this subject first"}

        # Generate quiz using Gemini
        prompt = f"""Generate {request.num_questions} multiple choice quiz questions from these notes:

{context[:3000]}

Format each question EXACTLY like this:
Q1: [question text]
A) [option A]
B) [option B]
C) [option C]
D) [option D]
Correct: [A/B/C/D]
Explanation: [why this is correct]
XP: [10-50 based on difficulty]

Make questions challenging but fair."""

        response = genai.GenerativeModel('gemini-1.5-flash').generate_content(prompt)

        return {
            "quiz": response.text,
            "subject": request.subject,
            "num_questions": request.num_questions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quiz generation failed: {str(e)}")

@app.post("/chat")
async def chat_with_notes(request: ChatRequest):
    try:
        context = get_relevant_context(request.subject, request.user_question)

        groq = get_groq_client()
        if not groq:
            # Fallback to Gemini if Groq fails
            prompt = f"""Context from notes: {context[:2000]}

Question: {request.user_question}

Answer the question based on the context above."""
            response = genai.GenerativeModel('gemini-1.5-flash').generate_content(prompt)
            return {
                "response": response.text,
                "subject": request.subject,
                "provider": "gemini"
            }

        chat_completion = groq.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"You are a helpful study assistant. Answer the question using this context: {context[:2000]}"
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
            "subject": request.subject,
            "provider": "groq"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@app.post("/language-tutor")
async def language_tutor(request: LanguageRequest):
    try:
        groq = get_groq_client()
        if not groq:
            # Fallback to Gemini
            prompt = f"""You are a {request.language} tutor teaching at {request.level} level.
Student said: {request.user_input}
Provide feedback and corrections in a friendly way."""
            response = genai.GenerativeModel('gemini-1.5-flash').generate_content(prompt)
            return {
                "tutor_response": response.text,
                "language": request.language,
                "provider": "gemini"
            }

        chat_completion = groq.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"You are a friendly {request.language} tutor teaching at {request.level} level. Provide corrections and encouragement."
                },
                {
                    "role": "user",
                    "content": request.user_input
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.8,
            max_tokens=300
        )

        return {
            "tutor_response": chat_completion.choices[0].message.content,
            "language": request.language,
            "provider": "groq"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Language tutor failed: {str(e)}")

@app.post("/generate-flashcards")
async def generate_flashcards(subject: str, num_cards: int = 10):
    try:
        context = get_relevant_context(subject)

        if context == "No notes found for this subject.":
            return {"error": "Please upload notes for this subject first"}

        prompt = f"""Create {num_cards} flashcards from these notes:

{context[:3000]}

Format each flashcard EXACTLY like this:
Card 1:
Front: [question or concept]
Back: [answer or explanation]
XP: 10

Make them concise and focused on key concepts."""

        response = genai.GenerativeModel('gemini-1.5-flash').generate_content(prompt)

        return {
            "flashcards": response.text,
            "subject": subject,
            "num_cards": num_cards
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Flashcard generation failed: {str(e)}")

@app.get("/performance-dashboard")
async def get_performance():
    return {
        "total_xp": user_stats.get("total_xp", 0),
        "quizzes_taken": user_stats.get("quizzes_taken", 0),
        "accuracy": user_stats.get("accuracy", 0),
        "total_notes": len(notes_storage),
        "subjects": list(set([name.split('_')[0] for name in notes_storage.keys()])) if notes_storage else []
    }

@app.get("/history")
async def get_history():
    return {
        "quiz_history": quiz_history[-20:],
        "total_quizzes": len(quiz_history)
    }

@app.post("/submit-quiz")
async def submit_quiz(score: int, total: int, subject: str):
    try:
        accuracy = int((score / total) * 100) if total > 0 else 0
        xp_earned = score * 10

        quiz_history.append({
            "subject": subject,
            "score": score,
            "total": total,
            "accuracy": accuracy,
            "xp_earned": xp_earned
        })

        user_stats["total_xp"] += xp_earned
        user_stats["quizzes_taken"] += 1
        user_stats["accuracy"] = int(sum([q["accuracy"] for q in quiz_history]) / len(quiz_history)) if quiz_history else 0

        return {
            "message": "Quiz submitted!",
            "xp_earned": xp_earned,
            "total_xp": user_stats["total_xp"],
            "accuracy": accuracy
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quiz submission failed: {str(e)}")

# For Vercel serverless function compatibility
handler = app
