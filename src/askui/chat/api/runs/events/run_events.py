from typing import Literal

from askui.chat.api.runs.events.event_base import EventBase
from askui.chat.api.runs.models import Run


class RunEvent(EventBase):
    data: Run
    event: Literal[
        "thread.run.created",
        "thread.run.queued",
        "thread.run.in_progress",
        "thread.run.completed",
        "thread.run.failed",
        "thread.run.cancelling",
        "thread.run.cancelled",
        "thread.run.expired",
    ]
