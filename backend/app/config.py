"""Application configuration using pydantic-settings."""

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "VibeCast Studio"
    debug: bool = False
    log_level: str = "info"

    # Database
    database_url: str = "sqlite:///./storage/vibecast.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Storage
    storage_path: Path = Path("./storage")

    # HuggingFace
    hf_home: Optional[str] = None

    # Claude API
    claude_api_key: Optional[str] = None

    # Model settings
    default_model: str = "vibevoice-community/VibeVoice-1.5B"
    realtime_model: str = "microsoft/VibeVoice-Realtime-0.5B"

    # Generation settings
    max_generation_duration_minutes: int = 90
    chunk_duration_minutes: int = 8
    crossfade_ms: int = 500

    # Rate limiting
    rate_limit_generation: str = "5/hour"
    rate_limit_preview: str = "30/hour"
    rate_limit_enhancement: str = "20/hour"

    # Safety
    enable_watermark: bool = True
    enable_disclaimer: bool = True

    @property
    def audio_path(self) -> Path:
        """Path for generated audio files."""
        return self.storage_path / "audio"

    @property
    def exports_path(self) -> Path:
        """Path for exported files."""
        return self.storage_path / "exports"

    @property
    def uploads_path(self) -> Path:
        """Path for uploaded files."""
        return self.storage_path / "uploads"

    @property
    def projects_path(self) -> Path:
        """Path for project data."""
        return self.storage_path / "projects"

    def ensure_directories(self) -> None:
        """Create all required storage directories."""
        for path in [
            self.audio_path,
            self.exports_path,
            self.uploads_path,
            self.projects_path,
            self.storage_path / "music",
        ]:
            path.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
