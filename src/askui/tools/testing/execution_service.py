from pathlib import Path

from askui.utils.api_utils import ConflictError, ListResponse, NotFoundError

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

    def find(self, query: ExecutionListQuery) -> ListResponse[Execution]:
        """List all available executions.

        Args:
            query (ExecutionListQuery): Query parameters for listing executions

        Returns:
            ListResponse[Execution]: ListResponse containing executions sorted by
                creation date
        """
        if not self._executions_dir.exists():
            return ListResponse(data=[])

        execution_files = list(self._executions_dir.glob("*.json"))
        executions: list[Execution] = []
        for f in execution_files:
            with f.open("r", encoding="utf-8") as file:
                executions.append(Execution.model_validate_json(file.read()))

        # Sort by creation date
        executions = sorted(
            executions, key=lambda e: e.created_at, reverse=(query.order == "desc")
        )

        # Apply before/after filters
        if query.after:
            executions = [e for e in executions if e.id > query.after]
        if query.before:
            executions = [e for e in executions if e.id < query.before]

        # Apply limit
        executions = executions[: query.limit]

        return ListResponse(
            data=executions,
            first_id=executions[0].id if executions else None,
            last_id=executions[-1].id if executions else None,
            has_more=len(execution_files) > query.limit,
        )

    def find_one(self, execution_id: ExecutionId) -> Execution:
        """Retrieve an execution by ID.

        Args:
            execution_id: ID of execution to retrieve

        Returns:
            Execution object

        Raises:
            FileNotFoundError: If execution doesn't exist
        """
        execution_file = self._executions_dir / f"{execution_id}.json"
        if not execution_file.exists():
            error_msg = f"Execution {execution_id} not found"
            raise FileNotFoundError(error_msg)

        with execution_file.open("r", encoding="utf-8") as f:
            return Execution.model_validate_json(f.read())

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
        """Modify an existing execution."""
        execution = self.find_one(execution_id)
        modified = execution.modify(params)
        execution_file = self._executions_dir / f"{execution_id}.json"
        with execution_file.open("w", encoding="utf-8") as f:
            f.write(modified.model_dump_json())
        return modified

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
