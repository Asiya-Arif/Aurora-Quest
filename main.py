from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from database import init_db
from routes import auth, chat, upload, quiz, language, progress
from config import settings

# Create upload directory
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)

# Initialize database
init_db()

app = FastAPI(
    title="Aurora Quest API",
    description="AI-powered study companion with RAG and gamification",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(quiz.router, prefix="/api", tags=["Quiz"])
app.include_router(language.router, prefix="/api/language", tags=["Language"])
app.include_router(progress.router, prefix="/api", tags=["Progress"])
# Note: Agora AI routes are handled via existing `chat` and `language` routers

# Mount static files
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.get("/")
async def serve_frontend():
    index_path = os.path.join(os.path.dirname(__file__), "index_quest.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type='text/html')
    return {"message": "Aurora Quest API", "version": "1.0.0", "docs": "/docs"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
