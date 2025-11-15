"""
Configuration settings for Aurora Quest
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App Configuration
    APP_NAME: str = "Aurora Quest"
    DEBUG: bool = True
    API_VERSION: str = "v1"
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/aurora_quest"
    # For development, use SQLite: "sqlite:///./aurora_quest.db"
    
    # JWT Authentication
    SECRET_KEY: str = "your-secret-key-change-in-production-use-openssl-rand-hex-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # Pinecone Vector Database
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_ENVIRONMENT: str = "gcp-starter"
    PINECONE_INDEX_NAME: str = "aurora-quest-docs"
    
    # Agora RTC Configuration
    AGORA_APP_ID: str = "your-agora-app-id"
    AGORA_APP_CERTIFICATE: str = ""
    AGORA_TOKEN_EXPIRATION: int = 3600  # 1 hour
    
    # Agora Chat Configuration (based on your credentials)
    AGORA_CHAT_APP_KEY: str = "611423203#1624023"
    AGORA_CHAT_REST_API: str = "https://a61.chat.agora.io"
    AGORA_CHAT_WEBSOCKET: str = "wss://msync-api-61.chat.agora.io"
    AGORA_CHAT_CLIENT_ID: Optional[str] = None
    AGORA_CHAT_CLIENT_SECRET: Optional[str] = None
    
    # File Upload Settings
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: list = [".pdf", ".txt", ".docx", ".pptx"]
    
    # XP and Gamification
    XP_PER_TASK: int = 50
    XP_PER_QUIZ: int = 100
    XP_PER_VOICE_SESSION: int = 75
    XP_STREAK_BONUS: int = 25
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://aurora-quest.vercel.app"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
