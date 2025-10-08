"""Chat API integration test configuration and fixtures."""

import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

import pytest
from askui.chat.api.app import app
from askui.chat.api.db.base import Base
from askui.chat.api.files.service import FileService
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


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
def test_db_engine():
    """Create in-memory SQLite database."""
    # Import all models to register them with Base.metadata

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def test_session_factory(test_db_engine):
    """Create session factory for testing."""
    SessionLocal = sessionmaker(bind=test_db_engine, expire_on_commit=False)

    @contextmanager
    def session_factory() -> Generator[Session, None, None]:
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    return session_factory


@pytest.fixture
def test_app_with_db(test_db_engine):
    """Create a test app with database tables created."""
    from askui.chat.api.db.base import Base
    from askui.chat.api.dependencies import SetEnvFromHeadersDep

    # Import all models to register them with Base.metadata
    from askui.chat.api.assistants.models import AssistantModel
    from askui.chat.api.threads.models import ThreadModel
    from askui.chat.api.messages.models import MessageModel
    from askui.chat.api.runs.models import RunModel
    from askui.chat.api.files.models import FileModel
    from askui.chat.api.mcp_configs.models import McpConfigModel
    from askui.chat.api.workflows.models import WorkflowModel, WorkflowTagModel
    from askui.chat.api.runs.events.models import EventModel
    from askui.chat.api.migrations.models import MigrationVersionModel

    # Create tables in the test database
    Base.metadata.create_all(test_db_engine)

    # Create a new app instance without lifespan
    test_app = FastAPI(
        title="AskUI Chat API",
        version="1.0.0",
        dependencies=[SetEnvFromHeadersDep],
    )

    # Import and include all routers
    from askui.chat.api.assistants.router import router as assistants_router
    from askui.chat.api.files.router import router as files_router
    from askui.chat.api.health.router import router as health_router
    from askui.chat.api.mcp_configs.router import router as mcp_configs_router
    from askui.chat.api.messages.router import router as messages_router
    from askui.chat.api.runs.router import router as runs_router
    from askui.chat.api.threads.router import router as threads_router
    from askui.chat.api.workflows.router import router as workflows_router

    v1_router = APIRouter(prefix="/v1")
    v1_router.include_router(assistants_router)
    v1_router.include_router(threads_router)
    v1_router.include_router(messages_router)
    v1_router.include_router(runs_router)
    v1_router.include_router(mcp_configs_router)
    v1_router.include_router(files_router)
    v1_router.include_router(workflows_router)
    v1_router.include_router(health_router)
    test_app.include_router(v1_router)

    return test_app


@pytest.fixture
def test_client_with_db(test_app_with_db, test_db_engine):
    """Get test client with database."""
    # Import all models to register them with Base.metadata
    from askui.chat.api.assistants.models import AssistantModel
    from askui.chat.api.threads.models import ThreadModel
    from askui.chat.api.messages.models import MessageModel
    from askui.chat.api.runs.models import RunModel
    from askui.chat.api.files.models import FileModel
    from askui.chat.api.mcp_configs.models import McpConfigModel
    from askui.chat.api.workflows.models import WorkflowModel, WorkflowTagModel
    from askui.chat.api.runs.events.models import EventModel
    from askui.chat.api.migrations.models import MigrationVersionModel

    # Ensure tables are created
    Base.metadata.create_all(test_db_engine)

    SessionLocal = sessionmaker(bind=test_db_engine, expire_on_commit=False)

    @contextmanager
    def session_factory() -> Generator[Session, None, None]:
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    from askui.chat.api.assistants.dependencies import get_assistant_service
    from askui.chat.api.assistants.service import AssistantService
    from askui.chat.api.dependencies import get_session_factory_dep, get_settings
    from askui.chat.api.files.dependencies import get_file_service
    from askui.chat.api.files.service import FileService
    from askui.chat.api.mcp_configs.dependencies import get_mcp_config_service
    from askui.chat.api.mcp_configs.service import McpConfigService
    from askui.chat.api.messages.dependencies import get_message_service
    from askui.chat.api.messages.service import MessageService
    from askui.chat.api.runs.dependencies import get_runs_service
    from askui.chat.api.runs.service import RunService
    from askui.chat.api.threads.dependencies import get_thread_service
    from askui.chat.api.threads.service import ThreadService
    from askui.chat.api.workflows.dependencies import get_workflow_service
    from askui.chat.api.workflows.service import WorkflowService

    def get_test_assistant_service() -> AssistantService:
        return AssistantService(session_factory)

    def get_test_file_service() -> FileService:
        return FileService(session_factory)

    def get_test_mcp_config_service() -> McpConfigService:
        return McpConfigService(session_factory, Path.cwd(), [])

    def get_test_message_service() -> MessageService:
        return MessageService(session_factory)

    def get_test_runs_service() -> RunService:
        from askui.chat.api.assistants.service import AssistantService
        from askui.chat.api.mcp_clients.manager import McpClientManagerManager
        from askui.chat.api.messages.chat_history_manager import ChatHistoryManager
        from askui.chat.api.settings import Settings

        mock_assistant_service = AssistantService(session_factory)
        mock_mcp_client_manager_manager = McpClientManagerManager()
        mock_chat_history_manager = ChatHistoryManager()
        mock_settings = Settings()

        return RunService(
            session_factory=session_factory,
            assistant_service=mock_assistant_service,
            mcp_client_manager_manager=mock_mcp_client_manager_manager,
            chat_history_manager=mock_chat_history_manager,
            settings=mock_settings,
        )

    def get_test_thread_service() -> ThreadService:
        from askui.chat.api.messages.service import MessageService
        from askui.chat.api.runs.service import RunService

        mock_message_service = MessageService(session_factory)
        mock_run_service = RunService(
            session_factory=session_factory,
            assistant_service=AssistantService(session_factory),
            mcp_client_manager_manager=McpClientManagerManager(),
            chat_history_manager=ChatHistoryManager(),
            settings=Settings(),
        )

        return ThreadService(
            session_factory=session_factory,
            message_service=mock_message_service,
            run_service=mock_run_service,
        )

    def get_test_workflow_service() -> WorkflowService:
        return WorkflowService(session_factory)

    def get_test_session_factory():
        return session_factory

    def get_test_settings():
        from askui.chat.api.settings import Settings
        settings = Settings()
        # Override the database URL to use the test database
        settings.db.url = f"sqlite:///:memory:"
        return settings

    # Override all dependencies
    test_app_with_db.dependency_overrides[get_settings] = get_test_settings
    test_app_with_db.dependency_overrides[get_session_factory_dep] = (
        get_test_session_factory
    )
    test_app_with_db.dependency_overrides[get_assistant_service] = (
        get_test_assistant_service
    )
    test_app_with_db.dependency_overrides[get_file_service] = get_test_file_service
    test_app_with_db.dependency_overrides[get_mcp_config_service] = (
        get_test_mcp_config_service
    )
    test_app_with_db.dependency_overrides[get_message_service] = (
        get_test_message_service
    )
    test_app_with_db.dependency_overrides[get_runs_service] = get_test_runs_service
    test_app_with_db.dependency_overrides[get_thread_service] = get_test_thread_service
    test_app_with_db.dependency_overrides[get_workflow_service] = (
        get_test_workflow_service
    )

    client = TestClient(test_app_with_db)
    yield client
    test_app_with_db.dependency_overrides.clear()


