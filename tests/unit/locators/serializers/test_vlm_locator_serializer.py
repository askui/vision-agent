import pytest
from askui.locators import Class, Description, Locator, Text
from askui.locators.locators import Image
from askui.locators.serializers import VlmLocatorSerializer

from PIL import Image as PILImage


TEST_IMAGE = PILImage.new('RGB', (100, 100), color='red')


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
    class_ = Class("textfield")
    result = vlm_serializer.serialize(class_)
    assert result == "an arbitrary textfield shown"


def test_serialize_class_no_name(vlm_serializer: VlmLocatorSerializer) -> None:
    class_ = Class()
    result = vlm_serializer.serialize(class_)
    assert result == "an arbitrary ui element (e.g., text, button, textfield, etc.)"


def test_serialize_description(vlm_serializer: VlmLocatorSerializer) -> None:
    desc = Description("a big red button")
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
