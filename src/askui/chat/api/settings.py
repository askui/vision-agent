from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings for the chat API."""

    model_config = SettingsConfigDict(
        env_prefix="ASKUI__CHAT_API__", env_nested_delimiter="__"
    )

    data_dir: Path = Field(
        default_factory=lambda: Path.cwd() / "chat",
        description="Base directory for storing chat data",
    )
    host: str = Field(
        default="127.0.0.1",
        description="Host for the chat API",
    )
    log_level: str | int = Field(
        default="info",
        description="Log level for the chat API",
    )
    port: int = Field(
        default=9261,
        description="Port for the chat API",
        ge=1024,
        le=65535,
    )
