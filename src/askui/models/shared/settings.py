import warnings

from anthropic import Omit, omit
from anthropic.types import AnthropicBetaParam
from anthropic.types.beta import (
    BetaTextBlockParam,
    BetaThinkingConfigParam,
    BetaToolChoiceParam,
)
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing_extensions import Literal

from askui.models.shared.prompts import ActSystemPrompt

COMPUTER_USE_20250124_BETA_FLAG = "computer-use-2025-01-24"
COMPUTER_USE_20251124_BETA_FLAG = "computer-use-2025-11-24"

CACHING_STRATEGY = Literal["read", "write", "both", "no"]


class MessageSettings(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    betas: list[AnthropicBetaParam] | Omit = omit
    max_tokens: int = 4096
    system: ActSystemPrompt | str | None = None
    thinking: BetaThinkingConfigParam | Omit = omit
    tool_choice: BetaToolChoiceParam | Omit = omit
    temperature: float | Omit = Field(default=omit, ge=0.0, le=1.0)

    @field_validator("system", mode="before")
    @classmethod
    def warn_string_deprecated(
        cls, v: ActSystemPrompt | str | list[BetaTextBlockParam] | Omit
    ) -> ActSystemPrompt | str | list[BetaTextBlockParam] | Omit:
        if isinstance(v, str):
            warnings.warn(
                "Setting 'system' as a string is deprecated and will be removed in a "
                "future version. Please use an instance of ActSystemPrompt instead.",
                DeprecationWarning,
                stacklevel=1,
            )
        return v


class ActSettings(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    messages: MessageSettings = Field(default_factory=MessageSettings)


class CachedExecutionToolSettings(BaseModel):
    delay_time_between_action: float = 0.5


class CachingSettings(BaseModel):
    strategy: CACHING_STRATEGY = "no"
    cache_dir: str = ".cache"
    filename: str = ""
    execute_cached_trajectory_tool_settings: CachedExecutionToolSettings = (
        CachedExecutionToolSettings()
    )
