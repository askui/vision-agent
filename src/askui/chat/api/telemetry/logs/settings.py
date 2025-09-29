import enum

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


class LogSettings(BaseModel):
    format: LogFormat = LogFormat.LOGFMT
    level: LogLevel = LogLevel.INFO
