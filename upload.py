from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List
import os
import aiofiles
from database import get_db
from models.user import User
from models.session import StudySession, StudyMaterial
from services.document_processor import DocumentProcessor
from services.gamification_service import GamificationService
from utils.auth import get_current_user
from config import settings

router = APIRouter()
document_processor = DocumentProcessor()
gamification_service = GamificationService()

@router.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Create study session
        session = StudySession(
            user_id=current_user.id,  # type: ignore
            session_type="upload"
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        
        # Create directory for session
        session_id = int(session.id)  # type: ignore
        session_dir = os.path.join(settings.UPLOAD_DIR, f"session_{session_id}")
        os.makedirs(session_dir, exist_ok=True)
        
        uploaded_files = []
        
        for file in files:
            # Validate filename
            filename = file.filename
            if not filename:
                raise HTTPException(status_code=400, detail="File name is required")
            
            # Save file
            file_path = os.path.join(session_dir, filename)
            
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            # Save to database
            material = StudyMaterial(
                session_id=session_id,
                filename=filename,
                file_path=file_path,
                file_type=filename.split('.')[-1],
                file_size=len(content)
            )
            db.add(material)
            
            # Process document for RAG
            success = await document_processor.process_document(file_path, session_id)
            
            if success:
                material.processed = True  # type: ignore
                uploaded_files.append(filename)
        
        # Update user stats
        current_user.materials_uploaded += len(files)  # type: ignore
        
        # Award XP
        gamification_service.award_xp(
            db=db,
            user_id=int(current_user.id),  # type: ignore
            xp_amount=settings.XP_PER_UPLOAD,
            action_type="upload"
        )
        
        # Update streak
        gamification_service.update_streak(db, int(current_user.id))  # type: ignore
        
        db.commit()
        
        return {
            "session_id": session.id,
            "files": uploaded_files,
            "message": "Files uploaded and processed successfully!"
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
