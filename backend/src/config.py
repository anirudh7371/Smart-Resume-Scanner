from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Smart Resume Screener"
    ENV: str = "development"
    DATABASE_URL: str = "mongodb://localhost:27017/"
    LLM_PROVIDER: str = "gemini"
    GEMINI_EMBEDDING_MODEL: str = "models/embedding-001"
    GEMINI_GENERATION_MODEL: str = "gemini-1.5-flash"
    GEMINI_API_KEY: str
    EMBEDDING_DIMENSION: int = 768

    class Config:
        env_file = ".env"

settings = Settings()