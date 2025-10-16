import enum
from typing import Literal

from pydantic import BaseModel


class LogLevel(str, enum.Enum):
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"


class LogFormat(str, enum.Enum):
    JSON = "json"
    LOGFMT = "logfmt"


class EqualsLogFilter(BaseModel):
    type: Literal["equals"]
    key: str
    value: str


LogFilter = EqualsLogFilter


class LogSettings(BaseModel):
    format: LogFormat = LogFormat.LOGFMT
    level: LogLevel = LogLevel.INFO
    filters: list[LogFilter] | None = None
