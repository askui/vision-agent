"""Callback for tracking token usage and reporting usage summaries."""

from __future__ import annotations

from typing import TYPE_CHECKING

from opentelemetry import trace
from pydantic import BaseModel
from typing_extensions import override

from askui.models.shared.conversation_callback import ConversationCallback
from askui.reporting import NULL_REPORTER

if TYPE_CHECKING:
    from askui.models.shared.agent_message_param import UsageParam
    from askui.models.shared.conversation import Conversation
    from askui.reporting import Reporter
    from askui.speaker.speaker import SpeakerResult
    from askui.utils.model_pricing import ModelPricing


class UsageSummary(BaseModel):
    """Accumulated token usage and optional cost breakdown for a conversation.

    Args:
        input_tokens (int | None): Total input tokens sent to the API.
        output_tokens (int | None): Total output tokens generated.
        cache_creation_input_tokens (int | None): Tokens used for cache creation.
        cache_read_input_tokens (int | None): Tokens read from cache.
        input_cost (float | None): Computed input cost in `currency`.
        output_cost (float | None): Computed output cost in `currency`.
        total_cost (float | None): Sum of `input_cost` and `output_cost`.
        currency (str | None): ISO 4217 currency code (e.g. ``"USD"``).
        input_cost_per_million_tokens (float | None): Rate used to compute `input_cost`.
        output_cost_per_million_tokens (float|None): Rate used to compute `output_cost`.
    """

    input_tokens: int | None = None
    output_tokens: int | None = None
    cache_creation_input_tokens: int | None = None
    cache_read_input_tokens: int | None = None
    input_cost: float | None = None
    output_cost: float | None = None
    total_cost: float | None = None
    currency: str | None = None
    input_cost_per_million_tokens: float | None = None
    output_cost_per_million_tokens: float | None = None


class UsageTrackingCallback(ConversationCallback):
    """Tracks token usage per step and reports a summary at conversation end.

    Args:
        reporter: Reporter to write the final usage summary to.
        pricing: Pricing information for cost calculation. If ``None``,
            no cost data is included in the usage summary.
    """

    def __init__(
        self,
        reporter: Reporter = NULL_REPORTER,
        pricing: ModelPricing | None = None,
    ) -> None:
        self._reporter = reporter
        self._pricing = pricing
        self._summary = UsageSummary()

    @override
    def on_conversation_start(self, conversation: Conversation) -> None:
        self._summary = UsageSummary()

    @override
    def on_step_end(
        self,
        conversation: Conversation,
        step_index: int,
        result: SpeakerResult,
    ) -> None:
        if result.usage:
            self._accumulate(result.usage)

    @override
    def on_conversation_end(self, conversation: Conversation) -> None:
        self._reporter.add_usage_summary(self._summary)

    @property
    def accumulated_usage(self) -> UsageSummary:
        """Current accumulated usage statistics."""
        return self._summary

    def _accumulate(self, step_usage: UsageParam) -> None:
        # Add step tokens to running totals (None counts as 0)
        self._summary.input_tokens = (self._summary.input_tokens or 0) + (
            step_usage.input_tokens or 0
        )
        self._summary.output_tokens = (self._summary.output_tokens or 0) + (
            step_usage.output_tokens or 0
        )
        self._summary.cache_creation_input_tokens = (
            self._summary.cache_creation_input_tokens or 0
        ) + (step_usage.cache_creation_input_tokens or 0)
        self._summary.cache_read_input_tokens = (
            self._summary.cache_read_input_tokens or 0
        ) + (step_usage.cache_read_input_tokens or 0)

        # Record per-step token counts on the current OTel span
        current_span = trace.get_current_span()
        current_span.set_attributes(
            {
                "input_tokens": step_usage.input_tokens or 0,
                "output_tokens": step_usage.output_tokens or 0,
                "cache_creation_input_tokens": (
                    step_usage.cache_creation_input_tokens or 0
                ),
                "cache_read_input_tokens": (step_usage.cache_read_input_tokens or 0),
            }
        )

        # Update costs from updated totals if pricing values are set
        if (
            self._pricing
            and self._pricing.input_cost_per_million_tokens
            and self._pricing.output_cost_per_million_tokens
        ):
            input_cost = (
                self._summary.input_tokens
                * self._pricing.input_cost_per_million_tokens
                / 1e6
            )
            output_cost = (
                self._summary.output_tokens
                * self._pricing.output_cost_per_million_tokens
                / 1e6
            )
            self._summary.input_cost = input_cost
            self._summary.output_cost = output_cost
            self._summary.total_cost = input_cost + output_cost
            self._summary.currency = self._pricing.currency
            self._summary.input_cost_per_million_tokens = (
                self._pricing.input_cost_per_million_tokens
            )
            self._summary.output_cost_per_million_tokens = (
                self._pricing.output_cost_per_million_tokens
            )
