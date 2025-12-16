from typing import Any, Iterator

from sqlalchemy import CTE, desc, select
from sqlalchemy.orm import Query, Session

from askui.chat.api.messages.models import (
    ROOT_MESSAGE_PARENT_ID,
    ContentBlockParam,
    Message,
    MessageCreate,
    ToolResultBlockParam,
    ToolUseBlockParam,
)
from askui.chat.api.messages.orms import MessageOrm
from askui.chat.api.models import MessageId, ThreadId, WorkspaceId
from askui.chat.api.threads.orms import ThreadOrm
from askui.utils.api_utils import (
    LIST_LIMIT_DEFAULT,
    ListOrder,
    ListQuery,
    ListResponse,
    NotFoundError,
)

_CANCELLED_TOOL_RESULT_CONTENT = (
    "Tool execution was cancelled because the previous run was interrupted. "
    "Please retry the operation if needed."
)


class MessageService:
    """Service for managing Message resources with database persistence."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def _create_cancelled_tool_results(
        self,
        workspace_id: WorkspaceId,
        thread_id: ThreadId,
        parent_message: Message,
        run_id: str | None,
    ) -> MessageId:
        """Create cancelled tool results if parent has pending tool_use blocks.

        Args:
            workspace_id (WorkspaceId): The workspace ID.
            thread_id (ThreadId): The thread ID.
            parent_message (Message): The parent message to check for tool_use blocks.
            run_id (str | None): The run ID to associate with the tool result message.

        Returns:
            MessageId: The ID of the created tool result message, or the parent
                message ID if no tool_use blocks were found.
        """
        if not isinstance(parent_message.content, list):
            return parent_message.id

        tool_use_blocks = [
            block
            for block in parent_message.content
            if isinstance(block, ToolUseBlockParam)
        ]
        if not tool_use_blocks:
            return parent_message.id

        tool_result_content: list[ContentBlockParam] = [
            ToolResultBlockParam(
                tool_use_id=block.id,
                content=_CANCELLED_TOOL_RESULT_CONTENT,
                is_error=True,
            )
            for block in tool_use_blocks
        ]
        tool_result_params = MessageCreate(
            role="user",
            content=tool_result_content,
            parent_id=parent_message.id,
            run_id=run_id,
        )
        tool_result_message = Message.create(
            workspace_id, thread_id, tool_result_params
        )
        self._session.add(MessageOrm.from_model(tool_result_message))
        return tool_result_message.id

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

    def _retrieve_latest_root(
        self, workspace_id: WorkspaceId, thread_id: ThreadId
    ) -> str | None:
        """Retrieve the latest root message ID in a thread.

        Args:
            workspace_id (WorkspaceId): The workspace ID.
            thread_id (ThreadId): The thread ID.

        Returns:
            str | None: The ID of the latest root message, or `None` if no root messages exist.
        """
        return self._session.execute(
            select(MessageOrm.id)
            .filter(
                MessageOrm.parent_id.is_(None),
                MessageOrm.thread_id == thread_id,
                MessageOrm.workspace_id == workspace_id,
            )
            .order_by(desc(MessageOrm.id))
            .limit(1)
        ).scalar_one_or_none()

    def _build_ancestors_cte(
        self, message_id: MessageId, workspace_id: WorkspaceId, thread_id: ThreadId
    ) -> CTE:
        """Build a recursive CTE to traverse up the message tree from a given message.

        Args:
            message_id (MessageId): The ID of the message to start traversing from.
            workspace_id (WorkspaceId): The workspace ID.
            thread_id (ThreadId): The thread ID.

        Returns:
            CTE: A recursive common table expression that contains all ancestors of the message.
        """
        # Build CTE to traverse up the tree from message_id
        _ancestors_cte = (
            select(MessageOrm.id, MessageOrm.parent_id)
            .filter(
                MessageOrm.id == message_id,
                MessageOrm.thread_id == thread_id,
                MessageOrm.workspace_id == workspace_id,
            )
            .cte(name="ancestors", recursive=True)
        )

        # Recursively traverse up until we hit NULL (root message)
        _ancestors_recursive = select(MessageOrm.id, MessageOrm.parent_id).filter(
            MessageOrm.id == _ancestors_cte.c.parent_id,
            _ancestors_cte.c.parent_id.is_not(None),
        )
        return _ancestors_cte.union_all(_ancestors_recursive)

    def _build_descendants_cte(self, message_id: MessageId) -> CTE:
        """Build a recursive CTE to traverse down the message tree from a given message.

        Args:
            message_id (MessageId): The ID of the message to start traversing from.

        Returns:
            CTE: A recursive common table expression that contains all descendants of the message.
        """
        # Build CTE to traverse down the tree from message_id
        _descendants_cte = (
            select(MessageOrm.id, MessageOrm.parent_id)
            .filter(
                MessageOrm.id == message_id,
            )
            .cte(name="descendants", recursive=True)
        )

        # Recursively traverse down
        _descendants_recursive = select(MessageOrm.id, MessageOrm.parent_id).filter(
            MessageOrm.parent_id == _descendants_cte.c.id,
        )
        return _descendants_cte.union_all(_descendants_recursive)

    def _retrieve_latest_leaf(self, message_id: MessageId) -> str | None:
        """Retrieve the latest leaf node in the subtree rooted at the given message.

        Args:
            message_id (MessageId): The ID of the root message to start from.

        Returns:
            str | None: The ID of the latest leaf node (highest ID), or `None` if no descendants exist.
        """
        # Build CTE to traverse down the tree from message_id
        _descendants_cte = self._build_descendants_cte(message_id)

        # Get the latest leaf (highest ID)
        return self._session.execute(
            select(_descendants_cte.c.id).order_by(desc(_descendants_cte.c.id)).limit(1)
        ).scalar_one_or_none()

    def _retrieve_branch_root(
        self, leaf_id: MessageId, workspace_id: WorkspaceId, thread_id: ThreadId
    ) -> str | None:
        """Retrieve the branch root node by traversing up from a leaf node.

        Args:
            leaf_id (MessageId): The ID of the leaf message to start from.
            workspace_id (WorkspaceId): The workspace ID.
            thread_id (ThreadId): The thread ID.

        Returns:
            str | None: The ID of the root node (with parent_id == NULL), or `None` if not found.
        """
        # Build CTE to traverse up the tree from leaf_id
        _ancestors_cte = self._build_ancestors_cte(leaf_id, workspace_id, thread_id)

        # Get the root node (the one with parent_id == NULL)
        return self._session.execute(
            select(MessageOrm.id).filter(
                MessageOrm.id.in_(select(_ancestors_cte.c.id)),
                MessageOrm.parent_id.is_(None),
            )
        ).scalar_one_or_none()

    def _build_path_query(self, path_start: str, path_end: str) -> Query[MessageOrm]:
        """Build a query for messages in the path from end to start.

        Args:
            path_start (str): The ID of the path start message (upper node).
            path_end (str): The ID of the path end message (lower node).

        Returns:
            Query[MessageOrm]: A query object for fetching messages in the path.
        """
        # Build path from path_end up to path_start using recursive CTE
        # Start from path_end and traverse upward following parent_id until we reach path_start
        _path_cte = (
            select(MessageOrm.id, MessageOrm.parent_id)
            .filter(
                MessageOrm.id == path_end,
            )
            .cte(name="path", recursive=True)
        )

        # Recursively fetch parent nodes, stopping before we go past path_start
        # No need to filter by thread_id/workspace_id - parent_id relationship ensures correct path
        _path_recursive = select(MessageOrm.id, MessageOrm.parent_id).filter(
            MessageOrm.id == _path_cte.c.parent_id,
            # Stop recursion: don't fetch parent of path_start
            _path_cte.c.id != path_start,
        )

        _path_cte = _path_cte.union_all(_path_recursive)

        return self._session.query(MessageOrm).join(
            _path_cte, MessageOrm.id == _path_cte.c.id
        )

    def retrieve_last_message_id(
        self, workspace_id: WorkspaceId, thread_id: ThreadId
    ) -> MessageId | None:
        """Get the last message ID in a thread. If no messages exist, return the root message ID."""
        return self._session.execute(
            select(MessageOrm.id)
            .filter(
                MessageOrm.thread_id == thread_id,
                MessageOrm.workspace_id == workspace_id,
            )
            .order_by(desc(MessageOrm.id))
            .limit(1)
        ).scalar_one_or_none()

    def create(
        self,
        workspace_id: WorkspaceId,
        thread_id: ThreadId,
        params: MessageCreate,
        inject_cancelled_tool_results: bool = False,
    ) -> Message:
        """Create a new message.

        Args:
            workspace_id (WorkspaceId): The workspace ID.
            thread_id (ThreadId): The thread ID.
            params (MessageCreate): The message creation parameters.
            inject_cancelled_tool_results (bool, optional): If `True`, inject cancelled
                tool results when the parent message has pending tool_use blocks.
                Defaults to `False`.
        """
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
            parent_id = self.retrieve_last_message_id(workspace_id, thread_id)

            # if the thread is empty, use the root message parent ID
            if parent_id is None:
                parent_id = ROOT_MESSAGE_PARENT_ID
            params.parent_id = parent_id

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

            # If parent has tool_use, create cancelled tool_result first
            if inject_cancelled_tool_results:
                params.parent_id = self._create_cancelled_tool_results(
                    workspace_id,
                    thread_id,
                    parent_message_orm.to_model(),
                    params.run_id,
                )

        message = Message.create(workspace_id, thread_id, params)
        message_orm = MessageOrm.from_model(message)
        self._session.add(message_orm)
        self._session.commit()
        return message

    def _get_path_endpoints(
        self, workspace_id: WorkspaceId, thread_id: ThreadId, query: ListQuery
    ) -> tuple[str, str] | None:
        """Determine the path start and end node IDs for path traversal.

        Executes queries to get concrete ID values for the path start and end nodes.

        Args:
            workspace_id (WorkspaceId): The workspace ID.
            thread_id (ThreadId): The thread ID.
            query (ListQuery): Pagination query (after/before, limit, order).

        Returns:
            tuple[str, str] | None: A tuple of (path_start, path_end) where path_start is the
                upper node and path_end is the lower node. Returns `None` if no messages exist
                in the thread.

        Raises:
            ValueError: If both `after` and `before` parameters are specified.
            NotFoundError: If the specified message in `before` or `after` does not exist.
        """
        if query.after and query.before:
            error_msg = "Cannot specify both 'after' and 'before' parameters"
            raise ValueError(error_msg)

        # Determine cursor and direction based on after/before and order
        # Key insight: (after+desc) and (before+asc) both traverse UP (towards root)
        #              (after+asc) and (before+desc) both traverse DOWN (towards leaves)
        _cursor = query.after or query.before
        _should_traverse_up = (query.after and query.order == "desc") or (
            query.before and query.order == "asc"
        )

        path_start: str | None
        path_end: str | None

        if _cursor:
            if _should_traverse_up:
                # Traverse UP: set path_end to cursor and find path_start by going to root
                path_end = _cursor
                path_start = self._retrieve_branch_root(
                    path_end, workspace_id, thread_id
                )
                if path_start is None:
                    error_msg = f"Message with id '{path_end}' not found"
                    raise NotFoundError(error_msg)
            else:
                # Traverse DOWN: set path_start to cursor and find path_end by going to leaf
                path_start = _cursor
                path_end = self._retrieve_latest_leaf(path_start)
                if path_end is None:
                    error_msg = f"Message with id '{path_start}' not found"
                    raise NotFoundError(error_msg)
        else:
            # No pagination - get the full branch from latest root to latest leaf
            path_end = self.retrieve_last_message_id(workspace_id, thread_id)
            if path_end is None:
                return None
            path_start = self._retrieve_branch_root(path_end, workspace_id, thread_id)
            if path_start is None:
                error_msg = f"Message with id '{path_end}' not found"
                raise NotFoundError(error_msg)

        return path_start, path_end

    def list_(
        self, workspace_id: WorkspaceId, thread_id: ThreadId, query: ListQuery
    ) -> ListResponse[Message]:
        """List messages in a tree path with pagination and filtering.

        Behavior:
        - If `after` is provided:
          - With `order=desc`: Returns path from `after` node up to root (excludes `after` itself)
          - With `order=asc`: Returns path from `after` node down to latest leaf (excludes `after` itself)
        - If `before` is provided:
          - With `order=asc`: Returns path from `before` node up to root (excludes `before` itself)
          - With `order=desc`: Returns path from `before` node down to latest leaf (excludes `before` itself)
        - If neither: Returns main branch (root to latest leaf in entire thread)

        The method identifies a start_id (upper node) and end_id (leaf node),
        traverses from end_id up to start_id, then applies the specified order.

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
        # Step 1: Get concrete path_start and path_end
        _endpoints = self._get_path_endpoints(workspace_id, thread_id, query)

        # If no messages exist yet, return empty response
        if _endpoints is None:
            return ListResponse(data=[], has_more=False)

        _path_start, _path_end = _endpoints

        # Step 2: Build path query from path_end up to path_start
        _query = self._build_path_query(_path_start, _path_end)

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
        batch_size: int = LIST_LIMIT_DEFAULT,
    ) -> Iterator[Message]:
        """Iterate through messages in batches."""

        has_more = True
        last_id: str | None = None
        while has_more:
            list_messages_response = self.list_(
                workspace_id=workspace_id,
                thread_id=thread_id,
                query=ListQuery(limit=batch_size, order=order, after=last_id),
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

    def list_siblings(
        self,
        workspace_id: WorkspaceId,
        thread_id: ThreadId,
        message_id: MessageId,
    ) -> list[Message]:
        """List all sibling messages for a given message.

        Sibling messages are messages that share the same `parent_id` as the specified message.
        The specified message itself is included in the results.
        Results are sorted by ID (chronological order, as IDs are BSON-based).

        Args:
            workspace_id (WorkspaceId): The workspace ID.
            thread_id (ThreadId): The thread ID.
            message_id (MessageId): The message ID to find siblings for.

        Returns:
            list[Message]: List of sibling messages sorted by ID.

        Raises:
            NotFoundError: If the specified message does not exist.
        """
        # Query for all sibling messages using a subquery to get parent_id
        _parent_id_subquery = (
            select(MessageOrm.parent_id)
            .filter(
                MessageOrm.id == message_id,
                MessageOrm.thread_id == thread_id,
                MessageOrm.workspace_id == workspace_id,
            )
            .scalar_subquery()
        )

        orms = (
            self._session.query(MessageOrm)
            .filter(
                MessageOrm.parent_id.is_not_distinct_from(_parent_id_subquery),
                MessageOrm.thread_id == thread_id,
                MessageOrm.workspace_id == workspace_id,
            )
            .order_by(desc(MessageOrm.id))
            .all()
        )

        # Validate that the message exists (if no results, message doesn't exist)
        if not orms:
            error_msg = f"Message {message_id} not found in thread {thread_id}"
            raise NotFoundError(error_msg)

        return [orm.to_model() for orm in orms]
