import asyncio
import queue
import threading
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal, Sequence, cast, overload

from pydantic import AwareDatetime, BaseModel, Field, computed_field

from askui.agent import VisionAgent
from askui.chat.api.messages.service import MessageEvent, MessageService
from askui.chat.api.models import Event
from askui.chat.api.utils import generate_time_ordered_id
from askui.models.shared.computer_agent_cb_param import OnMessageCbParam
from askui.models.shared.computer_agent_message_param import MessageParam

RunStatus = Literal[
    "queued",
    "in_progress",
    "completed",
    "cancelling",
    "cancelled",
    "failed",
    "expired",
]


class RunError(BaseModel):
    message: str
    code: Literal["server_error"]


class Run(BaseModel):
    id: str = Field(default_factory=lambda: generate_time_ordered_id("run"))
    thread_id: str
    created_at: AwareDatetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    started_at: AwareDatetime | None = None
    completed_at: AwareDatetime | None = None
    tried_cancelling_at: AwareDatetime | None = None
    cancelled_at: AwareDatetime | None = None
    expires_at: AwareDatetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc) + timedelta(minutes=10)
    )
    failed_at: AwareDatetime | None = None
    last_error: RunError | None = None
    object: Literal["run"] = "run"

    @computed_field
    @property
    def status(self) -> RunStatus:
        if self.cancelled_at:
            return "cancelled"
        if self.failed_at:
            return "failed"
        if self.completed_at:
            return "completed"
        if self.expires_at and self.expires_at < datetime.now(tz=timezone.utc):
            return "expired"
        if self.tried_cancelling_at:
            return "cancelling"
        if self.started_at:
            return "in_progress"
        return "queued"


class RunListResponse(BaseModel):
    object: Literal["list"] = "list"
    data: Sequence[Run]
    first_id: str | None = None
    last_id: str | None = None
    has_more: bool = False


class RunEvent(Event):
    data: Run
    event: Literal[
        "run.created",
        "run.started",
        "run.completed",
        "run.failed",
        "run.cancelled",
        "run.expired",
    ]


class Runner:
    def __init__(self, run: Run, base_dir: Path) -> None:
        self._run = run
        self._base_dir = base_dir
        self._runs_dir = base_dir / "runs"
        self._msg_service = MessageService(self._base_dir)

    def run(self, event_queue: queue.Queue[RunEvent | MessageEvent | None]) -> None:
        self._mark_started()
        event_queue.put(
            RunEvent(
                data=self._run,
                event="run.started",
            )
        )
        messages: list[MessageParam] = [
            cast("MessageParam", msg)
            for msg in self._msg_service.list_(self._run.thread_id).data
        ]

        def on_message(
            on_message_cb_param: OnMessageCbParam,
        ) -> MessageParam | None:
            message = self._msg_service.create(
                thread_id=self._run.thread_id,
                message=on_message_cb_param.message,
            )
            event_queue.put(
                MessageEvent(
                    data=message,
                    event="message.created",
                )
            )
            updated_run = self._retrieve_run()
            if updated_run.status == "cancelling":
                updated_run.cancelled_at = datetime.now(tz=timezone.utc)
                self._update_run_file(updated_run)
                event_queue.put(
                    RunEvent(
                        data=updated_run,
                        event="run.cancelled",
                    )
                )
                return None
            if updated_run.status == "expired":
                event_queue.put(
                    RunEvent(
                        data=updated_run,
                        event="run.expired",
                    )
                )
                return None
            return on_message_cb_param.message

        try:
            with VisionAgent() as agent:
                agent.act(messages, on_message=on_message)
            updated_run = self._retrieve_run()
            if updated_run.status == "in_progress":
                updated_run.completed_at = datetime.now(tz=timezone.utc)
                self._update_run_file(updated_run)
                event_queue.put(
                    RunEvent(
                        data=updated_run,
                        event="run.completed",
                    )
                )
        except Exception as e:  # noqa: BLE001
            updated_run = self._retrieve_run()
            updated_run.failed_at = datetime.now(tz=timezone.utc)
            updated_run.last_error = RunError(message=str(e), code="server_error")
            self._update_run_file(updated_run)
            event_queue.put(
                RunEvent(
                    data=updated_run,
                    event="run.failed",
                )
            )
        finally:
            event_queue.put(None)

    def _mark_started(self) -> None:
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


