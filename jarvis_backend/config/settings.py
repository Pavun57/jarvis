"""Configuration settings for Jarvis Backend."""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Gemini API
    GEMINI_API_KEY: str
    
    # Serper.dev API (for web search)
    SERPER_API_KEY: Optional[str] = None
    
    # PostgreSQL Database
    DATABASE_URL: str = "postgresql://jarvis:jarvis@localhost:5433/jarvis_db"
    
    # ChromaDB
    CHROMA_PERSIST_DIR: str = str(Path(__file__).parent.parent / "data" / "chroma_db")
    
    # Model Configuration
    GEMINI_MODEL: str = "gemini-2.5-flash"
    MAX_TOKENS: int = 8192
    TEMPERATURE: float = 0.7
    
    # Memory Configuration
    MAX_CONVERSATION_HISTORY: int = 50
    MEMORY_SEARCH_LIMIT: int = 10
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()

