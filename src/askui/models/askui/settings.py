import base64
from functools import cached_property

from pydantic import UUID4, BaseModel, Field, HttpUrl, SecretStr
from pydantic_settings import BaseSettings

COMPUTER_USE_BETA_FLAG = "computer-use-2024-10-22"


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
        return f"{self.inference_endpoint}/api/v1/workspaces/{self.workspace_id}"


class ClaudeSettingsBase(BaseModel):
    model: str = "claude-3-5-sonnet-20241022"
    askui: AskUiSettings = Field(default_factory=AskUiSettings)


class ClaudeSettings(ClaudeSettingsBase):
    resolution: tuple[int, int] = Field(default_factory=lambda: (1280, 800))
    max_tokens: int = 1000
    temperature: float = 0.0


class AskUiClaudeComputerAgentSettings(ClaudeSettingsBase):
    max_tokens: int = 4096
    only_n_most_recent_images: int = 3
    image_truncation_threshold: int = 10
    betas: list[str] = Field(default_factory=lambda: [COMPUTER_USE_BETA_FLAG])
