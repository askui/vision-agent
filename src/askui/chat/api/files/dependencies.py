from pathlib import Path

from fastapi import Depends

from askui.chat.api.dependencies import WorkspaceDirDep
from askui.chat.api.files.service import FileService


def get_file_service(workspace_dir: Path = WorkspaceDirDep) -> FileService:
    """Get FileService instance."""
    return FileService(workspace_dir)


FileServiceDep = Depends(get_file_service)
