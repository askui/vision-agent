import pytest

from askui import ComputerAgent


def test_validate_call_with_invalid_reporters_type_raises_value_error() -> None:
    with pytest.raises(ValueError):
        ComputerAgent(reporters="not_a_list")  # type: ignore[arg-type]


def test_validate_call_with_invalid_display_type_raises_value_error() -> None:
    with pytest.raises(ValueError):
        ComputerAgent(display=0)
