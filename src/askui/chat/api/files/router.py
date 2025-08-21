from fastapi import APIRouter, UploadFile, status
from fastapi.responses import FileResponse

from askui.chat.api.dependencies import ListQueryDep
from askui.chat.api.files.dependencies import FileServiceDep
from askui.chat.api.files.models import File as FileModel
from askui.chat.api.files.service import FileService
from askui.chat.api.models import FileId
from askui.utils.api_utils import ListQuery, ListResponse

router = APIRouter(prefix="/files", tags=["files"])


@router.get("")
def list_files(
    query: ListQuery = ListQueryDep,
    file_service: FileService = FileServiceDep,
) -> ListResponse[FileModel]:
    """List all files."""
    return file_service.list_(query=query)


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile,
    file_service: FileService = FileServiceDep,
) -> FileModel:
    """Upload a new file."""
    return await file_service.upload_file(file)


@router.get("/{file_id}")
def retrieve_file(
    file_id: FileId,
    file_service: FileService = FileServiceDep,
) -> FileModel:
    """Get file metadata by ID."""
    return file_service.retrieve(file_id)


@router.get("/{file_id}/content")
def download_file(
    file_id: FileId,
    file_service: FileService = FileServiceDep,
) -> FileResponse:
    """Retrieve a file by ID."""
    file, file_path = file_service.retrieve_file_content(file_id)
    return FileResponse(file_path, media_type=file.media_type, filename=file.filename)


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    file_id: FileId,
    file_service: FileService = FileServiceDep,
) -> None:
    """Delete a file by ID."""
    file_service.delete(file_id)
