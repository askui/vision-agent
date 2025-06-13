from typing import Literal

from askui.chat.api.messages.models import Message
from askui.chat.api.runs.runner.events.event_base import EventBase


class MessageEvent(EventBase):
    data: Message
    event: Literal[
        "thread.message.created",
        "thread.message.in_progress",
        "thread.message.completed",
        "thread.message.incomplete",
    ]
