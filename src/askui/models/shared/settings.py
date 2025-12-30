from datetime import datetime
from typing import Optional

from anthropic import Omit, omit
from anthropic.types import AnthropicBetaParam
from anthropic.types.beta import (
    BetaTextBlockParam,
    BetaThinkingConfigParam,
    BetaToolChoiceParam,
)
from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import Literal

from askui.models.shared.agent_message_param import ToolUseBlockParam, UsageParam

COMPUTER_USE_20250124_BETA_FLAG = "computer-use-2025-01-24"
COMPUTER_USE_20251124_BETA_FLAG = "computer-use-2025-11-24"

CACHING_STRATEGY = Literal["execute", "record", "both"]
CACHE_PARAMETER_IDENTIFICATION_STRATEGY = Literal["llm", "preset"]
CACHING_VISUAL_VERIFICATION_METHOD = Literal["phash", "ahash", "none"]


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


class CacheWritingSettings(BaseModel):
    """Settings for writing/recording cache files."""

    filename: str = ""
    parameter_identification_strategy: CACHE_PARAMETER_IDENTIFICATION_STRATEGY = "llm"
    visual_verification_method: CACHING_VISUAL_VERIFICATION_METHOD = "phash"
    visual_validation_region_size: int = 100
    visual_validation_threshold: int = 10


class CacheExecutionSettings(BaseModel):
    """Settings for executing/replaying cache files."""

    delay_time_between_action: float = 0.5


class CachingSettings(BaseModel):
    strategy: CACHING_STRATEGY | None = None
    cache_dir: str = ".askui_cache"
    writing_settings: CacheWritingSettings | None = None
    execution_settings: CacheExecutionSettings | None = None


class CacheFailure(BaseModel):
    timestamp: datetime
    step_index: int
    error_message: str
    failure_count_at_step: int


class CacheMetadata(BaseModel):
    version: str = "0.1"
    created_at: datetime
    goal: Optional[str] = None
    last_executed_at: Optional[datetime] = None
    token_usage: UsageParam | None = None
    execution_attempts: int = 0
    failures: list[CacheFailure] = Field(default_factory=list)
    is_valid: bool = True
    invalidation_reason: Optional[str] = None
    visual_verification_method: Optional[CACHING_VISUAL_VERIFICATION_METHOD] = None
    visual_validation_region_size: Optional[int] = None
    visual_validation_threshold: Optional[int] = None


class CacheFile(BaseModel):
    """Cache file structure (v0.1) wrapping trajectory with metadata."""

    metadata: CacheMetadata
    trajectory: list[ToolUseBlockParam]
    cache_parameters: dict[str, str] = Field(default_factory=dict)
