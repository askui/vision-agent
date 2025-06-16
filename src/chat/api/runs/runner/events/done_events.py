from typing import Literal

from chat.api.runs.runner.events.event_base import EventBase


class DoneEvent(EventBase):
    event: Literal["done"] = "done"
    data: Literal["[DONE]"] = "[DONE]"
