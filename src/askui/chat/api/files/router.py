from typing import Annotated

from fastapi import APIRouter, Header, UploadFile, status
from fastapi.responses import FileResponse

from askui.chat.api.dependencies import ListQueryDep
from askui.chat.api.files.dependencies import FileServiceDep
from askui.chat.api.files.models import File as FileModel
from askui.chat.api.files.models import FileId
from askui.chat.api.files.service import FileService
from askui.chat.api.models import WorkspaceId
from askui.utils.api_utils import ListQuery, ListResponse

router = APIRouter(prefix="/files", tags=["files"])


@router.get("")
def list_files(
    askui_workspace: Annotated[WorkspaceId | None, Header()] = None,
    query: ListQuery = ListQueryDep,
    file_service: FileService = FileServiceDep,
) -> ListResponse[FileModel]:
    """List all files."""
    return file_service.list_(workspace_id=askui_workspace, query=query)


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile,
    askui_workspace: Annotated[WorkspaceId, Header()],
    file_service: FileService = FileServiceDep,
) -> FileModel:
    """Upload a new file."""
    return await file_service.upload_file(workspace_id=askui_workspace, file=file)


@router.get("/{file_id}")
def retrieve_file(
    file_id: FileId,
    askui_workspace: Annotated[WorkspaceId | None, Header()] = None,
    file_service: FileService = FileServiceDep,
) -> FileModel:
    """Get file metadata by ID."""
    return file_service.retrieve(workspace_id=askui_workspace, file_id=file_id)


@router.get("/{file_id}/content")
def download_file(
    file_id: FileId,
    askui_workspace: Annotated[WorkspaceId | None, Header()] = None,
    file_service: FileService = FileServiceDep,
) -> FileResponse:
    """Retrieve a file by ID."""
    file, file_path = file_service.retrieve_file_content(
        workspace_id=askui_workspace, file_id=file_id
    )
    return FileResponse(file_path, media_type=file.media_type, filename=file.filename)


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    file_id: FileId,
    askui_workspace: Annotated[WorkspaceId, Header()],
    file_service: FileService = FileServiceDep,
) -> None:
    """Delete a file by ID."""
    file_service.delete(workspace_id=askui_workspace, file_id=file_id)
