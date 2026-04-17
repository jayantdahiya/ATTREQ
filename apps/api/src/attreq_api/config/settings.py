"""Core configuration settings for ATTREQ backend."""

import json

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application settings
    app_name: str = Field(default="ATTREQ", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_debug: bool = Field(default=False, alias="APP_DEBUG")

    # Database settings
    database_url: str = Field(alias="DATABASE_URL")
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(alias="POSTGRES_DB")
    postgres_user: str = Field(alias="POSTGRES_USER")
    postgres_password: str = Field(alias="POSTGRES_PASSWORD")

    # JWT settings
    secret_key: str = Field(alias="SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=15, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    jwt_refresh_token_expire_days: int = Field(default=7, alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS")

    # CORS settings
    backend_cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"], alias="BACKEND_CORS_ORIGINS"
    )
    trusted_hosts: list[str] = Field(
        default=["attreq.com", "*.attreq.com", "localhost", "127.0.0.1"],
        alias="TRUSTED_HOSTS",
    )

    # Google OAuth settings (optional)
    google_client_id: str | None = Field(default=None, alias="GOOGLE_CLIENT_ID")
    google_client_secret: str | None = Field(default=None, alias="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str | None = Field(default=None, alias="GOOGLE_REDIRECT_URI")

    # Redis settings
    redis_host: str = Field(default="redis", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_password: str | None = Field(default=None, alias="REDIS_PASSWORD")

    # Weaviate settings
    weaviate_host: str = Field(default="weaviate", alias="WEAVIATE_HOST")
    weaviate_port: int = Field(default=8080, alias="WEAVIATE_PORT")
    weaviate_scheme: str = Field(default="http", alias="WEAVIATE_SCHEME")

    # External API settings
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model_name: str = Field(default="gemini-2.0-flash", alias="GEMINI_MODEL_NAME")
    gemini_batch_size: int = Field(default=5, alias="GEMINI_BATCH_SIZE")
    openweather_api_key: str | None = Field(default=None, alias="OPENWEATHER_API_KEY")

    # File upload settings
    max_upload_size_mb: int = Field(default=10, alias="MAX_UPLOAD_SIZE_MB")
    upload_dir: str = Field(default="./uploads", alias="UPLOAD_DIR")

    @validator("backend_cors_origins", pre=True)
    def assemble_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            raw = v.strip()
            if raw.startswith("["):
                return json.loads(raw)
            return [i.strip() for i in raw.split(",") if i.strip()]
        if isinstance(v, list):
            return v
        raise ValueError("CORS origins must be a string or list")

    @validator("trusted_hosts", pre=True)
    def assemble_trusted_hosts(cls, v):
        """Parse trusted hosts from string or list."""
        if isinstance(v, str):
            raw = v.strip()
            if raw.startswith("["):
                return json.loads(raw)
            return [i.strip() for i in raw.split(",") if i.strip()]
        if isinstance(v, list):
            return v
        raise ValueError("Trusted hosts must be a string or list")

    @validator("secret_key")
    def validate_secret_key(cls, v):
        """Validate that secret key is provided and has minimum length."""
        if not v or len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False


# Create global settings instance
settings = Settings()
