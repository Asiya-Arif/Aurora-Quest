from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from groq import Groq
import os

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini (Free)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel('gemini-1.5-flash')

# Configure Groq (Free)
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

@app.post("/upload-notes")
async def upload_notes(file: UploadFile = File(...)):
    # Read PDF/document
    content = await file.read()
    text = extract_text_from_pdf(content)
    
    # Store in ChromaDB for RAG
    store_in_vector_db(text, file.filename)
    
    return {"message": "Notes uploaded successfully"}

@app.post("/generate-quiz")
async def generate_quiz(subject: str, num_questions: int = 5):
    # Retrieve relevant notes from vector DB
    notes = retrieve_from_vector_db(subject)
    
    prompt = f"""Generate {num_questions} quiz questions from these notes:
    {notes}
    
    Format each question as:
    Q: [question]
    A: [correct answer]
    Options: [A, B, C, D]
    Explanation: [detailed explanation]
    XP: [10-50 based on difficulty]
    """
    
    response = gemini_model.generate_content(prompt)
    quiz = parse_quiz_response(response.text)
    
    return {"quiz": quiz}

@app.post("/chat")
async def chat_with_notes(user_question: str, subject: str):
    # RAG: Retrieve relevant context from notes
    context = retrieve_from_vector_db(subject, query=user_question)
    
    # Use Groq for fast responses
    chat_completion = groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": f"You are a helpful tutor. Use this context: {context}"},
            {"role": "user", "content": user_question}
        ],
        model="llama-3.3-70b-versatile"
    )
    
    return {"response": chat_completion.choices[0].message.content}

@app.post("/language-tutor")
async def language_lesson(language: str, level: str, user_input: str):
    # Conversational language tutor using Groq
    chat = groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": f"You are a {language} tutor for {level} level. Provide corrections and encouragement."},
            {"role": "user", "content": user_input}
        ],
        model="llama-3.3-70b-versatile"
    )
    
    return {"tutor_response": chat.choices[0].message.content}

@app.post("/schedule-exam")
async def schedule_exam(subject: str, exam_date: str, notes_file: str):
    # Calculate days until exam
    # Generate daily quiz schedule
    # Store in database
    
    schedule = create_daily_quiz_schedule(subject, exam_date, notes_file)
    return {"schedule": schedule}

@app.get("/performance-dashboard")
async def get_performance(user_id: str):
    # Retrieve user stats from database
    stats = {
        "accuracy": calculate_accuracy(user_id),
        "weak_topics": identify_weak_topics(user_id),
        "strong_topics": identify_strong_topics(user_id),
        "total_xp": get_total_xp(user_id),
        "achievements": get_achievements(user_id)
    }
    return stats

@app.get("/history")
async def get_history(user_id: str):
    # Retrieve all past quizzes and flashcards
    history = fetch_user_history(user_id)
    return {"history": history}
