from datetime import datetime, timedelta
from typing import Optional
import base64, json, hmac, hashlib, time

# Minimal HS256-only JWT implementation (no external JWT lib required for dev)
class JWTError(Exception):
    pass

def _b64url_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode('ascii')

def _b64url_decode(s: str) -> bytes:
    padding = '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + padding)

class _JWT:
    @staticmethod
    def encode(payload, key, algorithm='HS256'):
        header = {"alg": "HS256", "typ": "JWT"}
        payload_copy = payload.copy()
        # Normalize datetime -> int timestamp
        if isinstance(payload_copy.get("exp"), datetime):
            payload_copy["exp"] = int(payload_copy["exp"].timestamp())
        header_b = _b64url_encode(json.dumps(header, separators=(",",":")).encode())
        payload_b = _b64url_encode(json.dumps(payload_copy, default=str, separators=(",",":")).encode())
        signing_input = f"{header_b}.{payload_b}".encode()
        sig = hmac.new(key.encode(), signing_input, hashlib.sha256).digest()
        sig_b = _b64url_encode(sig)
        return f"{header_b}.{payload_b}.{sig_b}"

    @staticmethod
    def decode(token, key, algorithms=None):
        try:
            header_b, payload_b, sig_b = token.split('.')
        except Exception:
            raise JWTError("Invalid token format")
        signing_input = f"{header_b}.{payload_b}".encode()
        expected_sig = hmac.new(key.encode(), signing_input, hashlib.sha256).digest()
        if not hmac.compare_digest(expected_sig, _b64url_decode(sig_b)):
            raise JWTError("Signature verification failed")
        payload_json = json.loads(_b64url_decode(payload_b))
        exp = payload_json.get("exp")
        if exp and int(time.time()) > int(exp):
            raise JWTError("Token expired")
        return payload_json

jwt = _JWT()

from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from config import settings
from database import get_db
from user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise credentials_exception

    sub = payload.get("sub")
    if sub is None:
        raise credentials_exception

    try:
        user_id = int(sub)
    except (TypeError, ValueError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user
