from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings

from askui.models.shared.computer_agent import ComputerAgentSettingsBase

COMPUTER_USE_BETA_FLAG = "computer-use-2024-10-22"


class AnthropicSettings(BaseSettings):
    api_key: SecretStr = Field(
        min_length=1,
        validation_alias="ANTHROPIC_API_KEY",
    )


class ClaudeSettingsBase(BaseModel):
    anthropic: AnthropicSettings = Field(default_factory=AnthropicSettings)


class ClaudeSettings(ClaudeSettingsBase):
    resolution: tuple[int, int] = Field(default_factory=lambda: (1280, 800))
    max_tokens: int = 1000
    temperature: float = 0.0


class ClaudeComputerAgentSettings(ComputerAgentSettingsBase, ClaudeSettingsBase):
    pass
