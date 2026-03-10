"""Pricing information for model API calls."""

from pydantic import BaseModel

_DEFAULT_PRICING: dict[str, "ModelPricing"] = {}


class ModelPricing(BaseModel):
    """Cost per 1 million tokens for a model.

    Args:
        input_cost_per_million_tokens (float): Cost per 1M input tokens in Currency.
        output_cost_per_million_tokens (float): Cost per 1M output tokens in Currency.
        currency (str): ISO 4217 currency code. Defaults to ``"USD"``.
    """

    input_cost_per_million_tokens: float
    output_cost_per_million_tokens: float
    currency: str = "USD"

    @classmethod
    def for_model(
        cls,
        model_id: str,
        input_cost_per_million_tokens: float | None = None,
        output_cost_per_million_tokens: float | None = None,
    ) -> "ModelPricing | None":
        """Resolve pricing for a model.

        If both cost parameters are provided, creates a ``ModelPricing``
        with those values. Otherwise, looks up built-in defaults by
        ``model_id``.

        Args:
            model_id (str): The model identifier.
            input_cost_per_million_tokens (float | None, optional): Override
                cost in USD per 1M input tokens.
            output_cost_per_million_tokens (float | None, optional): Override
                cost in USD per 1M output tokens.

        Returns:
            ModelPricing | None: Resolved pricing, or ``None`` if no match
                and no overrides provided.
        """
        if (
            input_cost_per_million_tokens is not None
            and output_cost_per_million_tokens is not None
        ):
            return cls(
                input_cost_per_million_tokens=input_cost_per_million_tokens,
                output_cost_per_million_tokens=output_cost_per_million_tokens,
            )
        return _DEFAULT_PRICING.get(model_id)


_DEFAULT_PRICING.update(
    {
        "claude-haiku-4-5-20251001": ModelPricing(
            input_cost_per_million_tokens=1.0,
            output_cost_per_million_tokens=5.0,
        ),
        "claude-sonnet-4-5-20250929": ModelPricing(
            input_cost_per_million_tokens=3.0,
            output_cost_per_million_tokens=15.0,
        ),
        "claude-opus-4-5-20251101": ModelPricing(
            input_cost_per_million_tokens=5.0,
            output_cost_per_million_tokens=25.0,
        ),
        "claude-sonnet-4-6": ModelPricing(
            input_cost_per_million_tokens=3.0,
            output_cost_per_million_tokens=15.0,
        ),
        "claude-opus-4-6": ModelPricing(
            input_cost_per_million_tokens=5.0,
            output_cost_per_million_tokens=25.0,
        ),
    }
)
