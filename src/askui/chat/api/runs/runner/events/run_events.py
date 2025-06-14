from typing import Literal

from askui.chat.api.runs.models import Run
from askui.chat.api.runs.runner.events.event_base import EventBase


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
