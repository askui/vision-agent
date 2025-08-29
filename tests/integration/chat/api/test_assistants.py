"""Integration tests for the assistants API endpoints."""

import tempfile
from pathlib import Path

from fastapi import status
from fastapi.testclient import TestClient

from askui.chat.api.assistants.models import Assistant
from askui.chat.api.assistants.service import AssistantService


class TestAssistantsAPI:
    """Test suite for the assistants API endpoints."""

    def test_list_assistants_empty(self, test_headers: dict[str, str]) -> None:
        """Test listing assistants when no assistants exist."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)

        # Create a test app with overridden dependencies
        from askui.chat.api.app import app
        from askui.chat.api.assistants.dependencies import get_assistant_service

        def override_assistant_service() -> AssistantService:
            return AssistantService(workspace_path)

        app.dependency_overrides[get_assistant_service] = override_assistant_service

        try:
            with TestClient(app) as client:
                response = client.get("/v1/assistants", headers=test_headers)

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["object"] == "list"
                assert data["data"] == []
                assert data["has_more"] is False
        finally:
            app.dependency_overrides.clear()

    def test_list_assistants_with_assistants(
        self, test_headers: dict[str, str]
    ) -> None:
        """Test listing assistants when assistants exist."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        assistants_dir = workspace_path / "assistants"
        assistants_dir.mkdir(parents=True, exist_ok=True)

        # Create a mock assistant
        workspace_id = test_headers["askui-workspace"]
        mock_assistant = Assistant(
            id="asst_test123",
            object="assistant",
            created_at=1234567890,
            name="Test Assistant",
            description="A test assistant",
            avatar="test_avatar.png",
            workspace_id=workspace_id,
        )
        (assistants_dir / "asst_test123.json").write_text(
            mock_assistant.model_dump_json()
        )

        # Create a test app with overridden dependencies
        from askui.chat.api.app import app
        from askui.chat.api.assistants.dependencies import get_assistant_service

        def override_assistant_service() -> AssistantService:
            return AssistantService(workspace_path)

        app.dependency_overrides[get_assistant_service] = override_assistant_service

        try:
            with TestClient(app) as client:
                response = client.get("/v1/assistants", headers=test_headers)

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["object"] == "list"
                assert len(data["data"]) == 1
                assert data["data"][0]["id"] == "asst_test123"
                assert data["data"][0]["name"] == "Test Assistant"
        finally:
            app.dependency_overrides.clear()

    def test_list_assistants_with_pagination(
        self, test_headers: dict[str, str]
    ) -> None:
        """Test listing assistants with pagination parameters."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        assistants_dir = workspace_path / "assistants"
        assistants_dir.mkdir(parents=True, exist_ok=True)

        # Create multiple mock assistants
        workspace_id = test_headers["askui-workspace"]
        for i in range(5):
            mock_assistant = Assistant(
                id=f"asst_test{i}",
                object="assistant",
                created_at=1234567890 + i,
                name=f"Test Assistant {i}",
                description=f"Test assistant {i}",
                workspace_id=workspace_id,
            )
            (assistants_dir / f"asst_test{i}.json").write_text(
                mock_assistant.model_dump_json()
            )

        from askui.chat.api.app import app
        from askui.chat.api.assistants.dependencies import get_assistant_service

        def override_assistant_service() -> AssistantService:
            return AssistantService(workspace_path)

        app.dependency_overrides[get_assistant_service] = override_assistant_service

        try:
            with TestClient(app) as client:
                response = client.get("/v1/assistants?limit=3", headers=test_headers)

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert len(data["data"]) == 3
                assert data["has_more"] is True
        finally:
            app.dependency_overrides.clear()

    def test_create_assistant(self, test_headers: dict[str, str]) -> None:
        """Test creating a new assistant."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)

        from askui.chat.api.app import app
        from askui.chat.api.assistants.dependencies import get_assistant_service

        def override_assistant_service() -> AssistantService:
            return AssistantService(workspace_path)

        app.dependency_overrides[get_assistant_service] = override_assistant_service

        try:
            with TestClient(app) as client:
                assistant_data = {
                    "name": "New Test Assistant",
                    "description": "A newly created test assistant",
                    "avatar": "new_avatar.png",
                }
                response = client.post(
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
        finally:
            app.dependency_overrides.clear()

    def test_create_assistant_minimal(self, test_headers: dict[str, str]) -> None:
        """Test creating an assistant with minimal data."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)

        from askui.chat.api.app import app
        from askui.chat.api.assistants.dependencies import get_assistant_service

        def override_assistant_service() -> AssistantService:
            return AssistantService(workspace_path)

        app.dependency_overrides[get_assistant_service] = override_assistant_service

        try:
            with TestClient(app) as client:
                response = client.post("/v1/assistants", json={}, headers=test_headers)

                assert response.status_code == status.HTTP_201_CREATED
                data = response.json()
                assert data["object"] == "assistant"
                assert data["name"] is None
                assert data["description"] is None
                assert data["avatar"] is None
        finally:
            app.dependency_overrides.clear()

    def test_create_assistant_with_tools_and_system(
        self, test_headers: dict[str, str]
    ) -> None:
        """Test creating a new assistant with tools and system prompt."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)

        # Create a test app with overridden dependencies
        from askui.chat.api.app import app
        from askui.chat.api.assistants.dependencies import get_assistant_service

        def override_assistant_service() -> AssistantService:
            return AssistantService(workspace_path)

        app.dependency_overrides[get_assistant_service] = override_assistant_service

        try:
            with TestClient(app) as client:
                response = client.post(
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
        finally:
            app.dependency_overrides.clear()

    def test_create_assistant_with_empty_tools(
        self, test_headers: dict[str, str]
    ) -> None:
        """Test creating a new assistant with empty tools list."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)

        # Create a test app with overridden dependencies
        from askui.chat.api.app import app
        from askui.chat.api.assistants.dependencies import get_assistant_service

        def override_assistant_service() -> AssistantService:
            return AssistantService(workspace_path)

        app.dependency_overrides[get_assistant_service] = override_assistant_service

        try:
            with TestClient(app) as client:
                response = client.post(
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
        finally:
            app.dependency_overrides.clear()

    def test_retrieve_assistant(self, test_headers: dict[str, str]) -> None:
        """Test retrieving an existing assistant."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        assistants_dir = workspace_path / "assistants"
        assistants_dir.mkdir(parents=True, exist_ok=True)

        mock_assistant = Assistant(
            id="asst_test123",
            object="assistant",
            created_at=1234567890,
            name="Test Assistant",
            description="A test assistant",
        )
        (assistants_dir / "asst_test123.json").write_text(
            mock_assistant.model_dump_json()
        )

        from askui.chat.api.app import app
        from askui.chat.api.assistants.dependencies import get_assistant_service

        def override_assistant_service() -> AssistantService:
            return AssistantService(workspace_path)

        app.dependency_overrides[get_assistant_service] = override_assistant_service

        try:
            with TestClient(app) as client:
                response = client.get(
                    "/v1/assistants/asst_test123", headers=test_headers
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["id"] == "asst_test123"
                assert data["name"] == "Test Assistant"
                assert data["description"] == "A test assistant"
        finally:
            app.dependency_overrides.clear()

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

    def test_modify_assistant(self, test_headers: dict[str, str]) -> None:
        """Test modifying an existing assistant."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        assistants_dir = workspace_path / "assistants"
        assistants_dir.mkdir(parents=True, exist_ok=True)

        workspace_id = test_headers["askui-workspace"]
        mock_assistant = Assistant(
            id="asst_test123",
            object="assistant",
            created_at=1234567890,
            name="Original Name",
            description="Original description",
            workspace_id=workspace_id,
        )
        (assistants_dir / "asst_test123.json").write_text(
            mock_assistant.model_dump_json()
        )

        from askui.chat.api.app import app
        from askui.chat.api.assistants.dependencies import get_assistant_service

        def override_assistant_service() -> AssistantService:
            return AssistantService(workspace_path)

        app.dependency_overrides[get_assistant_service] = override_assistant_service

        try:
            with TestClient(app) as client:
                modify_data = {
                    "name": "Modified Name",
                    "description": "Modified description",
                }
                response = client.post(
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
        finally:
            app.dependency_overrides.clear()

    def test_modify_assistant_with_tools_and_system(
        self, test_headers: dict[str, str]
    ) -> None:
        """Test modifying an assistant with tools and system prompt."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        assistants_dir = workspace_path / "assistants"
        assistants_dir.mkdir(parents=True, exist_ok=True)

        workspace_id = test_headers["askui-workspace"]
        mock_assistant = Assistant(
            id="asst_test123",
            object="assistant",
            created_at=1234567890,
            name="Original Name",
            description="Original description",
            workspace_id=workspace_id,
        )
        (assistants_dir / "asst_test123.json").write_text(
            mock_assistant.model_dump_json()
        )

        from askui.chat.api.app import app
        from askui.chat.api.assistants.dependencies import get_assistant_service

        def override_assistant_service() -> AssistantService:
            return AssistantService(workspace_path)

        app.dependency_overrides[get_assistant_service] = override_assistant_service

        try:
            with TestClient(app) as client:
                modify_data = {
                    "name": "Modified Name",
                    "tools": ["new_tool1", "new_tool2"],
                    "system": "You are a modified custom assistant.",
                }
                response = client.post(
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
        finally:
            app.dependency_overrides.clear()

    def test_modify_assistant_partial(self, test_headers: dict[str, str]) -> None:
        """Test modifying an assistant with partial data."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        assistants_dir = workspace_path / "assistants"
        assistants_dir.mkdir(parents=True, exist_ok=True)

        workspace_id = test_headers["askui-workspace"]
        mock_assistant = Assistant(
            id="asst_test123",
            object="assistant",
            created_at=1234567890,
            name="Original Name",
            description="Original description",
            workspace_id=workspace_id,
        )
        (assistants_dir / "asst_test123.json").write_text(
            mock_assistant.model_dump_json()
        )

        from askui.chat.api.app import app
        from askui.chat.api.assistants.dependencies import get_assistant_service

        def override_assistant_service() -> AssistantService:
            return AssistantService(workspace_path)

        app.dependency_overrides[get_assistant_service] = override_assistant_service

        try:
            with TestClient(app) as client:
                modify_data = {"name": "Only Name Modified"}
                response = client.post(
                    "/v1/assistants/asst_test123",
                    json=modify_data,
                    headers=test_headers,
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["name"] == "Only Name Modified"
                assert data["description"] == "Original description"  # Unchanged
        finally:
            app.dependency_overrides.clear()

    def test_modify_assistant_not_found(
        self, test_client: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test modifying a non-existent assistant."""
        modify_data = {"name": "Modified Name"}
        response = test_client.post(
            "/v1/assistants/asst_nonexistent123", json=modify_data, headers=test_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_assistant(self, test_headers: dict[str, str]) -> None:
        """Test deleting an existing assistant."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        assistants_dir = workspace_path / "assistants"
        assistants_dir.mkdir(parents=True, exist_ok=True)

        workspace_id = test_headers["askui-workspace"]
        mock_assistant = Assistant(
            id="asst_test123",
            object="assistant",
            created_at=1234567890,
            name="Test Assistant",
            workspace_id=workspace_id,
        )
        (assistants_dir / "asst_test123.json").write_text(
            mock_assistant.model_dump_json()
        )

        from askui.chat.api.app import app
        from askui.chat.api.assistants.dependencies import get_assistant_service

        def override_assistant_service() -> AssistantService:
            return AssistantService(workspace_path)

        app.dependency_overrides[get_assistant_service] = override_assistant_service

        try:
            with TestClient(app) as client:
                response = client.delete(
                    "/v1/assistants/asst_test123", headers=test_headers
                )

                assert response.status_code == status.HTTP_204_NO_CONTENT
                assert response.content == b""
        finally:
            app.dependency_overrides.clear()

    def test_delete_assistant_not_found(
        self, test_client: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test deleting a non-existent assistant."""
        response = test_client.delete(
            "/v1/assistants/asst_nonexistent123", headers=test_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_modify_default_assistant_forbidden(
        self, test_headers: dict[str, str]
    ) -> None:
        """Test that modifying a default assistant returns 403 Forbidden."""
        # Create a default assistant (no workspace_id)
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        assistants_dir = workspace_path / "assistants"
        assistants_dir.mkdir(parents=True, exist_ok=True)

        default_assistant = Assistant(
            id="asst_default123",
            object="assistant",
            created_at=1234567890,
            name="Default Assistant",
            description="This is a default assistant",
            workspace_id=None,  # No workspace_id = default
        )
        (assistants_dir / "asst_default123.json").write_text(
            default_assistant.model_dump_json()
        )

        from askui.chat.api.app import app
        from askui.chat.api.assistants.dependencies import get_assistant_service

        def override_assistant_service() -> AssistantService:
            return AssistantService(workspace_path)

        app.dependency_overrides[get_assistant_service] = override_assistant_service

        try:
            with TestClient(app) as client:
                # Try to modify the default assistant
                response = client.post(
                    "/v1/assistants/asst_default123",
                    headers=test_headers,
                    json={"name": "Modified Name"},
                )
                assert response.status_code == 403
                assert "cannot be modified" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_delete_default_assistant_forbidden(
        self, test_headers: dict[str, str]
    ) -> None:
        """Test that deleting a default assistant returns 403 Forbidden."""
        # Create a default assistant (no workspace_id)
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        assistants_dir = workspace_path / "assistants"
        assistants_dir.mkdir(parents=True, exist_ok=True)

        default_assistant = Assistant(
            id="asst_default456",
            object="assistant",
            created_at=1234567890,
            name="Default Assistant",
            description="This is a default assistant",
            workspace_id=None,  # No workspace_id = default
        )
        (assistants_dir / "asst_default456.json").write_text(
            default_assistant.model_dump_json()
        )

        from askui.chat.api.app import app
        from askui.chat.api.assistants.dependencies import get_assistant_service

        def override_assistant_service() -> AssistantService:
            return AssistantService(workspace_path)

        app.dependency_overrides[get_assistant_service] = override_assistant_service

        try:
            with TestClient(app) as client:
                # Try to delete the default assistant
                response = client.delete(
                    "/v1/assistants/asst_default456",
                    headers=test_headers,
                )
                assert response.status_code == 403
                assert "cannot be deleted" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_list_assistants_includes_default_and_workspace(
        self, test_headers: dict[str, str]
    ) -> None:
        """Test that listing assistants includes both default and
        workspace-scoped ones.
        """
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        assistants_dir = workspace_path / "assistants"
        assistants_dir.mkdir(parents=True, exist_ok=True)

        # Create a default assistant (no workspace_id)
        default_assistant = Assistant(
            id="asst_default789",
            object="assistant",
            created_at=1234567890,
            name="Default Assistant",
            description="This is a default assistant",
            workspace_id=None,  # No workspace_id = default
        )
        (assistants_dir / "asst_default789.json").write_text(
            default_assistant.model_dump_json()
        )

        # Create a workspace-scoped assistant
        workspace_id = test_headers["askui-workspace"]
        workspace_assistant = Assistant(
            id="asst_workspace123",
            object="assistant",
            created_at=1234567890,
            name="Workspace Assistant",
            description="This is a workspace assistant",
            workspace_id=workspace_id,
        )
        (assistants_dir / "asst_workspace123.json").write_text(
            workspace_assistant.model_dump_json()
        )

        from askui.chat.api.app import app
        from askui.chat.api.assistants.dependencies import get_assistant_service

        def override_assistant_service() -> AssistantService:
            return AssistantService(workspace_path)

        app.dependency_overrides[get_assistant_service] = override_assistant_service

        try:
            with TestClient(app) as client:
                # List assistants - should include both
                response = client.get("/v1/assistants", headers=test_headers)
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
                assert workspace_assistant_data["workspace_id"] == workspace_id
        finally:
            app.dependency_overrides.clear()

    def test_retrieve_default_assistant_success(
        self, test_headers: dict[str, str]
    ) -> None:
        """Test that retrieving a default assistant works."""
        # Create a default assistant (no workspace_id)
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        assistants_dir = workspace_path / "assistants"
        assistants_dir.mkdir(parents=True, exist_ok=True)

        default_assistant = Assistant(
            id="asst_defaultretrieve",
            object="assistant",
            created_at=1234567890,
            name="Default Assistant",
            description="This is a default assistant",
            workspace_id=None,  # No workspace_id = default
        )
        (assistants_dir / "asst_defaultretrieve.json").write_text(
            default_assistant.model_dump_json()
        )

        from askui.chat.api.app import app
        from askui.chat.api.assistants.dependencies import get_assistant_service

        def override_assistant_service() -> AssistantService:
            return AssistantService(workspace_path)

        app.dependency_overrides[get_assistant_service] = override_assistant_service

        try:
            with TestClient(app) as client:
                # Retrieve the default assistant
                response = client.get(
                    "/v1/assistants/asst_defaultretrieve",
                    headers=test_headers,
                )
                assert response.status_code == 200

                data = response.json()
                assert data["id"] == "asst_defaultretrieve"
                assert data["workspace_id"] is None
        finally:
            app.dependency_overrides.clear()

    def test_workspace_scoped_assistant_operations_success(
        self, test_headers: dict[str, str]
    ) -> None:
        """Test that workspace-scoped assistants can be modified and deleted."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        assistants_dir = workspace_path / "assistants"
        assistants_dir.mkdir(parents=True, exist_ok=True)

        workspace_id = test_headers["askui-workspace"]
        workspace_assistant = Assistant(
            id="asst_workspaceops",
            object="assistant",
            created_at=1234567890,
            name="Workspace Assistant",
            description="This is a workspace assistant",
            workspace_id=workspace_id,
        )
        (assistants_dir / "asst_workspaceops.json").write_text(
            workspace_assistant.model_dump_json()
        )

        from askui.chat.api.app import app
        from askui.chat.api.assistants.dependencies import get_assistant_service

        def override_assistant_service() -> AssistantService:
            return AssistantService(workspace_path)

        app.dependency_overrides[get_assistant_service] = override_assistant_service

        try:
            with TestClient(app) as client:
                # Modify the workspace assistant
                response = client.post(
                    "/v1/assistants/asst_workspaceops",
                    headers=test_headers,
                    json={"name": "Modified Workspace Assistant"},
                )
                assert response.status_code == 200

                data = response.json()
                assert data["name"] == "Modified Workspace Assistant"
                assert data["workspace_id"] == workspace_id

                # Delete the workspace assistant
                response = client.delete(
                    "/v1/assistants/asst_workspaceops",
                    headers=test_headers,
                )
                assert response.status_code == 204

                # Verify it's deleted
                response = client.get(
                    "/v1/assistants/asst_workspaceops",
                    headers=test_headers,
                )
                assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()
