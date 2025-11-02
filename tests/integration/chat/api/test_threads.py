"""Integration tests for the threads API endpoints."""

from typing import TYPE_CHECKING
from uuid import UUID

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from askui.chat.api.threads.models import ThreadCreate
from askui.chat.api.threads.service import ThreadService

if TYPE_CHECKING:
    from askui.chat.api.models import WorkspaceId


class TestThreadsAPI:
    """Test suite for the threads API endpoints."""

    def test_list_threads_empty(
        self, test_client: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test listing threads when no threads exist."""
        response = test_client.get("/v1/threads", headers=test_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["object"] == "list"
        assert data["data"] == []
        assert data["has_more"] is False

    def test_list_threads_with_threads(
        self,
        test_db_session: Session,
        test_headers: dict[str, str],
        test_workspace_id: str,
    ) -> None:
        """Test listing threads when threads exist."""
        from askui.chat.api.app import app
        from askui.chat.api.threads.dependencies import get_thread_service

        thread_service = ThreadService(test_db_session)
        workspace_id: WorkspaceId = UUID(test_workspace_id)
        # Create a thread via the service
        created_thread = thread_service.create(
            workspace_id=workspace_id,
            params=ThreadCreate(name="Test Thread"),
        )

        def override_thread_service() -> ThreadService:
            return ThreadService(test_db_session)

        app.dependency_overrides[get_thread_service] = override_thread_service

        try:
            with TestClient(app) as client:
                response = client.get("/v1/threads", headers=test_headers)

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["object"] == "list"
                assert len(data["data"]) == 1
                assert data["data"][0]["id"] == created_thread.id
                assert data["data"][0]["name"] == "Test Thread"
        finally:
            app.dependency_overrides.clear()

    def test_list_threads_with_pagination(
        self,
        test_db_session: Session,
        test_headers: dict[str, str],
        test_workspace_id: str,
    ) -> None:
        """Test listing threads with pagination parameters."""
        from askui.chat.api.app import app
        from askui.chat.api.threads.dependencies import get_thread_service

        thread_service = ThreadService(test_db_session)
        workspace_id: WorkspaceId = UUID(test_workspace_id)
        # Create multiple threads via the service
        for i in range(5):
            thread_service.create(
                workspace_id=workspace_id,
                params=ThreadCreate(name=f"Test Thread {i}"),
            )

        def override_thread_service() -> ThreadService:
            return ThreadService(test_db_session)

        app.dependency_overrides[get_thread_service] = override_thread_service

        try:
            with TestClient(app) as client:
                response = client.get("/v1/threads?limit=3", headers=test_headers)

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert len(data["data"]) == 3
                assert data["has_more"] is True
        finally:
            app.dependency_overrides.clear()

    def test_create_thread(
        self, test_db_session: Session, test_headers: dict[str, str]
    ) -> None:
        """Test creating a new thread."""
        from askui.chat.api.app import app
        from askui.chat.api.threads.dependencies import get_thread_service

        def override_thread_service() -> ThreadService:
            return ThreadService(test_db_session)

        app.dependency_overrides[get_thread_service] = override_thread_service

        try:
            with TestClient(app) as client:
                thread_data = {
                    "name": "New Test Thread",
                }
                response = client.post(
                    "/v1/threads", json=thread_data, headers=test_headers
                )

                assert response.status_code == status.HTTP_201_CREATED
                data = response.json()
                assert data["name"] == "New Test Thread"
                assert data["object"] == "thread"
                assert "id" in data
                assert "created_at" in data
        finally:
            app.dependency_overrides.clear()

    def test_create_thread_minimal(
        self, test_db_session: Session, test_headers: dict[str, str]
    ) -> None:
        """Test creating a thread with minimal data."""
        from askui.chat.api.app import app
        from askui.chat.api.threads.dependencies import get_thread_service

        def override_thread_service() -> ThreadService:
            return ThreadService(test_db_session)

        app.dependency_overrides[get_thread_service] = override_thread_service

        try:
            with TestClient(app) as client:
                response = client.post("/v1/threads", json={}, headers=test_headers)

                assert response.status_code == status.HTTP_201_CREATED
                data = response.json()
                assert data["object"] == "thread"
                assert data["name"] is None
        finally:
            app.dependency_overrides.clear()

    def test_retrieve_thread(
        self,
        test_db_session: Session,
        test_headers: dict[str, str],
        test_workspace_id: str,
    ) -> None:
        """Test retrieving an existing thread."""
        from askui.chat.api.app import app
        from askui.chat.api.threads.dependencies import get_thread_service

        thread_service = ThreadService(test_db_session)
        workspace_id: WorkspaceId = UUID(test_workspace_id)
        # Create a thread via the service
        created_thread = thread_service.create(
            workspace_id=workspace_id,
            params=ThreadCreate(name="Test Thread"),
        )

        def override_thread_service() -> ThreadService:
            return ThreadService(test_db_session)

        app.dependency_overrides[get_thread_service] = override_thread_service

        try:
            with TestClient(app) as client:
                response = client.get(
                    f"/v1/threads/{created_thread.id}", headers=test_headers
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["id"] == created_thread.id
                assert data["name"] == "Test Thread"
        finally:
            app.dependency_overrides.clear()

    def test_retrieve_thread_not_found(
        self, test_client: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test retrieving a non-existent thread."""
        response = test_client.get(
            "/v1/threads/thread_nonexistent123", headers=test_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data

    def test_modify_thread(
        self,
        test_db_session: Session,
        test_headers: dict[str, str],
        test_workspace_id: str,
    ) -> None:
        """Test modifying an existing thread."""
        from askui.chat.api.app import app
        from askui.chat.api.threads.dependencies import get_thread_service

        thread_service = ThreadService(test_db_session)
        workspace_id: WorkspaceId = UUID(test_workspace_id)
        # Create a thread via the service
        created_thread = thread_service.create(
            workspace_id=workspace_id,
            params=ThreadCreate(name="Original Name"),
        )

        def override_thread_service() -> ThreadService:
            return ThreadService(test_db_session)

        app.dependency_overrides[get_thread_service] = override_thread_service

        try:
            with TestClient(app) as client:
                modify_data = {
                    "name": "Modified Name",
                }
                response = client.post(
                    f"/v1/threads/{created_thread.id}",
                    json=modify_data,
                    headers=test_headers,
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["name"] == "Modified Name"
                assert data["id"] == created_thread.id
                # API returns Unix timestamp, convert datetime to timestamp for
                # comparison
                assert data["created_at"] == int(created_thread.created_at.timestamp())
        finally:
            app.dependency_overrides.clear()

    def test_modify_thread_partial(
        self,
        test_db_session: Session,
        test_headers: dict[str, str],
        test_workspace_id: str,
    ) -> None:
        """Test modifying a thread with partial data."""
        from askui.chat.api.app import app
        from askui.chat.api.threads.dependencies import get_thread_service

        thread_service = ThreadService(test_db_session)
        workspace_id: WorkspaceId = UUID(test_workspace_id)
        # Create a thread via the service
        created_thread = thread_service.create(
            workspace_id=workspace_id,
            params=ThreadCreate(name="Original Name"),
        )

        def override_thread_service() -> ThreadService:
            return ThreadService(test_db_session)

        app.dependency_overrides[get_thread_service] = override_thread_service

        try:
            with TestClient(app) as client:
                modify_data = {"name": "Only Name Modified"}
                response = client.post(
                    f"/v1/threads/{created_thread.id}",
                    json=modify_data,
                    headers=test_headers,
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["name"] == "Only Name Modified"
        finally:
            app.dependency_overrides.clear()

    def test_modify_thread_not_found(
        self, test_client: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test modifying a non-existent thread."""
        modify_data = {"name": "Modified Name"}
        response = test_client.post(
            "/v1/threads/thread_nonexistent123", json=modify_data, headers=test_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_thread(
        self,
        test_db_session: Session,
        test_headers: dict[str, str],
        test_workspace_id: str,
    ) -> None:
        """Test deleting an existing thread."""
        from askui.chat.api.app import app
        from askui.chat.api.threads.dependencies import get_thread_service

        thread_service = ThreadService(test_db_session)
        workspace_id: WorkspaceId = UUID(test_workspace_id)
        # Create a thread via the service
        created_thread = thread_service.create(
            workspace_id=workspace_id,
            params=ThreadCreate(name="Test Thread"),
        )

        def override_thread_service() -> ThreadService:
            return ThreadService(test_db_session)

        app.dependency_overrides[get_thread_service] = override_thread_service

        try:
            with TestClient(app) as client:
                response = client.delete(
                    f"/v1/threads/{created_thread.id}", headers=test_headers
                )

                assert response.status_code == status.HTTP_204_NO_CONTENT
                assert response.content == b""
        finally:
            app.dependency_overrides.clear()

    def test_delete_thread_not_found(
        self, test_client: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test deleting a non-existent thread."""
        response = test_client.delete(
            "/v1/threads/thread_nonexistent123", headers=test_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
