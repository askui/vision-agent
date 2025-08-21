from pathlib import Path

from fastapi import Depends

from askui.chat.api.dependencies import WorkspaceDirDep
from askui.chat.api.messages.dependencies import MessageServiceDep
from askui.chat.api.messages.service import MessageService
from askui.chat.api.repositories.file_repositories import FileThreadRepository
from askui.chat.api.threads.service import ThreadService


def get_thread_service(
    workspace_dir: Path = WorkspaceDirDep,
    message_service: MessageService = MessageServiceDep,
) -> ThreadService:
    """Get ThreadService instance with file repository."""
    repository = FileThreadRepository(workspace_dir)
    return ThreadService(
        repository=repository,
        message_service=message_service,
    )


ThreadServiceDep = Depends(get_thread_service)
