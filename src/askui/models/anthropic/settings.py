from anthropic import NotGiven
from anthropic.types.beta import BetaToolChoiceAutoParam, BetaToolChoiceParam
from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings

from askui.models.shared.computer_agent import ComputerAgentSettingsBase
from askui.models.shared.settings import ChatCompletionsCreateSettings, ThinkingSettings

NOT_GIVEN = NotGiven()


class AnthropicSettings(BaseSettings):
    api_key: SecretStr = Field(
        default=...,
        min_length=1,
        validation_alias="ANTHROPIC_API_KEY",
    )


class ClaudeSettingsBase(BaseModel):
    anthropic: AnthropicSettings = Field(default_factory=lambda: AnthropicSettings())


class ClaudeSettings(ClaudeSettingsBase):
    resolution: tuple[int, int] = Field(default_factory=lambda: (1280, 800))
    chat_completions_create_settings: ChatCompletionsCreateSettings = Field(
        default_factory=ChatCompletionsCreateSettings,
        description="Settings for ChatCompletions",
    )


class ClaudeComputerAgentSettings(ComputerAgentSettingsBase, ClaudeSettingsBase):
    thinking: ThinkingSettings | None = None
    tool_choice: BetaToolChoiceParam | BetaToolChoiceAutoParam = (
        BetaToolChoiceAutoParam(type="auto")
    )
