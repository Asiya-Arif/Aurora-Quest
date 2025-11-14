from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models.user import User
from models.session import StudySession
from services.agora_ai_service import agora_ai_service
from utils.auth import get_current_user

router = APIRouter()

class LanguageStartRequest(BaseModel):
    language: str
    proficiency_level: str = "beginner"

class LanguageExerciseRequest(BaseModel):
    language: str
    proficiency_level: str = "beginner"
    topic: str = "general_conversation"

@router.post("/start")
async def start_language_session(
    request: LanguageStartRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Create session
        session = StudySession(
            user_id=current_user.id,
            session_type="language",
            language=request.language
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        
        # Get Agora AI Language Session
        ai_session = await agora_ai_service.start_language_session(
            language=request.language,
            user_id=str(current_user.id),
            proficiency_level=request.proficiency_level
        )
        
        if ai_session.get("status") != "success":
            raise HTTPException(status_code=500, detail="Failed to start language session")
        
        return {
            "session_id": session.id,
            "ai_tutor_name": ai_session.get("ai_tutor_name"),
            "language": request.language,
            "proficiency_level": request.proficiency_level,
            "initial_prompt": ai_session.get("initial_prompt"),
            "voice_enabled": ai_session.get("voice_enabled"),
            "real_time_feedback": ai_session.get("real_time_feedback"),
            "status": "ready"
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/exercise")
async def get_language_exercise(
    request: LanguageExerciseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        exercise = await agora_ai_service.generate_language_exercise(
            language=request.language,
            proficiency_level=request.proficiency_level,
            topic=request.topic
        )
        
        if exercise.get("status") != "success":
            raise HTTPException(status_code=500, detail="Failed to generate exercise")
        
        return exercise
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feedback")
async def get_pronunciation_feedback(
    audio_url: str,
    phrase: str,
    language: str,
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        feedback = await agora_ai_service.get_pronunciation_feedback(
            user_audio_url=audio_url,
            phrase=phrase,
            language=language,
            session_id=str(session_id)
        )
        
        if feedback.get("status") != "success":
            raise HTTPException(status_code=500, detail="Failed to get feedback")
        
        return feedback
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

