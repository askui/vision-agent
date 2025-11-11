from fastapi import APIRouter, status
from pydantic import BaseModel

from askui import __version__

router = APIRouter(prefix="/info", tags=["info"])


class Info(BaseModel):
    version: str


@router.get(
    "",
    summary="Get API Information",
    response_description="Return API information",
    status_code=status.HTTP_200_OK,
)
def get_info() -> Info:
    return Info(version=__version__)
