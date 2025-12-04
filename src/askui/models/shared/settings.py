from anthropic import Omit, omit
from anthropic.types import AnthropicBetaParam
from anthropic.types.beta import (
    BetaTextBlockParam,
    BetaThinkingConfigParam,
    BetaToolChoiceParam,
)
from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import Literal

COMPUTER_USE_20250124_BETA_FLAG = "computer-use-2025-01-24"
COMPUTER_USE_20251124_BETA_FLAG = "computer-use-2025-11-24"

CACHING_STRATEGY = Literal["read", "write", "both", "no"]


class MessageSettings(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    betas: list[AnthropicBetaParam] | Omit = omit
    max_tokens: int = 4096
    system: str | list[BetaTextBlockParam] | Omit = omit
    thinking: BetaThinkingConfigParam | Omit = omit
    tool_choice: BetaToolChoiceParam | Omit = omit
    temperature: float | Omit = Field(default=omit, ge=0.0, le=1.0)


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
