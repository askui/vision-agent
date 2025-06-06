from typing import Literal

from pydantic import BaseModel


class Event(BaseModel):
    object: Literal["event"] = "event"


class DoneEvent(Event):
    event: Literal["done"] = "done"
    data: Literal["[DONE]"] = "[DONE]"


class ErrorEvent(Event):
    event: Literal["error"] = "error"
    data: str
