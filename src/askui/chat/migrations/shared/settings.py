from pathlib import Path
from typing import Annotated
from uuid import UUID

from pydantic import AwareDatetime, Field, PlainSerializer
from pydantic_settings import BaseSettings, SettingsConfigDict

# Local models to avoid dependencies on askui.chat.api
UnixDatetime = Annotated[
    AwareDatetime,
    PlainSerializer(
        lambda v: int(v.timestamp()),
        return_type=int,
    ),
]

AssistantId = Annotated[str, Field(pattern=r"^asst_[a-z0-9]+$")]
WorkspaceId = UUID


class SettingsV1(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ASKUI__CHAT_API__", env_nested_delimiter="__"
    )

    data_dir: Path = Field(
        default_factory=lambda: Path.cwd() / "chat",
        description="Base directory for chat data (used during migration)",
    )
