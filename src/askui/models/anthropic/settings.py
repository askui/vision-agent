from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings

from askui.models.shared.computer_agent import ComputerAgentSettingsBase
from askui.models.shared.settings import ChatCompletionsCreateSettings


class AnthropicSettings(BaseModel):
    api_key: SecretStr = Field(
        default=...,
        min_length=1,
        validation_alias="ANTHROPIC_API_KEY",
    )


class ClaudeSettingsBase(BaseSettings):
    anthropic: AnthropicSettings = Field(default=...)


class ClaudeSettings(ClaudeSettingsBase):
    resolution: tuple[int, int] = Field(default_factory=lambda: (1280, 800))
    chat_completions_create_settings: ChatCompletionsCreateSettings = Field(
        default_factory=ChatCompletionsCreateSettings,
        description="Settings for ChatCompletions",
    )


class ClaudeComputerAgentSettings(ComputerAgentSettingsBase, ClaudeSettingsBase):
    pass
