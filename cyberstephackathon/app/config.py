from functools import lru_cache
from pathlib import Path

from pydantic import Field
# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment and .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="AirGap", validation_alias="APP_NAME")
    app_env: str = Field(default="development", validation_alias="APP_ENV")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    data_dir: Path = Field(default=Path("data"), validation_alias="DATA_DIR")
    uploads_dir: Path = Field(default=Path("data/uploads"), validation_alias="UPLOADS_DIR")
    chroma_dir: Path = Field(default=Path("data/chroma"), validation_alias="CHROMA_DIR")
    sqlite_path: Path = Field(default=Path("data/airgap.sqlite3"), validation_alias="SQLITE_PATH")

    # Lightweight defaults for laptops with limited RAM.
    whisper_model: str = Field(default="tiny", validation_alias="WHISPER_MODEL")
    whisper_compute_type: str = Field(default="int8", validation_alias="WHISPER_COMPUTE_TYPE")
    whisper_device: str = Field(default="cpu", validation_alias="WHISPER_DEVICE")
    whisper_language: str | None = Field(default=None, validation_alias="WHISPER_LANGUAGE")

    ollama_base_url: str = Field(default="http://localhost:11434", validation_alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="qwen2.5:0.5b", validation_alias="OLLAMA_MODEL")
    embedding_model: str = Field(
        default="paraphrase-multilingual-MiniLM-L12-v2", validation_alias="EMBEDDING_MODEL"
    )

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
