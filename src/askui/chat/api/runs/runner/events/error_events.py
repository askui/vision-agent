from typing import Literal

from pydantic import BaseModel

from askui.chat.api.runs.runner.events.event_base import EventBase


class ErrorEventDataError(BaseModel):
    message: str


class ErrorEventData(BaseModel):
    error: ErrorEventDataError


class ErrorEvent(EventBase):
    event: Literal["error"] = "error"
    data: ErrorEventData
