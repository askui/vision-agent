from pydantic import TypeAdapter

from askui.chat.api.runs.events.done_events import DoneEvent
from askui.chat.api.runs.events.error_events import ErrorEvent
from askui.chat.api.runs.events.message_events import MessageEvent
from askui.chat.api.runs.events.run_events import RunEvent

Event = DoneEvent | ErrorEvent | MessageEvent | RunEvent

EventAdapter: TypeAdapter[Event] = TypeAdapter(Event)
