from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database_quest import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # Gamification
    total_xp = Column(Integer, default=0)
    total_points = Column(Integer, default=0)
    current_level = Column(Integer, default=1)
    current_streak = Column(Integer, default=0)
    global_rank = Column(Integer, default=0)
    
    # Stats
    study_time_today = Column(Float, default=0)
    quizzes_completed = Column(Integer, default=0)
    badges_earned = Column(Integer, default=0)
    materials_uploaded = Column(Integer, default=0)
    study_sessions = Column(Integer, default=0)
    quiz_accuracy = Column(Float, default=0.0)
    
    # Dates
    last_active_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sessions = relationship("StudySession", back_populates="user", cascade="all, delete-orphan")
    achievements = relationship("UserAchievement", back_populates="user", cascade="all, delete-orphan")
