import base64
from functools import cached_property

from pydantic import UUID4, Field, HttpUrl, SecretStr
from pydantic_settings import BaseSettings

from askui.models.models import ModelName
from askui.models.shared.computer_agent import ComputerAgentSettingsBase


class AskUiSettings(BaseSettings):
    """Settings for AskUI API."""

    inference_endpoint: HttpUrl = Field(
        default_factory=lambda: HttpUrl("https://inference.askui.com"),  # noqa: F821
        validation_alias="ASKUI_INFERENCE_ENDPOINT",
    )
    workspace_id: UUID4 = Field(
        validation_alias="ASKUI_WORKSPACE_ID",
    )
    token: SecretStr = Field(
        validation_alias="ASKUI_TOKEN",
    )

    @cached_property
    def authorization_header(self) -> str:
        token_str = self.token.get_secret_value()
        token_base64 = base64.b64encode(token_str.encode()).decode()
        return f"Basic {token_base64}"

    @cached_property
    def base_url(self) -> str:
        # NOTE(OS): Pydantic parses urls with trailing slashes
        # meaning "https://inference.askui.com" turns into -> "https://inference.askui.com/"
        # https://github.com/pydantic/pydantic/issues/7186
        return f"{self.inference_endpoint}api/v1/workspaces/{self.workspace_id}"


class AskUiComputerAgentSettings(ComputerAgentSettingsBase):
    model: str = ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022
    askui: AskUiSettings = Field(default_factory=AskUiSettings)
