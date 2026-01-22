import pytest

from askui import VisionAgent


def test_validate_call_with_invalid_act_model_type_raises_value_error() -> None:
    class InvalidActModel:
        pass

    with pytest.raises(ValueError):
        VisionAgent(act_model=InvalidActModel())  # type: ignore


def test_validate_call_with_invalid_get_model_type_raises_value_error() -> None:
    class InvalidGetModel:
        pass

    with pytest.raises(ValueError):
        VisionAgent(get_model=InvalidGetModel())  # type: ignore


def test_validate_call_with_invalid_locate_model_type_raises_value_error() -> None:
    class InvalidLocateModel:
        pass

    with pytest.raises(ValueError):
        VisionAgent(locate_model=InvalidLocateModel())  # type: ignore
