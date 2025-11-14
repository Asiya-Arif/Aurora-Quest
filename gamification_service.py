from sqlalchemy.orm import Session
from models.user import User
from models.gamification import Achievement, UserAchievement
from datetime import datetime, timedelta

class GamificationService:
    @staticmethod
    def award_xp(db: Session, user_id: int, xp_amount: int, action_type: str) -> int:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return 0
        
        user.total_xp += xp_amount  # type: ignore
        user.total_points += xp_amount  # type: ignore
        
        # Calculate level (every 1000 XP = 1 level)
        user.current_level = (user.total_xp // 1000) + 1  # type: ignore
        
        db.commit()
        
        # Check for achievements
        GamificationService.check_achievements(db, user)
        
        return xp_amount
    
    @staticmethod
    def update_streak(db: Session, user_id: int) -> int:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return 0
        
        today = datetime.utcnow().date()
        last_active_dt = user.last_active_date
        last_active = last_active_dt.date() if last_active_dt is not None else None  # type: ignore
        
        if last_active:
            days_diff = (today - last_active).days
            if days_diff == 1:
                user.current_streak += 1  # type: ignore
            elif days_diff > 1:
                user.current_streak = 1  # type: ignore
        else:
            user.current_streak = 1  # type: ignore
        
        user.last_active_date = datetime.utcnow()  # type: ignore
        db.commit()
        
        return user.current_streak  # type: ignore
    
    @staticmethod
    def check_achievements(db: Session, user: User):
        achievements = db.query(Achievement).all()
        
        for achievement in achievements:
            # Check if user already has this achievement
            existing = db.query(UserAchievement).filter(
                UserAchievement.user_id == user.id,
                UserAchievement.achievement_id == achievement.id
            ).first()
            
            if existing:
                continue
            
            # Check criteria
            earned = False
            if achievement.criteria_type == 'streak' and user.current_streak >= achievement.criteria_value:  # type: ignore
                earned = True
            elif achievement.criteria_type == 'quiz_count' and user.quizzes_completed >= achievement.criteria_value:  # type: ignore
                earned = True
            elif achievement.criteria_type == 'xp' and user.total_xp >= achievement.criteria_value:  # type: ignore
                earned = True
            
            if earned:
                user_achievement = UserAchievement(
                    user_id=user.id,  # type: ignore
                    achievement_id=achievement.id
                )
                db.add(user_achievement)
                user.badges_earned += 1  # type: ignore
                user.total_xp += achievement.xp_reward  # type: ignore
                db.commit()
