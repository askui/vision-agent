from typing import Any, Iterator

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from askui.chat.api.messages.models import (
    ROOT_MESSAGE_PARENT_ID,
    Message,
    MessageCreate,
)
from askui.chat.api.messages.orms import MessageOrm
from askui.chat.api.models import MessageId, ThreadId, WorkspaceId
from askui.chat.api.threads.orms import ThreadOrm
from askui.utils.api_utils import (
    LIST_LIMIT_MAX,
    ListOrder,
    ListQuery,
    ListResponse,
    NotFoundError,
)


class MessageService:
    """Service for managing Message resources with database persistence."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def _find_by_id(
        self, workspace_id: WorkspaceId, thread_id: ThreadId, message_id: MessageId
    ) -> MessageOrm:
        """Find message by ID."""
        message_orm: MessageOrm | None = (
            self._session.query(MessageOrm)
            .filter(
                MessageOrm.id == message_id,
                MessageOrm.thread_id == thread_id,
                MessageOrm.workspace_id == workspace_id,
            )
            .first()
        )
        if message_orm is None:
            error_msg = f"Message {message_id} not found in thread {thread_id}"
            raise NotFoundError(error_msg)
        return message_orm

    def retrieve_last_message_id(
        self, workspace_id: WorkspaceId, thread_id: ThreadId
    ) -> MessageId:
        """Get the last message ID in a thread. If no messages exist, return the root message ID."""
        return (
            self._session.execute(
                select(MessageOrm.id)
                .filter(
                    MessageOrm.thread_id == thread_id,
                    MessageOrm.workspace_id == workspace_id,
                )
                .order_by(desc(MessageOrm.id))
                .limit(1)
            ).scalar_one_or_none()
            or ROOT_MESSAGE_PARENT_ID
        )

    def create(
        self,
        workspace_id: WorkspaceId,
        thread_id: ThreadId,
        params: MessageCreate,
    ) -> Message:
        """Create a new message."""
        # Validate thread exists
        thread_orm: ThreadOrm | None = (
            self._session.query(ThreadOrm)
            .filter(
                ThreadOrm.id == thread_id,
                ThreadOrm.workspace_id == workspace_id,
            )
            .first()
        )
        if thread_orm is None:
            error_msg = f"Thread {thread_id} not found"
            raise NotFoundError(error_msg)

        if (
            params.parent_id is None
        ):  # If no parent ID is provided, use the last message in the thread
            params.parent_id = self.retrieve_last_message_id(workspace_id, thread_id)

        # Validate parent message exists (if not root)
        if params.parent_id and params.parent_id != ROOT_MESSAGE_PARENT_ID:
            parent_message_orm: MessageOrm | None = (
                self._session.query(MessageOrm)
                .filter(
                    MessageOrm.id == params.parent_id,
                    MessageOrm.thread_id == thread_id,
                    MessageOrm.workspace_id == workspace_id,
                )
                .first()
            )
            if parent_message_orm is None:
                error_msg = (
                    f"Parent message {params.parent_id} not found in thread {thread_id}"
                )
                raise NotFoundError(error_msg)

        message = Message.create(workspace_id, thread_id, params)
        message_orm = MessageOrm.from_model(message)
        self._session.add(message_orm)
        self._session.commit()
        return message

    def _get_path_endpoints(
        self, workspace_id: WorkspaceId, thread_id: ThreadId, query: ListQuery
    ) -> tuple[str, str] | None:
        """Determine the branch root and leaf node IDs for path traversal.

        Executes queries to get concrete ID values for the branch root and leaf nodes.

        Args:
            workspace_id (WorkspaceId): The workspace ID.
            thread_id (ThreadId): The thread ID.
            query (ListQuery): Pagination query (after/before, limit, order).

        Returns:
            tuple[str, str] | None: A tuple of (branch_root_id, leaf_id) where branch_root_id is the
                upper node (root) and leaf_id is the leaf node. Returns `None` if no messages exist
                in the thread.

        Raises:
            ValueError: If both `after` and `before` parameters are specified.
            NotFoundError: If the specified message in `before` or `after` does not exist.
        """
        if query.after and query.before:
            error_msg = "Cannot specify both 'after' and 'before' parameters"
            raise ValueError(error_msg)

        branch_root_id: str | None
        leaf_id: str | None
        if query.after:
            # Case 1: Set leaf_id to query.after and find the root by traversing up
            leaf_id = query.after

            # Build CTE to traverse up the tree from 'after' node
            _ancestors_cte = (
                select(MessageOrm.id, MessageOrm.parent_id)
                .filter(
                    MessageOrm.id == leaf_id,
                    MessageOrm.thread_id == thread_id,
                    MessageOrm.workspace_id == workspace_id,
                )
                .cte(name="ancestors", recursive=True)
            )

            # Recursively traverse up until we hit ROOT_MESSAGE_PARENT_ID
            _ancestors_recursive = select(MessageOrm.id, MessageOrm.parent_id).filter(
                MessageOrm.id == _ancestors_cte.c.parent_id,
                _ancestors_cte.c.parent_id != ROOT_MESSAGE_PARENT_ID,
            )
            _ancestors_cte = _ancestors_cte.union_all(_ancestors_recursive)

            # Get the root node (the one with parent_id == ROOT_MESSAGE_PARENT_ID)
            branch_root_id = self._session.execute(
                select(MessageOrm.id).filter(
                    MessageOrm.id.in_(select(_ancestors_cte.c.id)),
                    MessageOrm.parent_id == ROOT_MESSAGE_PARENT_ID,
                )
            ).scalar_one_or_none()

            if branch_root_id is None:
                error_msg = f"Message with id '{leaf_id}' not found"
                raise NotFoundError(error_msg)

        else:
            # Case 2: Set branch_root_id to query.before or ROOT node, then find latest leaf
            if query.before:
                branch_root_id = query.before
            else:
                # Get the latest root message
                branch_root_id = self._session.execute(
                    select(MessageOrm.id)
                    .filter(
                        MessageOrm.parent_id == ROOT_MESSAGE_PARENT_ID,
                        MessageOrm.thread_id == thread_id,
                        MessageOrm.workspace_id == workspace_id,
                    )
                    .order_by(desc(MessageOrm.id))
                    .limit(1)
                ).scalar_one_or_none()

                # If no messages exist yet, return None
                if branch_root_id is None:
                    return None

            # Build CTE to traverse down the tree from branch_root_id
            _descendants_cte = (
                select(MessageOrm.id, MessageOrm.parent_id)
                .filter(
                    MessageOrm.id == branch_root_id,
                )
                .cte(name="descendants", recursive=True)
            )

            # Recursively traverse down
            _descendants_recursive = select(MessageOrm.id, MessageOrm.parent_id).filter(
                MessageOrm.parent_id == _descendants_cte.c.id,
            )
            _descendants_cte = _descendants_cte.union_all(_descendants_recursive)

            # Get the latest leaf (highest ID)
            leaf_id = self._session.execute(
                select(_descendants_cte.c.id)
                .order_by(desc(_descendants_cte.c.id))
                .limit(1)
            ).scalar_one_or_none()

            # If no descendants found (e.g., query.before points to non-existent message)
            if leaf_id is None:
                _msg_id = branch_root_id
                error_msg = f"Message with id '{_msg_id}' not found"
                raise NotFoundError(error_msg)

        return branch_root_id, leaf_id

    def list_(
        self, workspace_id: WorkspaceId, thread_id: ThreadId, query: ListQuery
    ) -> ListResponse[Message]:
        """List messages in a tree path with pagination and filtering.

        Behavior:
        - If `before` is provided: Returns path from before that node down to latest leaf in its subtree (excludes the `after` node itself)
        - If `after` is provided: Returns path from after that node up to root (excludes the `after` node itself)
        - If neither: Returns main branch (root to latest leaf in entire thread)

        The method always identifies a start_id (upper node) and end_id (leaf node),
        then traverses from end_id up to start_id.

        Args:
            workspace_id (WorkspaceId): The workspace ID.
            thread_id (ThreadId): The thread ID.
            query (ListQuery): Pagination query (after/before, limit, order).

        Returns:
            ListResponse[Message]: Paginated list of messages in the tree path.

        Raises:
            ValueError: If both `after` and `before` parameters are specified.
            NotFoundError: If the specified message in `before` or `after` does not exist.
        """
        # Step 1: Get concrete branch_root_id and leaf_id
        _endpoints = self._get_path_endpoints(workspace_id, thread_id, query)

        # If no messages exist yet, return empty response
        if _endpoints is None:
            return ListResponse(data=[], has_more=False)

        _branch_root_id, _leaf_id = _endpoints

        # Step 2: Build path from leaf_id up to branch_root_id using recursive CTE
        # Start from leaf_id and traverse upward following parent_id until we reach branch_root_id
        _path_cte = (
            select(MessageOrm.id, MessageOrm.parent_id)
            .filter(
                MessageOrm.id == _leaf_id,
            )
            .cte(name="path", recursive=True)
        )

        # Recursively fetch parent nodes, stopping before we go past branch_root_id
        # No need to filter by thread_id/workspace_id - parent_id relationship ensures correct path
        _path_recursive = select(MessageOrm.id, MessageOrm.parent_id).filter(
            MessageOrm.id == _path_cte.c.parent_id,
            # Stop recursion: don't fetch parent of branch_root_id
            _path_cte.c.id != _branch_root_id,
        )

        _path_cte = _path_cte.union_all(_path_recursive)

        # Step 3: Fetch messages with pagination and ordering
        _query = self._session.query(MessageOrm).join(
            _path_cte, MessageOrm.id == _path_cte.c.id
        )

        # Build all filters at once for better query planning
        _filters: list[Any] = []
        if query.after:
            _filters.append(MessageOrm.id != query.after)
        if query.before:
            _filters.append(MessageOrm.id != query.before)

        if _filters:
            _query = _query.filter(*_filters)

        orms = (
            _query.order_by(
                MessageOrm.id if query.order == "asc" else desc(MessageOrm.id)
            )
            .limit(query.limit + 1)
            .all()
        )

        if not orms:
            return ListResponse(data=[], has_more=False)

        has_more = len(orms) > query.limit
        data = [orm.to_model() for orm in orms[: query.limit]]

        return ListResponse(
            data=data,
            has_more=has_more,
            first_id=data[0].id if data else None,
            last_id=data[-1].id if data else None,
        )

    def iter(
        self,
        workspace_id: WorkspaceId,
        thread_id: ThreadId,
        order: ListOrder = "asc",
        batch_size: int = LIST_LIMIT_MAX,
    ) -> Iterator[Message]:
        """Iterate through messages in batches."""

        has_more = True
        last_id: str | None = None
        while has_more:
            list_messages_response = self.list_(
                workspace_id=workspace_id,
                thread_id=thread_id,
                query=ListQuery(limit=batch_size, order=order, before=last_id),
            )
            has_more = list_messages_response.has_more
            last_id = list_messages_response.last_id
            for msg in list_messages_response.data:
                yield msg

    def retrieve(
        self, workspace_id: WorkspaceId, thread_id: ThreadId, message_id: MessageId
    ) -> Message:
        """Retrieve message by ID."""
        message_orm = self._find_by_id(workspace_id, thread_id, message_id)
        return message_orm.to_model()

    def delete(
        self, workspace_id: WorkspaceId, thread_id: ThreadId, message_id: MessageId
    ) -> None:
        """Delete a message."""
        message_orm = self._find_by_id(workspace_id, thread_id, message_id)
        self._session.delete(message_orm)
        self._session.commit()
