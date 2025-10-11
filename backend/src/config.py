from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Smart Resume Screener"
    ENV: str = "development"
    DATABASE_URL: str
    LLM_PROVIDER: str = "gemini"
    EMBEDDING_MODEL: str = "models/embedding-001"
    LLM_MODEL: str = "gemini-1.5-flash"
    GEMINI_API_KEY: str = "YOUR_API_KEY"

    class Config:
        env_file = ".env"