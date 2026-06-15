from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    ANTHROPIC_API_KEY: str
    OPENAI_API_KEY: str
    TAVILY_API_KEY: str
    GEMINI_API_KEY: str

    DATABASE_URL: str

    # Qdrant vector database
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "research_sources"

    class Config:
        env_file = str(BASE_DIR / ".env")


settings = Settings()