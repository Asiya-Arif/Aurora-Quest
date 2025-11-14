from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models.user import User
from models.session import ChatMessage, StudySession
from services.rag_service import RAGService
from services.gamification_service import GamificationService
from utils.auth import get_current_user
from config import settings

router = APIRouter()
rag_service = RAGService()
gamification_service = GamificationService()

class ChatRequest(BaseModel):
    query: str
    session_id: int

class ChatResponse(BaseModel):
    response: str
    xp_earned: int

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Verify session belongs to user
        session = db.query(StudySession).filter(
            StudySession.id == request.session_id,
            StudySession.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get RAG response
        response = await rag_service.get_response(
            query=request.query,
            session_id=request.session_id
        )
        
        # Save messages
        user_msg = ChatMessage(
            session_id=request.session_id,
            message_type="user",
            content=request.query
        )
        ai_msg = ChatMessage(
            session_id=request.session_id,
            message_type="ai",
            content=response
        )
        
        db.add(user_msg)
        db.add(ai_msg)
        
        # Award XP
        xp_earned = gamification_service.award_xp(
            db=db,
            user_id=current_user.id,
            xp_amount=settings.XP_PER_CHAT,
            action_type="chat"
        )

        # Persist messages and update session XP using a DB update to avoid
        # static type-checker issues with SQLAlchemy descriptors.
        db.add(user_msg)
        db.add(ai_msg)
        db.flush()

        db.query(StudySession).filter(StudySession.id == session.id).update({
            "xp_earned": StudySession.xp_earned + xp_earned
        })

        db.commit()

        return ChatResponse(response=response, xp_earned=xp_earned)
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
