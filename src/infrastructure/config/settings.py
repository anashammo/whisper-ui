"""Application settings using Pydantic for configuration management"""
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Uses Pydantic for validation and type conversion.
    Settings can be overridden via .env file or environment variables.
    """

    # Application
    app_name: str = Field(default="Whisper Transcription API", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")

    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_prefix: str = Field(default="/api/v1", description="API prefix")

    # CORS Configuration
    cors_origins: List[str] = Field(
        default=["http://localhost:4200", "http://localhost:3000","*"],
        description="Allowed CORS origins" 
    )

    # Database Configuration
    database_url: str = Field(
        default="sqlite:///./whisper_transcriptions.db",
        description="Database connection URL"
    )

    # File Storage Configuration
    upload_dir: str = Field(default="./uploads", description="Upload directory path")
    max_file_size_mb: int = Field(default=25, description="Maximum file size in MB")
    max_duration_seconds: int = Field(default=30, description="Maximum audio duration in seconds")

    # Whisper Configuration
    whisper_model: str = Field(
        default="base",
        description="Whisper model size (tiny, base, small, medium, large)"
    )
    whisper_device: str = Field(
        default="cuda",
        description="Device for Whisper (cuda or cpu)"
    )
    whisper_compute_type: str = Field(
        default="float16",
        description="Compute type for Whisper (float16, float32, int8)"
    )

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")

    # LLM Configuration
    llm_base_url: str = Field(
        default="http://localhost:11434/v1",
        description="Base URL for LLM API (OpenAI-compatible, e.g., Ollama)"
    )
    llm_model: str = Field(
        default="llama3",
        description="LLM model name (e.g., llama3, mistral, etc.)"
    )
    llm_timeout_seconds: int = Field(
        default=60,
        description="Timeout for LLM requests in seconds"
    )
    llm_temperature: float = Field(
        default=0.3,
        description="LLM temperature for generation (0.0-1.0, lower = more focused)"
    )

    class Config:
        # Try backend-specific .env first, then fall back to root .env for backward compatibility
        env_file = ("src/presentation/api/.env", ".env")
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env file


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses lru_cache to ensure settings are loaded only once.
    This is the recommended way to access settings throughout the application.

    Returns:
        Settings instance
    """
    return Settings()
