from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Sequence

from pydantic import AwareDatetime, BaseModel, Field, computed_field

from askui.chat.api.utils import generate_time_ordered_id

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
    expires_at: AwareDatetime | None = None
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


class RunService:
    """
    Service for managing runs. Handles creation, retrieval, listing, and cancellation of runs.
    """

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir
        self._runs_dir = base_dir / "runs"

    def _run_path(self, thread_id: str, run_id: str) -> Path:
        return self._runs_dir / f"{thread_id}__{run_id}.json"

    def create(self, thread_id: str, stream: bool) -> Run:
        run = Run(thread_id=thread_id)
        self._runs_dir.mkdir(parents=True, exist_ok=True)
        run_file = self._run_path(thread_id, run.id)
        with run_file.open("w") as f:
            f.write(run.model_dump_json())
        return run

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
