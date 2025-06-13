from askui.chat.api.runs.runner.events.done_events import DoneEvent
from askui.chat.api.runs.runner.events.error_events import ErrorEvent
from askui.chat.api.runs.runner.events.message_delta_events import MessageDeltaEvent
from askui.chat.api.runs.runner.events.message_events import MessageEvent
from askui.chat.api.runs.runner.events.run_events import RunEvent
from askui.chat.api.runs.runner.events.run_step_events import (
    RunStepDeltaEvent,
    RunStepEvent,
)

Events = (
    DoneEvent
    | ErrorEvent
    | MessageDeltaEvent
    | MessageEvent
    | RunEvent
    | RunStepDeltaEvent
    | RunStepEvent
)
