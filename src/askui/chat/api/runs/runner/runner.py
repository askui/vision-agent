import logging
import queue
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from askui.agent import VisionAgent
from askui.chat.api.messages.message_persisted_service import (
    MessagePersisted,
    MessagePersistedService,
)
from askui.chat.api.messages.models import (
    Message,
    map_message_param_content_to_message_content,
)
from askui.chat.api.messages.service import MessagePatch, MessageService
from askui.chat.api.models import MAX_MESSAGES_PER_THREAD, ListQuery
from askui.chat.api.run_steps.models import (
    RunStep,
    RunStepDetailsMessageCreation,
    RunStepDetailsMessageCreationMessageCreation,
    RunStepError,
)
from askui.chat.api.run_steps.service import RunStepService
from askui.chat.api.runs.models import Run, RunError
from askui.chat.api.runs.runner.events.done_events import DoneEvent
from askui.chat.api.runs.runner.events.error_events import (
    ErrorEvent,
    ErrorEventData,
    ErrorEventDataError,
)
from askui.chat.api.runs.runner.events.events import Events
from askui.chat.api.runs.runner.events.message_delta_events import (
    MessageDelta,
    MessageDeltaEvent,
    MessageDeltaEventData,
    map_message_content_to_message_delta_content,
)
from askui.chat.api.runs.runner.events.message_events import MessageEvent
from askui.chat.api.runs.runner.events.run_events import RunEvent
from askui.chat.api.runs.runner.events.run_step_events import RunStepEvent
from askui.models.models import ModelName
from askui.models.shared.computer_agent_cb_param import OnMessageCbParam
from askui.models.shared.computer_agent_message_param import MessageParam

logger = logging.getLogger(__name__)


