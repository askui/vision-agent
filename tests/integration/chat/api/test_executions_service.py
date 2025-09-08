"""Integration tests for execution service with status transition validation."""

import uuid
from pathlib import Path

import pytest

from askui.chat.api.executions.models import (
    Execution,
    ExecutionCreateParams,
    ExecutionModifyParams,
    ExecutionStatus,
    InvalidStatusTransitionError,
)
from askui.chat.api.executions.service import ExecutionService
from askui.chat.api.models import WorkspaceId
from askui.utils.api_utils import ListQuery, NotFoundError


class TestExecutionService:
    """Test execution service with status transition validation."""

    @pytest.fixture
    def execution_service(self, tmp_path: Path) -> ExecutionService:
        """Create an execution service for testing."""
        return ExecutionService(tmp_path)

    @pytest.fixture
    def workspace_id(self) -> WorkspaceId:
        """Create a test workspace ID."""
        return uuid.uuid4()

    @pytest.fixture
    def create_params(self) -> ExecutionCreateParams:
        """Create sample execution creation parameters."""
        return ExecutionCreateParams(
            workflow="wf_test123",
            thread="thread_test123",
            status=ExecutionStatus.PENDING,
        )

    @pytest.fixture
    def sample_execution(
        self,
        execution_service: ExecutionService,
        workspace_id: WorkspaceId,
        create_params: ExecutionCreateParams,
    ) -> Execution:
        """Create a sample execution for testing."""
        return execution_service.create(workspace_id=workspace_id, params=create_params)

    def test_create_execution_success(
        self,
        execution_service: ExecutionService,
        workspace_id: WorkspaceId,
        create_params: ExecutionCreateParams,
    ) -> None:
        """Test successful execution creation."""
        execution = execution_service.create(
            workspace_id=workspace_id, params=create_params
        )

        assert execution.workflow == create_params.workflow
        assert execution.thread == create_params.thread
        assert execution.status == create_params.status
        assert execution.workspace_id == workspace_id
        assert execution.object == "execution"
        assert execution.id.startswith("exec_")
        assert execution.created_at is not None

    def test_retrieve_execution_success(
        self,
        execution_service: ExecutionService,
        workspace_id: WorkspaceId,
        sample_execution: Execution,
    ) -> None:
        """Test successful execution retrieval."""
        retrieved = execution_service.retrieve(
            workspace_id=workspace_id, execution_id=sample_execution.id
        )

        assert retrieved.id == sample_execution.id
        assert retrieved.workflow == sample_execution.workflow
        assert retrieved.thread == sample_execution.thread
        assert retrieved.status == sample_execution.status
        assert retrieved.workspace_id == sample_execution.workspace_id

    def test_retrieve_execution_not_found(
        self, execution_service: ExecutionService, workspace_id: WorkspaceId
    ) -> None:
        """Test retrieving non-existent execution raises NotFoundError."""
        with pytest.raises(NotFoundError) as exc_info:
            execution_service.retrieve(
                workspace_id=workspace_id, execution_id="exec_nonexistent123"
            )

        assert "not found" in str(exc_info.value)

    def test_modify_execution_valid_transition(
        self,
        execution_service: ExecutionService,
        workspace_id: WorkspaceId,
        sample_execution: Execution,
    ) -> None:
        """Test successful execution modification with valid status transition."""
        modify_params = ExecutionModifyParams(status=ExecutionStatus.PASSED)
        modified = execution_service.modify(
            workspace_id=workspace_id,
            execution_id=sample_execution.id,
            params=modify_params,
        )

        assert modified.id == sample_execution.id
        assert modified.status == ExecutionStatus.PASSED
        assert modified.workflow == sample_execution.workflow
        assert modified.thread == sample_execution.thread

    def test_modify_execution_invalid_transition_raises_error(
        self,
        execution_service: ExecutionService,
        workspace_id: WorkspaceId,
        sample_execution: Execution,
    ) -> None:
        """Test that invalid status transition raises InvalidStatusTransitionError."""
        # First transition to a final state
        modify_params = ExecutionModifyParams(status=ExecutionStatus.PASSED)
        execution_service.modify(
            workspace_id=workspace_id,
            execution_id=sample_execution.id,
            params=modify_params,
        )

        # Try to transition from final state to non-final state
        invalid_params = ExecutionModifyParams(status=ExecutionStatus.PENDING)
        with pytest.raises(InvalidStatusTransitionError) as exc_info:
            execution_service.modify(
                workspace_id=workspace_id,
                execution_id=sample_execution.id,
                params=invalid_params,
            )

        assert exc_info.value.from_status == ExecutionStatus.PASSED
        assert exc_info.value.to_status == ExecutionStatus.PENDING
        assert "Invalid status transition from 'passed' to 'pending'" in str(
            exc_info.value
        )

    def test_modify_execution_same_status_allowed(
        self,
        execution_service: ExecutionService,
        workspace_id: WorkspaceId,
        sample_execution: Execution,
    ) -> None:
        """Test that modifying to the same status is allowed (no-op)."""
        modify_params = ExecutionModifyParams(status=ExecutionStatus.PENDING)
        modified = execution_service.modify(
            workspace_id=workspace_id,
            execution_id=sample_execution.id,
            params=modify_params,
        )

        assert modified.status == ExecutionStatus.PENDING
        assert modified.id == sample_execution.id

    def test_modify_execution_not_found(
        self, execution_service: ExecutionService, workspace_id: WorkspaceId
    ) -> None:
        """Test modifying non-existent execution raises NotFoundError."""
        modify_params = ExecutionModifyParams(status=ExecutionStatus.PASSED)

        with pytest.raises(NotFoundError) as exc_info:
            execution_service.modify(
                workspace_id=workspace_id,
                execution_id="exec_nonexistent123",
                params=modify_params,
            )

        assert "not found" in str(exc_info.value)

    def test_list_executions_success(
        self,
        execution_service: ExecutionService,
        workspace_id: WorkspaceId,
        sample_execution: Execution,
    ) -> None:
        """Test successful execution listing."""
        query = ListQuery(limit=10, order="desc")
        result = execution_service.list_(workspace_id=workspace_id, query=query)

        assert result.object == "list"
        assert len(result.data) >= 1
        assert any(execution.id == sample_execution.id for execution in result.data)

    def test_list_executions_with_filters(
        self,
        execution_service: ExecutionService,
        workspace_id: WorkspaceId,
        create_params: ExecutionCreateParams,
    ) -> None:
        """Test execution listing with workflow and thread filters."""
        # Create multiple executions with different workflows and threads
        execution_service.create(workspace_id=workspace_id, params=create_params)

        different_params = ExecutionCreateParams(
            workflow="wf_different456",
            thread="thread_different456",
            status=ExecutionStatus.PENDING,
        )
        execution_service.create(workspace_id=workspace_id, params=different_params)

        query = ListQuery(limit=10, order="desc")

        # Test workflow filter
        workflow_filtered = execution_service.list_(
            workspace_id=workspace_id,
            query=query,
            workflow_id=create_params.workflow,
        )
        assert len(workflow_filtered.data) >= 1
        assert all(
            exec.workflow == create_params.workflow for exec in workflow_filtered.data
        )

        # Test thread filter
        thread_filtered = execution_service.list_(
            workspace_id=workspace_id,
            query=query,
            thread_id=create_params.thread,
        )
        assert len(thread_filtered.data) >= 1
        assert all(exec.thread == create_params.thread for exec in thread_filtered.data)

        # Test combined filters
        combined_filtered = execution_service.list_(
            workspace_id=workspace_id,
            query=query,
            workflow_id=create_params.workflow,
            thread_id=create_params.thread,
        )
        assert len(combined_filtered.data) >= 1
        assert all(
            exec.workflow == create_params.workflow
            and exec.thread == create_params.thread
            for exec in combined_filtered.data
        )

    def test_persistence_across_service_instances(
        self,
        tmp_path: Path,
        workspace_id: WorkspaceId,
        create_params: ExecutionCreateParams,
    ) -> None:
        """Test that executions persist across service instances."""
        # Create execution with first service instance
        service1 = ExecutionService(tmp_path)
        execution = service1.create(workspace_id=workspace_id, params=create_params)

        # Retrieve with second service instance
        service2 = ExecutionService(tmp_path)
        retrieved = service2.retrieve(
            workspace_id=workspace_id, execution_id=execution.id
        )

        assert retrieved.id == execution.id
        assert retrieved.status == execution.status
        assert retrieved.workflow == execution.workflow

    def test_modify_execution_persists_changes(
        self,
        tmp_path: Path,
        workspace_id: WorkspaceId,
        create_params: ExecutionCreateParams,
    ) -> None:
        """Test that execution modifications are persisted to filesystem."""
        # Create execution
        service1 = ExecutionService(tmp_path)
        execution = service1.create(workspace_id=workspace_id, params=create_params)

        # Modify execution
        modify_params = ExecutionModifyParams(status=ExecutionStatus.PASSED)
        service1.modify(
            workspace_id=workspace_id,
            execution_id=execution.id,
            params=modify_params,
        )

        # Verify changes persist with new service instance
        service2 = ExecutionService(tmp_path)
        retrieved = service2.retrieve(
            workspace_id=workspace_id, execution_id=execution.id
        )
        assert retrieved.status == ExecutionStatus.PASSED

    @pytest.mark.parametrize(
        "valid_transition",
        [
            (ExecutionStatus.PENDING, ExecutionStatus.INCOMPLETE),
            (ExecutionStatus.PENDING, ExecutionStatus.PASSED),
            (ExecutionStatus.PENDING, ExecutionStatus.FAILED),
            (ExecutionStatus.PENDING, ExecutionStatus.SKIPPED),
            (ExecutionStatus.INCOMPLETE, ExecutionStatus.PENDING),
            (ExecutionStatus.INCOMPLETE, ExecutionStatus.PASSED),
            (ExecutionStatus.INCOMPLETE, ExecutionStatus.FAILED),
            (ExecutionStatus.INCOMPLETE, ExecutionStatus.SKIPPED),
        ],
    )
    def test_valid_transitions_parametrized(
        self,
        execution_service: ExecutionService,
        workspace_id: WorkspaceId,
        valid_transition: tuple[ExecutionStatus, ExecutionStatus],
    ) -> None:
        """Test all valid status transitions (parametrized)."""
        from_status, to_status = valid_transition

        # Create execution with initial status
        create_params = ExecutionCreateParams(
            workflow="wf_test123",
            thread="thread_test123",
            status=from_status,
        )
        execution = execution_service.create(
            workspace_id=workspace_id, params=create_params
        )

        # Modify to target status
        modify_params = ExecutionModifyParams(status=to_status)
        modified = execution_service.modify(
            workspace_id=workspace_id,
            execution_id=execution.id,
            params=modify_params,
        )

        assert modified.status == to_status

    @pytest.mark.parametrize(
        "invalid_transition",
        [
            (ExecutionStatus.PASSED, ExecutionStatus.PENDING),
            (ExecutionStatus.PASSED, ExecutionStatus.INCOMPLETE),
            (ExecutionStatus.PASSED, ExecutionStatus.FAILED),
            (ExecutionStatus.PASSED, ExecutionStatus.SKIPPED),
            (ExecutionStatus.FAILED, ExecutionStatus.PENDING),
            (ExecutionStatus.FAILED, ExecutionStatus.INCOMPLETE),
            (ExecutionStatus.FAILED, ExecutionStatus.PASSED),
            (ExecutionStatus.FAILED, ExecutionStatus.SKIPPED),
            (ExecutionStatus.SKIPPED, ExecutionStatus.PENDING),
            (ExecutionStatus.SKIPPED, ExecutionStatus.INCOMPLETE),
            (ExecutionStatus.SKIPPED, ExecutionStatus.PASSED),
            (ExecutionStatus.SKIPPED, ExecutionStatus.FAILED),
        ],
    )
    def test_invalid_transitions_parametrized(
        self,
        execution_service: ExecutionService,
        workspace_id: WorkspaceId,
        invalid_transition: tuple[ExecutionStatus, ExecutionStatus],
    ) -> None:
        """Test all invalid status transitions (parametrized)."""
        from_status, to_status = invalid_transition

        # Create execution with initial status
        create_params = ExecutionCreateParams(
            workflow="wf_test123",
            thread="thread_test123",
            status=from_status,
        )
        execution = execution_service.create(
            workspace_id=workspace_id, params=create_params
        )

        # Try to modify to invalid target status
        modify_params = ExecutionModifyParams(status=to_status)
        with pytest.raises(InvalidStatusTransitionError) as exc_info:
            execution_service.modify(
                workspace_id=workspace_id,
                execution_id=execution.id,
                params=modify_params,
            )

        assert exc_info.value.from_status == from_status
        assert exc_info.value.to_status == to_status
