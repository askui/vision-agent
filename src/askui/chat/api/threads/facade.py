from collections.abc import AsyncGenerator

from askui.chat.api.messages.models import Message, MessageCreateParams
from askui.chat.api.messages.service import MessageService
from askui.chat.api.models import ThreadId, WorkspaceId
from askui.chat.api.runs.models import Run, RunCreateParams, ThreadAndRunCreateParams
from askui.chat.api.runs.runner.events.events import Events
from askui.chat.api.runs.service import RunService
from askui.chat.api.threads.service import ThreadService
from askui.utils.api_utils import ListQuery, ListResponse


class ThreadFacade:
    """
    Facade service that coordinates operations across threads, messages, and runs.
    """

    def __init__(
        self,
        thread_service: ThreadService,
        message_service: MessageService,
        run_service: RunService,
    ) -> None:
        self._thread_service = thread_service
        self._message_service = message_service
        self._run_service = run_service

    def _ensure_thread_exists(self, thread_id: ThreadId) -> None:
        """Validate that a thread exists before allowing operations on it."""
        self._thread_service.retrieve(thread_id)

    def create_message(
        self, thread_id: ThreadId, params: MessageCreateParams
    ) -> Message:
        """Create a message, ensuring the thread exists first."""
        self._ensure_thread_exists(thread_id)
        return self._message_service.create(thread_id, params)

    async def create_run(
        self, workspace_id: WorkspaceId, thread_id: ThreadId, params: RunCreateParams
    ) -> tuple[Run, AsyncGenerator[Events, None]]:
        """Create a run, ensuring the thread exists first."""
        self._ensure_thread_exists(thread_id)
        return await self._run_service.create(
            workspace_id=workspace_id,
            thread_id=thread_id,
            params=params,
        )

    async def create_thread_and_run(
        self, workspace_id: WorkspaceId, params: ThreadAndRunCreateParams
    ) -> tuple[Run, AsyncGenerator[Events, None]]:
        """Create a thread and a run, ensuring the thread exists first."""
        thread = self._thread_service.create(params.thread)
        return await self._run_service.create(
            workspace_id=workspace_id,
            thread_id=thread.id,
            params=params,
        )

    def list_messages(
        self, thread_id: ThreadId, query: ListQuery
    ) -> ListResponse[Message]:
        """List messages, ensuring the thread exists first."""
        self._ensure_thread_exists(thread_id)
        return self._message_service.list_(thread_id, query)

    def list_runs(self, thread_id: ThreadId, query: ListQuery) -> ListResponse[Run]:
        """List runs, ensuring the thread exists first."""
        self._ensure_thread_exists(thread_id)
        return self._run_service.list_(thread_id, query)
