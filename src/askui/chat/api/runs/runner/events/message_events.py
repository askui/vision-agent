from typing import Literal

from askui.chat.api.messages.message_persisted_service import MessagePersisted
from askui.chat.api.runs.runner.events.event_base import EventBase


class MessageEvent(EventBase):
    data: MessagePersisted
    event: Literal["thread.message.created"]
