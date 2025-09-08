import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from askui.chat.api.models import ExecutionId, ThreadId, WorkspaceId, WorkspaceResource
from askui.chat.api.workflows.models import WorkflowId
from askui.utils.datetime_utils import now
from askui.utils.id_utils import generate_time_ordered_id
from askui.utils.not_given import NOT_GIVEN, BaseModelWithNotGiven, NotGiven


class ExecutionStatus(str, Enum):
    """The current status of the workflow execution."""

    PASSED = "passed"
    FAILED = "failed"
    PENDING = "pending"
    INCOMPLETE = "incomplete"
    SKIPPED = "skipped"


class InvalidStatusTransitionError(ValueError):
    """Raised when attempting an invalid status transition."""

    def __init__(
        self, from_status: ExecutionStatus, to_status: ExecutionStatus
    ) -> None:
        error_msg = f"Invalid status transition from '{from_status}' to '{to_status}'"
        super().__init__(error_msg)
        self.from_status = from_status
        self.to_status = to_status


# Status transition map: defines which status transitions are allowed
_STATUS_TRANSITIONS: dict[ExecutionStatus, set[ExecutionStatus]] = {
    # PENDING can transition to any status except PENDING (to avoid no-op updates)
    ExecutionStatus.PENDING: {
        ExecutionStatus.INCOMPLETE,
        ExecutionStatus.PASSED,
        ExecutionStatus.FAILED,
        ExecutionStatus.SKIPPED,
    },
    # INCOMPLETE can only transition to final states (no going backwards)
    ExecutionStatus.INCOMPLETE: {
        ExecutionStatus.PASSED,
        ExecutionStatus.FAILED,
        ExecutionStatus.SKIPPED,
    },
    # Final states (PASSED, FAILED, SKIPPED) cannot transition to other states
    ExecutionStatus.PASSED: set(),
    ExecutionStatus.FAILED: set(),
    ExecutionStatus.SKIPPED: set(),
}


def _validate_status_transition(
    from_status: ExecutionStatus, to_status: ExecutionStatus
) -> None:
    """
    Validate that a status transition is allowed.

    Args:
        from_status (ExecutionStatus): The current status.
        to_status (ExecutionStatus): The target status.

    Raises:
        InvalidStatusTransitionError: If the transition is not allowed.
    """
    if from_status == to_status:
        # Allow same-status updates (no-op)
        return

    allowed_transitions = _STATUS_TRANSITIONS.get(from_status, set())
    if to_status not in allowed_transitions:
        raise InvalidStatusTransitionError(from_status, to_status)


class ExecutionCreateParams(BaseModel):
    """
    Parameters for creating an execution via API.
    """

    workflow: WorkflowId
    thread: ThreadId


class ExecutionModifyParams(BaseModelWithNotGiven):
    """
    Parameters for modifying an execution via API.
    Only status can be updated.
    """

    status: ExecutionStatus | NotGiven = NOT_GIVEN


class Execution(WorkspaceResource):
    """
    A workflow execution resource in the chat API.

    Args:
        id (ExecutionId): The id of the execution. Must start with the 'exec_' prefix and be
            followed by one or more alphanumerical characters.
        object (Literal['execution']): The object type, always 'execution'.
        created_at (datetime.datetime): The creation time as a datetime.
        workflow (WorkflowId): The id of the workflow being executed. Must start with the 'wf_' prefix.
        thread (ThreadId): The id of the thread this execution is associated with. Must start with the 'thread_' prefix.
        status (ExecutionStatus): The current status of the workflow execution.
        workspace_id (WorkspaceId | None, optional): The workspace this execution belongs to.
    """

    id: ExecutionId
    object: Literal["execution"] = "execution"
    created_at: datetime.datetime
    workflow: WorkflowId
    thread: ThreadId
    status: ExecutionStatus = Field(
        ..., description="The current status of the workflow execution."
    )

    @classmethod
    def create(
        cls, workspace_id: WorkspaceId | None, params: ExecutionCreateParams
    ) -> "Execution":
        return cls(
            id=generate_time_ordered_id("exec"),
            created_at=now(),
            workspace_id=workspace_id,
            status=ExecutionStatus.PENDING,
            **params.model_dump(),
        )

    def modify(self, params: ExecutionModifyParams) -> "Execution":
        """
        Modify the execution with the provided parameters.

        Args:
            params (ExecutionModifyParams): The parameters to update.

        Returns:
            Execution: A new execution instance with the updated values.

        Raises:
            InvalidStatusTransitionError: If attempting an invalid status transition.
        """
        update_data = {
            k: v for k, v in params.model_dump().items() if v is not NOT_GIVEN
        }

        # Validate status transition if status is being updated
        if "status" in update_data:
            new_status = update_data["status"]
            _validate_status_transition(self.status, new_status)

        return Execution.model_validate(
            {
                **self.model_dump(),
                **update_data,
            }
        )
