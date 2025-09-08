"""
Integration tests for execution router endpoints with status transition validation.
"""

import tempfile
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from askui.chat.api.app import app
from askui.chat.api.executions.models import ExecutionStatus
from askui.chat.api.executions.service import ExecutionService
from askui.chat.api.models import WorkspaceId
from askui.chat.api.workflows.models import WorkflowCreateParams
from askui.chat.api.workflows.service import WorkflowService


class TestExecutionRouter:
    """Test execution router endpoints with status transition validation."""

    @pytest.fixture
    def temp_workspace_dir(self) -> Path:
        """Create a temporary workspace directory for testing."""
        temp_dir = tempfile.mkdtemp()
        return Path(temp_dir)

    @pytest.fixture
    def workflow_service(self, temp_workspace_dir: Path) -> WorkflowService:
        """Create a workflow service for testing."""
        return WorkflowService(temp_workspace_dir)

    @pytest.fixture
    def execution_service(
        self, temp_workspace_dir: Path, workflow_service: WorkflowService
    ) -> ExecutionService:
        """Create an execution service for testing."""
        return ExecutionService(temp_workspace_dir, workflow_service)

    @pytest.fixture
    def client(
        self,
        temp_workspace_dir: Path,
        workflow_service: WorkflowService,
        execution_service: ExecutionService,
    ) -> TestClient:
        """Create a test client for the FastAPI app with overridden dependencies."""
        from askui.chat.api.executions.dependencies import get_execution_service
        from askui.chat.api.workflows.dependencies import get_workflow_service

        # Override service dependencies directly
        app.dependency_overrides[get_workflow_service] = lambda: workflow_service
        app.dependency_overrides[get_execution_service] = lambda: execution_service

        client = TestClient(app)

        # Clean up overrides after test (this will be called when fixture is torn down)
        yield client
        app.dependency_overrides.clear()

    @pytest.fixture
    def workspace_id(self) -> WorkspaceId:
        """Create a test workspace ID."""
        return uuid.uuid4()

    @pytest.fixture
    def test_workflow_id(
        self, workflow_service: WorkflowService, workspace_id: WorkspaceId
    ) -> str:
        """Create a test workflow and return its ID."""
        workflow_params = WorkflowCreateParams(
            name="Test Workflow",
            description="A test workflow for execution testing",
        )
        workflow = workflow_service.create(
            workspace_id=workspace_id, params=workflow_params
        )
        return workflow.id

    @pytest.fixture
    def execution_data(self, test_workflow_id: str) -> dict[str, str]:
        """Create sample execution data."""
        return {
            "workflow": test_workflow_id,
            "thread": "thread_test123",
        }

    def test_create_execution_success(
        self,
        client: TestClient,
        workspace_id: WorkspaceId,
        execution_data: dict[str, str],
    ) -> None:
        """Test successful execution creation."""
        response = client.post(
            "/v1/executions/",
            json=execution_data,
            headers={"askui-workspace": str(workspace_id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["workflow"] == execution_data["workflow"]
        assert data["thread"] == execution_data["thread"]
        assert data["status"] == ExecutionStatus.PENDING.value
        assert data["object"] == "execution"
        assert "id" in data
        assert "created_at" in data

    def test_modify_execution_valid_transition(
        self,
        client: TestClient,
        workspace_id: WorkspaceId,
        execution_data: dict[str, str],
    ) -> None:
        """Test successful execution modification with valid status transition."""
        # First create an execution
        create_response = client.post(
            "/v1/executions/",
            json=execution_data,
            headers={"askui-workspace": str(workspace_id)},
        )
        assert create_response.status_code == 200
        execution = create_response.json()
        execution_id = execution["id"]

        # Then modify it with a valid transition (PENDING -> PASSED)
        modify_data = {"status": ExecutionStatus.PASSED.value}
        modify_response = client.patch(
            f"/v1/executions/{execution_id}",
            json=modify_data,
            headers={"askui-workspace": str(workspace_id)},
        )

        assert modify_response.status_code == 200
        modified_execution = modify_response.json()
        assert modified_execution["status"] == ExecutionStatus.PASSED.value
        assert modified_execution["id"] == execution_id

    def test_modify_execution_invalid_transition(
        self,
        client: TestClient,
        workspace_id: WorkspaceId,
        execution_data: dict[str, str],
    ) -> None:
        """Test execution modification with invalid status transition returns 422."""
        # First create an execution and transition it to a final state
        create_response = client.post(
            "/v1/executions/",
            json=execution_data,
            headers={"askui-workspace": str(workspace_id)},
        )
        assert create_response.status_code == 200
        execution = create_response.json()
        execution_id = execution["id"]

        # Transition to final state (PENDING -> PASSED)
        modify_data = {"status": ExecutionStatus.PASSED.value}
        modify_response = client.patch(
            f"/v1/executions/{execution_id}",
            json=modify_data,
            headers={"askui-workspace": str(workspace_id)},
        )
        assert modify_response.status_code == 200

        # Try to transition from final state to non-final state (PASSED -> PENDING)
        invalid_modify_data = {"status": ExecutionStatus.PENDING.value}
        invalid_response = client.patch(
            f"/v1/executions/{execution_id}",
            json=invalid_modify_data,
            headers={"askui-workspace": str(workspace_id)},
        )

        # FastAPI should convert ValueError to 422 Unprocessable Entity
        assert invalid_response.status_code == 422
        error_data = invalid_response.json()
        assert "detail" in error_data
        # The error should contain information about the invalid transition
        error_detail = str(error_data["detail"])
        assert "Invalid status transition" in error_detail
        assert "passed" in error_detail
        assert "pending" in error_detail

    def test_modify_execution_same_status_allowed(
        self,
        client: TestClient,
        workspace_id: WorkspaceId,
        execution_data: dict[str, str],
    ) -> None:
        """Test that modifying to the same status is allowed (no-op)."""
        # Create an execution
        create_response = client.post(
            "/v1/executions/",
            json=execution_data,
            headers={"askui-workspace": str(workspace_id)},
        )
        assert create_response.status_code == 200
        execution = create_response.json()
        execution_id = execution["id"]

        # Modify to the same status (PENDING -> PENDING)
        modify_data = {"status": ExecutionStatus.PENDING.value}
        modify_response = client.patch(
            f"/v1/executions/{execution_id}",
            json=modify_data,
            headers={"askui-workspace": str(workspace_id)},
        )

        assert modify_response.status_code == 200
        modified_execution = modify_response.json()
        assert modified_execution["status"] == ExecutionStatus.PENDING.value

    def test_modify_execution_multiple_valid_transitions(
        self,
        client: TestClient,
        workspace_id: WorkspaceId,
        execution_data: dict[str, str],
    ) -> None:
        """Test multiple valid status transitions in sequence."""
        # Create an execution
        create_response = client.post(
            "/v1/executions/",
            json=execution_data,
            headers={"askui-workspace": str(workspace_id)},
        )
        assert create_response.status_code == 200
        execution = create_response.json()
        execution_id = execution["id"]

        # Valid transition sequence: PENDING -> INCOMPLETE -> PASSED
        transitions = [
            (ExecutionStatus.INCOMPLETE.value, 200),
            (ExecutionStatus.PASSED.value, 200),
        ]

        for status, expected_code in transitions:
            modify_data = {"status": status}
            modify_response = client.patch(
                f"/v1/executions/{execution_id}",
                json=modify_data,
                headers={"askui-workspace": str(workspace_id)},
            )

            assert modify_response.status_code == expected_code
            if expected_code == 200:
                modified_execution = modify_response.json()
                assert modified_execution["status"] == status

    def test_modify_execution_not_found(
        self, client: TestClient, workspace_id: WorkspaceId
    ) -> None:
        """Test modifying non-existent execution returns 404."""
        modify_data = {"status": ExecutionStatus.PASSED.value}
        response = client.patch(
            "/v1/executions/exec_nonexistent123",
            json=modify_data,
            headers={"askui-workspace": str(workspace_id)},
        )

        assert response.status_code == 404

    def test_retrieve_execution_success(
        self,
        client: TestClient,
        workspace_id: WorkspaceId,
        execution_data: dict[str, str],
    ) -> None:
        """Test successful execution retrieval."""
        # Create an execution
        create_response = client.post(
            "/v1/executions/",
            json=execution_data,
            headers={"askui-workspace": str(workspace_id)},
        )
        assert create_response.status_code == 200
        execution = create_response.json()
        execution_id = execution["id"]

        # Retrieve the execution
        retrieve_response = client.get(
            f"/v1/executions/{execution_id}",
            headers={"askui-workspace": str(workspace_id)},
        )

        assert retrieve_response.status_code == 200
        retrieved_execution = retrieve_response.json()
        assert retrieved_execution["id"] == execution_id
        assert retrieved_execution["status"] == ExecutionStatus.PENDING.value

    def test_list_executions_success(
        self,
        client: TestClient,
        workspace_id: WorkspaceId,
        execution_data: dict[str, str],
    ) -> None:
        """Test successful execution listing."""
        # Create an execution
        create_response = client.post(
            "/v1/executions/",
            json=execution_data,
            headers={"askui-workspace": str(workspace_id)},
        )
        assert create_response.status_code == 200

        # List executions
        list_response = client.get(
            "/v1/executions/",
            headers={"askui-workspace": str(workspace_id)},
        )

        assert list_response.status_code == 200
        data = list_response.json()
        assert "data" in data
        assert "object" in data
        assert data["object"] == "list"
        assert len(data["data"]) >= 1

    @pytest.mark.parametrize(
        "final_status",
        [
            ExecutionStatus.PASSED,
            ExecutionStatus.FAILED,
            ExecutionStatus.SKIPPED,
        ],
    )
    @pytest.mark.parametrize(
        "invalid_target",
        [
            ExecutionStatus.PENDING,
            ExecutionStatus.INCOMPLETE,
        ],
    )
    def test_final_states_cannot_transition_parametrized(
        self,
        client: TestClient,
        workspace_id: WorkspaceId,
        execution_data: dict[str, str],
        final_status: ExecutionStatus,
        invalid_target: ExecutionStatus,
    ) -> None:
        """
        Test that final states cannot transition to non-final states (parametrized).
        """
        # Create an execution
        create_response = client.post(
            "/v1/executions/",
            json=execution_data,
            headers={"askui-workspace": str(workspace_id)},
        )
        assert create_response.status_code == 200
        execution = create_response.json()
        execution_id = execution["id"]

        # Transition to final state
        modify_data = {"status": final_status.value}
        modify_response = client.patch(
            f"/v1/executions/{execution_id}",
            json=modify_data,
            headers={"askui-workspace": str(workspace_id)},
        )
        assert modify_response.status_code == 200

        # Try to transition to invalid target
        invalid_modify_data = {"status": invalid_target.value}
        invalid_response = client.patch(
            f"/v1/executions/{execution_id}",
            json=invalid_modify_data,
            headers={"askui-workspace": str(workspace_id)},
        )

        assert invalid_response.status_code == 422
        error_data = invalid_response.json()
        error_detail = str(error_data["detail"])
        assert "Invalid status transition" in error_detail
        assert final_status.value in error_detail
        assert invalid_target.value in error_detail
