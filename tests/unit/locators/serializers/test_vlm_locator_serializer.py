import pytest
from PIL import Image as PILImage

from askui.locators import Element, Prompt, Text
from askui.locators.locators import Image, Locator
from askui.locators.relatable import CircularDependencyError
from askui.locators.serializers import VlmLocatorSerializer

TEST_IMAGE = PILImage.new("RGB", (100, 100), color="red")


@pytest.fixture
def vlm_serializer() -> VlmLocatorSerializer:
    return VlmLocatorSerializer()


def test_serialize_text_similar(vlm_serializer: VlmLocatorSerializer) -> None:
    text = Text("hello", match_type="similar", similarity_threshold=80)
    result = vlm_serializer.serialize(text)
    assert result == 'text similar to "hello"'


def test_serialize_text_exact(vlm_serializer: VlmLocatorSerializer) -> None:
    text = Text("hello", match_type="exact")
    result = vlm_serializer.serialize(text)
    assert result == 'text "hello"'


def test_serialize_text_contains(vlm_serializer: VlmLocatorSerializer) -> None:
    text = Text("hello", match_type="contains")
    result = vlm_serializer.serialize(text)
    assert result == 'text containing text "hello"'


def test_serialize_text_regex(vlm_serializer: VlmLocatorSerializer) -> None:
    text = Text("h.*o", match_type="regex")
    result = vlm_serializer.serialize(text)
    assert result == 'text matching regex "h.*o"'


def test_serialize_class(vlm_serializer: VlmLocatorSerializer) -> None:
    class_ = Element("textfield")
    result = vlm_serializer.serialize(class_)
    assert result == "an arbitrary textfield shown"


def test_serialize_class_no_name(vlm_serializer: VlmLocatorSerializer) -> None:
    class_ = Element()
    result = vlm_serializer.serialize(class_)
    assert result == "an arbitrary ui element (e.g., text, button, textfield, etc.)"


def test_serialize_description(vlm_serializer: VlmLocatorSerializer) -> None:
    desc = Prompt("a big red button")
    result = vlm_serializer.serialize(desc)
    assert result == "a big red button"


def test_serialize_with_relation_raises(vlm_serializer: VlmLocatorSerializer) -> None:
    text = Text("hello")
    text.above_of(Text("world"))
    with pytest.raises(NotImplementedError):
        vlm_serializer.serialize(text)


def test_serialize_image(vlm_serializer: VlmLocatorSerializer) -> None:
    image = Image(TEST_IMAGE)
    with pytest.raises(NotImplementedError):
        vlm_serializer.serialize(image)


def test_serialize_unsupported_locator_type(
    vlm_serializer: VlmLocatorSerializer,
) -> None:
    class UnsupportedLocator(Locator):
        pass

    with pytest.raises(ValueError, match="Unsupported locator type:.*"):
        vlm_serializer.serialize(UnsupportedLocator())


def test_serialize_simple_cycle_raises(vlm_serializer: VlmLocatorSerializer) -> None:
    text1 = Text("hello")
    text2 = Text("world")
    text1.above_of(text2)
    text2.above_of(text1)
    with pytest.raises(CircularDependencyError):
        vlm_serializer.serialize(text1)


def test_serialize_self_reference_cycle_raises(
    vlm_serializer: VlmLocatorSerializer,
) -> None:
    text = Text("hello")
    text.above_of(text)
    with pytest.raises(CircularDependencyError):
        vlm_serializer.serialize(text)


def test_serialize_deep_cycle_raises(vlm_serializer: VlmLocatorSerializer) -> None:
    text1 = Text("hello")
    text2 = Text("world")
    text3 = Text("earth")
    text1.above_of(text2)
    text2.above_of(text3)
    text3.above_of(text1)
    with pytest.raises(CircularDependencyError):
        vlm_serializer.serialize(text1)
