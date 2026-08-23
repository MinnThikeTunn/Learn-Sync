from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "LearnSync AI"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Supabase Settings
    SUPABASE_URL: str = "https://example.supabase.co"
    SUPABASE_KEY: str = "public-anon-key"
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    
    # RabbitMQ Settings
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    
    # AI / LLM Settings
    GEMINI_API_KEY: Optional[str] = None
    EMBEDDING_DIMENSION: int = 1536
    RRF_K_PARAMETER: int = 60
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
