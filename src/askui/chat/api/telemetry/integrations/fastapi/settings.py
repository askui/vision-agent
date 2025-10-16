from pydantic import BaseModel, Field

from askui.chat.api.telemetry.logs.settings import LogSettings


class TelemetrySettings(BaseModel):
    log: LogSettings = Field(default_factory=LogSettings)
