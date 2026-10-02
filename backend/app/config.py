"""Configuration management for APEX OSINT."""

import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "APEX OSINT"
    APP_VERSION: str = "1.0.0"
    TAGLINE: str = "Intelligence, connected."
    DEBUG: bool = False

    # Server settings
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    # Database settings
    # Default to local SQLite with aiosqlite for zero-config local operation.
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///apex_osint.db",
        description="SQLAlchemy async database connection string"
    )

    # Gemini AI configuration
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="Google Gemini API Key")
    GEMINI_MODEL: str = Field(default="gemini-3.5-flash-lite", description="Gemini model identifier")
    GEMINI_TEMPERATURE: float = 0.2
    GEMINI_MAX_OUTPUT_TOKENS: int = 4096

    # Optional 3rd party OSINT API keys
    GITHUB_TOKEN: Optional[str] = None
    VIRUSTOTAL_API_KEY: Optional[str] = None
    SHODAN_API_KEY: Optional[str] = None
    SECURITYTRAILS_API_KEY: Optional[str] = None
    HIBP_API_KEY: Optional[str] = None

    # Safety and SSRF protections
    BLOCK_PRIVATE_NETWORKS: bool = True
    HTTP_TIMEOUT_SECONDS: float = 12.0
    HTTP_MAX_REDIRECTS: int = 3
    MAX_RESPONSE_BYTES: int = 5 * 1024 * 1024  # 5 MB cap

    # Investigation budget defaults
    DEFAULT_MAX_DEPTH: int = 2
    DEFAULT_MAX_REQUESTS: int = 150
    DEFAULT_MAX_MODULES: int = 30
    DEFAULT_MAX_RUNTIME_SECONDS: int = 180
    DEFAULT_MAX_AI_CALLS: int = 10

    # Rate limiting
    DEFAULT_MODULE_RATE_LIMIT: float = 2.0  # requests per second per host


settings = Settings()
