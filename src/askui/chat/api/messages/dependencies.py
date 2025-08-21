from pathlib import Path

from fastapi import Depends

from askui.chat.api.dependencies import WorkspaceDirDep
from askui.chat.api.messages.service import MessageService
from askui.chat.api.repositories.file_repositories import FileMessageRepository


def get_message_service(
    workspace_dir: Path = WorkspaceDirDep,
) -> MessageService:
    """Get MessageService instance with file repository."""
    repository = FileMessageRepository(workspace_dir)
    return MessageService(repository)


MessageServiceDep = Depends(get_message_service)
