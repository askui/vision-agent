from typing import Literal

from anthropic.types.beta import BetaToolChoiceAutoParam, BetaToolChoiceParam
from pydantic import BaseModel, Field

COMPUTER_USE_20241022_BETA_FLAG = "computer-use-2024-10-22"
COMPUTER_USE_20250124_BETA_FLAG = "computer-use-2025-01-24"


class ThinkingConfigDisabledParam(BaseModel):
    type: Literal["disabled"] = "disabled"


class ThinkingConfigEnabledParam(BaseModel):
    type: Literal["enabled"] = "enabled"
    budget_tokens: int = Field(ge=1024, default=2048)


ThinkingConfigParam = ThinkingConfigDisabledParam | ThinkingConfigEnabledParam


class AgentSettings(BaseModel):
    """Settings for agents."""

    max_tokens: int = 4096
    only_n_most_recent_images: int = 3
    image_truncation_threshold: int = 10
    betas: list[str] = Field(default_factory=list)
    thinking: ThinkingConfigParam = Field(default_factory=ThinkingConfigDisabledParam)
    tool_choice: BetaToolChoiceParam = Field(
        default_factory=lambda: BetaToolChoiceAutoParam(
            type="auto", disable_parallel_tool_use=False
        )
    )
