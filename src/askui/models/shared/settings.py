from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import Literal

from askui.models.shared.agent_message_param import ThinkingConfigParam, ToolChoiceParam
from askui.models.shared.prompts import (
    ActSystemPrompt,
    GetSystemPrompt,
    LocateSystemPrompt,
)

COMPUTER_USE_20250124_BETA_FLAG = "computer-use-2025-01-24"
COMPUTER_USE_20251124_BETA_FLAG = "computer-use-2025-11-24"

CACHING_STRATEGY = Literal["read", "write", "both", "no"]


class MessageSettings(BaseModel):
    """Settings for message creation in ActModel operations.

    The `thinking` and `tool_choice` fields are provider-specific dictionaries.
    For Anthropic models, see: anthropic.types.beta.BetaThinkingConfigParam
    and anthropic.types.beta.BetaToolChoiceParam
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    betas: list[str] | None = None
    max_tokens: int = 8192
    system: ActSystemPrompt | None = None
    thinking: ThinkingConfigParam | None = None
    tool_choice: ToolChoiceParam | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=1.0)


class ActSettings(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    messages: MessageSettings = Field(default_factory=MessageSettings)


class GetSettings(BaseModel):
    """Settings for GetModel operations (data extraction from images/PDFs)."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    max_tokens: int = 4096
    temperature: float = Field(default=0.5, ge=0.0, le=1.0)
    system_prompt: GetSystemPrompt | None = None
    timeout: float | None = None


class LocateSettings(BaseModel):
    """Settings for LocateModel operations (UI element location)."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    query_type: str | None = None
    confidence_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    max_detections: int = 10
    timeout: float | None = None
    system_prompt: LocateSystemPrompt | None = None


class CachedExecutionToolSettings(BaseModel):
    delay_time_between_action: float = 0.5


class CachingSettings(BaseModel):
    strategy: CACHING_STRATEGY = "no"
    cache_dir: str = ".cache"
    filename: str = ""
    execute_cached_trajectory_tool_settings: CachedExecutionToolSettings = (
        CachedExecutionToolSettings()
    )
