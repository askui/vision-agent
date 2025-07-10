from typing import Literal

from anthropic import NOT_GIVEN, NotGiven
from anthropic.types import AnthropicBetaParam
from anthropic.types.beta import (
    BetaTextBlockParam,
    BetaThinkingConfigParam,
    BetaToolChoiceParam,
)
from pydantic import BaseModel, ConfigDict, Field

COMPUTER_USE_20241022_BETA_FLAG = "computer-use-2024-10-22"
COMPUTER_USE_20250124_BETA_FLAG = "computer-use-2025-01-24"


class MessageSettings(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    betas: list[AnthropicBetaParam] | NotGiven = NOT_GIVEN
    max_tokens: int = 4096
    model: (
        Literal["anthropic-claude-3-5-sonnet-20241022", "claude-sonnet-4-20250514"]  # noqa: PYI051
        | str
        | NotGiven
    ) = NOT_GIVEN
    system: str | list[BetaTextBlockParam] | NotGiven = NOT_GIVEN
    thinking: BetaThinkingConfigParam | NotGiven = NOT_GIVEN
    tool_choice: BetaToolChoiceParam | NotGiven = NOT_GIVEN


class ActSettings(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    messages: MessageSettings = Field(default_factory=MessageSettings)
    only_n_most_recent_images: int = 3
    image_truncation_threshold: int = 10
