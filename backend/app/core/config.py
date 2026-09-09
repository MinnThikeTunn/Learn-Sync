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
    RABBITMQ_EXCHANGE: str = "learnsync.events"

    # Distributed infrastructure.  Leave REDIS_URL empty for local fallback mode.
    REDIS_URL: Optional[str] = None
    REDIS_KEY_PREFIX: str = "learnsync"
    REDIS_STREAM_KEY: str = "learnsync:events"
    REDIS_STREAM_MAXLEN: int = 100000
    ASYNC_DOCUMENT_PROCESSING: bool = False
    ARTIFACT_CACHE_TTL_SECONDS: int = 3600
    DISTRIBUTED_LOCK_TIMEOUT_SECONDS: int = 30
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    FEYNMAN_RPM_LIMIT: int = 10

    # Celery Background Worker Settings
    CELERY_APP_NAME: str = "learnsync"
    CELERY_TASK_NAME: str = "learnsync.process_document"
    CELERY_TASK_MAX_RETRIES: int = 3
    CELERY_TASK_RETRY_BACKOFF: bool = True
    
    # Google OAuth & Calendar / Gmail Settings
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:3000/api/auth/callback/google"
    
    # AI / LLM Settings (Gemini & OpenRouter Free Tier)
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"  # Default fast model, works with standard Gemini API
    GEMINI_MAX_TOKENS: int = 2048
    GEMINI_TEMPERATURE: float = 0.2
    
    # OpenRouter Free Tier Settings
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_MODEL: str = "meta-llama/llama-3.3-70b-instruct:free"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_PROVIDER: str = "openrouter"  # "openrouter" | "gemini" | "deterministic"
    
    EMBEDDING_DIMENSION: int = 1536
    RRF_K_PARAMETER: int = 60
    
    # Rate Limiting & Safety Budgets (Requests Per Minute)
    LLM_RPM_LIMIT: int = 15
    LLM_RETRY_ATTEMPTS: int = 3
    LLM_RETRY_BACKOFF_SECONDS: float = 2.0
    
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

