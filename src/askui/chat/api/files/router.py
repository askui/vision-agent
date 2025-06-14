import tempfile
from pathlib import Path
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, UploadFile, status
from fastapi import File as FastAPIFile
from fastapi.responses import StreamingResponse

from askui.chat.api.files.dependencies import FileServiceDep
from askui.chat.api.files.service import File, FileService
from askui.chat.api.models import FileId, ListQuery, ListQueryDep, ListResponse

router = APIRouter(prefix="/files", tags=["files"])


@router.get("")
def list_files(
    query: ListQuery = ListQueryDep,
    file_service: FileService = FileServiceDep,
) -> ListResponse[File]:
    """List all files."""
    return file_service.list_(query=query)


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: Annotated[UploadFile, FastAPIFile(...)],
    file_service: FileService = FileServiceDep,
) -> File:
    """Upload a file.

    Args:
        file (UploadFile): The file to upload
        purpose (FilePurpose): Purpose of the file
        file_service (FileService): File service instance

    Returns:
        File: Created file object

    Raises:
        HTTPException: If purpose is not supported
    """
    # Create a temporary file with a unique name
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_path = Path(temp_file.name)
        try:
            # Write uploaded content to temp file
            content = await file.read()
            temp_file.write(content)
            temp_file.flush()  # Ensure all data is written to disk

            # Create file using the temp file and original filename if available
            return file_service.create(
                temp_path,
                filename=file.filename,
            )
        finally:
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()


@router.get("/{file_id}")
def retrieve_file(
    file_id: FileId,
    file_service: FileService = FileServiceDep,
) -> File:
    """Get a file by ID."""
    try:
        return file_service.retrieve(file_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/{file_id}/content")
def download_file(
    file_id: FileId,
    file_service: FileService = FileServiceDep,
) -> StreamingResponse:
    """Download a file's content."""
    try:
        file = file_service.retrieve(file_id)
        content = file_service.get_content(file_id)
        return StreamingResponse(
            iter([content]),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{quote(file.filename)}"',
                "Content-Length": str(file.bytes),
            },
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    file_id: FileId,
    file_service: FileService = FileServiceDep,
) -> None:
    """Delete a file."""
    try:
        file_service.delete(file_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
