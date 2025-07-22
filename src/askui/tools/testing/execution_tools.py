from pathlib import Path

import jsonref
from pydantic import BaseModel, validate_call
from typing_extensions import override

from askui.models.shared.tools import Tool
from askui.utils.api_utils import ListResponse, NotFoundError

from .execution_models import (
    Execution,
    ExecutionId,
    ExecutionListQuery,
    ExecutionModifyParams,
)
from .execution_service import ExecutionService


class ListExecutionToolInput(BaseModel):
    query: ExecutionListQuery


class ListExecutionTool(Tool):
    def __init__(self, base_dir: Path) -> None:
        super().__init__(
            name="list_executions",
            description="List executions with optional filtering",
            input_schema=jsonref.replace_refs(
                ListExecutionToolInput.model_json_schema(),
                lazy_load=False,
                proxies=False,
            ),
        )
        self._service = ExecutionService(base_dir)

    @override
    @validate_call
    def __call__(self, query: ExecutionListQuery) -> ListResponse[Execution]:
        """
        List executions with optional filtering.

        Args:
            query (ExecutionListQuery): Query parameters for filtering executions.

        Returns:
            ListResponse[Execution]: List of executions matching the query.
        """
        try:
            return self._service.list_(query=query)
        except NotFoundError as e:
            raise ValueError(str(e)) from e


class RetrieveExecutionToolInput(BaseModel):
    execution_id: ExecutionId


class RetrieveExecutionTool(Tool):
    def __init__(self, base_dir: Path) -> None:
        super().__init__(
            name="retrieve_execution",
            description="Retrieve an execution by id",
            input_schema=jsonref.replace_refs(
                RetrieveExecutionToolInput.model_json_schema(),
                lazy_load=False,
                proxies=False,
            ),
        )
        self._service = ExecutionService(base_dir)

    @override
    @validate_call
    def __call__(self, execution_id: ExecutionId) -> Execution:
        """
        Retrieve an execution by id.

        Args:
            execution_id (str): The id of the execution to retrieve.

        Returns:
            Execution: The execution object.
        """
        return self._service.retrieve(execution_id=execution_id)


class CreateExecutionToolInput(BaseModel):
    execution: Execution


class CreateExecutionTool(Tool):
    def __init__(self, base_dir: Path) -> None:
        super().__init__(
            name="create_execution",
            description="Create a new execution",
            input_schema=jsonref.replace_refs(
                CreateExecutionToolInput.model_json_schema(),
                lazy_load=False,
                proxies=False,
            ),
        )
        self._service = ExecutionService(base_dir)

    @override
    @validate_call
    def __call__(self, execution: Execution) -> Execution:
        """
        Create a new execution.

        Args:
            execution (Execution): The execution object to create.

        Returns:
            Execution: The created execution object.
        """
        return self._service.create(execution=execution)


class ModifyExecutionToolInput(BaseModel):
    execution_id: ExecutionId
    params: ExecutionModifyParams


class ModifyExecutionTool(Tool):
    def __init__(self, base_dir: Path) -> None:
        super().__init__(
            name="modify_execution",
            description="Modify an existing execution",
            input_schema=jsonref.replace_refs(
                ModifyExecutionToolInput.model_json_schema(),
                lazy_load=False,
                proxies=False,
            ),
        )
        self._service = ExecutionService(base_dir)

    @override
    @validate_call
    def __call__(
        self, execution_id: ExecutionId, params: ExecutionModifyParams
    ) -> Execution:
        """
        Modify an existing execution.

        Args:
            execution_id (str): The id of the execution to modify.
            params (ExecutionModifyParams): The parameters to modify.

        Returns:
            Execution: The modified execution object.
        """
        return self._service.modify(execution_id=execution_id, params=params)


class DeleteExecutionToolInput(BaseModel):
    execution_id: ExecutionId


class DeleteExecutionTool(Tool):
    def __init__(self, base_dir: Path) -> None:
        super().__init__(
            name="delete_execution",
            description="Delete an execution",
            input_schema=jsonref.replace_refs(
                DeleteExecutionToolInput.model_json_schema(),
                lazy_load=False,
                proxies=False,
            ),
        )
        self._service = ExecutionService(base_dir)

    @override
    @validate_call
    def __call__(self, execution_id: ExecutionId) -> None:
        """
        Delete an execution by id.

        Args:
            execution_id (str): The id of the execution to delete.
        """
        self._service.delete(execution_id=execution_id)
