"""Unit tests for model pricing resolution and cost calculation."""

from unittest.mock import MagicMock

import pytest

from askui.models.shared.agent_message_param import UsageParam
from askui.models.shared.usage_tracking_callback import (
    UsageSummary,
    UsageTrackingCallback,
)
from askui.utils.model_pricing import ModelPricing


class TestModelPricingForModel:
    def test_exact_match_sonnet_4_6(self) -> None:
        pricing = ModelPricing.for_model("claude-sonnet-4-6")
        assert pricing is not None
        assert pricing.input_cost_per_million_tokens == 3.0
        assert pricing.output_cost_per_million_tokens == 15.0

    def test_exact_match_opus_4_6(self) -> None:
        pricing = ModelPricing.for_model("claude-opus-4-6")
        assert pricing is not None
        assert pricing.input_cost_per_million_tokens == 5.0
        assert pricing.output_cost_per_million_tokens == 25.0

    def test_exact_match_haiku(self) -> None:
        pricing = ModelPricing.for_model("claude-haiku-4-5-20251001")
        assert pricing is not None
        assert pricing.input_cost_per_million_tokens == 1.0
        assert pricing.output_cost_per_million_tokens == 5.0

    def test_unknown_model_returns_none(self) -> None:
        assert ModelPricing.for_model("unknown-model-v1") is None

    def test_empty_string_returns_none(self) -> None:
        assert ModelPricing.for_model("") is None

    def test_partial_model_id_returns_none(self) -> None:
        assert ModelPricing.for_model("claude-sonnet-4") is None

    def test_override_costs(self) -> None:
        pricing = ModelPricing.for_model(
            "claude-sonnet-4-6",
            input_cost_per_million_tokens=99.0,
            output_cost_per_million_tokens=199.0,
        )
        assert pricing is not None
        assert pricing.input_cost_per_million_tokens == 99.0
        assert pricing.output_cost_per_million_tokens == 199.0

    def test_override_costs_unknown_model(self) -> None:
        pricing = ModelPricing.for_model(
            "unknown-model",
            input_cost_per_million_tokens=1.0,
            output_cost_per_million_tokens=2.0,
        )
        assert pricing is not None
        assert pricing.input_cost_per_million_tokens == 1.0


def _get_usage_summary(reporter_mock: MagicMock) -> UsageSummary:
    return reporter_mock.add_usage_summary.call_args[0][0]  # type: ignore[no-any-return]


class TestUsageTrackingCallbackCost:
    def _make_callback(
        self, pricing: ModelPricing | None = None
    ) -> tuple[UsageTrackingCallback, MagicMock]:
        reporter = MagicMock()
        callback = UsageTrackingCallback(reporter=reporter, pricing=pricing)
        return callback, reporter

    def test_cost_included_when_pricing_set(self) -> None:
        pricing = ModelPricing(
            input_cost_per_million_tokens=3.0,
            output_cost_per_million_tokens=15.0,
        )
        callback, reporter = self._make_callback(pricing)
        callback._accumulated_usage = UsageParam(
            input_tokens=1_000_000,
            output_tokens=100_000,
        )
        callback.on_conversation_end(MagicMock())

        summary = _get_usage_summary(reporter)
        assert summary.total_cost == pytest.approx(4.5)
        assert summary.input_cost == pytest.approx(3.0)
        assert summary.output_cost == pytest.approx(1.5)
        assert summary.currency == "USD"
        assert summary.input_cost_per_million_tokens == 3.0
        assert summary.output_cost_per_million_tokens == 15.0

    def test_no_cost_when_pricing_none(self) -> None:
        callback, reporter = self._make_callback(pricing=None)
        callback._accumulated_usage = UsageParam(
            input_tokens=500,
            output_tokens=200,
        )
        callback.on_conversation_end(MagicMock())

        summary = _get_usage_summary(reporter)
        assert summary.total_cost is None
        assert summary.currency is None

    def test_zero_tokens_produce_zero_cost(self) -> None:
        pricing = ModelPricing(
            input_cost_per_million_tokens=3.0,
            output_cost_per_million_tokens=15.0,
        )
        callback, reporter = self._make_callback(pricing)
        callback._accumulated_usage = UsageParam(
            input_tokens=0,
            output_tokens=0,
        )
        callback.on_conversation_end(MagicMock())

        summary = _get_usage_summary(reporter)
        assert summary.total_cost == 0.0

    def test_none_tokens_treated_as_zero(self) -> None:
        pricing = ModelPricing(
            input_cost_per_million_tokens=3.0,
            output_cost_per_million_tokens=15.0,
        )
        callback, reporter = self._make_callback(pricing)
        callback._accumulated_usage = UsageParam()
        callback.on_conversation_end(MagicMock())

        summary = _get_usage_summary(reporter)
        assert summary.total_cost == 0.0

    def test_cost_calculation_accuracy(self) -> None:
        pricing = ModelPricing(
            input_cost_per_million_tokens=15.0,
            output_cost_per_million_tokens=75.0,
        )
        callback, reporter = self._make_callback(pricing)
        callback._accumulated_usage = UsageParam(
            input_tokens=50_000,
            output_tokens=10_000,
        )
        callback.on_conversation_end(MagicMock())

        summary = _get_usage_summary(reporter)
        expected_input = 50_000 * 15.0 / 1_000_000
        expected_output = 10_000 * 75.0 / 1_000_000
        assert summary.input_cost == pytest.approx(expected_input)
        assert summary.output_cost == pytest.approx(expected_output)
        assert summary.total_cost == pytest.approx(expected_input + expected_output)
