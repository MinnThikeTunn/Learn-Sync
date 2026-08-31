from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "LearnSync AI"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    ENVIRONMENT: str = "development"
    
    # Supabase Settings
    SUPABASE_URL: str = "https://example.supabase.co"
    SUPABASE_KEY: str = "public-anon-key"
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_JWT_SECRET: Optional[str] = None
    
    # RabbitMQ Settings
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    
    # Google OAuth & Calendar / Gmail Settings
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:3000/api/auth/callback/google"
    
    # AI / LLM Settings (Gemini 3 Flash / 1.5 Flash)
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"  # Default fast model, works with standard Gemini API
    GEMINI_MAX_TOKENS: int = 2048
    GEMINI_TEMPERATURE: float = 0.2
    EMBEDDING_DIMENSION: int = 1536
    RRF_K_PARAMETER: int = 60
    
    # Rate Limiting & Safety Budgets (Requests Per Minute)
    LLM_RPM_LIMIT: int = 15
    LLM_RETRY_ATTEMPTS: int = 3
    LLM_RETRY_BACKOFF_SECONDS: float = 2.0
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

