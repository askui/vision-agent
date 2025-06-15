import logging
import queue
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from askui.agent import VisionAgent
from askui.chat.api.messages.service import MessageCreateRequest, MessageService
from askui.chat.api.models import MAX_MESSAGES_PER_THREAD, ListQuery
from askui.chat.api.runs.models import Run, RunError
from askui.chat.api.runs.runner.events.done_events import DoneEvent
from askui.chat.api.runs.runner.events.error_events import (
    ErrorEvent,
    ErrorEventData,
    ErrorEventDataError,
)
from askui.chat.api.runs.runner.events.events import Events
from askui.chat.api.runs.runner.events.message_events import MessageEvent
from askui.chat.api.runs.runner.events.run_events import RunEvent
from askui.models.models import ModelName
from askui.models.shared.computer_agent_cb_param import OnMessageCbParam
from askui.models.shared.computer_agent_message_param import (
    Base64ImageSourceParam,
    ImageBlockParam,
    MessageParam,
    TextBlockParam,
)
from askui.tools.pynput.pynput_agent_os import PynputAgentOs
from askui.utils.image_utils import ImageSource

if TYPE_CHECKING:
    from askui.tools.agent_os import InputEvent

logger = logging.getLogger(__name__)


ASKUI_VISION_AGENT_ID = "asst_ge3tiojsga3dgnruge3di2u5ov36shedkcslxnmca"
HUMAN_AGENT_ID = "asst_ge3tiojsga3dgnruge3di2u5ov36shedkcslxnmcb"


