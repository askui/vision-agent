from askui.chat.api.dependencies import SessionFactoryDep
from askui.chat.api.files.service import FileService
from fastapi import Depends


def get_file_service(session_factory=SessionFactoryDep) -> FileService:
    """Get FileService instance."""
    return FileService(session_factory)


FileServiceDep = Depends(get_file_service)
