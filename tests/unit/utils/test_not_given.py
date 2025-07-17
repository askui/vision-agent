import pytest
from pydantic import ValidationError

from askui.utils.not_given import NOT_GIVEN, BaseModelWithNotGiven, NotGiven


class DummyModel(BaseModelWithNotGiven):
    value: int | NotGiven = NOT_GIVEN


def test_notgiven_singleton() -> None:
    assert NotGiven() is NOT_GIVEN
    assert NotGiven() is NotGiven()
    assert repr(NOT_GIVEN) == "NOT_GIVEN"
    assert str(NOT_GIVEN) == "NOT_GIVEN"
    assert not bool(NOT_GIVEN)


def test_notgiven_as_method_param() -> None:
    def func(x: int | NotGiven = NOT_GIVEN) -> int:
        return 42 if isinstance(x, NotGiven) else x

    assert func() == 42
    assert func(5) == 5


def test_notgiven_in_condition() -> None:
    fallback = 123
    val = NOT_GIVEN
    result = val if val is not NOT_GIVEN else fallback
    assert result == fallback
    val2 = 99
    result2 = val2 if val2 is not NOT_GIVEN else fallback
    assert result2 == 99


def test_notgivenfield_in_pydantic_model() -> None:
    m1 = DummyModel()
    assert m1.value is NOT_GIVEN
    m2 = DummyModel(value=7)
    assert m2.value == 7


def test_notgivenfield_serialization() -> None:
    m = DummyModel()
    dumped = m.model_dump()
    # Should not include 'value' if NOT_GIVEN
    assert "value" not in dumped
    m2 = DummyModel(value=10)
    dumped2 = m2.model_dump()
    assert "value" in dumped2 and dumped2["value"] == 10


def test_notgivenfield_json_dump() -> None:
    m = DummyModel()
    json_str = m.model_dump_json()
    # Should not include 'value' in JSON if NOT_GIVEN
    assert json_str == "{}"
    m2 = DummyModel(value=11)
    json_str2 = m2.model_dump_json()
    assert json_str2 == '{"value":11}'


def test_notgiven_equality() -> None:
    assert NOT_GIVEN == NotGiven()
    assert NOT_GIVEN is NotGiven()
    assert NOT_GIVEN != 0
    assert NOT_GIVEN is not None
    assert NOT_GIVEN != "NOT_GIVEN"


def test_notgivenfield_validation() -> None:
    # Should accept int or NOT_GIVEN
    DummyModel(value=NOT_GIVEN)
    DummyModel(value=5)
    # Should raise for wrong type
    with pytest.raises(ValidationError):
        DummyModel(value="bad")


def test_notgivenfield_deserialization() -> None:
    # Should default to NOT_GIVEN if missing
    m = DummyModel.model_validate({})
    assert m.value is NOT_GIVEN
    # Should parse int
    m2 = DummyModel.model_validate({"value": 42})
    assert m2.value == 42
