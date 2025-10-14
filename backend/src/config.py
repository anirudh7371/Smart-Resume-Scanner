from pydantic_settings import BaseSettings
from typing import ClassVar

class Settings(BaseSettings):
    APP_NAME: str = "Smart Resume Screener"
    ENV: str = "development"
    DATABASE_URL: str = "mongodb://localhost:27017/"
    LLM_PROVIDER: str = "gemini"
    OLLAMA_MODEL: ClassVar[str] = "llama3.2"
    GEMINI_EMBEDDING_MODEL: str = "models/text-embedding-004"
    GEMINI_API_KEY: str
    EMBEDDING_DIMENSION: int = 768

    class Config:
        env_file = ".env"

settings = Settings()