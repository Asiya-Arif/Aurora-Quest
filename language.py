from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from database import get_db
from models.user import User
from models.session import StudySession, ChatMessage
from services.agora_ai_service import agora_ai_service
from services.rag_service import RAGService
from services.gamification_service import GamificationService
from utils.auth import get_current_user
from config import settings

router = APIRouter()
rag_service = RAGService()
gamification_service = GamificationService()

class LanguageStartRequest(BaseModel):
    language: str
    proficiency_level: str = "beginner"

class LanguageExerciseRequest(BaseModel):
    language: str
    proficiency_level: str = "beginner"
    topic: str = "general_conversation"

class LanguageChatRequest(BaseModel):
    message: str
    language: str
    session_id: int

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

@router.post("/chat")
async def language_tutor_chat(
    request: LanguageChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Chat with AI language tutor with RAG support from uploaded materials"""
    try:
        # Verify session
        session = db.query(StudySession).filter(
            StudySession.id == request.session_id,
            StudySession.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get conversation history for context
        recent_messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == request.session_id
        ).order_by(ChatMessage.created_at.desc()).limit(6).all()
        
        conversation_history = []
        for msg in reversed(recent_messages):
            role = "user" if msg.message_type == "user" else "assistant"
            conversation_history.append({
                "role": role,
                "content": msg.content
            })
        
        # Get AI tutor response with RAG
        response = await rag_service.get_language_tutor_response(
            query=request.message,
            language=request.language,
            session_id=request.session_id,
            conversation_history=conversation_history
        )
        
        # Save messages
        user_msg = ChatMessage(
            session_id=request.session_id,
            message_type="user",
            content=request.message
        )
        ai_msg = ChatMessage(
            session_id=request.session_id,
            message_type="ai",
            content=response
        )
        
        db.add(user_msg)
        db.add(ai_msg)
        
        # Award XP for language practice
        xp_earned = gamification_service.award_xp(
            db=db,
            user_id=int(current_user.id),
            xp_amount=settings.XP_PER_CHAT,
            action_type="language_chat"
        )
        
        # Update session
        db.query(StudySession).filter(StudySession.id == session.id).update({
            "xp_earned": StudySession.xp_earned + xp_earned
        })
        
        db.commit()
        
        return {
            "response": response,
            "xp_earned": xp_earned,
            "language": request.language
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
