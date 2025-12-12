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

from askui.models.anthropic.factory import AnthropicApiProvider
from askui.models.shared.agent_message_param import ToolUseBlockParam

COMPUTER_USE_20250124_BETA_FLAG = "computer-use-2025-01-24"
COMPUTER_USE_20251124_BETA_FLAG = "computer-use-2025-11-24"

CACHING_STRATEGY = Literal["read", "write", "both", "no"]
PLACEHOLDER_IDENTIFICATION_STRATEGY = Literal["llm", "preset"]


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


class CacheWriterSettings(BaseModel):
    placeholder_identification_strategy: PLACEHOLDER_IDENTIFICATION_STRATEGY = "llm"
    llm_placeholder_id_api_provider: AnthropicApiProvider = "askui"


class CachingSettings(BaseModel):
    strategy: CACHING_STRATEGY = "no"
    cache_dir: str = ".cache"
    filename: str = ""
    execute_cached_trajectory_tool_settings: CachedExecutionToolSettings = (
        CachedExecutionToolSettings()
    )
    cache_writer_settings: CacheWriterSettings = CacheWriterSettings()


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
    execution_attempts: int = 0
    failures: list[CacheFailure] = Field(default_factory=list)
    is_valid: bool = True
    invalidation_reason: Optional[str] = None


class CacheFile(BaseModel):
    """Cache file structure (v0.1) wrapping trajectory with metadata."""

    metadata: CacheMetadata
    trajectory: list[ToolUseBlockParam]
    placeholders: dict[str, str] = Field(default_factory=dict)
