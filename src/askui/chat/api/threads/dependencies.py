from pathlib import Path

from fastapi import Depends

from askui.chat.api.dependencies import WorkspaceDirDep
from askui.chat.api.messages.dependencies import MessageServiceDep
from askui.chat.api.messages.service import MessageService
from askui.chat.api.runs.dependencies import RunServiceDep
from askui.chat.api.runs.service import RunService
from askui.chat.api.threads.facade import ThreadFacade
from askui.chat.api.threads.service import ThreadService


def get_thread_service(
    workspace_dir: Path = WorkspaceDirDep,
    message_service: MessageService = MessageServiceDep,
    run_service: RunService = RunServiceDep,
) -> ThreadService:
    """Get ThreadService instance."""
    return ThreadService(
        base_dir=workspace_dir,
        message_service=message_service,
        run_service=run_service,
    )


ThreadServiceDep = Depends(get_thread_service)


def get_thread_facade(
    thread_service: ThreadService = ThreadServiceDep,
    message_service: MessageService = MessageServiceDep,
    run_service: RunService = RunServiceDep,
) -> ThreadFacade:
    return ThreadFacade(
        thread_service=thread_service,
        message_service=message_service,
        run_service=run_service,
    )


ThreadFacadeDep = Depends(get_thread_facade)
