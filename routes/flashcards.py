from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from database import get_db
from models.user import User
from services.rag_service import RAGService
from services.gamification_service import GamificationService
from utils.auth import get_current_user
from config import settings

router = APIRouter()
rag_service = RAGService()
gamification_service = GamificationService()

class FlashcardGenerateRequest(BaseModel):
    session_id: int
    num_cards: int = 10

class FlashcardResponse(BaseModel):
    flashcards: List[dict]
    session_id: int

@router.post("/flashcards/generate", response_model=FlashcardResponse)
async def generate_flashcards(
    request: FlashcardGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate flashcards from uploaded study materials"""
    try:
        # Generate flashcards using RAG
        flashcards = await rag_service.generate_flashcards(
            session_id=request.session_id,
            num_cards=request.num_cards
        )
        
        if not flashcards:
            raise HTTPException(status_code=500, detail="Failed to generate flashcards")
        
        # Award XP for generating flashcards
        xp_earned = gamification_service.award_xp(
            db=db,
            user_id=int(current_user.id),
            xp_amount=settings.XP_PER_CHAT,  # Same as chat
            action_type="flashcard"
        )
        
        db.commit()
        
        return FlashcardResponse(
            flashcards=flashcards,
            session_id=request.session_id
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
