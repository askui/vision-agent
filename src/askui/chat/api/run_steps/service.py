from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Sequence

from pydantic import AwareDatetime, BaseModel, Field, computed_field

from askui.chat.api.models import Event
from askui.chat.api.utils import generate_time_ordered_id

RunStepStatus = Literal[
    "in_progress",
    "completed",
    "failed",
    "cancelled",
    "expired",
]


class RunStepError(BaseModel):
    """Error details for a failed run step."""

    message: str
    code: Literal["server_error", "rate_limit_exceeded"]


class RunStepDetailsMessageCreation


class RunStepDetailsMessageCreation(BaseModel):
    """Details about the message creation run step."""

    type: Literal["message_creation"] = "message_creation"
    message_creation: dict


class RunStepDetailsToolCalls(BaseModel):
    """Details about the tool calls run step."""

    type: Literal["tool_calls"] = "tool_calls"
    tool_calls: list[dict]


RunStepDetails = RunStepDetailsMessageCreation | RunStepDetailsToolCalls


class RunStep(BaseModel):
    """A step in a run's execution."""

    id: str = Field(default_factory=lambda: generate_time_ordered_id("step"))
    run_id: str
    thread_id: str
    assistant_id: str
    created_at: AwareDatetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    completed_at: AwareDatetime | None = None
    cancelled_at: AwareDatetime | None = None
    expired_at: AwareDatetime | None = None
    failed_at: AwareDatetime | None = None
    last_error: RunStepError | None = None
    type: Literal["message_creation", "tool_calls"]
    step_details: RunStepDetails
    object: Literal["thread.run.step"] = "thread.run.step"

    @computed_field
    @property
    def status(self) -> RunStepStatus:
        if self.cancelled_at:
            return "cancelled"
        if self.failed_at:
            return "failed"
        if self.completed_at:
            return "completed"
        return "in_progress"


class RunStepListResponse(BaseModel):
    """Response model for listing run steps."""

    object: Literal["list"] = "list"
    data: Sequence[RunStep]
    first_id: str | None = None
    last_id: str | None = None
    has_more: bool = False


class RunStepEvent(Event):
    """Event for run step status changes."""

    data: RunStep
    event: Literal[
        "thread.run.step.created",
        "thread.run.step.in_progress",
        "thread.run.step.completed",
        "thread.run.step.failed",
        "thread.run.step.cancelled",
    ]


class RunStepService:
    """Service for managing run steps."""

    def __init__(self, base_dir: Path) -> None:
        """Initialize run step service.

        Args:
            base_dir: Base directory to store run step data
        """
        self._base_dir = base_dir
        self._steps_dir = base_dir / "runs" / "steps"

    def _step_path(self, thread_id: str, run_id: str, step_id: str) -> Path:
        """Get the path for a run step file.

        Args:
            thread_id: ID of the thread
            run_id: ID of the run
            step_id: ID of the step

        Returns:
            Path to the run step file
        """
        return self._steps_dir / f"{thread_id}__{run_id}__{step_id}.json"

    def create(
        self,
        thread_id: str,
        run_id: str,
        step_type: Literal["message_creation", "tool_calls"] = "message_creation",
        step_details: RunStepDetails | None = None,
    ) -> RunStep:
        """Create a new run step.

        Args:
            thread_id: ID of the thread
            run_id: ID of the run
            step_type: Type of the step
            step_details: Details about the step

        Returns:
            Created run step
        """
        step = RunStep(
            run_id=run_id,
            thread_id=thread_id,
            type=step_type,
            step_details=step_details,
        )
        self._steps_dir.mkdir(parents=True, exist_ok=True)
        self._update_step_file(step)
        return step

    def _update_step_file(self, step: RunStep) -> None:
        """Update the run step file.

        Args:
            step: Run step to update
        """
        step_file = self._step_path(step.thread_id, step.run_id, step.id)
        with step_file.open("w") as f:
            f.write(step.model_dump_json())

    def retrieve(self, thread_id: str, run_id: str, step_id: str) -> RunStep:
        """Retrieve a run step.

        Args:
            thread_id: ID of the thread
            run_id: ID of the run
            step_id: ID of the step

        Returns:
            Run step

        Raises:
            FileNotFoundError: If step doesn't exist
        """
        step_file = self._step_path(thread_id, run_id, step_id)
        if not step_file.exists():
            error_msg = f"Run step {step_id} not found in run {run_id}"
            raise FileNotFoundError(error_msg)
        with step_file.open("r") as f:
            return RunStep.model_validate_json(f.read())

    def list_(
        self,
        thread_id: str,
        run_id: str,
        limit: int | None = None,
        after: str | None = None,
        before: str | None = None,
        order: Literal["asc", "desc"] = "desc",
    ) -> RunStepListResponse:
        """List run steps.

        Args:
            thread_id: ID of the thread
            run_id: ID of the run
            limit: Optional maximum number of steps to return
            after: Optional step ID after which steps are returned
            before: Optional step ID before which steps are returned
            order: Sort order, either "asc" or "desc". Defaults to "desc"

        Returns:
            List of run steps
        """
        if not self._steps_dir.exists():
            return RunStepListResponse(data=[])

        step_files = list(self._steps_dir.glob(f"{thread_id}__{run_id}__*.json"))
        steps: list[RunStep] = []
        for f in step_files:
            with f.open("r") as file:
                steps.append(RunStep.model_validate_json(file.read()))

        # Sort by creation date
        steps = sorted(steps, key=lambda s: s.created_at, reverse=(order == "desc"))

        # Apply before/after filters
        if after:
            steps = [s for s in steps if s.id > after]
        if before:
            steps = [s for s in steps if s.id < before]

        # Apply limit if specified
        if limit is not None:
            steps = steps[:limit]

        return RunStepListResponse(
            data=steps,
            first_id=steps[0].id if steps else None,
            last_id=steps[-1].id if steps else None,
            has_more=len(step_files) > (limit or len(step_files)),
        )

    def update_status(
        self,
        thread_id: str,
        run_id: str,
        step_id: str,
        status: RunStepStatus,
        error: RunStepError | None = None,
    ) -> RunStep:
        """Update a run step's status.

        Args:
            thread_id: ID of the thread
            run_id: ID of the run
            step_id: ID of the step
            status: New status
            error: Optional error details

        Returns:
            Updated run step

        Raises:
            FileNotFoundError: If step doesn't exist
        """
        step = self.retrieve(thread_id, run_id, step_id)
        now = datetime.now(tz=timezone.utc)

        match status:
            case "in_progress":
                step.started_at = now
            case "completed":
                step.completed_at = now
            case "failed":
                step.failed_at = now
                if error:
                    step.last_error = error
            case "cancelled":
                step.cancelled_at = now
            case "expired":
                step.expired_at = now

        self._update_step_file(step)
        return step
