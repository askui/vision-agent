from collections.abc import AsyncGenerator

from askui.chat.api.models import WorkspaceId
from askui.chat.api.runs.events.events import Event
from askui.chat.api.runs.models import Run, ThreadAndRunCreate
from askui.chat.api.runs.service import RunService
from askui.chat.api.threads.service import ThreadService


class ThreadFacade:
    """
    Facade service that coordinates operations across threads, messages, and runs.
    """

    def __init__(
        self,
        thread_service: ThreadService,
        run_service: RunService,
    ) -> None:
        self._thread_service = thread_service
        self._run_service = run_service

    async def create_thread_and_run(
        self, workspace_id: WorkspaceId, params: ThreadAndRunCreate
    ) -> tuple[Run, AsyncGenerator[Event, None]]:
        """Create a thread and a run, ensuring the thread exists first."""
        thread = self._thread_service.create(workspace_id, params.thread)
        return await self._run_service.create(
            workspace_id=workspace_id,
            thread_id=thread.id,
            params=params,
        )
