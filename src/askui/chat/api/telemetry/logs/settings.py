import logging
from typing import Literal

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

LogFormat = Literal["JSON", "LOGFMT"]
LogLevel = Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]


class EqualsLogFilter(BaseModel):
    type: Literal["equals"]
    key: str
    value: str


LogFilter = EqualsLogFilter


class LogSettings(BaseModel):
    format: LogFormat = Field("LOGFMT")
    level: LogLevel = Field("INFO")
    filters: list[LogFilter] | None = None
