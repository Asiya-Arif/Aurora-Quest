from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
# Use plain str for email to avoid requiring the 'email-validator' package in dev
# (production: prefer EmailStr and install 'pydantic[email]')
from database import get_db
from models.user import User
from utils.auth import verify_password, get_password_hash, create_access_token
from datetime import timedelta
from config import settings

router = APIRouter()

class UserRegister(BaseModel):
    name: str
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/register", response_model=Token)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create token
    access_token = create_access_token(
        data={"sub": str(new_user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, str(user.hashed_password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# Dev-only: Allow login with any password for testing
@router.post("/dev-login", response_model=Token)
async def dev_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """DEV ONLY: Login with any password. Creates user if doesn't exist."""
    email = form_data.username
    print(f"[DEV] Attempting dev-login for email: {email}")
    
    try:
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            # Create user on first login for dev convenience
            print(f"[DEV] Creating new user: {email}")
            try:
                hashed_password = get_password_hash(form_data.password)
            except Exception as e:
                # If password hashing fails (e.g., bcrypt issue), use plaintext for dev
                print(f"[DEV] Password hashing failed ({e}), using plaintext for dev")
                hashed_password = form_data.password
            
            user = User(
                email=email,
                name=email.split('@')[0],
                hashed_password=hashed_password
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"[DEV] User created successfully: {user.id}")
        
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        print(f"[DEV] Token generated for user {user.id}")
        return {"access_token": access_token, "token_type": "bearer"}
    
    except Exception as e:
        print(f"[DEV] Login error: {e}")
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")
