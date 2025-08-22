from pathlib import Path
from typing import Callable

from askui.utils.api_utils import (
    ConflictError,
    ListResponse,
    NotFoundError,
    list_resources,
)
from askui.utils.not_given import NOT_GIVEN

from .execution_models import (
    Execution,
    ExecutionId,
    ExecutionListQuery,
    ExecutionModifyParams,
)


def _build_execution_filter_fn(
    query: ExecutionListQuery,
) -> Callable[[Execution], bool]:
    def filter_fn(execution: Execution) -> bool:
        return (
            (query.feature == NOT_GIVEN or execution.feature == query.feature)
            and (query.scenario == NOT_GIVEN or execution.scenario == query.scenario)
            and (query.example == NOT_GIVEN or execution.example == query.example)
        )

    return filter_fn


class ExecutionService:
    """Service for managing Execution resources with filesystem persistence."""

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir
        self._executions_dir = base_dir / "executions"

    def _get_execution_path(self, execution_id: ExecutionId, new: bool = False) -> Path:
        execution_path = self._executions_dir / f"{execution_id}.json"
        exists = execution_path.exists()
        if new and exists:
            error_msg = f"Execution {execution_id} already exists"
            raise ConflictError(error_msg)
        if not new and not exists:
            error_msg = f"Execution {execution_id} not found"
            raise NotFoundError(error_msg)
        return execution_path

    def list_(self, query: ExecutionListQuery) -> ListResponse[Execution]:
        return list_resources(
            base_dir=self._executions_dir,
            query=query,
            resource_type=Execution,
            filter_fn=_build_execution_filter_fn(query),
        )

    def retrieve(self, execution_id: ExecutionId) -> Execution:
        try:
            execution_path = self._get_execution_path(execution_id)
            return Execution.model_validate_json(execution_path.read_text())
        except FileNotFoundError as e:
            error_msg = f"Execution {execution_id} not found"
            raise NotFoundError(error_msg) from e

    def create(self, execution: Execution) -> Execution:
        self._save(execution, new=True)
        return execution

    def modify(
        self, execution_id: ExecutionId, params: ExecutionModifyParams
    ) -> Execution:
        execution = self.retrieve(execution_id)
        modified = execution.modify(params)
        return self._save(modified)

    def delete(self, execution_id: ExecutionId) -> None:
        try:
            self._get_execution_path(execution_id).unlink()
        except FileNotFoundError as e:
            error_msg = f"Execution {execution_id} not found"
            raise NotFoundError(error_msg) from e

    def _save(self, execution: Execution, new: bool = False) -> Execution:
        self._executions_dir.mkdir(parents=True, exist_ok=True)
        execution_file = self._get_execution_path(execution.id, new=new)
        execution_file.write_text(execution.model_dump_json(), encoding="utf-8")
        return execution
