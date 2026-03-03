"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with defaults for local development."""

    # Database
    database_url: str = "postgresql+asyncpg://accompaniment:accompaniment@localhost:5432/accompaniment"
    database_url_sync: str = "postgresql://accompaniment:accompaniment@localhost:5432/accompaniment"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "mistral"
    ollama_fallback_model: str = "neural-chat"

    # Storage
    storage_path: str = "./data/storage"
    storage_backend: str = "filesystem"

    # Audio
    soundfont_path: str = "./backend/assets/soundfonts/piano.sf2"
    crepe_model_capacity: str = "full"
    max_upload_size_mb: int = 100
    max_audio_duration_seconds: int = 600

    # Auth
    jwt_secret: str = "change-this-to-a-random-secret-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 1440

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # Cache
    melody_cache_ttl: int = 604800  # 7 days

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True

    # Prometheus
    prometheus_enabled: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
