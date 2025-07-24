from pathlib import Path

from pydantic import ValidationError

from askui.utils.api_utils import (
    ConflictError,
    ListResponse,
    NotFoundError,
    list_resource_paths,
)
from askui.utils.not_given import NOT_GIVEN

from .execution_models import (
    Execution,
    ExecutionId,
    ExecutionListQuery,
    ExecutionModifyParams,
)


class ExecutionService:
    """
    Service for managing Execution resources with filesystem persistence.

    Args:
        base_dir (Path): Base directory for storing execution data.
    """

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir
        self._executions_dir = base_dir / "executions"
        self._executions_dir.mkdir(parents=True, exist_ok=True)

    def list_(
        self,
        query: ExecutionListQuery,
    ) -> ListResponse[Execution]:
        execution_paths = list_resource_paths(self._executions_dir, query)
        executions: list[Execution] = []
        for f in execution_paths:
            try:
                execution = Execution.model_validate_json(f.read_text())
                if (
                    (query.feature == NOT_GIVEN or execution.feature == query.feature)
                    and (
                        query.scenario == NOT_GIVEN
                        or execution.scenario == query.scenario
                    )
                    and (
                        query.example == NOT_GIVEN or execution.example == query.example
                    )
                ):
                    executions.append(execution)
            except ValidationError:  # noqa: PERF203
                continue
        has_more = len(executions) > query.limit
        executions = executions[: query.limit]
        return ListResponse(
            data=executions,
            first_id=executions[0].id if executions else None,
            last_id=executions[-1].id if executions else None,
            has_more=has_more,
        )

    def retrieve(self, execution_id: ExecutionId) -> Execution:
        execution_file = self._executions_dir / f"{execution_id}.json"
        if not execution_file.exists():
            error_msg = f"Execution {execution_id} not found"
            raise NotFoundError(error_msg)
        return Execution.model_validate_json(execution_file.read_text())

    def create(self, execution: Execution) -> Execution:
        execution_file = self._executions_dir / f"{execution.id}.json"
        if execution_file.exists():
            error_msg = f"Execution {execution.id} already exists"
            raise ConflictError(error_msg)
        execution_file.write_text(execution.model_dump_json())
        return execution

    def modify(
        self, execution_id: ExecutionId, params: ExecutionModifyParams
    ) -> Execution:
        execution = self.retrieve(execution_id)
        modified = execution.modify(params)
        return self._save(modified)

    def _save(self, execution: Execution) -> Execution:
        execution_file = self._executions_dir / f"{execution.id}.json"
        execution_file.write_text(execution.model_dump_json())
        return execution

    def delete(self, execution_id: ExecutionId) -> None:
        execution_file = self._executions_dir / f"{execution_id}.json"
        if not execution_file.exists():
            error_msg = f"Execution {execution_id} not found"
            raise NotFoundError(error_msg)
        execution_file.unlink()
