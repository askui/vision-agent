from typing import Literal

from pydantic import BaseModel


class EventBase(BaseModel):
    object: Literal["event"] = "event"
