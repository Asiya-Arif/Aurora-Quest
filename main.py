from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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

genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))

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

notes_storage: Dict[str, str] = {}
quiz_history: List[dict] = []
user_stats: Dict[str, int] = {"total_xp": 0, "quizzes_taken": 0, "accuracy": 0}

_groq_client = None

def get_groq_client():
    global _groq_client
    if _groq_client is None:
        try:
            from groq import Groq
            _groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        except Exception as e:
            print(f"Groq init failed: {e}")
    return _groq_client

def extract_pdf_text(pdf_bytes: bytes) -> str:
    try:
        pdf_file = io.BytesIO(pdf_bytes)
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PDF extraction failed: {str(e)}")

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

@app.get("/")
async def root():
    return {"message": "Aurora Quest API - Running! 🌈✨", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "notes": len(notes_storage)}

@app.post("/upload-notes")
async def upload_notes(file: UploadFile = File(...)):
    try:
        content = await file.read()
        if file.filename.endswith('.pdf'):
            text = extract_pdf_text(content)
        else:
            text = content.decode('utf-8')
        notes_storage[file.filename] = text
        return {"message": "Success", "filename": file.filename, "characters": len(text)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-quiz")
async def generate_quiz(request: QuizRequest):
    try:
        context = get_relevant_context(request.subject)
        if context == "No notes found for this subject.":
            return {"error": "Please upload notes first"}

        prompt = f"""Generate {request.num_questions} quiz questions from: {context[:3000]}

Format:
Q1: [question]
A) [option A]
B) [option B]
C) [option C]
D) [option D]
Correct: [A/B/C/D]
Explanation: [why]
XP: [10-50]"""

        response = genai.GenerativeModel('gemini-1.5-flash').generate_content(prompt)
        return {"quiz": response.text, "subject": request.subject}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat_with_notes(request: ChatRequest):
    try:
        context = get_relevant_context(request.subject, request.user_question)
        groq = get_groq_client()

        if not groq:
            prompt = f"Context: {context[:2000]}\n\nQ: {request.user_question}"
            response = genai.GenerativeModel('gemini-1.5-flash').generate_content(prompt)
            return {"response": response.text, "provider": "gemini"}

        chat = groq.chat.completions.create(
            messages=[
                {"role": "system", "content": f"Context: {context[:2000]}"},
                {"role": "user", "content": request.user_question}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=500
        )
        return {"response": chat.choices[0].message.content, "provider": "groq"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/language-tutor")
async def language_tutor(request: LanguageRequest):
    try:
        groq = get_groq_client()
        if not groq:
            prompt = f"You are a {request.language} tutor. Student: {request.user_input}"
            response = genai.GenerativeModel('gemini-1.5-flash').generate_content(prompt)
            return {"tutor_response": response.text, "provider": "gemini"}

        chat = groq.chat.completions.create(
            messages=[
                {"role": "system", "content": f"You are a {request.language} tutor at {request.level} level."},
                {"role": "user", "content": request.user_input}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.8,
            max_tokens=300
        )
        return {"tutor_response": chat.choices[0].message.content, "provider": "groq"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-flashcards")
async def generate_flashcards(subject: str, num_cards: int = 10):
    try:
        context = get_relevant_context(subject)
        if context == "No notes found for this subject.":
            return {"error": "Please upload notes first"}

        prompt = f"Create {num_cards} flashcards from: {context[:3000]}"
        response = genai.GenerativeModel('gemini-1.5-flash').generate_content(prompt)
        return {"flashcards": response.text, "subject": subject}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/performance-dashboard")
async def get_performance():
    return {
        "total_xp": user_stats.get("total_xp", 0),
        "quizzes_taken": user_stats.get("quizzes_taken", 0),
        "accuracy": user_stats.get("accuracy", 0),
        "total_notes": len(notes_storage)
    }

@app.get("/history")
async def get_history():
    return {"quiz_history": quiz_history[-20:], "total": len(quiz_history)}

@app.post("/submit-quiz")
async def submit_quiz(score: int, total: int, subject: str):
    try:
        accuracy = int((score / total) * 100) if total > 0 else 0
        xp_earned = score * 10
        quiz_history.append({"subject": subject, "score": score, "total": total, "xp": xp_earned})
        user_stats["total_xp"] += xp_earned
        user_stats["quizzes_taken"] += 1
        if quiz_history:
            user_stats["accuracy"] = int(sum([q.get("accuracy", 0) for q in quiz_history]) / len(quiz_history))
        return {"message": "Submitted!", "xp_earned": xp_earned, "total_xp": user_stats["total_xp"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

handler = app
