"""Unit tests for the MessageService."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy.orm import Session

from askui.chat.api.messages.models import (
    ROOT_MESSAGE_PARENT_ID,
    Message,
    MessageCreate,
)
from askui.chat.api.messages.service import MessageService
from askui.chat.api.threads.models import Thread
from askui.chat.api.threads.orms import ThreadOrm
from askui.utils.api_utils import ListQuery


class TestMessageServicePagination:
    """Test pagination behavior with different order and after/before parameters."""

    @pytest.fixture
    def _workspace_id(self) -> UUID:
        """Create a test workspace ID."""
        return uuid4()

    @pytest.fixture
    def _thread_id(self, test_db_session: Session, _workspace_id: UUID) -> str:
        """Create a test thread."""
        _thread = Thread(
            id="thread_testpagination",
            object="thread",
            created_at=datetime.now(timezone.utc),
            name="Test Thread for Pagination",
            workspace_id=_workspace_id,
        )
        _thread_orm = ThreadOrm.from_model(_thread)
        test_db_session.add(_thread_orm)
        test_db_session.commit()
        return _thread.id

    @pytest.fixture
    def _message_service(self, test_db_session: Session) -> MessageService:
        """Create a MessageService instance."""
        return MessageService(test_db_session)

    @pytest.fixture
    def _messages(
        self,
        _message_service: MessageService,
        _workspace_id: UUID,
        _thread_id: str,
    ) -> list[Message]:
        """Create two branches of messages for testing.

        Branch 1: Messages 0-9 (linear chain from ROOT)
        Branch 2: Messages 10-19 (separate linear chain from ROOT)
        """
        _created_messages: list[Message] = []

        # Create first branch: messages 0-9 (linear chain)
        for i in range(10):
            _msg = _message_service.create(
                workspace_id=_workspace_id,
                thread_id=_thread_id,
                params=MessageCreate(
                    role="user" if i % 2 == 0 else "assistant",
                    content=f"Test message {i}",
                    parent_id=(
                        ROOT_MESSAGE_PARENT_ID
                        if i == 0
                        else _created_messages[i - 1].id
                    ),
                ),
            )
            _created_messages.append(_msg)

        # Create second branch: messages 10-19 (separate linear chain from ROOT)
        for i in range(10, 20):
            _msg = _message_service.create(
                workspace_id=_workspace_id,
                thread_id=_thread_id,
                params=MessageCreate(
                    role="user" if i % 2 == 0 else "assistant",
                    content=f"Test message {i}",
                    parent_id=(
                        ROOT_MESSAGE_PARENT_ID
                        if i == 10
                        else _created_messages[i - 1].id
                    ),
                ),
            )
            _created_messages.append(_msg)

        return _created_messages

    def test_list_asc_without_after(
        self,
        _message_service: MessageService,
        _workspace_id: UUID,
        _thread_id: str,
        _messages: list[Message],
    ) -> None:
        """Test listing messages in ascending order without 'after' parameter."""
        # Without before/after, gets latest branch (branch 2)
        _response = _message_service.list_(
            workspace_id=_workspace_id,
            thread_id=_thread_id,
            query=ListQuery(limit=5, order="asc"),
        )

        assert len(_response.data) == 5
        # Should get the first 5 messages from branch 2 (10, 11, 12, 13, 14)
        assert [_msg.content for _msg in _response.data] == [
            "Test message 10",
            "Test message 11",
            "Test message 12",
            "Test message 13",
            "Test message 14",
        ]
        assert _response.has_more is True

    def test_list_asc_with_after(
        self,
        _message_service: MessageService,
        _workspace_id: UUID,
        _thread_id: str,
        _messages: list[Message],
    ) -> None:
        """Test listing messages in ascending order with 'after' parameter."""
        # First, get the first page from branch 2 (default)
        _first_page = _message_service.list_(
            workspace_id=_workspace_id,
            thread_id=_thread_id,
            query=ListQuery(limit=3, order="asc"),
        )

        assert len(_first_page.data) == 3
        assert [_msg.content for _msg in _first_page.data] == [
            "Test message 10",
            "Test message 11",
            "Test message 12",
        ]

        # Now get the second page using 'after'
        _second_page = _message_service.list_(
            workspace_id=_workspace_id,
            thread_id=_thread_id,
            query=ListQuery(limit=3, order="asc", after=_first_page.last_id),
        )

        assert len(_second_page.data) == 3
        # Should get the next 3 messages (13, 14, 15)
        assert [_msg.content for _msg in _second_page.data] == [
            "Test message 13",
            "Test message 14",
            "Test message 15",
        ]
        assert _second_page.has_more is True

        # Get the third page
        _third_page = _message_service.list_(
            workspace_id=_workspace_id,
            thread_id=_thread_id,
            query=ListQuery(limit=3, order="asc", after=_second_page.last_id),
        )

        assert len(_third_page.data) == 3
        # Should get the next 3 messages (16, 17, 18)
        assert [_msg.content for _msg in _third_page.data] == [
            "Test message 16",
            "Test message 17",
            "Test message 18",
        ]

    def test_list_desc_without_after(
        self,
        _message_service: MessageService,
        _workspace_id: UUID,
        _thread_id: str,
        _messages: list[Message],
    ) -> None:
        """Test listing messages in descending order without 'after' parameter."""
        # Without before/after, gets latest branch (branch 2)
        _response = _message_service.list_(
            workspace_id=_workspace_id,
            thread_id=_thread_id,
            query=ListQuery(limit=5, order="desc"),
        )

        assert len(_response.data) == 5
        # Should get the last 5 messages from branch 2 (19, 18, 17, 16, 15)
        assert [_msg.content for _msg in _response.data] == [
            "Test message 19",
            "Test message 18",
            "Test message 17",
            "Test message 16",
            "Test message 15",
        ]
        assert _response.has_more is True

    def test_list_desc_with_after(
        self,
        _message_service: MessageService,
        _workspace_id: UUID,
        _thread_id: str,
        _messages: list[Message],
    ) -> None:
        """Test listing messages in descending order with 'after' parameter."""
        # First, get the first page from branch 2 (default)
        _first_page = _message_service.list_(
            workspace_id=_workspace_id,
            thread_id=_thread_id,
            query=ListQuery(limit=3, order="desc"),
        )

        assert len(_first_page.data) == 3
        assert [_msg.content for _msg in _first_page.data] == [
            "Test message 19",
            "Test message 18",
            "Test message 17",
        ]

        # Now get the second page using 'after'
        _second_page = _message_service.list_(
            workspace_id=_workspace_id,
            thread_id=_thread_id,
            query=ListQuery(limit=3, order="desc", after=_first_page.last_id),
        )

        assert len(_second_page.data) == 3
        # Should get the previous 3 messages (16, 15, 14)
        assert [_msg.content for _msg in _second_page.data] == [
            "Test message 16",
            "Test message 15",
            "Test message 14",
        ]

    def test_iter_asc(
        self,
        _message_service: MessageService,
        _workspace_id: UUID,
        _thread_id: str,
        _messages: list[Message],
    ) -> None:
        """Test iterating through messages in ascending order."""
        # Without before/after, iter returns the latest branch (branch 2)
        _collected_messages: list[Message] = list(
            _message_service.iter(
                workspace_id=_workspace_id,
                thread_id=_thread_id,
                order="asc",
                batch_size=3,
            )
        )

        # Should get all 10 messages from branch 2 in ascending order
        assert len(_collected_messages) == 10
        assert [_msg.content for _msg in _collected_messages] == [
            f"Test message {i}" for i in range(10, 20)
        ]

    def test_iter_desc(
        self,
        _message_service: MessageService,
        _workspace_id: UUID,
        _thread_id: str,
        _messages: list[Message],
    ) -> None:
        """Test iterating through messages in descending order."""
        # Without before/after, iter returns the latest branch (branch 2)
        _collected_messages: list[Message] = list(
            _message_service.iter(
                workspace_id=_workspace_id,
                thread_id=_thread_id,
                order="desc",
                batch_size=3,
            )
        )

        # Should get all 10 messages from branch 2 in descending order
        assert len(_collected_messages) == 10
        assert [_msg.content for _msg in _collected_messages] == [
            f"Test message {i}" for i in range(19, 9, -1)
        ]

    def test_list_asc_with_before(
        self,
        _message_service: MessageService,
        _workspace_id: UUID,
        _thread_id: str,
        _messages: list[Message],
    ) -> None:
        """Test listing messages in ascending order with 'before' parameter."""
        # Get messages before message 7 in ascending order
        # Should get messages from root up to (but excluding) message 7
        _response = _message_service.list_(
            workspace_id=_workspace_id,
            thread_id=_thread_id,
            query=ListQuery(limit=10, order="asc", before=_messages[7].id),
        )

        # Should get messages 0-6 in ascending order
        assert len(_response.data) == 7
        assert [_msg.content for _msg in _response.data] == [
            f"Test message {i}" for i in range(7)
        ]
        assert _response.has_more is False

    def test_list_desc_with_before(
        self,
        _message_service: MessageService,
        _workspace_id: UUID,
        _thread_id: str,
        _messages: list[Message],
    ) -> None:
        """Test listing messages in descending order with 'before' parameter."""
        # Get messages before (i.e., after in the tree) message 3 in descending
        # order. Should get messages from message 3 down to the latest leaf
        # (excluding message 3)
        _response = _message_service.list_(
            workspace_id=_workspace_id,
            thread_id=_thread_id,
            query=ListQuery(limit=10, order="desc", before=_messages[3].id),
        )

        # Should get messages 9-4 in descending order (excluding message 3)
        assert len(_response.data) == 6
        assert [_msg.content for _msg in _response.data] == [
            f"Test message {i}" for i in range(9, 3, -1)
        ]
        assert _response.has_more is False

    def test_list_asc_with_before_paginated(
        self,
        _message_service: MessageService,
        _workspace_id: UUID,
        _thread_id: str,
        _messages: list[Message],
    ) -> None:
        """Test listing messages in ascending order with 'before' and pagination."""
        # Get 3 messages before message 7 in ascending order
        _response = _message_service.list_(
            workspace_id=_workspace_id,
            thread_id=_thread_id,
            query=ListQuery(limit=3, order="asc", before=_messages[7].id),
        )

        # Should get messages 0-2 in ascending order
        assert len(_response.data) == 3
        assert [_msg.content for _msg in _response.data] == [
            "Test message 0",
            "Test message 1",
            "Test message 2",
        ]
        assert _response.has_more is True

    def test_list_desc_with_before_paginated(
        self,
        _message_service: MessageService,
        _workspace_id: UUID,
        _thread_id: str,
        _messages: list[Message],
    ) -> None:
        """Test listing messages in descending order with 'before' and pagination."""
        # Get 3 messages before (after in tree) message 3 in descending order
        _response = _message_service.list_(
            workspace_id=_workspace_id,
            thread_id=_thread_id,
            query=ListQuery(limit=3, order="desc", before=_messages[3].id),
        )

        # Should get messages 9-7 in descending order
        assert len(_response.data) == 3
        assert [_msg.content for _msg in _response.data] == [
            "Test message 9",
            "Test message 8",
            "Test message 7",
        ]
        assert _response.has_more is True

    def test_list_branch1_with_after(
        self,
        _message_service: MessageService,
        _workspace_id: UUID,
        _thread_id: str,
        _messages: list[Message],
    ) -> None:
        """Test querying branch 1 by starting from its first message."""
        # Query from the first message of branch 1 downward
        _response = _message_service.list_(
            workspace_id=_workspace_id,
            thread_id=_thread_id,
            query=ListQuery(limit=20, order="asc", after=_messages[0].id),
        )

        # Should get messages 1-9 from branch 1 (excluding message 0)
        assert len(_response.data) == 9
        assert [_msg.content for _msg in _response.data] == [
            f"Test message {i}" for i in range(1, 10)
        ]
        assert _response.has_more is False

    def test_list_branch2_with_after(
        self,
        _message_service: MessageService,
        _workspace_id: UUID,
        _thread_id: str,
        _messages: list[Message],
    ) -> None:
        """Test querying branch 2 by starting from its first message."""
        # Query from the first message of branch 2 downward
        _response = _message_service.list_(
            workspace_id=_workspace_id,
            thread_id=_thread_id,
            query=ListQuery(limit=20, order="asc", after=_messages[10].id),
        )

        # Should get messages 11-19 from branch 2 (excluding message 10)
        assert len(_response.data) == 9
        assert [_msg.content for _msg in _response.data] == [
            f"Test message {i}" for i in range(11, 20)
        ]
        assert _response.has_more is False

    def test_list_branches_separately(
        self,
        _message_service: MessageService,
        _workspace_id: UUID,
        _thread_id: str,
        _messages: list[Message],
    ) -> None:
        """Test that the two branches are separate by querying from each."""
        # Get branch 1: query from branch 1's last message going up
        _branch1_response = _message_service.list_(
            workspace_id=_workspace_id,
            thread_id=_thread_id,
            query=ListQuery(limit=20, order="desc", after=_messages[9].id),
        )

        # Should get messages 9-0 from branch 1 in descending order
        assert len(_branch1_response.data) == 9
        assert [_msg.content for _msg in _branch1_response.data] == [
            f"Test message {i}" for i in range(8, -1, -1)
        ]

        # Get branch 2: query from branch 2's last message going up
        _branch2_response = _message_service.list_(
            workspace_id=_workspace_id,
            thread_id=_thread_id,
            query=ListQuery(limit=20, order="desc", after=_messages[19].id),
        )

        # Should get messages 19-10 from branch 2 in descending order
        assert len(_branch2_response.data) == 9
        assert [_msg.content for _msg in _branch2_response.data] == [
            f"Test message {i}" for i in range(18, 9, -1)
        ]

        # Verify no overlap between branches
        _branch1_ids = {_msg.id for _msg in _branch1_response.data}
        _branch2_ids = {_msg.id for _msg in _branch2_response.data}
        assert _branch1_ids.isdisjoint(_branch2_ids)
