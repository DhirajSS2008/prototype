"""Application configuration using Pydantic settings."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    APP_NAME: str = "LiquiSense"
    DEBUG: bool = True

    # Database (MySQL)
    DATABASE_URL: str = "mysql+pymysql://root:12345@localhost/liqui_sense"

    # JWT Auth
    SECRET_KEY: str = "liqui-sense-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = False  # Disabled by default for Windows dev

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

<<<<<<< HEAD
    # Gemini API (primary AI engine)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # Groq API (legacy fallback)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # SMTP Email
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""

    # Resend Email (Functional delivery)
    RESEND_API_KEY: str = ""
    RESEND_FROM_NAME: str = "LiquiSense"
    RESEND_FROM_EMAIL: str = "onboarding@resend.dev" # Default for trial, user can change
=======
    # Claude API
    ANTHROPIC_API_KEY: str = ""
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73

    # File upload
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
