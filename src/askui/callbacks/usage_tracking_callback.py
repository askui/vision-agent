"""Callback for tracking token usage and reporting usage summaries."""

from __future__ import annotations

from typing import TYPE_CHECKING

from opentelemetry import trace
from typing_extensions import override

from askui.callbacks.conversation_callback import ConversationCallback
from askui.models.shared.agent_message_param import UsageParam
from askui.reporting import NULL_REPORTER, Reporter

if TYPE_CHECKING:
    from askui.models.shared.conversation import Conversation
    from askui.speaker.speaker import SpeakerResult


class UsageTrackingCallback(ConversationCallback):
    """Tracks token usage per step and reports a summary at conversation end.

    Args:
        reporter: Reporter to write the final usage summary to.
    """

    def __init__(self, reporter: Reporter = NULL_REPORTER) -> None:
        self._reporter = reporter
        self._accumulated_usage = UsageParam()

    @override
    def on_conversation_start(self, conversation: Conversation) -> None:
        self._accumulated_usage = UsageParam()

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
        self._reporter.add_usage_summary(self._accumulated_usage.model_dump())

    @property
    def accumulated_usage(self) -> UsageParam:
        """Current accumulated usage statistics."""
        return self._accumulated_usage

    def _accumulate(self, step_usage: UsageParam) -> None:
        self._accumulated_usage.input_tokens = (
            self._accumulated_usage.input_tokens or 0
        ) + (step_usage.input_tokens or 0)
        self._accumulated_usage.output_tokens = (
            self._accumulated_usage.output_tokens or 0
        ) + (step_usage.output_tokens or 0)
        self._accumulated_usage.cache_creation_input_tokens = (
            self._accumulated_usage.cache_creation_input_tokens or 0
        ) + (step_usage.cache_creation_input_tokens or 0)
        self._accumulated_usage.cache_read_input_tokens = (
            self._accumulated_usage.cache_read_input_tokens or 0
        ) + (step_usage.cache_read_input_tokens or 0)

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
