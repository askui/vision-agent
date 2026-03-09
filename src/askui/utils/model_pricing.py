"""Pricing information for model API calls."""

from pydantic import BaseModel


class ModelPricing(BaseModel):
    """Cost per 1 million tokens for a model.

    Args:
        input_cost_per_million_tokens (float): Cost in USD per 1M input tokens.
        output_cost_per_million_tokens (float): Cost in USD per 1M output tokens.
        currency (str): ISO 4217 currency code. Defaults to ``"USD"``.
    """

    input_cost_per_million_tokens: float
    output_cost_per_million_tokens: float
    currency: str = "USD"


_DEFAULT_PRICING: dict[str, ModelPricing] = {
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


def resolve_default_pricing(model_id: str) -> ModelPricing | None:
    """Resolve default pricing for a model ID by prefix matching.

    Tries exact match first, then longest-prefix match.

    Args:
        model_id (str): The model identifier.

    Returns:
        ModelPricing | None: Default pricing, or ``None`` if no match found.
    """
    if model_id in _DEFAULT_PRICING:
        return _DEFAULT_PRICING[model_id]
    return None
