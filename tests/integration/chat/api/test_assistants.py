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
        mock_assistant = Assistant(
            id="asst_test123",
            object="assistant",
            created_at=1234567890,
            name="Test Assistant",
            description="A test assistant",
            avatar="test_avatar.png",
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
        for i in range(5):
            mock_assistant = Assistant(
                id=f"asst_test{i}",
                object="assistant",
                created_at=1234567890 + i,
                name=f"Test Assistant {i}",
                description=f"Test assistant {i}",
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

        mock_assistant = Assistant(
            id="asst_test123",
            object="assistant",
            created_at=1234567890,
            name="Original Name",
            description="Original description",
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

    def test_modify_assistant_partial(self, test_headers: dict[str, str]) -> None:
        """Test modifying an assistant with partial data."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        assistants_dir = workspace_path / "assistants"
        assistants_dir.mkdir(parents=True, exist_ok=True)

        mock_assistant = Assistant(
            id="asst_test123",
            object="assistant",
            created_at=1234567890,
            name="Original Name",
            description="Original description",
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

        mock_assistant = Assistant(
            id="asst_test123",
            object="assistant",
            created_at=1234567890,
            name="Test Assistant",
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
