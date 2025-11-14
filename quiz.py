from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from database import get_db
from models.user import User
from models.session import Quiz, QuizQuestion, StudySession
from services.rag_service import RAGService
from services.gamification_service import GamificationService
from utils.auth import get_current_user
from config import settings

router = APIRouter()
rag_service = RAGService()
gamification_service = GamificationService()

class QuizGenerateRequest(BaseModel):
    session_id: int
    num_questions: int = 5

class QuizAnswer(BaseModel):
    question_id: int
    answer: str

class QuizSubmitRequest(BaseModel):
    quiz_id: int
    answers: List[QuizAnswer]

@router.post("/quiz/generate")
async def generate_quiz(
    request: QuizGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Verify session
        session = db.query(StudySession).filter(
            StudySession.id == request.session_id,
            StudySession.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Generate questions using RAG
        questions_data = await rag_service.generate_quiz(
            session_id=request.session_id,
            num_questions=request.num_questions
        )
        
        if not questions_data:
            raise HTTPException(status_code=500, detail="Failed to generate quiz")
        
        # Create quiz
        quiz = Quiz(
            session_id=request.session_id,
            total_questions=len(questions_data)
        )
        db.add(quiz)
        db.commit()
        db.refresh(quiz)
        
        # Add questions
        questions = []
        for q_data in questions_data:
            question = QuizQuestion(
                quiz_id=quiz.id,
                question_text=q_data['question'],
                option_a=q_data['option_a'],
                option_b=q_data['option_b'],
                option_c=q_data['option_c'],
                option_d=q_data['option_d'],
                correct_answer=q_data['correct']
            )
            db.add(question)
            questions.append({
                'id': question.id,
                'question': q_data['question'],
                'option_a': q_data['option_a'],
                'option_b': q_data['option_b'],
                'option_c': q_data['option_c'],
                'option_d': q_data['option_d']
            })
        
        db.commit()
        
        return {
            "quiz_id": quiz.id,
            "questions": questions
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/quiz/submit")
async def submit_quiz(
    request: QuizSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        quiz = db.query(Quiz).filter(Quiz.id == request.quiz_id).first()
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        # Grade quiz
        correct_count = 0
        
        for answer in request.answers:
            question = db.query(QuizQuestion).filter(
                QuizQuestion.id == answer.question_id
            ).first()
            
            if question:
                question.user_answer = answer.answer  # type: ignore
                question.is_correct = (answer.answer == question.correct_answer)  # type: ignore
                is_correct_value = (answer.answer == question.correct_answer)
                if is_correct_value:
                    correct_count += 1
        
        quiz.completed = True  # type: ignore
        quiz.correct_answers = correct_count  # type: ignore
        quiz_score = (correct_count / quiz.total_questions) * 100
        quiz.score = quiz_score  # type: ignore
        
        # Update user stats
        current_user.quizzes_completed += 1  # type: ignore
        prev_accuracy = float(current_user.quiz_accuracy)  # type: ignore
        total_accuracy = ((prev_accuracy * (int(current_user.quizzes_completed) - 1)) + quiz_score) / int(current_user.quizzes_completed)  # type: ignore
        current_user.quiz_accuracy = round(total_accuracy, 2)  # type: ignore
        
        # Award XP
        xp_earned = gamification_service.award_xp(
            db=db,
            user_id=int(current_user.id),  # type: ignore
            xp_amount=correct_count * settings.XP_PER_QUIZ_QUESTION,
            action_type="quiz"
        )
        
        db.commit()
        
        return {
            "score": quiz.score,
            "correct_answers": correct_count,
            "total_questions": quiz.total_questions,
            "xp_earned": xp_earned
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