@pytest.fixture
def test_client_and_session_factory(test_app_with_db, test_db_engine):
    """Get test client and session factory that use the same database."""
    # Ensure tables are created
    Base.metadata.create_all(test_db_engine)

    SessionLocal = sessionmaker(bind=test_db_engine, expire_on_commit=False)

    @contextmanager
    def session_factory() -> Generator[Session, None, None]:
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    from askui.chat.api.assistants.dependencies import get_assistant_service
    from askui.chat.api.assistants.service import AssistantService
    from askui.chat.api.dependencies import get_session_factory_dep, get_settings
    from askui.chat.api.files.dependencies import get_file_service
    from askui.chat.api.files.service import FileService
    from askui.chat.api.mcp_configs.dependencies import get_mcp_config_service
    from askui.chat.api.mcp_configs.service import McpConfigService
    from askui.chat.api.messages.dependencies import get_message_service
    from askui.chat.api.messages.service import MessageService
    from askui.chat.api.runs.dependencies import get_runs_service
    from askui.chat.api.runs.service import RunService
    from askui.chat.api.threads.dependencies import get_thread_service
    from askui.chat.api.threads.service import ThreadService
    from askui.chat.api.workflows.dependencies import get_workflow_service
    from askui.chat.api.workflows.service import WorkflowService

    def get_test_assistant_service() -> AssistantService:
        return AssistantService(session_factory)

    def get_test_file_service() -> FileService:
        return FileService(session_factory)

    def get_test_mcp_config_service() -> McpConfigService:
        return McpConfigService(session_factory, Path.cwd(), [])

    def get_test_message_service() -> MessageService:
        return MessageService(session_factory)

    def get_test_runs_service() -> RunService:
        from askui.chat.api.assistants.service import AssistantService
        from askui.chat.api.mcp_clients.manager import McpClientManagerManager
        from askui.chat.api.messages.chat_history_manager import ChatHistoryManager
        from askui.chat.api.settings import Settings

        mock_assistant_service = AssistantService(session_factory)
        mock_mcp_client_manager_manager = McpClientManagerManager()
        mock_chat_history_manager = ChatHistoryManager()
        mock_settings = Settings()

        return RunService(
            session_factory=session_factory,
            assistant_service=mock_assistant_service,
            mcp_client_manager_manager=mock_mcp_client_manager_manager,
            chat_history_manager=mock_chat_history_manager,
            settings=mock_settings,
        )

    def get_test_thread_service() -> ThreadService:
        from askui.chat.api.messages.service import MessageService
        from askui.chat.api.runs.service import RunService

        mock_message_service = MessageService(session_factory)
        mock_run_service = RunService(
            session_factory=session_factory,
            assistant_service=AssistantService(session_factory),
            mcp_client_manager_manager=McpClientManagerManager(),
            chat_history_manager=ChatHistoryManager(),
            settings=Settings(),
        )

        return ThreadService(
            session_factory=session_factory,
            message_service=mock_message_service,
            run_service=mock_run_service,
        )

    def get_test_workflow_service() -> WorkflowService:
        return WorkflowService(session_factory)

    def get_test_session_factory():
        return session_factory

    # Override all dependencies
    test_app_with_db.dependency_overrides[get_session_factory_dep] = (
        get_test_session_factory
    )
    test_app_with_db.dependency_overrides[get_assistant_service] = (
        get_test_assistant_service
    )
    test_app_with_db.dependency_overrides[get_file_service] = get_test_file_service
    test_app_with_db.dependency_overrides[get_mcp_config_service] = (
        get_test_mcp_config_service
    )
    test_app_with_db.dependency_overrides[get_message_service] = (
        get_test_message_service
    )
    test_app_with_db.dependency_overrides[get_runs_service] = get_test_runs_service
    test_app_with_db.dependency_overrides[get_thread_service] = get_test_thread_service
    test_app_with_db.dependency_overrides[get_workflow_service] = (
        get_test_workflow_service
    )

    client = TestClient(test_app_with_db)
    yield client, session_factory
    test_app_with_db.dependency_overrides.clear()


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
