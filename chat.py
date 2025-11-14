from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models.user import User
from models.session import ChatMessage, StudySession
from services.gamification_service import GamificationService
from utils.auth import get_current_user
from config import settings

# Router setup
router = APIRouter()
gamification_service = GamificationService()

# Try to import RAG service; fall back to mock if langchain unavailable
try:
    from services.rag_service import RAGService as RealRAGService
    rag_service = RealRAGService()
except Exception as e:
    print(f"⚠️  RAG service unavailable (langchain not installed): {e}")
    # Mock RAG service for development
    class MockRAGService:
        async def get_response(self, query: str, session_id: int | None = None):
            return "This is a mock response. Install langchain for real RAG features."
    rag_service = MockRAGService()

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
        # Verify session belongs to user (create if missing)
        session = None
        if request.session_id:
            session = db.query(StudySession).filter(
                StudySession.id == request.session_id,
                StudySession.user_id == current_user.id
            ).first()
        if not session:
            # create a new session for this user
            session = StudySession(user_id=current_user.id, session_type="web")
            db.add(session)
            db.commit()
            db.refresh(session)
        
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
        user_id = getattr(current_user, 'id', None)  # type: ignore
        xp_earned = gamification_service.award_xp(
            db=db,
            user_id=user_id,  # type: ignore
            xp_amount=settings.XP_PER_CHAT,
            action_type="chat"
        )
        
        # Update session XP
        session.xp_earned = (session.xp_earned or 0) + xp_earned  # type: ignore
        
        db.commit()
        
        return ChatResponse(response=response, xp_earned=xp_earned)
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/sessions')
async def create_session(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new StudySession for the current user and return its id."""
    try:
        session = StudySession(user_id=current_user.id, session_type='web')
        db.add(session)
        db.commit()
        db.refresh(session)
        return {"session_id": session.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
