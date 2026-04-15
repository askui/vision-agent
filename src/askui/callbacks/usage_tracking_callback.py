"""Callback for tracking token usage and reporting usage summaries."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from opentelemetry import trace
from pydantic import BaseModel, Field
from typing_extensions import Self, override

from askui.callbacks.conversation_callback import ConversationCallback
from askui.reporting import NULL_REPORTER

if TYPE_CHECKING:
    from askui.models.shared.agent_message_param import UsageParam
    from askui.models.shared.conversation import Conversation
    from askui.reporting import Reporter
    from askui.speaker.speaker import SpeakerResult
    from askui.utils.model_pricing import ModelPricing

_USD_CURRENCY = "USD"


class UsageSummary(BaseModel):
    """Accumulated token usage and optional cost breakdown for a conversation.

    Args:
        input_tokens (int | None): Total input tokens sent to the API.
        output_tokens (int | None): Total output tokens generated.
        cache_creation_input_tokens (int | None): Tokens used for cache creation.
        cache_read_input_tokens (int | None): Tokens read from cache.
        input_token_cost (float | None): Computed cost for input tokens in `currency`.
        output_token_cost (float | None): Computed cost for output tokens in `currency`.
        cache_write_token_cost (float | None): Computed cost for cache write tokens in
        `currency`.
        cache_read_token_cost (float | None): Computed cost for cache read tokens in
        `currency`.
        total_cost (float | None): Sum of all computed cost values.
        currency (str | None): ISO 4217 currency code (e.g. ``"USD"``).
        input_cost_per_million_tokens (float | None): Rate used to compute `input_cost`.
        output_cost_per_million_tokens (float|None): Rate used to compute `output_cost`.
    """

    input_tokens: int | None = None
    output_tokens: int | None = None
    cache_creation_input_tokens: int | None = None
    cache_read_input_tokens: int | None = None
    input_token_cost: float | None = None
    output_token_cost: float | None = None
    cache_write_token_cost: float | None = None
    cache_read_token_cost: float | None = None
    total_cost: float | None = None
    currency: str | None = None
    input_cost_per_million_tokens: float | None = None
    output_cost_per_million_tokens: float | None = None
    cache_write_cost_per_million_tokens: float | None = None
    cache_read_cost_per_million_tokens: float | None = None
    per_conversation_summaries: list[ConversationUsageSummary] | None = None

    @classmethod
    def create(cls, pricing: ModelPricing | None = None) -> "UsageSummary":
        """Create a summary configured with optional model pricing."""
        if pricing is None:
            return cls()
        return cls(
            input_cost_per_million_tokens=pricing.input_cost_per_million_tokens,
            output_cost_per_million_tokens=pricing.output_cost_per_million_tokens,
            cache_write_cost_per_million_tokens=(
                pricing.cache_write_cost_per_million_tokens
            ),
            cache_read_cost_per_million_tokens=(
                pricing.cache_read_cost_per_million_tokens
            ),
        )

    @classmethod
    def create_from(cls, summary: "UsageSummary") -> "UsageSummary":
        """Create a new summary that reuses pricing fields from `summary`."""
        return cls(
            input_cost_per_million_tokens=summary.input_cost_per_million_tokens,
            output_cost_per_million_tokens=summary.output_cost_per_million_tokens,
            cache_write_cost_per_million_tokens=(
                summary.cache_write_cost_per_million_tokens
            ),
            cache_read_cost_per_million_tokens=(
                summary.cache_read_cost_per_million_tokens
            ),
        )

    def add_usage(self, usage: UsageParam) -> None:
        """Add token counts from `usage`."""
        self.input_tokens = (self.input_tokens or 0) + (usage.input_tokens or 0)
        self.output_tokens = (self.output_tokens or 0) + (usage.output_tokens or 0)
        self.cache_creation_input_tokens = (self.cache_creation_input_tokens or 0) + (
            usage.cache_creation_input_tokens or 0
        )
        self.cache_read_input_tokens = (self.cache_read_input_tokens or 0) + (
            usage.cache_read_input_tokens or 0
        )

    def generate(self) -> Self:
        """Compute and populate cost fields from current token and pricing fields."""
        if not self._has_pricing():
            self._clear_cost_fields()
            return self

        input_tokens = self.input_tokens or 0
        output_tokens = self.output_tokens or 0
        cache_write_tokens = self.cache_creation_input_tokens or 0
        cache_read_tokens = self.cache_read_input_tokens or 0

        assert self.input_cost_per_million_tokens is not None
        assert self.output_cost_per_million_tokens is not None
        assert self.cache_write_cost_per_million_tokens is not None
        assert self.cache_read_cost_per_million_tokens is not None

        self.input_token_cost = self._calculate_cost(
            input_tokens, self.input_cost_per_million_tokens
        )
        self.output_token_cost = self._calculate_cost(
            output_tokens, self.output_cost_per_million_tokens
        )
        self.cache_write_token_cost = self._calculate_cost(
            cache_write_tokens, self.cache_write_cost_per_million_tokens
        )
        self.cache_read_token_cost = self._calculate_cost(
            cache_read_tokens, self.cache_read_cost_per_million_tokens
        )
        self.total_cost = (
            (self.input_token_cost or 0.0)
            + (self.output_token_cost or 0.0)
            + (self.cache_write_token_cost or 0.0)
            + (self.cache_read_token_cost or 0.0)
        )
        self.currency = _USD_CURRENCY
        return self

    def token_attributes(self) -> dict[str, int]:
        """Return token fields for telemetry attributes."""
        return {
            "input_tokens": self.input_tokens or 0,
            "output_tokens": self.output_tokens or 0,
            "cache_creation_input_tokens": self.cache_creation_input_tokens or 0,
            "cache_read_input_tokens": self.cache_read_input_tokens or 0,
        }

    def _has_pricing(self) -> bool:
        return (
            self.input_cost_per_million_tokens is not None
            and self.output_cost_per_million_tokens is not None
            and self.cache_write_cost_per_million_tokens is not None
            and self.cache_read_cost_per_million_tokens is not None
        )

    def _clear_cost_fields(self) -> None:
        self.input_token_cost = None
        self.output_token_cost = None
        self.cache_write_token_cost = None
        self.cache_read_token_cost = None
        self.total_cost = None
        self.currency = None

    @staticmethod
    def _calculate_cost(tokens: int, rate_per_million_tokens: float) -> float:
        return rate_per_million_tokens * tokens / 1e6


class StepUsageSummary(UsageSummary):
    """Usage summary for a single step."""

    step_index: int


class ConversationUsageSummary(UsageSummary):
    """Usage summary for one conversation including per-step breakdown.

    Args:
        conversation_index (int): 1-based index of the conversation within the
            current agent lifecycle.
        conversation_id (str): Unique identifier of the conversation.
        step_summaries (list[StepUsageSummary]): Per-step usage summaries.
        duration_seconds (float | None): Wall-clock duration of the conversation
            in seconds, measured between `on_conversation_start` and
            `on_conversation_end`. `None` if duration was not tracked.
    """

    conversation_index: int
    conversation_id: str
    step_summaries: list[StepUsageSummary] = Field(default_factory=list)
    duration_seconds: float | None = None


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
        self._summary: UsageSummary = UsageSummary.create(pricing)
        self._per_conversation_usage: UsageSummary = UsageSummary.create(pricing)
        self._per_conversation_summaries: list[ConversationUsageSummary] = []
        self._per_step_summaries: list[StepUsageSummary] = []
        self._conversation_index: int = 0
        self._conversation_start_time: datetime | None = None

    @override
    def on_conversation_start(self, conversation: Conversation) -> None:
        self._per_conversation_usage = UsageSummary.create_from(self._summary)
        self._per_step_summaries = []
        self._conversation_index += 1
        self._conversation_start_time = datetime.now(tz=timezone.utc)

    @override
    def on_step_end(
        self,
        conversation: Conversation,
        step_index: int,
        result: SpeakerResult,
    ) -> None:
        step_usage: UsageParam | None = result.usage
        if step_usage is None:
            return

        step_summary = self._create_step_summary(
            step_index=step_index, usage=step_usage
        )
        self._per_step_summaries.append(step_summary)
        self._per_conversation_usage.add_usage(step_usage)
        self._summary.add_usage(step_usage)

        current_span = trace.get_current_span()
        current_span.set_attributes(step_summary.token_attributes())

    @override
    def on_truncation_summarize(self, usage: UsageParam) -> None:
        self._per_conversation_usage.add_usage(usage)
        self._summary.add_usage(usage)

    @override
    def on_conversation_end(self, conversation: Conversation) -> None:
        generated_steps: list[StepUsageSummary] = [
            step_summary.generate() for step_summary in self._per_step_summaries
        ]
        duration_seconds: float | None = None
        if self._conversation_start_time is not None:
            duration_seconds = (
                datetime.now(tz=timezone.utc) - self._conversation_start_time
            ).total_seconds()
        conversation_summary = self._create_conversation_summary(
            conversation=conversation,
            generated_step_summaries=generated_steps,
            duration_seconds=duration_seconds,
        )
        self._per_conversation_summaries.append(conversation_summary)
        self._summary.per_conversation_summaries = list(
            self._per_conversation_summaries
        )
        self._reporter.add_usage_summary(self._summary.generate().model_copy(deep=True))

    @property
    def accumulated_usage(self) -> UsageSummary:
        """Current accumulated usage statistics."""
        return self._summary

    def _create_step_summary(
        self, step_index: int, usage: UsageParam
    ) -> StepUsageSummary:
        return StepUsageSummary(
            step_index=step_index,
            input_tokens=usage.input_tokens or 0,
            output_tokens=usage.output_tokens or 0,
            cache_creation_input_tokens=usage.cache_creation_input_tokens or 0,
            cache_read_input_tokens=usage.cache_read_input_tokens or 0,
            input_cost_per_million_tokens=self._summary.input_cost_per_million_tokens,
            output_cost_per_million_tokens=self._summary.output_cost_per_million_tokens,
            cache_write_cost_per_million_tokens=(
                self._summary.cache_write_cost_per_million_tokens
            ),
            cache_read_cost_per_million_tokens=(
                self._summary.cache_read_cost_per_million_tokens
            ),
        )

    def _create_conversation_summary(
        self,
        conversation: Conversation,
        generated_step_summaries: list[StepUsageSummary],
        duration_seconds: float | None = None,
    ) -> ConversationUsageSummary:
        conversation_summary = ConversationUsageSummary(
            conversation_index=self._conversation_index,
            conversation_id=conversation.conversation_id,
            step_summaries=generated_step_summaries,
            duration_seconds=duration_seconds,
            input_tokens=self._per_conversation_usage.input_tokens,
            output_tokens=self._per_conversation_usage.output_tokens,
            cache_creation_input_tokens=(
                self._per_conversation_usage.cache_creation_input_tokens
            ),
            cache_read_input_tokens=self._per_conversation_usage.cache_read_input_tokens,
            input_cost_per_million_tokens=(
                self._per_conversation_usage.input_cost_per_million_tokens
            ),
            output_cost_per_million_tokens=(
                self._per_conversation_usage.output_cost_per_million_tokens
            ),
            cache_write_cost_per_million_tokens=(
                self._per_conversation_usage.cache_write_cost_per_million_tokens
            ),
            cache_read_cost_per_million_tokens=(
                self._per_conversation_usage.cache_read_cost_per_million_tokens
            ),
        )
        return conversation_summary.generate()
