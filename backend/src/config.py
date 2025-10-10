from pydantic import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Smart Resume Screener"
    ENV: str = "development"
    DATABASE_URL: str
    LLM_PROVIDER: str = "gemini"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    LLM_MODEL: str = ""
    GEMINI_API_KEY: str = None