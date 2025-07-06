from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from askui.models.anthropic.messages_api import AnthropicMessagesApiSettings
from askui.models.askui.inference_api import AskUiInferenceApiSettings
from askui.models.shared.settings import ActSettings
from askui.telemetry import TelemetrySettings


class AnthropicSettings(BaseModel):
    messages_api: AnthropicMessagesApiSettings = Field(
        default_factory=AnthropicMessagesApiSettings
    )


class AskUiSettings(BaseModel):
    inference_api: AskUiInferenceApiSettings = Field(
        default_factory=AskUiInferenceApiSettings
    )


class Settings(BaseSettings):
    """Main settings class"""

    model_config = SettingsConfigDict(
        env_prefix="ASKUI__VA__",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter="__",
        extra="ignore",
    )

    telemetry: TelemetrySettings = Field(default_factory=TelemetrySettings)
    act: ActSettings = Field(default_factory=ActSettings)
    anthropic: AnthropicSettings = Field(default_factory=AnthropicSettings)
    askui: AskUiSettings = Field(default_factory=AskUiSettings)


SETTINGS = Settings()
