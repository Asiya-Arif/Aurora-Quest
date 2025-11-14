from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models.user import User
from models.session import StudySession
from services.agora_service import AgoraService
from utils.auth import get_current_user

router = APIRouter()
agora_service = AgoraService()

class LanguageStartRequest(BaseModel):
    language: str

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
        
        # Generate Agora credentials
        # Generate Agora credentials
        user_id = getattr(current_user, 'id', None)  # type: ignore
        channel_name = agora_service.generate_channel_name(
            user_id=user_id,  # type: ignore
            language=request.language
        )
        
        credentials = agora_service.generate_token(
            channel_name=channel_name,
            uid=user_id  # type: ignore
        )
        
        return {
            "session_id": session.id,
            "agora_token": credentials["token"],
            "channel_name": channel_name,
            "app_id": credentials["app_id"],
            "uid": current_user.id
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
