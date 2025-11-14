from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.session import StudySession
from utils.auth import get_current_user

router = APIRouter()

@router.get("/user/profile")
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return {
        "user_id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "total_xp": current_user.total_xp,
        "total_points": current_user.total_points,
        "current_level": current_user.current_level,
        "current_streak": current_user.current_streak,
        "study_time_today": current_user.study_time_today,
        "quizzes_completed": current_user.quizzes_completed,
        "badges_earned": current_user.badges_earned,
        "materials_uploaded": current_user.materials_uploaded,
        "study_sessions": current_user.study_sessions,
        "quiz_accuracy": current_user.quiz_accuracy
    }

@router.get("/user/sessions")
async def get_user_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sessions = db.query(StudySession).filter(
        StudySession.user_id == current_user.id
    ).order_by(StudySession.start_time.desc()).limit(20).all()
    
    return [
        {
            "id": s.id,
            "session_type": s.session_type,
            "language": s.language,
            "start_time": s.start_time.isoformat(),
            "duration_minutes": s.duration_minutes,
            "xp_earned": s.xp_earned
        }
        for s in sessions
    ]
