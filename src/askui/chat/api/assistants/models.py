from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

from askui.chat.api.models import UnixDatetime
from askui.chat.api.utils import generate_time_ordered_id


class Assistant(BaseModel):
    """An assistant that can be used in a thread."""

    id: str = Field(default_factory=lambda: generate_time_ordered_id("asst"))
    created_at: UnixDatetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    name: str | None = None
    description: str | None = None
    object: Literal["assistant"] = "assistant"
    avatar: str | None = Field(default=None, description="URL of the avatar image")
