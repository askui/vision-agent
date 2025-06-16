from typing import Literal

from chat.api.messages.service import Message
from chat.api.runs.runner.events.event_base import EventBase


class MessageEvent(EventBase):
    data: Message
    event: Literal["thread.message.created"]
