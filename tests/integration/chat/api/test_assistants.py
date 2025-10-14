"""Integration tests for the assistants API endpoints."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from askui.chat.api.assistants.models import Assistant
from askui.chat.api.assistants.orms import AssistantOrm
from askui.chat.api.models import WorkspaceId


class TestAssistantsAPI:
    """Test suite for the assistants API endpoints."""

    def _create_test_assistant(
        self,
        assistant_id: str,
        workspace_id: WorkspaceId | None = None,
        name: str = "Test Assistant",
        description: str = "A test assistant",
        avatar: str | None = None,
        created_at: datetime | None = None,
    ) -> Assistant:
        """Create a test assistant model."""
        if created_at is None:
            created_at = datetime.fromtimestamp(1234567890, tz=timezone.utc)
        return Assistant(
            id=assistant_id,
            object="assistant",
            created_at=created_at,
            name=name,
            description=description,
            avatar=avatar,
            workspace_id=workspace_id,
        )

    def _add_assistant_to_db(
        self, assistant: Assistant, test_db_session: Session
    ) -> None:
        """Add an assistant to the test database."""
        assistant_orm = AssistantOrm.from_model(assistant)
        test_db_session.add(assistant_orm)
        test_db_session.commit()

    def test_list_assistants_empty(
        self, test_headers: dict[str, str], test_client: TestClient
    ) -> None:
        """Test listing assistants when no assistants exist."""
        response = test_client.get("/v1/assistants", headers=test_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["object"] == "list"
        assert data["data"] == []
        assert data["has_more"] is False

    def test_list_assistants_with_assistants(
        self,
        test_headers: dict[str, str],
        test_db_session: Session,
        test_client: TestClient,
    ) -> None:
        """Test listing assistants when assistants exist."""
        workspace_id = UUID(test_headers["askui-workspace"])  # WorkspaceId is UUID4
        mock_assistant = self._create_test_assistant(
            "asst_test123", workspace_id=workspace_id, avatar="test_avatar.png"
        )
        self._add_assistant_to_db(mock_assistant, test_db_session)
        response = test_client.get("/v1/assistants", headers=test_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["object"] == "list"
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == "asst_test123"
        assert data["data"][0]["name"] == "Test Assistant"
        assert data["data"][0]["description"] == "A test assistant"
        assert data["data"][0]["avatar"] == "test_avatar.png"
        assert data["has_more"] is False

    def test_list_assistants_with_pagination(
        self,
        test_headers: dict[str, str],
        test_db_session: Session,
        test_client: TestClient,
    ) -> None:
        """Test listing assistants with pagination parameters."""
        workspace_id = UUID(test_headers["askui-workspace"])  # WorkspaceId is UUID4

        # Create multiple mock assistants in the database
        for i in range(5):
            mock_assistant = self._create_test_assistant(
                f"asst_test{i}",
                workspace_id=workspace_id,
                name=f"Test Assistant {i}",
                description=f"Test assistant {i}",
                created_at=datetime.fromtimestamp(1234567890 + i, tz=timezone.utc),
            )
            self._add_assistant_to_db(mock_assistant, test_db_session)

        response = test_client.get("/v1/assistants?limit=3", headers=test_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["data"]) == 3
        assert data["has_more"] is True

    def test_create_assistant(
        self, test_headers: dict[str, str], test_client: TestClient
    ) -> None:
        """Test creating a new assistant."""
        assistant_data = {
            "name": "New Test Assistant",
            "description": "A newly created test assistant",
            "avatar": "new_avatar.png",
        }
        response = test_client.post(
            "/v1/assistants", json=assistant_data, headers=test_headers
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "New Test Assistant"
        assert data["description"] == "A newly created test assistant"
        assert data["avatar"] == "new_avatar.png"
        assert data["object"] == "assistant"
        assert "id" in data
        assert "created_at" in data

    def test_create_assistant_minimal(
        self, test_headers: dict[str, str], test_client: TestClient
    ) -> None:
        """Test creating an assistant with minimal data."""
        response = test_client.post("/v1/assistants", json={}, headers=test_headers)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["object"] == "assistant"
        assert data["name"] is None
        assert data["description"] is None
        assert data["avatar"] is None

    def test_create_assistant_with_tools_and_system(
        self, test_headers: dict[str, str], test_client: TestClient
    ) -> None:
        """Test creating a new assistant with tools and system prompt."""
        response = test_client.post(
            "/v1/assistants",
            headers=test_headers,
            json={
                "name": "Custom Assistant",
                "description": "A custom assistant with tools",
                "tools": ["tool1", "tool2", "tool3"],
                "system": "You are a helpful custom assistant.",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Custom Assistant"
        assert data["description"] == "A custom assistant with tools"
        assert data["tools"] == ["tool1", "tool2", "tool3"]
        assert data["system"] == "You are a helpful custom assistant."
        assert "id" in data
        assert "created_at" in data

    def test_create_assistant_with_empty_tools(
        self, test_headers: dict[str, str], test_client: TestClient
    ) -> None:
        """Test creating a new assistant with empty tools list."""
        response = test_client.post(
            "/v1/assistants",
            headers=test_headers,
            json={
                "name": "Empty Tools Assistant",
                "tools": [],
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Empty Tools Assistant"
        assert data["tools"] == []
        assert "id" in data
        assert "created_at" in data

    def test_retrieve_assistant(
        self,
        test_headers: dict[str, str],
        test_db_session: Session,
        test_client: TestClient,
    ) -> None:
        """Test retrieving an existing assistant."""
        mock_assistant = self._create_test_assistant("asst_test123")
        self._add_assistant_to_db(mock_assistant, test_db_session)
        response = test_client.get("/v1/assistants/asst_test123", headers=test_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == "asst_test123"
        assert data["name"] == "Test Assistant"
        assert data["description"] == "A test assistant"

    def test_retrieve_assistant_not_found(
        self, test_client: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test retrieving a non-existent assistant."""
        response = test_client.get(
            "/v1/assistants/asst_nonexistent123", headers=test_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data

    def test_modify_assistant(
        self,
        test_headers: dict[str, str],
        test_db_session: Session,
        test_client: TestClient,
    ) -> None:
        """Test modifying an existing assistant."""
        workspace_id = UUID(test_headers["askui-workspace"])  # WorkspaceId is UUID4
        mock_assistant = self._create_test_assistant(
            "asst_test123",
            workspace_id=workspace_id,
            name="Original Name",
            description="Original description",
        )
        self._add_assistant_to_db(mock_assistant, test_db_session)
        modify_data = {
            "name": "Modified Name",
            "description": "Modified description",
        }
        response = test_client.post(
            "/v1/assistants/asst_test123",
            json=modify_data,
            headers=test_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Modified Name"
        assert data["description"] == "Modified description"
        assert data["id"] == "asst_test123"
        assert data["created_at"] == 1234567890

    def test_modify_assistant_with_tools_and_system(
        self,
        test_headers: dict[str, str],
        test_db_session: Session,
        test_client: TestClient,
    ) -> None:
        """Test modifying an assistant with tools and system prompt."""
        workspace_id = UUID(test_headers["askui-workspace"])  # WorkspaceId is UUID4
        mock_assistant = self._create_test_assistant(
            "asst_test123",
            workspace_id=workspace_id,
            name="Original Name",
            description="Original description",
        )
        self._add_assistant_to_db(mock_assistant, test_db_session)
        modify_data = {
            "name": "Modified Name",
            "tools": ["new_tool1", "new_tool2"],
            "system": "You are a modified custom assistant.",
        }
        response = test_client.post(
            "/v1/assistants/asst_test123",
            json=modify_data,
            headers=test_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Modified Name"
        assert data["tools"] == ["new_tool1", "new_tool2"]
        assert data["system"] == "You are a modified custom assistant."
        assert data["id"] == "asst_test123"
        assert data["created_at"] == 1234567890

    def test_modify_assistant_partial(
        self,
        test_headers: dict[str, str],
        test_db_session: Session,
        test_client: TestClient,
    ) -> None:
        """Test modifying an assistant with partial data."""
        workspace_id = UUID(test_headers["askui-workspace"])  # WorkspaceId is UUID4
        mock_assistant = self._create_test_assistant(
            "asst_test123",
            workspace_id=workspace_id,
            name="Original Name",
            description="Original description",
        )
        self._add_assistant_to_db(mock_assistant, test_db_session)
        modify_data = {"name": "Only Name Modified"}
        response = test_client.post(
            "/v1/assistants/asst_test123",
            json=modify_data,
            headers=test_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Only Name Modified"
        assert data["description"] == "Original description"  # Unchanged

    def test_modify_assistant_not_found(
        self, test_client: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test modifying a non-existent assistant."""
        modify_data = {"name": "Modified Name"}
        response = test_client.post(
            "/v1/assistants/asst_nonexistent123", json=modify_data, headers=test_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_assistant(
        self,
        test_headers: dict[str, str],
        test_db_session: Session,
        test_client: TestClient,
    ) -> None:
        """Test deleting an existing assistant."""
        workspace_id = UUID(test_headers["askui-workspace"])  # WorkspaceId is UUID4
        mock_assistant = self._create_test_assistant(
            "asst_test123", workspace_id=workspace_id
        )
        self._add_assistant_to_db(mock_assistant, test_db_session)
        response = test_client.delete(
            "/v1/assistants/asst_test123", headers=test_headers
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b""

    def test_delete_assistant_not_found(
        self, test_client: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test deleting a non-existent assistant."""
        response = test_client.delete(
            "/v1/assistants/asst_nonexistent123", headers=test_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_modify_default_assistant_forbidden(
        self,
        test_headers: dict[str, str],
        test_db_session: Session,
        test_client: TestClient,
    ) -> None:
        """Test that modifying a default assistant returns 403 Forbidden."""
        default_assistant = self._create_test_assistant(
            "asst_default123",
            workspace_id=None,  # No workspace_id = default
            name="Default Assistant",
            description="This is a default assistant",
        )
        self._add_assistant_to_db(default_assistant, test_db_session)
        # Try to modify the default assistant
        response = test_client.post(
            "/v1/assistants/asst_default123",
            headers=test_headers,
            json={"name": "Modified Name"},
        )
        assert response.status_code == 403
        assert "cannot be modified" in response.json()["detail"]

    def test_delete_default_assistant_forbidden(
        self,
        test_headers: dict[str, str],
        test_db_session: Session,
        test_client: TestClient,
    ) -> None:
        """Test that deleting a default assistant returns 403 Forbidden."""
        default_assistant = self._create_test_assistant(
            "asst_default456",
            workspace_id=None,  # No workspace_id = default
            name="Default Assistant",
            description="This is a default assistant",
        )
        self._add_assistant_to_db(default_assistant, test_db_session)
        # Try to delete the default assistant
        response = test_client.delete(
            "/v1/assistants/asst_default456",
            headers=test_headers,
        )
        assert response.status_code == 403
        assert "cannot be deleted" in response.json()["detail"]

    def test_list_assistants_includes_default_and_workspace(
        self,
        test_headers: dict[str, str],
        test_db_session: Session,
        test_client: TestClient,
    ) -> None:
        """Test that listing assistants includes both default and
        workspace-scoped ones.
        """
        # Create a default assistant (no workspace_id)
        default_assistant = self._create_test_assistant(
            "asst_default789",
            workspace_id=None,  # No workspace_id = default
            name="Default Assistant",
            description="This is a default assistant",
        )
        self._add_assistant_to_db(default_assistant, test_db_session)

        # Create a workspace-scoped assistant
        workspace_id = UUID(test_headers["askui-workspace"])  # WorkspaceId is UUID4
        workspace_assistant = self._create_test_assistant(
            "asst_workspace123",
            workspace_id=workspace_id,
            name="Workspace Assistant",
            description="This is a workspace assistant",
        )
        self._add_assistant_to_db(workspace_assistant, test_db_session)

        # List assistants - should include both
        response = test_client.get("/v1/assistants", headers=test_headers)
        assert response.status_code == 200

        data = response.json()
        assistant_ids = [assistant["id"] for assistant in data["data"]]

        # Should include both default and workspace assistants
        assert "asst_default789" in assistant_ids
        assert "asst_workspace123" in assistant_ids

        # Verify workspace_id fields
        default_assistant_data = next(
            a for a in data["data"] if a["id"] == "asst_default789"
        )
        workspace_assistant_data = next(
            a for a in data["data"] if a["id"] == "asst_workspace123"
        )

        assert default_assistant_data["workspace_id"] is None
        assert workspace_assistant_data["workspace_id"] == str(workspace_id)

    def test_retrieve_default_assistant_success(
        self,
        test_headers: dict[str, str],
        test_db_session: Session,
        test_client: TestClient,
    ) -> None:
        """Test that retrieving a default assistant works."""
        default_assistant = self._create_test_assistant(
            "asst_defaultretrieve",
            workspace_id=None,  # No workspace_id = default
            name="Default Assistant",
            description="This is a default assistant",
        )
        self._add_assistant_to_db(default_assistant, test_db_session)
        # Retrieve the default assistant
        response = test_client.get(
            "/v1/assistants/asst_defaultretrieve",
            headers=test_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == "asst_defaultretrieve"
        assert data["workspace_id"] is None

    def test_workspace_scoped_assistant_operations_success(
        self,
        test_headers: dict[str, str],
        test_db_session: Session,
        test_client: TestClient,
    ) -> None:
        """Test that workspace-scoped assistants can be modified and deleted."""
        workspace_id = UUID(test_headers["askui-workspace"])  # WorkspaceId is UUID4
        workspace_id = UUID(test_headers["askui-workspace"])  # WorkspaceId is UUID4
        workspace_id = UUID(test_headers["askui-workspace"])  # WorkspaceId is UUID4
        workspace_assistant = self._create_test_assistant(
            "asst_workspaceops",
            workspace_id=workspace_id,
            name="Workspace Assistant",
            description="This is a workspace assistant",
        )
        self._add_assistant_to_db(workspace_assistant, test_db_session)
        # Modify the workspace assistant
        response = test_client.post(
            "/v1/assistants/asst_workspaceops",
            headers=test_headers,
            json={"name": "Modified Workspace Assistant"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "Modified Workspace Assistant"
        assert data["workspace_id"] == str(workspace_id)

        # Delete the workspace assistant
        response = test_client.delete(
            "/v1/assistants/asst_workspaceops",
            headers=test_headers,
        )
        assert response.status_code == 204

        # Verify it's deleted
        response = test_client.get(
            "/v1/assistants/asst_workspaceops",
            headers=test_headers,
        )
        assert response.status_code == 404
