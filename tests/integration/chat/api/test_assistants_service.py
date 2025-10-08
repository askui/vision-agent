"""Unit tests for the assistants service."""

import uuid
from contextlib import contextmanager

import pytest
from askui.chat.api.assistants.schemas import (
    AssistantCreateParams,
    AssistantModifyParams,
)
from askui.chat.api.assistants.service import AssistantService
from askui.chat.api.db.base import Base
from askui.utils.api_utils import ListQuery
from askui.utils.not_given import NOT_GIVEN
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def test_db_engine():
    """Create in-memory SQLite database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def test_session_factory(test_db_engine):
    """Create session factory for testing."""
    SessionLocal = sessionmaker(bind=test_db_engine, expire_on_commit=False)

    @contextmanager
    def session_factory():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    return session_factory


@pytest.fixture
def assistant_service(test_session_factory):
    """Create assistant service for testing."""
    return AssistantService(test_session_factory)


@pytest.fixture
def test_workspace_id():
    """Get a test workspace ID."""
    return str(uuid.uuid4())


class TestAssistantService:
    """Test suite for the AssistantService."""

    def test_create_assistant(
        self, assistant_service: AssistantService, test_workspace_id: str
    ) -> None:
        """Test creating a new assistant."""
        params = AssistantCreateParams(
            name="Test Assistant",
            description="A test assistant",
            tools=["tool1", "tool2"],
            system="You are a helpful assistant.",
        )

        assistant = assistant_service.create(
            workspace_id=test_workspace_id, params=params
        )

        assert assistant.name == "Test Assistant"
        assert assistant.description == "A test assistant"
        assert assistant.tools == ["tool1", "tool2"]
        assert assistant.system == "You are a helpful assistant."
        assert str(assistant.workspace_id) == test_workspace_id
        assert assistant.id.startswith("asst_")
        assert assistant.created_at is not None

    def test_list_assistants_empty(
        self, assistant_service: AssistantService, test_workspace_id: str
    ) -> None:
        """Test listing assistants when no assistants exist."""
        query = ListQuery()
        result = assistant_service.list_(workspace_id=test_workspace_id, query=query)

        assert len(result.data) == 0
        assert result.has_more is False
        assert result.first_id is None
        assert result.last_id is None

    def test_list_assistants_with_data(
        self, assistant_service: AssistantService, test_workspace_id: str
    ) -> None:
        """Test listing assistants when assistants exist."""
        # Create multiple assistants
        for i in range(3):
            params = AssistantCreateParams(
                name=f"Assistant {i}",
                description=f"Test assistant {i}",
                tools=[],
                system=None,
            )
            assistant_service.create(workspace_id=test_workspace_id, params=params)

        query = ListQuery()
        result = assistant_service.list_(workspace_id=test_workspace_id, query=query)

        assert len(result.data) == 3
        assert result.has_more is False
        assert result.first_id is not None
        assert result.last_id is not None
        assert (
            result.data[0].name == "Assistant 2"
        )  # Should be ordered by created_at desc (newest first)

    def test_retrieve_assistant(
        self, assistant_service: AssistantService, test_workspace_id: str
    ) -> None:
        """Test retrieving an existing assistant."""
        params = AssistantCreateParams(
            name="Test Assistant",
            description="A test assistant",
            tools=[],
            system=None,
        )
        created_assistant = assistant_service.create(
            workspace_id=test_workspace_id, params=params
        )

        retrieved_assistant = assistant_service.retrieve(
            workspace_id=test_workspace_id, assistant_id=created_assistant.id
        )

        assert retrieved_assistant.id == created_assistant.id
        assert retrieved_assistant.name == "Test Assistant"
        assert retrieved_assistant.description == "A test assistant"

    def test_modify_assistant(
        self, assistant_service: AssistantService, test_workspace_id: str
    ) -> None:
        """Test modifying an existing assistant."""
        params = AssistantCreateParams(
            name="Original Name",
            description="Original description",
            tools=[],
            system=None,
        )
        created_assistant = assistant_service.create(
            workspace_id=test_workspace_id, params=params
        )

        modify_params = AssistantModifyParams(
            name="Modified Name",
            description="Modified description",
            tools=["new_tool"],
            system="You are a modified assistant.",
        )

        modified_assistant = assistant_service.modify(
            workspace_id=test_workspace_id,
            assistant_id=created_assistant.id,
            params=modify_params,
        )

        assert modified_assistant.id == created_assistant.id
        assert modified_assistant.name == "Modified Name"
        assert modified_assistant.description == "Modified description"
        assert modified_assistant.tools == ["new_tool"]
        assert modified_assistant.system == "You are a modified assistant."

    def test_modify_assistant_partial(
        self, assistant_service: AssistantService, test_workspace_id: str
    ) -> None:
        """Test modifying an assistant with partial data."""
        params = AssistantCreateParams(
            name="Original Name",
            description="Original description",
            tools=[],
            system=None,
        )
        created_assistant = assistant_service.create(
            workspace_id=test_workspace_id, params=params
        )

        modify_params = AssistantModifyParams(
            name="Modified Name",
            description=NOT_GIVEN,
            tools=NOT_GIVEN,
            system=NOT_GIVEN,
        )

        modified_assistant = assistant_service.modify(
            workspace_id=test_workspace_id,
            assistant_id=created_assistant.id,
            params=modify_params,
        )

        assert modified_assistant.id == created_assistant.id
        assert modified_assistant.name == "Modified Name"
        assert modified_assistant.description == "Original description"  # Unchanged
        assert modified_assistant.tools == []  # Unchanged
        assert modified_assistant.system is None  # Unchanged

    def test_delete_assistant(
        self, assistant_service: AssistantService, test_workspace_id: str
    ) -> None:
        """Test deleting an existing assistant."""
        params = AssistantCreateParams(
            name="Test Assistant",
            description="A test assistant",
            tools=[],
            system=None,
        )
        created_assistant = assistant_service.create(
            workspace_id=test_workspace_id, params=params
        )

        # Delete the assistant
        assistant_service.delete(
            workspace_id=test_workspace_id, assistant_id=created_assistant.id
        )

        # Try to retrieve it - should raise NotFoundError
        with pytest.raises(Exception):  # Should be NotFoundError
            assistant_service.retrieve(
                workspace_id=test_workspace_id, assistant_id=created_assistant.id
            )

    def test_workspace_isolation(self, assistant_service: AssistantService) -> None:
        """Test that assistants are isolated by workspace."""
        workspace1 = str(uuid.uuid4())
        workspace2 = str(uuid.uuid4())

        # Create assistant in workspace1
        params1 = AssistantCreateParams(
            name="Workspace 1 Assistant", tools=[], system=None
        )
        assistant1 = assistant_service.create(workspace_id=workspace1, params=params1)

        # Create assistant in workspace2
        params2 = AssistantCreateParams(
            name="Workspace 2 Assistant", tools=[], system=None
        )
        assistant2 = assistant_service.create(workspace_id=workspace2, params=params2)

        # List assistants in workspace1 - should only see assistant1
        query = ListQuery()
        result1 = assistant_service.list_(workspace_id=workspace1, query=query)
        assert len(result1.data) == 1
        assert result1.data[0].id == assistant1.id

        # List assistants in workspace2 - should only see assistant2
        result2 = assistant_service.list_(workspace_id=workspace2, query=query)
        assert len(result2.data) == 1
        assert result2.data[0].id == assistant2.id

        # Try to retrieve assistant1 from workspace2 - should fail
        with pytest.raises(Exception):  # Should be NotFoundError
            assistant_service.retrieve(
                workspace_id=workspace2, assistant_id=assistant1.id
            )
        with pytest.raises(Exception):  # Should be NotFoundError
            assistant_service.retrieve(
                workspace_id=workspace2, assistant_id=assistant1.id
            )
