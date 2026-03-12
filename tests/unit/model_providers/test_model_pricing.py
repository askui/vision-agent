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
    @pytest.mark.parametrize(
        ("model_id", "expected_input", "expected_output"),
        [
            ("claude-haiku-4-5-20251001", 1.0, 5.0),
            ("claude-sonnet-4-5-20250929", 3.0, 15.0),
            ("claude-opus-4-5-20251101", 5.0, 25.0),
            ("claude-sonnet-4-6", 3.0, 15.0),
            ("claude-opus-4-6", 5.0, 25.0),
        ],
    )
    def test_known_model_returns_default_pricing(
        self,
        model_id: str,
        expected_input: float,
        expected_output: float,
    ) -> None:
        pricing = ModelPricing.for_model(model_id)
        assert pricing is not None
        assert pricing.input_cost_per_million_tokens == expected_input
        assert pricing.output_cost_per_million_tokens == expected_output

    @pytest.mark.parametrize(
        "model_id",
        ["unknown-model-v1", "", "claude-sonnet-4"],
    )
    def test_unknown_model_returns_none(self, model_id: str) -> None:
        assert ModelPricing.for_model(model_id) is None

    @pytest.mark.parametrize(
        ("model_id", "input_cost", "output_cost"),
        [
            ("claude-sonnet-4-6", 99.0, 199.0),
            ("unknown-model", 1.0, 2.0),
        ],
    )
    def test_override_costs(
        self,
        model_id: str,
        input_cost: float,
        output_cost: float,
    ) -> None:
        pricing = ModelPricing.for_model(
            model_id,
            input_cost_per_million_tokens=input_cost,
            output_cost_per_million_tokens=output_cost,
        )
        assert pricing is not None
        assert pricing.input_cost_per_million_tokens == input_cost
        assert pricing.output_cost_per_million_tokens == output_cost


def _get_usage_summary(reporter_mock: MagicMock) -> UsageSummary:
    return reporter_mock.add_usage_summary.call_args[0][0]  # type: ignore[no-any-return]


class TestUsageTrackingCallbackCost:
    def _make_callback(
        self, pricing: ModelPricing | None = None
    ) -> tuple[UsageTrackingCallback, MagicMock]:
        reporter = MagicMock()
        callback = UsageTrackingCallback(reporter=reporter, pricing=pricing)
        return callback, reporter

    @pytest.mark.parametrize(
        (
            "input_tokens",
            "output_tokens",
            "input_rate",
            "output_rate",
            "expected_input_cost",
            "expected_output_cost",
        ),
        [
            (1_000_000, 100_000, 3.0, 15.0, 3.0, 1.5),
            (50_000, 10_000, 15.0, 75.0, 0.75, 0.75),
            (0, 0, 3.0, 15.0, 0.0, 0.0),
        ],
    )
    def test_cost_calculation(
        self,
        input_tokens: int,
        output_tokens: int,
        input_rate: float,
        output_rate: float,
        expected_input_cost: float,
        expected_output_cost: float,
    ) -> None:
        pricing = ModelPricing(
            input_cost_per_million_tokens=input_rate,
            output_cost_per_million_tokens=output_rate,
        )
        callback, reporter = self._make_callback(pricing)
        callback._accumulate(
            UsageParam(input_tokens=input_tokens, output_tokens=output_tokens)
        )
        callback.on_conversation_end(MagicMock())

        summary = _get_usage_summary(reporter)
        assert summary.input_cost == pytest.approx(expected_input_cost)
        assert summary.output_cost == pytest.approx(expected_output_cost)
        assert summary.total_cost == pytest.approx(
            expected_input_cost + expected_output_cost
        )
        assert summary.currency == "USD"
        assert summary.input_cost_per_million_tokens == input_rate
        assert summary.output_cost_per_million_tokens == output_rate

    def test_no_cost_when_pricing_none(self) -> None:
        callback, reporter = self._make_callback(pricing=None)
        callback._accumulate(UsageParam(input_tokens=500, output_tokens=200))
        callback.on_conversation_end(MagicMock())

        summary = _get_usage_summary(reporter)
        assert summary.total_cost is None
        assert summary.currency is None

    def test_none_tokens_treated_as_zero(self) -> None:
        pricing = ModelPricing(
            input_cost_per_million_tokens=3.0,
            output_cost_per_million_tokens=15.0,
        )
        callback, reporter = self._make_callback(pricing)
        callback._accumulate(UsageParam())
        callback.on_conversation_end(MagicMock())

        summary = _get_usage_summary(reporter)
        assert summary.total_cost == 0.0
