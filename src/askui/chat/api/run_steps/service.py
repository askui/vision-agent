from pathlib import Path
from typing import Literal

from askui.chat.api.models import (
    AssistantId,
    ListQuery,
    ListResponse,
    RunId,
    ThreadId,
    UnixDatetime,
)
from askui.chat.api.run_steps.models import (
    RunStep,
    RunStepDetails,
    RunStepError,
    RunStepId,
    StepType,
)


class RunStepService:
    """Service for managing run steps."""

    def __init__(self, base_dir: Path) -> None:
        """Initialize run step service.

        Args:
            base_dir: Base directory to store run step data
        """
        self._base_dir = base_dir
        self._steps_dir = base_dir / "run_steps"

    def _step_path(self, thread_id: ThreadId, run_id: RunId, step_id: str) -> Path:
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
        thread_id: ThreadId,
        run_id: RunId,
        step_type: StepType,
        step_details: RunStepDetails,
        assistant_id: AssistantId,
    ) -> RunStep:
        """Create a new run step.

        Args:
            thread_id (ThreadId): ID of the thread
            run_id (RunId): ID of the run
            step_type (StepType): Type of the step
            step_details (RunStepDetails): Details about the step
            assistant_id (AssistantId): ID of the assistant.

        Returns:
            RunStep: Created run step
        """
        step = RunStep(
            run_id=run_id,
            thread_id=thread_id,
            type=step_type,
            step_details=step_details,
            assistant_id=assistant_id,
        )
        self._steps_dir.mkdir(parents=True, exist_ok=True)
        self._update_step_file(step)
        return step

    def _update_step_file(self, step: RunStep) -> None:
        """Update the run step file.

        Args:
            step (RunStep): Run step to update
        """
        step_file = self._step_path(step.thread_id, step.run_id, step.id)
        with step_file.open("w") as f:
            f.write(step.model_dump_json())

    def retrieve(
        self, thread_id: ThreadId, run_id: RunId, step_id: RunStepId
    ) -> RunStep:
        """Retrieve a run step.

        Args:
            thread_id (ThreadId): ID of the thread
            run_id (RunId): ID of the run
            step_id (RunStepId): ID of the step

        Returns:
            RunStep: Run step

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
        thread_id: ThreadId,
        run_id: RunId,
        query: ListQuery,
    ) -> ListResponse[RunStep]:
        """List run steps.

        Args:
            thread_id (ThreadId): ID of the thread
            run_id (RunId): ID of the run
            query (ListQuery): Query parameters for listing steps

        Returns:
            RunStepListResponse: List of run steps
        """
        if not self._steps_dir.exists():
            return ListResponse(data=[])

        step_files = list(self._steps_dir.glob(f"{thread_id}__{run_id}__*.json"))
        steps: list[RunStep] = []
        for f in step_files:
            with f.open("r") as file:
                steps.append(RunStep.model_validate_json(file.read()))

        # Sort by creation date
        steps = sorted(
            steps, key=lambda s: s.created_at, reverse=(query.order == "desc")
        )

        # Apply before/after filters
        if query.after:
            steps = [s for s in steps if s.id > query.after]
        if query.before:
            steps = [s for s in steps if s.id < query.before]

        # Apply limit if specified
        if query.limit:
            steps = steps[: query.limit]

        return ListResponse(
            data=steps,
            first_id=steps[0].id if steps else None,
            last_id=steps[-1].id if steps else None,
            has_more=len(step_files) > query.limit,
        )

    def update_status(
        self,
        thread_id: ThreadId,
        run_id: RunId,
        step_id: RunStepId,
        status: Literal["completed", "failed", "cancelled", "expired"],
        now: UnixDatetime,
        error: RunStepError | None = None,
    ) -> RunStep:
        """Update a run step's status.

        Args:
            thread_id (ThreadId): ID of the thread
            run_id (RunId): ID of the run
            step_id (RunStepId): ID of the step
            status (RunStepStatus): New status
            error (RunStepError | None): Optional error details

        Returns:
            RunStep: Updated run step

        Raises:
            FileNotFoundError: If step doesn't exist
        """
        step = self.retrieve(thread_id, run_id, step_id)

        match status:
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
