from fastapi import APIRouter, status
from pydantic import BaseModel

router = APIRouter(prefix="/health", tags=["healthcheck"])


class HealthCheck(BaseModel):
    status: str = "OK"


@router.get(
    "",
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
)
def get_health() -> HealthCheck:
    return HealthCheck(status="OK")
