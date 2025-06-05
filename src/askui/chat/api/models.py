from typing import Literal

from pydantic import BaseModel


class Event(BaseModel):
    object: Literal["event"] = "event"
