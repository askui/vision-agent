from pathlib import Path

from fastapi import Depends

from askui.chat.api.dependencies import WorkspaceDirDep
from askui.chat.api.messages.service import MessageService


def get_message_service(
    workspace_dir: Path = WorkspaceDirDep,
) -> MessageService:
    """Get MessagePersistedService instance."""
    return MessageService(workspace_dir)


MessageServiceDep = Depends(get_message_service)