class Runner:
    def __init__(self, run: Run, base_dir: Path) -> None:
        self._run = run
        self._base_dir = base_dir
        self._runs_dir = base_dir / "runs"
        self._msg_persisted_service = MessagePersistedService(self._base_dir)
        self._msg_service = MessageService(service=self._msg_persisted_service)
        self._run_step_service = RunStepService(self._base_dir)

    def run(  # TODO Do in other process
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
        messages: list[MessageParam] = [
            MessageParam(
                role=msg.role,
                content=msg.content,
            )
            for msg in self._msg_persisted_service.list_(
                thread_id=self._run.thread_id,
                query=ListQuery(limit=MAX_MESSAGES_PER_THREAD, order="asc"),
            )
        ]  # TODO We need to transform this so that Anthropic can take it (tool use blocks only in user messages)

        index = 0
        message: MessagePersisted | None = None
        run_step: RunStep | None = None

        def on_message(
            on_message_cb_param: OnMessageCbParam,
        ) -> MessageParam | None:
            nonlocal index
            nonlocal message
            nonlocal run_step
            index += 1
            if index == 1:
                message = self._msg_persisted_service.create(
                    thread_id=self._run.thread_id,
                    message=MessagePersisted(
                        assistant_id=self._run.assistant_id,
                        role="assistant",
                        content=[],
                        run_id=self._run.id,
                        thread_id=self._run.thread_id,
                    ),
                )
                run_step = self._run_step_service.create(
                    assistant_id=self._run.assistant_id,
                    thread_id=self._run.thread_id,
                    run_id=self._run.id,
                    step_type="message_creation",
                    step_details=RunStepDetailsMessageCreation(
                        type="message_creation",
                        message_creation=RunStepDetailsMessageCreationMessageCreation(
                            message_id=message.id,
                        ),
                    ),
                )
                event_queue.put(
                    RunStepEvent(
                        data=run_step,
                        event="thread.run.step.created",
                    )
                )
                event_queue.put(
                    RunStepEvent(
                        data=run_step,
                        event="thread.run.step.in_progress",
                    )
                )
                msg = Message.from_message_persisted(message)
                event_queue.put(
                    MessageEvent(
                        data=msg,
                        event="thread.message.created",
                    )
                )
                event_queue.put(
                    MessageEvent(
                        data=msg,
                        event="thread.message.in_progress",
                    )
                )
            assert message is not None
            self._msg_persisted_service.extend_content(
                thread_id=self._run.thread_id,
                message_id=message.id,
                content=on_message_cb_param.message.content,
            )
            content = map_message_param_content_to_message_content(
                on_message_cb_param.message.content
            )
            delta_content = map_message_content_to_message_delta_content(
                content,
            )
            event_queue.put(
                MessageDeltaEvent(
                    data=MessageDeltaEventData(
                        id=message.id,
                        delta=MessageDelta(  # TODO Why can the role be changed inside the delta?
                            role=message.role,
                            content=delta_content,
                        ),
                    )
                )
            )
            updated_run = self._retrieve_run()
            if updated_run.status in ("cancelling", "expired"):
                return None
            return on_message_cb_param.message

        try:
            with VisionAgent() as agent:
                agent.act(
                    messages,
                    on_message=on_message,
                    model=ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022,  # TODO Use selected model
                )
            if message:
                msg = self._msg_service.patch(
                    thread_id=self._run.thread_id,
                    message_id=message.id,
                    patch=MessagePatch(
                        completed_at=datetime.now(tz=timezone.utc),
                    ),
                )
                event_queue.put(
                    MessageEvent(
                        data=msg,
                        event="thread.message.completed",
                    )
                )
                # TODO Incomplete message
            updated_run = self._retrieve_run()
            if updated_run.status == "in_progress":
                if run_step:
                    run_step = self._run_step_service.update_status(
                        thread_id=self._run.thread_id,
                        run_id=self._run.id,
                        step_id=run_step.id,
                        status="completed",
                        now=datetime.now(tz=timezone.utc),
                    )
                    event_queue.put(
                        RunStepEvent(
                            data=run_step,
                            event="thread.run.step.completed",
                        )
                    )
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
                if run_step:
                    run_step = self._run_step_service.update_status(
                        thread_id=self._run.thread_id,
                        run_id=self._run.id,
                        step_id=run_step.id,
                        status="cancelled",
                        now=datetime.now(tz=timezone.utc),
                    )
                    event_queue.put(
                        RunStepEvent(
                            data=run_step,
                            event="thread.run.step.cancelled",
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
                if run_step:
                    run_step = self._run_step_service.update_status(
                        thread_id=self._run.thread_id,
                        run_id=self._run.id,
                        step_id=run_step.id,
                        status="expired",
                        now=datetime.now(tz=timezone.utc),
                    )
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
            if run_step:
                run_step = self._run_step_service.update_status(
                    thread_id=self._run.thread_id,
                    run_id=self._run.id,
                    step_id=run_step.id,
                    status="failed",
                    now=updated_run.failed_at,
                    error=RunStepError(
                        message=updated_run.last_error.message,
                        code="server_error",
                    ),
                )
                event_queue.put(
                    RunStepEvent(
                        data=run_step,
                        event="thread.run.step.failed",
                    )
                )
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
            )  # TODO Not sure what to put in here

    def _mark_run_as_started(self) -> None:
        self._run.started_at = datetime.now(tz=timezone.utc)
        self._update_run_file(self._run)

    def _should_abort(self, run: Run) -> bool:
        return run.status in ("cancelled", "cancelling", "expired")

    def _update_run_file(self, run: Run) -> None:  # TODO Do in run service
        run_file = self._runs_dir / f"{run.thread_id}__{run.id}.json"
        with run_file.open("w") as f:
            f.write(run.model_dump_json())

    def _retrieve_run(self) -> Run:  # TODO Do in run service
        run_file = self._runs_dir / f"{self._run.thread_id}__{self._run.id}.json"
        with run_file.open("r") as f:
            return Run.model_validate_json(f.read())
