"""Integration tests for the assistants API endpoints."""

from datetime import datetime, timezone

from askui.chat.api.assistants.models import AssistantModel
from fastapi import status
from fastapi.testclient import TestClient


class TestAssistantsAPI:
    """Test suite for the assistants API endpoints."""

    def test_list_assistants_empty(
        self, test_client_with_db: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test listing assistants when no assistants exist."""
        response = test_client_with_db.get("/v1/assistants", headers=test_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["object"] == "list"
        assert data["data"] == []
        assert data["has_more"] is False
        assert data["first_id"] is None
        assert data["last_id"] is None

    def test_list_assistants_with_assistants(
        self, test_client_and_session_factory, test_headers: dict[str, str]
    ) -> None:
        """Test listing assistants when assistants exist."""
        test_client, session_factory = test_client_and_session_factory

        # Create a test assistant in the database
        with session_factory() as session:
            db_assistant = AssistantModel(
                id="asst_test123",
                workspace_id=test_headers["askui-workspace"],
                created_at=datetime.now(timezone.utc),
                name="Test Assistant",
                description="A test assistant",
                avatar="test_avatar.png",
                tools=[],
                system=None,
            )
            session.add(db_assistant)
            session.commit()

        response = test_client.get("/v1/assistants", headers=test_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["object"] == "list"
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == "asst_test123"
        assert data["data"][0]["name"] == "Test Assistant"

    def test_list_assistants_with_pagination(
        self, test_client_and_session_factory, test_headers: dict[str, str]
    ) -> None:
        """Test listing assistants with pagination parameters."""
        test_client, session_factory = test_client_and_session_factory

        # Create multiple test assistants in the database
        with session_factory() as session:
            for i in range(5):
                db_assistant = AssistantModel(
                    id=f"asst_test{i}",
                    workspace_id=test_headers["askui-workspace"],
                    created_at=datetime.now(timezone.utc),
                    name=f"Test Assistant {i}",
                    description=f"Test assistant {i}",
                    tools=[],
                    system=None,
                )
                session.add(db_assistant)
            session.commit()

        response = test_client.get("/v1/assistants?limit=3", headers=test_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["data"]) == 3
        assert data["has_more"] is True

    def test_create_assistant(
        self, test_client_with_db: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test creating a new assistant."""
        assistant_data = {
            "name": "New Test Assistant",
            "description": "A newly created test assistant",
            "avatar": "new_avatar.png",
        }
        response = test_client_with_db.post(
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
        self, test_client_with_db: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test creating an assistant with minimal data."""
        response = test_client_with_db.post(
            "/v1/assistants", json={}, headers=test_headers
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["object"] == "assistant"
        assert data["name"] is None
        assert data["description"] is None
        assert data["avatar"] is None

    def test_create_assistant_with_tools_and_system(
        self, test_client_with_db: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test creating a new assistant with tools and system prompt."""
        response = test_client_with_db.post(
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
        self, test_client_with_db: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test creating a new assistant with empty tools list."""
        response = test_client_with_db.post(
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
        self, test_client_and_session_factory, test_headers: dict[str, str]
    ) -> None:
        """Test retrieving an existing assistant."""
        test_client, session_factory = test_client_and_session_factory

        # Create a test assistant in the database
        with session_factory() as session:
            db_assistant = AssistantModel(
                id="asst_test123",
                workspace_id=test_headers["askui-workspace"],
                created_at=datetime.now(timezone.utc),
                name="Test Assistant",
                description="A test assistant",
                tools=[],
                system=None,
            )
            session.add(db_assistant)
            session.commit()

        response = test_client.get("/v1/assistants/asst_test123", headers=test_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == "asst_test123"
        assert data["name"] == "Test Assistant"
        assert data["description"] == "A test assistant"

    def test_retrieve_assistant_not_found(
        self, test_client_with_db: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test retrieving a non-existent assistant."""
        response = test_client_with_db.get(
            "/v1/assistants/asst_nonexistent123", headers=test_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data

    def test_modify_assistant(
        self, test_client_and_session_factory, test_headers: dict[str, str]
    ) -> None:
        """Test modifying an existing assistant."""
        test_client, session_factory = test_client_and_session_factory

        # Create a test assistant in the database
        with session_factory() as session:
            db_assistant = AssistantModel(
                id="asst_test123",
                workspace_id=test_headers["askui-workspace"],
                created_at=datetime.now(timezone.utc),
                name="Original Name",
                description="Original description",
                tools=[],
                system=None,
            )
            session.add(db_assistant)
            session.commit()

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

    def test_modify_assistant_with_tools_and_system(
        self, test_client_and_session_factory, test_headers: dict[str, str]
    ) -> None:
        """Test modifying an assistant with tools and system prompt."""
        test_client, session_factory = test_client_and_session_factory

        # Create a test assistant in the database
        with session_factory() as session:
            db_assistant = AssistantModel(
                id="asst_test123",
                workspace_id=test_headers["askui-workspace"],
                created_at=datetime.now(timezone.utc),
                name="Original Name",
                description="Original description",
                tools=[],
                system=None,
            )
            session.add(db_assistant)
            session.commit()

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

    def test_modify_assistant_partial(
        self, test_client_and_session_factory, test_headers: dict[str, str]
    ) -> None:
        """Test modifying an assistant with partial data."""
        test_client, session_factory = test_client_and_session_factory

        # Create a test assistant in the database
        with session_factory() as session:
            db_assistant = AssistantModel(
                id="asst_test123",
                workspace_id=test_headers["askui-workspace"],
                created_at=datetime.now(timezone.utc),
                name="Original Name",
                description="Original description",
                tools=[],
                system=None,
            )
            session.add(db_assistant)
            session.commit()

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
        self, test_client_with_db: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test modifying a non-existent assistant."""
        modify_data = {"name": "Modified Name"}
        response = test_client_with_db.post(
            "/v1/assistants/asst_nonexistent123", json=modify_data, headers=test_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_assistant(
        self, test_client_and_session_factory, test_headers: dict[str, str]
    ) -> None:
        """Test deleting an existing assistant."""
        test_client, session_factory = test_client_and_session_factory

        # Create a test assistant in the database
        with session_factory() as session:
            db_assistant = AssistantModel(
                id="asst_test123",
                workspace_id=test_headers["askui-workspace"],
                created_at=datetime.now(timezone.utc),
                name="Test Assistant",
                tools=[],
                system=None,
            )
            session.add(db_assistant)
            session.commit()

        response = test_client.delete(
            "/v1/assistants/asst_test123", headers=test_headers
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b""

    def test_delete_assistant_not_found(
        self, test_client_with_db: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test deleting a non-existent assistant."""
        response = test_client_with_db.delete(
            "/v1/assistants/asst_nonexistent123", headers=test_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_modify_default_assistant_forbidden(
        self, test_client_and_session_factory, test_headers: dict[str, str]
    ) -> None:
        """Test that modifying a default assistant returns 403 Forbidden."""
        test_client, session_factory = test_client_and_session_factory

        # Create a default assistant (no workspace_id) in the database
        with session_factory() as session:
            db_assistant = AssistantModel(
                id="asst_default123",
                workspace_id=None,  # No workspace_id = default
                created_at=datetime.now(timezone.utc),
                name="Default Assistant",
                description="This is a default assistant",
                tools=[],
                system=None,
            )
            session.add(db_assistant)
            session.commit()

        # Try to modify the default assistant
        response = test_client.post(
            "/v1/assistants/asst_default123",
            headers=test_headers,
            json={"name": "Modified Name"},
        )
        assert response.status_code == 403
        assert "cannot be modified" in response.json()["detail"]

    def test_delete_default_assistant_forbidden(
        self, test_client_and_session_factory, test_headers: dict[str, str]
    ) -> None:
        """Test that deleting a default assistant returns 403 Forbidden."""
        test_client, session_factory = test_client_and_session_factory

        # Create a default assistant (no workspace_id) in the database
        with session_factory() as session:
            db_assistant = AssistantModel(
                id="asst_default456",
                workspace_id=None,  # No workspace_id = default
                created_at=datetime.now(timezone.utc),
                name="Default Assistant",
                description="This is a default assistant",
                tools=[],
                system=None,
            )
            session.add(db_assistant)
            session.commit()

        # Try to delete the default assistant
        response = test_client.delete(
            "/v1/assistants/asst_default456",
            headers=test_headers,
        )
        assert response.status_code == 403
        assert "cannot be deleted" in response.json()["detail"]

    def test_list_assistants_includes_default_and_workspace(
        self, test_client_and_session_factory, test_headers: dict[str, str]
    ) -> None:
        """Test that listing assistants includes both default and
        workspace-scoped ones.
        """
        test_client, session_factory = test_client_and_session_factory

        # Create a default assistant (no workspace_id) in the database
        with session_factory() as session:
            default_assistant = AssistantModel(
                id="asst_default789",
                workspace_id=None,  # No workspace_id = default
                created_at=datetime.now(timezone.utc),
                name="Default Assistant",
                description="This is a default assistant",
                tools=[],
                system=None,
            )
            session.add(default_assistant)

            # Create a workspace-scoped assistant
            workspace_assistant = AssistantModel(
                id="asst_workspace123",
                workspace_id=test_headers["askui-workspace"],
                created_at=datetime.now(timezone.utc),
                name="Workspace Assistant",
                description="This is a workspace assistant",
                tools=[],
                system=None,
            )
            session.add(workspace_assistant)
            session.commit()

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
        assert (
            workspace_assistant_data["workspace_id"] == test_headers["askui-workspace"]
        )

    def test_retrieve_default_assistant_success(
        self, test_client_and_session_factory, test_headers: dict[str, str]
    ) -> None:
        """Test that retrieving a default assistant works."""
        test_client, session_factory = test_client_and_session_factory

        # Create a default assistant (no workspace_id) in the database
        with session_factory() as session:
            db_assistant = AssistantModel(
                id="asst_defaultretrieve",
                workspace_id=None,  # No workspace_id = default
                created_at=datetime.now(timezone.utc),
                name="Default Assistant",
                description="This is a default assistant",
                tools=[],
                system=None,
            )
            session.add(db_assistant)
            session.commit()

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
        self, test_client_and_session_factory, test_headers: dict[str, str]
    ) -> None:
        """Test that workspace-scoped assistants can be modified and deleted."""
        test_client, session_factory = test_client_and_session_factory

        # Create a workspace-scoped assistant in the database
        with session_factory() as session:
            db_assistant = AssistantModel(
                id="asst_workspaceops",
                workspace_id=test_headers["askui-workspace"],
                created_at=datetime.now(timezone.utc),
                name="Workspace Assistant",
                description="This is a workspace assistant",
                tools=[],
                system=None,
            )
            session.add(db_assistant)
            session.commit()

        # Modify the workspace assistant
        response = test_client.post(
            "/v1/assistants/asst_workspaceops",
            headers=test_headers,
            json={"name": "Modified Workspace Assistant"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "Modified Workspace Assistant"
        assert data["workspace_id"] == test_headers["askui-workspace"]

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
