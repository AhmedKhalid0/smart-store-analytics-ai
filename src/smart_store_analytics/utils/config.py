"""Configuration and environment settings loader."""

import os
from pathlib import Path
from typing import Optional

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    from pydantic import Field

    class Settings(BaseSettings):
        """Application runtime configuration."""

        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",
        )

        app_name: str = "smart-store-analytics-ai"
        app_env: str = "development"
        log_level: str = "INFO"

        host: str = "127.0.0.1"
        port: int = 8095

        detector_model: str = "yolov8n.pt"
        detection_confidence_threshold: float = 0.35
        tracking_iou_threshold: float = 0.30
        tracking_max_age_frames: int = 30

        max_queue_length_threshold: int = 5
        max_queue_wait_seconds: int = 180

        data_dir: Path = Field(default_factory=lambda: Path("./data"))
        outputs_dir: Path = Field(default_factory=lambda: Path("./outputs"))

        def ensure_directories(self) -> None:
            """Ensures required directories exist."""
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self.outputs_dir.mkdir(parents=True, exist_ok=True)

except ImportError:
    from pydantic import BaseModel, Field

    class Settings(BaseModel):  # type: ignore
        """Fallback settings model."""

        app_name: str = "smart-store-analytics-ai"
        app_env: str = "development"
        log_level: str = "INFO"

        host: str = "127.0.0.1"
        port: int = 8095

        detector_model: str = "yolov8n.pt"
        detection_confidence_threshold: float = 0.35
        tracking_iou_threshold: float = 0.30
        tracking_max_age_frames: int = 30

        max_queue_length_threshold: int = 5
        max_queue_wait_seconds: int = 180

        data_dir: Path = Field(default_factory=lambda: Path("./data"))
        outputs_dir: Path = Field(default_factory=lambda: Path("./outputs"))

        def ensure_directories(self) -> None:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self.outputs_dir.mkdir(parents=True, exist_ok=True)


_settings_instance: Optional[Settings] = None


def get_settings() -> Settings:
    """Returns singleton Settings instance."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance
