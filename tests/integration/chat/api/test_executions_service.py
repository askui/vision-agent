"""Integration tests for execution service with status transition validation."""

import uuid
from pathlib import Path
from unittest.mock import Mock

import pytest
import pytest_asyncio

from askui.chat.api.assistants.service import AssistantService
from askui.chat.api.executions.models import (
    Execution,
    ExecutionCreateParams,
    ExecutionModifyParams,
    ExecutionStatus,
    InvalidStatusTransitionError,
)
from askui.chat.api.executions.service import ExecutionService
from askui.chat.api.messages.service import MessageService
from askui.chat.api.models import WorkspaceId
from askui.chat.api.runs.service import RunService
from askui.chat.api.threads.facade import ThreadFacade
from askui.chat.api.threads.service import ThreadService
from askui.chat.api.workflows.models import WorkflowCreateParams
from askui.chat.api.workflows.service import WorkflowService
from askui.utils.api_utils import ListQuery, NotFoundError


class TestExecutionService:
    """Test execution service with status transition validation."""

    @pytest.fixture
    def workflow_service(self, tmp_path: Path) -> WorkflowService:
        """Create a workflow service for testing."""
        return WorkflowService(tmp_path)

    @pytest.fixture
    def assistant_service(self, tmp_path: Path) -> AssistantService:
        """Create an assistant service for testing."""
        return AssistantService(tmp_path)

    @pytest.fixture
    def mock_mcp_config_service(self) -> Mock:
        """Create a mock MCP config service for testing."""
        mock_service = Mock()
        mock_service.list_.return_value.data = []
        return mock_service

    @pytest.fixture
    def mock_message_translator(self) -> Mock:
        """Create a mock message translator for testing."""
        return Mock()

    @pytest.fixture
    def thread_service(
        self,
        tmp_path: Path,
        message_service: MessageService,
        run_service: RunService,
    ) -> ThreadService:
        """Create a thread service for testing."""
        return ThreadService(tmp_path, message_service, run_service)

    @pytest.fixture
    def message_service(self, tmp_path: Path) -> MessageService:
        """Create a message service for testing."""
        return MessageService(tmp_path)

    @pytest.fixture
    def run_service(
        self,
        tmp_path: Path,
        assistant_service: AssistantService,
        mock_mcp_config_service: Mock,
        message_service: MessageService,
        mock_message_translator: Mock,
    ) -> RunService:
        """Create a run service for testing."""
        return RunService(
            tmp_path,
            assistant_service,
            mock_mcp_config_service,
            message_service,
            mock_message_translator,
        )

    @pytest.fixture
    def thread_facade(
        self,
        thread_service: ThreadService,
        message_service: MessageService,
        run_service: RunService,
    ) -> ThreadFacade:
        """Create a thread facade for testing."""
        return ThreadFacade(thread_service, message_service, run_service)

    @pytest.fixture
    def execution_service(
        self,
        tmp_path: Path,
        workflow_service: WorkflowService,
        thread_facade: ThreadFacade,
    ) -> ExecutionService:
        """Create an execution service for testing."""
        return ExecutionService(tmp_path, workflow_service, thread_facade)

    @pytest.fixture
    def workspace_id(self) -> WorkspaceId:
        """Create a test workspace ID."""
        return uuid.uuid4()

    @pytest.fixture
    def test_assistant_id(
        self, assistant_service: AssistantService, workspace_id: WorkspaceId
    ) -> str:
        """Create a test assistant and return its ID."""
        from askui.chat.api.assistants.models import AssistantCreateParams

        assistant_params = AssistantCreateParams(
            name="Test Assistant",
            description="A test assistant for execution testing",
        )
        assistant = assistant_service.create(
            workspace_id=workspace_id, params=assistant_params
        )
        return assistant.id

    @pytest.fixture
    def test_workflow_id(
        self,
        workflow_service: WorkflowService,
        workspace_id: WorkspaceId,
        test_assistant_id: str,
    ) -> str:
        """Create a test workflow and return its ID."""
        workflow_params = WorkflowCreateParams(
            name="Test Workflow",
            description="A test workflow for execution testing",
            assistant_id=test_assistant_id,
        )
        workflow = workflow_service.create(
            workspace_id=workspace_id, params=workflow_params
        )
        return workflow.id

    @pytest.fixture
    def create_params(self, test_workflow_id: str) -> ExecutionCreateParams:
        """Create sample execution creation parameters."""
        return ExecutionCreateParams(
            workflow_id=test_workflow_id,
        )

    @pytest_asyncio.fixture
    async def sample_execution(
        self,
        execution_service: ExecutionService,
        workspace_id: WorkspaceId,
        create_params: ExecutionCreateParams,
    ) -> Execution:
        """Create a sample execution for testing."""
        execution, _ = await execution_service.create(
            workspace_id=workspace_id, params=create_params
        )
        return execution

    @pytest.mark.asyncio
    async def test_create_execution_success(
        self,
        execution_service: ExecutionService,
        workspace_id: WorkspaceId,
        create_params: ExecutionCreateParams,
    ) -> None:
        """Test successful execution creation."""
        execution, _ = await execution_service.create(
            workspace_id=workspace_id, params=create_params
        )

        assert execution.workflow_id == create_params.workflow_id
        assert execution.thread_id is not None  # Thread is created automatically
        assert execution.status == ExecutionStatus.PENDING
        assert execution.workspace_id == workspace_id
        assert execution.object == "execution"
        assert execution.id.startswith("exec_")
        assert execution.created_at is not None

    @pytest.mark.asyncio
    async def test_create_execution_with_nonexistent_workflow_fails(
        self,
        execution_service: ExecutionService,
        workspace_id: WorkspaceId,
    ) -> None:
        """
        Test that creating execution with non-existent workflow raises NotFoundError.
        """
        invalid_params = ExecutionCreateParams(
            workflow_id="wf_nonexistent123",
        )

        with pytest.raises(NotFoundError) as exc_info:
            await execution_service.create(
                workspace_id=workspace_id, params=invalid_params
            )

        assert "Workflow wf_nonexistent123 not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_execution_with_workflow_from_different_workspace_fails(
        self,
        tmp_path: Path,
        test_workflow_id: str,
    ) -> None:
        """Test that creating execution with workflow from different workspace fails."""
        # Create execution service with different workspace
        different_workspace_id = uuid.uuid4()
        workflow_service = WorkflowService(tmp_path)
        # Create minimal thread facade for this test
        mock_thread_service = Mock()
        mock_message_service = Mock()
        mock_run_service = Mock()
        thread_facade = ThreadFacade(
            mock_thread_service, mock_message_service, mock_run_service
        )
        execution_service = ExecutionService(tmp_path, workflow_service, thread_facade)

        invalid_params = ExecutionCreateParams(
            workflow_id=test_workflow_id,
        )

        with pytest.raises(NotFoundError) as exc_info:
            await execution_service.create(
                workspace_id=different_workspace_id, params=invalid_params
            )

        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_retrieve_execution_success(
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
        assert retrieved.workflow_id == sample_execution.workflow_id
        assert retrieved.thread_id == sample_execution.thread_id
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

    @pytest.mark.asyncio
    async def test_modify_execution_valid_transition(
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
        assert modified.workflow_id == sample_execution.workflow_id
        assert modified.thread_id == sample_execution.thread_id

    @pytest.mark.asyncio
    async def test_modify_execution_invalid_transition_raises_error(
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

    @pytest.mark.asyncio
    async def test_modify_execution_same_status_allowed(
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

    @pytest.mark.asyncio
    async def test_list_executions_success(
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

    @pytest.mark.asyncio
    async def test_list_executions_with_filters(
        self,
        execution_service: ExecutionService,
        workflow_service: WorkflowService,
        workspace_id: WorkspaceId,
        create_params: ExecutionCreateParams,
        test_assistant_id: str,
    ) -> None:
        """Test execution listing with workflow and thread filters."""
        # Create multiple executions with different workflows and threads
        first_execution, _ = await execution_service.create(
            workspace_id=workspace_id, params=create_params
        )

        # Create a second workflow for the different execution
        different_workflow_params = WorkflowCreateParams(
            name="Different Test Workflow",
            description="A different test workflow for execution filtering testing",
            assistant_id=test_assistant_id,
        )
        different_workflow = workflow_service.create(
            workspace_id=workspace_id, params=different_workflow_params
        )

        different_params = ExecutionCreateParams(
            workflow_id=different_workflow.id,
        )
        second_execution, _ = await execution_service.create(
            workspace_id=workspace_id, params=different_params
        )

        query = ListQuery(limit=10, order="desc")

        # Test workflow filter
        workflow_filtered = execution_service.list_(
            workspace_id=workspace_id,
            query=query,
            workflow_id=create_params.workflow_id,
        )
        assert len(workflow_filtered.data) >= 1
        assert all(
            execution.workflow_id == create_params.workflow_id
            for execution in workflow_filtered.data
        )

        # Test thread filter - use the actual thread_id from the first execution
        thread_filtered = execution_service.list_(
            workspace_id=workspace_id,
            query=query,
            thread_id=first_execution.thread_id,
        )
        assert len(thread_filtered.data) >= 1
        assert all(
            execution.thread_id == first_execution.thread_id
            for execution in thread_filtered.data
        )

        # Test combined filters
        combined_filtered = execution_service.list_(
            workspace_id=workspace_id,
            query=query,
            workflow_id=create_params.workflow_id,
            thread_id=first_execution.thread_id,
        )
        assert len(combined_filtered.data) >= 1
        assert all(
            execution.workflow_id == create_params.workflow_id
            and execution.thread_id == first_execution.thread_id
            for execution in combined_filtered.data
        )

    @pytest.mark.asyncio
    async def test_persistence_across_service_instances(
        self,
        workspace_id: WorkspaceId,
        execution_service: ExecutionService,
        create_params: ExecutionCreateParams,
    ) -> None:
        """Test that executions persist across service instances."""
        # Create execution with existing service instance
        execution, _ = await execution_service.create(
            workspace_id=workspace_id, params=create_params
        )

        retrieved = execution_service.retrieve(
            workspace_id=workspace_id, execution_id=execution.id
        )

        assert retrieved.id == execution.id
        assert retrieved.status == execution.status
        assert retrieved.workflow_id == execution.workflow_id

    @pytest.mark.asyncio
    async def test_modify_execution_persists_changes(
        self,
        workspace_id: WorkspaceId,
        execution_service: ExecutionService,
        create_params: ExecutionCreateParams,
    ) -> None:
        """Test that execution modifications are persisted to filesystem."""
        # Create execution using existing service
        execution, _ = await execution_service.create(
            workspace_id=workspace_id, params=create_params
        )

        # Modify execution
        modify_params = ExecutionModifyParams(status=ExecutionStatus.PASSED)
        execution_service.modify(
            workspace_id=workspace_id,
            execution_id=execution.id,
            params=modify_params,
        )

        # Verify changes persist with new service instance
        retrieved = execution_service.retrieve(
            workspace_id=workspace_id, execution_id=execution.id
        )
        assert retrieved.status == ExecutionStatus.PASSED

    @pytest.mark.parametrize(
        "target_status",
        [
            ExecutionStatus.INCOMPLETE,
            ExecutionStatus.PASSED,
            ExecutionStatus.FAILED,
            ExecutionStatus.SKIPPED,
        ],
    )
    @pytest.mark.asyncio
    async def test_valid_transitions_from_pending(
        self,
        execution_service: ExecutionService,
        workspace_id: WorkspaceId,
        test_workflow_id: str,
        target_status: ExecutionStatus,
    ) -> None:
        """Test all valid transitions from PENDING status (parametrized)."""
        # Create execution (always starts as PENDING)
        create_params = ExecutionCreateParams(
            workflow_id=test_workflow_id,
        )
        execution, _ = await execution_service.create(
            workspace_id=workspace_id, params=create_params
        )

        # Test transition from PENDING to target status
        modify_params = ExecutionModifyParams(status=target_status)
        modified = execution_service.modify(
            workspace_id=workspace_id,
            execution_id=execution.id,
            params=modify_params,
        )

        assert modified.status == target_status

    @pytest.mark.parametrize(
        "target_status",
        [
            ExecutionStatus.PASSED,
            ExecutionStatus.FAILED,
            ExecutionStatus.SKIPPED,
        ],
    )
    @pytest.mark.asyncio
    async def test_valid_transitions_from_incomplete(
        self,
        execution_service: ExecutionService,
        workspace_id: WorkspaceId,
        test_workflow_id: str,
        target_status: ExecutionStatus,
    ) -> None:
        """Test all valid transitions from INCOMPLETE status (parametrized)."""
        # Create execution and move to INCOMPLETE
        create_params = ExecutionCreateParams(
            workflow_id=test_workflow_id,
        )
        execution, _ = await execution_service.create(
            workspace_id=workspace_id, params=create_params
        )

        # First move to INCOMPLETE
        incomplete_params = ExecutionModifyParams(status=ExecutionStatus.INCOMPLETE)
        execution = execution_service.modify(
            workspace_id=workspace_id,
            execution_id=execution.id,
            params=incomplete_params,
        )

        # Test transition from INCOMPLETE to target status
        modify_params = ExecutionModifyParams(status=target_status)
        modified = execution_service.modify(
            workspace_id=workspace_id,
            execution_id=execution.id,
            params=modify_params,
        )

        assert modified.status == target_status

    @pytest.mark.asyncio
    async def test_incomplete_cannot_go_back_to_pending(
        self,
        execution_service: ExecutionService,
        workspace_id: WorkspaceId,
        test_workflow_id: str,
    ) -> None:
        """Test that INCOMPLETE cannot transition back to PENDING."""
        # Create execution and move to INCOMPLETE
        create_params = ExecutionCreateParams(
            workflow_id=test_workflow_id,
        )
        execution, _ = await execution_service.create(
            workspace_id=workspace_id, params=create_params
        )

        # Move to INCOMPLETE
        incomplete_params = ExecutionModifyParams(status=ExecutionStatus.INCOMPLETE)
        execution = execution_service.modify(
            workspace_id=workspace_id,
            execution_id=execution.id,
            params=incomplete_params,
        )

        # Try to go back to PENDING (should fail)
        pending_params = ExecutionModifyParams(status=ExecutionStatus.PENDING)
        with pytest.raises(InvalidStatusTransitionError) as exc_info:
            execution_service.modify(
                workspace_id=workspace_id,
                execution_id=execution.id,
                params=pending_params,
            )

        assert exc_info.value.from_status == ExecutionStatus.INCOMPLETE
        assert exc_info.value.to_status == ExecutionStatus.PENDING

    @pytest.mark.parametrize(
        "final_status",
        [
            ExecutionStatus.PASSED,
            ExecutionStatus.FAILED,
            ExecutionStatus.SKIPPED,
        ],
    )
    @pytest.mark.parametrize(
        "target_status",
        [
            ExecutionStatus.PENDING,
            ExecutionStatus.INCOMPLETE,
            ExecutionStatus.PASSED,
            ExecutionStatus.FAILED,
            ExecutionStatus.SKIPPED,
        ],
    )
    @pytest.mark.asyncio
    async def test_final_states_cannot_transition(
        self,
        execution_service: ExecutionService,
        workspace_id: WorkspaceId,
        test_workflow_id: str,
        final_status: ExecutionStatus,
        target_status: ExecutionStatus,
    ) -> None:
        """
        Test that final states cannot transition to any other status (parametrized).
        """
        # Skip same-status transitions (they're allowed as no-ops)
        if final_status == target_status:
            pytest.skip("Same-status transitions are allowed as no-ops")

        # Create execution and move to final state
        create_params = ExecutionCreateParams(
            workflow_id=test_workflow_id,
        )
        execution, _ = await execution_service.create(
            workspace_id=workspace_id, params=create_params
        )

        # Move to final status (via INCOMPLETE if needed for realistic flow)
        if final_status in [ExecutionStatus.PASSED, ExecutionStatus.FAILED]:
            # Realistic flow: PENDING → INCOMPLETE → PASSED/FAILED
            incomplete_params = ExecutionModifyParams(status=ExecutionStatus.INCOMPLETE)
            execution = execution_service.modify(
                workspace_id=workspace_id,
                execution_id=execution.id,
                params=incomplete_params,
            )

        # Move to final status
        final_params = ExecutionModifyParams(status=final_status)
        execution = execution_service.modify(
            workspace_id=workspace_id,
            execution_id=execution.id,
            params=final_params,
        )

        # Try to transition from final state to target status (should fail)
        modify_params = ExecutionModifyParams(status=target_status)
        with pytest.raises(InvalidStatusTransitionError) as exc_info:
            execution_service.modify(
                workspace_id=workspace_id,
                execution_id=execution.id,
                params=modify_params,
            )

        assert exc_info.value.from_status == final_status
        assert exc_info.value.to_status == target_status
