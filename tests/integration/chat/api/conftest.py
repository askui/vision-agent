"""Chat API integration test configuration and fixtures."""

import tempfile
import uuid
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from askui.chat.api.app import app
from askui.chat.api.files.service import FileService


@pytest.fixture
def test_app() -> FastAPI:
    """Get the FastAPI test application."""
    return app


@pytest.fixture
def test_client(test_app: FastAPI) -> TestClient:
    """Get a test client for the FastAPI application."""
    return TestClient(test_app)


@pytest.fixture
def temp_workspace_dir() -> Path:
    """Create a temporary workspace directory for testing."""
    temp_dir = tempfile.mkdtemp()
    return Path(temp_dir)


@pytest.fixture
def test_workspace_id() -> str:
    """Get a test workspace ID."""
    return str(uuid.uuid4())


@pytest.fixture
def test_headers(test_workspace_id: str) -> dict[str, str]:
    """Get test headers with workspace ID."""
    return {"askui-workspace": test_workspace_id}


@pytest.fixture
def mock_file_service(temp_workspace_dir: Path) -> FileService:
    """Create a mock file service with temporary workspace."""
    return FileService(temp_workspace_dir)


def create_test_app_with_overrides(workspace_path: Path) -> FastAPI:
    """Create a test app with all dependencies overridden."""
    from askui.chat.api.app import app
    from askui.chat.api.dependencies import SetEnvFromHeadersDep, get_workspace_dir
    from askui.chat.api.files.dependencies import get_file_service

    # Create a copy of the app to avoid modifying the global one
    test_app = FastAPI()
    test_app.router = app.router

    def override_workspace_dir() -> Path:
        return workspace_path

    def override_file_service() -> FileService:
        return FileService(workspace_path)

    def override_set_env_from_headers() -> None:
        # No-op for testing
        pass

    test_app.dependency_overrides[get_workspace_dir] = override_workspace_dir
    test_app.dependency_overrides[get_file_service] = override_file_service
    test_app.dependency_overrides[SetEnvFromHeadersDep] = override_set_env_from_headers

    return test_app