class Runner:
    def __init__(self, run: Run, base_dir: Path) -> None:
        self._run = run
        self._base_dir = base_dir
        self._runs_dir = base_dir / "runs"
        self._msg_service = MessageService(self._base_dir)
        self._agent_os = PynputAgentOs()

    def _run_human_agent(self, event_queue: queue.Queue[Events]) -> None:
        message = self._msg_service.create(
            thread_id=self._run.thread_id,
            request=MessageCreateRequest(
                role="user",
                content=[
                    TextBlockParam(
                        type="text",
                        text="Let me take over and show you what I want you to do...",
                    ),
                ],
                run_id=self._run.id,
            ),
        )
        event_queue.put(
            MessageEvent(
                data=message,
                event="thread.message.created",
            )
        )
        self._agent_os.start_listening()
        screenshot = self._agent_os.screenshot()
        image_src = ImageSource(screenshot)
        recorded_events: list[InputEvent] = []
        while True:
            updated_run = self._retrieve_run()
            if self._should_abort(updated_run):
                break
            event = self._agent_os.poll_event()
            if event and not event.pressed:
                recorded_events.append(event)
                button = (
                    f'the "{event.button}" mouse button'
                    if event.button != "unknown"
                    else "a mouse button"
                )
                message = self._msg_service.create(
                    thread_id=self._run.thread_id,
                    request=MessageCreateRequest(
                        role="user",
                        content=[
                            ImageBlockParam(
                                type="image",
                                source=Base64ImageSourceParam(
                                    data=image_src.to_base64(),
                                    media_type="image/png",
                                ),
                            ),
                            TextBlockParam(
                                type="text",
                                text=f"I moved the mouse to x={event.x}, y={event.y} and clicked {button}.",
                            ),
                        ],
                        run_id=self._run.id,
                    ),
                )
                event_queue.put(
                    MessageEvent(
                        data=message,
                        event="thread.message.created",
                    )
                )
            screenshot = self._agent_os.screenshot()
            image_src = ImageSource(screenshot)
            time.sleep(0.25)
        self._agent_os.stop_listening()
        if len(recorded_events) == 0:
            text = "Nevermind, I didn't do anything."
        else:
            text = (
                "Can you describe what I did so that I know "
                "you understand what to do next time when I ask you to do it? "
                "Feel free to ask me questions if you don't understand what I did."
            )
        message = self._msg_service.create(
            thread_id=self._run.thread_id,
            request=MessageCreateRequest(
                role="user",
                content=[
                    TextBlockParam(
                        type="text",
                        text=text,
                    )
                ],
                run_id=self._run.id,
            ),
        )
        event_queue.put(
            MessageEvent(
                data=message,
                event="thread.message.created",
            )
        )

    def _run_askui_vision_agent(self, event_queue: queue.Queue[Events]) -> None:
        messages: list[MessageParam] = [
            MessageParam(
                role=msg.role,
                content=msg.content,
            )
            for msg in self._msg_service.list_(
                thread_id=self._run.thread_id,
                query=ListQuery(limit=MAX_MESSAGES_PER_THREAD, order="asc"),
            )
        ]

        def on_message(
            on_message_cb_param: OnMessageCbParam,
        ) -> MessageParam | None:
            message = self._msg_service.create(
                thread_id=self._run.thread_id,
                request=MessageCreateRequest(
                    assistant_id=self._run.assistant_id
                    if on_message_cb_param.message.role == "assistant"
                    else None,
                    role=on_message_cb_param.message.role,
                    content=on_message_cb_param.message.content,
                    run_id=self._run.id,
                ),
            )
            event_queue.put(
                MessageEvent(
                    data=message,
                    event="thread.message.created",
                )
            )
            updated_run = self._retrieve_run()
            if self._should_abort(updated_run):
                return None
            return on_message_cb_param.message

        with VisionAgent() as agent:
            agent.act(
                messages,
                on_message=on_message,
                model=ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022,
            )

    def run(
        self,
        event_queue: queue.Queue[Events],
    ) -> None:
        self._mark_run_as_started()
        event_queue.put(
            RunEvent(
                data=self._run,
                event="thread.run.in_progress",
            )
        )
        try:
            if self._run.assistant_id == HUMAN_AGENT_ID:
                self._run_human_agent(event_queue)
            elif self._run.assistant_id == ASKUI_VISION_AGENT_ID:
                self._run_askui_vision_agent(event_queue)
            updated_run = self._retrieve_run()
            if updated_run.status == "in_progress":
                updated_run.completed_at = datetime.now(tz=timezone.utc)
                self._update_run_file(updated_run)
                event_queue.put(
                    RunEvent(
                        data=updated_run,
                        event="thread.run.completed",
                    )
                )
            if updated_run.status == "cancelling":
                event_queue.put(
                    RunEvent(
                        data=updated_run,
                        event="thread.run.cancelling",
                    )
                )
                updated_run.cancelled_at = datetime.now(tz=timezone.utc)
                self._update_run_file(updated_run)
                event_queue.put(
                    RunEvent(
                        data=updated_run,
                        event="thread.run.cancelled",
                    )
                )
            if updated_run.status == "expired":
                event_queue.put(
                    RunEvent(
                        data=updated_run,
                        event="thread.run.expired",
                    )
                )
            event_queue.put(DoneEvent())
        except Exception as e:  # noqa: BLE001
            logger.exception("Exception in runner: %s", e)
            updated_run = self._retrieve_run()
            updated_run.failed_at = datetime.now(tz=timezone.utc)
            updated_run.last_error = RunError(message=str(e), code="server_error")
            self._update_run_file(updated_run)
            event_queue.put(
                RunEvent(
                    data=updated_run,
                    event="thread.run.failed",
                )
            )
            event_queue.put(
                ErrorEvent(
                    data=ErrorEventData(error=ErrorEventDataError(message=str(e)))
                )
            )

    def _mark_run_as_started(self) -> None:
        self._run.started_at = datetime.now(tz=timezone.utc)
        self._update_run_file(self._run)

    def _should_abort(self, run: Run) -> bool:
        return run.status in ("cancelled", "cancelling", "expired")

    def _update_run_file(self, run: Run) -> None:
        run_file = self._runs_dir / f"{run.thread_id}__{run.id}.json"
        with run_file.open("w") as f:
            f.write(run.model_dump_json())

    def _retrieve_run(self) -> Run:
        run_file = self._runs_dir / f"{self._run.thread_id}__{self._run.id}.json"
        with run_file.open("r") as f:
            return Run.model_validate_json(f.read())