class RunService:
    """
    Service for managing runs. Handles creation, retrieval, listing, and cancellation of runs.
    """

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir
        self._runs_dir = base_dir / "runs"

    def _run_path(self, thread_id: str, run_id: str) -> Path:
        return self._runs_dir / f"{thread_id}__{run_id}.json"

    def _create_run(self, thread_id: str) -> Run:
        run = Run(thread_id=thread_id)
        self._runs_dir.mkdir(parents=True, exist_ok=True)
        self._update_run_file(run)
        return run

    @overload
    def create(self, thread_id: str, stream: Literal[False]) -> Run: ...

    @overload
    def create(
        self, thread_id: str, stream: Literal[True]
    ) -> AsyncGenerator[RunEvent | MessageEvent, None]: ...

    @overload
    def create(
        self, thread_id: str, stream: bool
    ) -> Run | AsyncGenerator[RunEvent | MessageEvent, None]: ...

    def create(
        self, thread_id: str, stream: bool
    ) -> Run | AsyncGenerator[RunEvent | MessageEvent, None]:
        run = self._create_run(thread_id)
        event_queue: queue.Queue[RunEvent | MessageEvent | None] = queue.Queue()
        runner = Runner(run, self._base_dir)
        thread = threading.Thread(target=runner.run, args=(event_queue,))
        thread.start()
        if stream:

            async def event_stream() -> AsyncGenerator[RunEvent | MessageEvent, None]:
                yield RunEvent(
                    data=run,
                    event="run.created",
                )
                loop = asyncio.get_event_loop()
                while True:
                    event = await loop.run_in_executor(None, event_queue.get)
                    if event is None:
                        break
                    yield event

            return event_stream()
        return run

    def _update_run_file(self, run: Run) -> None:
        run_file = self._run_path(run.thread_id, run.id)
        with run_file.open("w") as f:
            f.write(run.model_dump_json())

    def retrieve(self, run_id: str) -> Run:
        # Find the file by run_id
        for f in self._runs_dir.glob(f"*__{run_id}.json"):
            with f.open("r") as file:
                return Run.model_validate_json(file.read())
        error_msg = f"Run {run_id} not found"
        raise FileNotFoundError(error_msg)

    def list_(self, thread_id: str | None = None) -> RunListResponse:
        if not self._runs_dir.exists():
            return RunListResponse(data=[])
        if thread_id:
            run_files = list(self._runs_dir.glob(f"{thread_id}__*.json"))
        else:
            run_files = list(self._runs_dir.glob("*__*.json"))
        runs: list[Run] = []
        for f in run_files:
            with f.open("r") as file:
                runs.append(Run.model_validate_json(file.read()))
        runs = sorted(runs, key=lambda r: r.created_at, reverse=True)
        return RunListResponse(
            data=runs,
            first_id=runs[0].id if runs else None,
            last_id=runs[-1].id if runs else None,
            has_more=False,
        )

    def cancel(self, run_id: str) -> Run:
        run = self.retrieve(run_id)
        if run.status in ("cancelled", "cancelling", "completed", "failed", "expired"):
            return run
        run.tried_cancelling_at = datetime.now(tz=timezone.utc)
        for f in self._runs_dir.glob(f"*__{run_id}.json"):
            with f.open("w") as file:
                file.write(run.model_dump_json())
            return run
        # Find the file by run_id
        error_msg = f"Run {run_id} not found"
        raise FileNotFoundError(error_msg)
