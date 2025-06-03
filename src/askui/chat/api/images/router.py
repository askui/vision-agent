from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from askui.chat.api.dependencies import SettingsDep
from askui.chat.api.settings import Settings

router = APIRouter(prefix="/images", tags=["images"])


@router.get("/{image_path:path}")
def get_image(
    image_path: str,
    settings: Settings = SettingsDep,
) -> FileResponse:
    """Get an image by path."""
    full_path = settings.data_dir / "images" / image_path
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(full_path)
