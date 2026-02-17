from typing import NamedTuple

from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import Literal

from askui.models.shared.agent_message_param import ThinkingConfigParam, ToolChoiceParam
from askui.models.shared.prompts import (
    ActSystemPrompt,
    GetSystemPrompt,
    LocateSystemPrompt,
)


class Resolution(NamedTuple):
    """Screen resolution for image scaling operations.

    Used by vision models to scale images to a standard size before processing.

    Args:
        width (int): The width in pixels.
        height (int): The height in pixels.
    """

    width: int
    height: int


DEFAULT_LOCATE_RESOLUTION = Resolution(1280, 800)
DEFAULT_GET_RESOLUTION = Resolution(1280, 800)

COMPUTER_USE_20250124_BETA_FLAG = "computer-use-2025-01-24"
COMPUTER_USE_20251124_BETA_FLAG = "computer-use-2025-11-24"

CACHING_STRATEGY = Literal["read", "write", "both", "no"]


class MessageSettings(BaseModel):
    """Settings for message creation in ActModel operations.

    These settings control how messages are sent to the underlying model API
    during agent action execution.

    Args:
        betas (list[str] | None): Anthropic API beta features to enable.
            Example: `["computer-use-2025-01-24"]` for computer use capabilities.
        max_tokens (int): Maximum number of tokens the model can generate in
            its response. Higher values allow longer responses but increase
            cost and latency. Default: 8192.
        system (ActSystemPrompt | None): Custom system prompt that defines
            the agent's behavior and capabilities. If None, uses the default
            agent system prompt.
        thinking (ThinkingConfigParam | None): Configuration for thinking feature.
            When enabled, the model spends more time reasoning before responding.
        tool_choice (ToolChoiceParam | None): How the model should select
            tools. Options include "auto", "any", or a specific tool name.
        temperature (float | None): Controls response randomness. 0.0 produces
            deterministic outputs, 1.0 produces creative/varied outputs.
            Default: None (uses model default).
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    betas: list[str] | None = None
    max_tokens: int = 8192
    system: ActSystemPrompt | None = None
    thinking: ThinkingConfigParam | None = None
    tool_choice: ToolChoiceParam | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=1.0)


class ActSettings(BaseModel):
    """Settings for ActModel operations (agent actions).

    Controls the behavior of agent action execution, including how messages
    are created and sent to the underlying model.

    Args:
        messages (MessageSettings): Settings for message creation including
            max tokens, temperature, and system prompt configuration.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    messages: MessageSettings = Field(default_factory=MessageSettings)


class GetSettings(BaseModel):
    """Settings for GetModel operations (data extraction from images/PDFs).

    Controls how GetModel extracts information from visual sources like
    screenshots, images, and PDF documents.

    Args:
        max_tokens (int): Maximum tokens for the model response. Higher values
            allow more detailed extractions but increase cost. Default: 4096.
            Note: Not all providers currently use this setting.
        temperature (float): Controls response randomness. Lower values (e.g.,
            0.0) produce more deterministic extractions, higher values allow
            more varied responses. Default: 0.5. Range: 0.0-1.0.
            Note: Not all providers currently use this setting.
        system_prompt (GetSystemPrompt | None): Custom system prompt for the
            extraction task. If None, uses the default extraction prompt.
        timeout (float | None): Timeout in seconds for the API call. If None,
            uses the provider's default timeout.
            Note: Reserved for future use; not currently implemented.
        resolution (Resolution): Target resolution for scaling images before
            processing. Images are scaled to fit within this resolution while
            maintaining aspect ratio. This affects quality vs. token usage.
            Default: 1280x800.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    max_tokens: int = 4096
    temperature: float = Field(default=0.5, ge=0.0, le=1.0)
    system_prompt: GetSystemPrompt | None = None
    timeout: float | None = None
    resolution: Resolution = DEFAULT_GET_RESOLUTION


class LocateSettings(BaseModel):
    """Settings for LocateModel operations (UI element location).

    Controls how LocateModel finds UI elements in screenshots based on
    text, images, or natural language descriptions.

    Args:
        query_type (str | None): Type of query being performed. Used by some
            providers to optimize detection strategies.
            Note: Reserved for future use; not currently implemented.
        confidence_threshold (float): Minimum confidence score (0.0-1.0) for
            a detection to be considered valid. Higher values reduce false
            positives but may miss valid elements. Default: 0.8.
            Note: Not all providers currently use this setting.
        max_detections (int): Maximum number of elements to return when
            multiple matches are found. Default: 10.
            Note: Not all providers currently use this setting.
        timeout (float | None): Timeout in seconds for the API call. If None,
            uses the provider's default timeout.
            Note: Reserved for future use; not currently implemented.
        system_prompt (LocateSystemPrompt | None): Custom system prompt for
            element location. If None, uses the default locate prompt.
            Note: Not all providers currently use this setting.
        resolution (Resolution): Target resolution for scaling images before
            processing. Images are scaled to fit within this resolution while
            maintaining aspect ratio. Default: 1280x800.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    query_type: str | None = None
    confidence_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    max_detections: int = 10
    timeout: float | None = None
    system_prompt: LocateSystemPrompt | None = None
    resolution: Resolution = DEFAULT_LOCATE_RESOLUTION


class CachedExecutionToolSettings(BaseModel):
    """Settings for executing cached action trajectories.

    Args:
        delay_time_between_action (float): Delay in seconds between replaying
            cached actions. Allows time for UI to respond. Default: 0.5.
    """

    delay_time_between_action: float = 0.5


class CachingSettings(BaseModel):
    """Settings for caching agent action trajectories.

    Enables recording and replaying of agent actions for testing or
    performance optimization.

    Args:
        strategy (CACHING_STRATEGY): Caching mode. Options:
            - "no": Caching disabled (default)
            - "read": Replay actions from cache
            - "write": Record actions to cache
            - "both": Read from cache if available, otherwise record
        cache_dir (str): Directory path for storing cache files.
            Default: ".cache".
        filename (str): Name of the cache file. If empty, auto-generated.
        execute_cached_trajectory_tool_settings (CachedExecutionToolSettings):
            Settings for replaying cached actions.
    """

    strategy: CACHING_STRATEGY = "no"
    cache_dir: str = ".cache"
    filename: str = ""
    execute_cached_trajectory_tool_settings: CachedExecutionToolSettings = (
        CachedExecutionToolSettings()
    )
