import pytest

from askui import VisionAgent


def test_validate_call_with_non_pydantic_invalid_types_raises_value_error() -> None:
    class InvalidModelRouter:
        pass

    with pytest.raises(ValueError):
        VisionAgent(model_router=InvalidModelRouter())  # type: ignore
