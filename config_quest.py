from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080
    
    # OpenAI
    OPENAI_API_KEY: str
    
    # Agora
    AGORA_APP_ID: str
    AGORA_APP_CERTIFICATE: str
    
    # Paths
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 52428800
    
    # Gamification
    XP_PER_CHAT: int = 10
    XP_PER_QUIZ_QUESTION: int = 20
    XP_PER_VOICE_MINUTE: int = 15
    XP_PER_UPLOAD: int = 50
    
    model_config = ConfigDict(extra="ignore", env_file=".env")

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
