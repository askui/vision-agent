import pathlib
import re

import pytest
from PIL import Image as PILImage
from pytest_mock import MockerFixture

from askui.locators import Element, Image, Prompt, Text
from askui.locators.locators import Locator
from askui.locators.relatable import CircularDependencyError
from askui.locators.serializers import AskUiLocatorSerializer
from askui.models.askui.ai_element_utils import AiElementCollection
from askui.reporting import CompositeReporter
from askui.utils.image_utils import image_to_base64

TEST_IMAGE = PILImage.new("RGB", (100, 100), color="red")
TEST_IMAGE_BASE64 = image_to_base64(TEST_IMAGE)


@pytest.fixture
def askui_serializer(path_fixtures: pathlib.Path) -> AskUiLocatorSerializer:
    return AskUiLocatorSerializer(
        ai_element_collection=AiElementCollection(
            additional_ai_element_locations=[path_fixtures / "images"]
        ),
        reporter=CompositeReporter(),
    )


def test_serialize_text_without_content(
    askui_serializer: AskUiLocatorSerializer,
) -> None:
    text = Text()
    result = askui_serializer.serialize(text)
    assert result["instruction"] == "text"
    assert result["customElements"] == []


def test_serialize_text_without_content_in_relation(
    askui_serializer: AskUiLocatorSerializer,
) -> None:
    locator = Text().right_of(Text("Name"))
    result = askui_serializer.serialize(locator)
    assert (
        result["instruction"]
        == "text index 0 right of intersection_area element_center_line text <|string|>Name<|string|>"
    )
    assert result["customElements"] == []


def test_serialize_text_similar(askui_serializer: AskUiLocatorSerializer) -> None:
    text = Text("hello", match_type="similar", similarity_threshold=80)
    result = askui_serializer.serialize(text)
    assert (
        result["instruction"]
        == "text with text <|string|>hello<|string|> that matches to 80 %"
    )
    assert result["customElements"] == []


def test_serialize_text_exact(askui_serializer: AskUiLocatorSerializer) -> None:
    text = Text("hello", match_type="exact")
    result = askui_serializer.serialize(text)
    assert result["instruction"] == "text equals text <|string|>hello<|string|>"
    assert result["customElements"] == []


def test_serialize_text_contains(askui_serializer: AskUiLocatorSerializer) -> None:
    text = Text("hello", match_type="contains")
    result = askui_serializer.serialize(text)
    assert result["instruction"] == "text contain text <|string|>hello<|string|>"
    assert result["customElements"] == []


def test_serialize_text_regex(askui_serializer: AskUiLocatorSerializer) -> None:
    text = Text("h.*o", match_type="regex")
    result = askui_serializer.serialize(text)
    assert result["instruction"] == "text match regex pattern <|string|>h.*o<|string|>"
    assert result["customElements"] == []


def test_serialize_class_no_name(askui_serializer: AskUiLocatorSerializer) -> None:
    class_ = Element()
    result = askui_serializer.serialize(class_)
    assert result["instruction"] == "element"
    assert result["customElements"] == []


def test_serialize_description(askui_serializer: AskUiLocatorSerializer) -> None:
    desc = Prompt("a big red button")
    result = askui_serializer.serialize(desc)
    assert result["instruction"] == "pta <|string|>a big red button<|string|>"
    assert result["customElements"] == []


CUSTOM_ELEMENT_STR_PATTERN = re.compile(
    r"^custom element with text <|string|>.*<|string|>$"
)


def test_serialize_image(askui_serializer: AskUiLocatorSerializer) -> None:
    image = Image(TEST_IMAGE)
    result = askui_serializer.serialize(image)
    assert re.match(CUSTOM_ELEMENT_STR_PATTERN, result["instruction"])
    assert len(result["customElements"]) == 1
    custom_element = result["customElements"][0]
    assert custom_element["customImage"] == f"data:image/png;base64,{TEST_IMAGE_BASE64}"
    assert custom_element["threshold"] == image._threshold
    assert custom_element["stopThreshold"] == image._stop_threshold
    assert "mask" not in custom_element
    assert custom_element["rotationDegreePerStep"] == image._rotation_degree_per_step
    assert custom_element["imageCompareFormat"] == image._image_compare_format
    assert custom_element["name"] == image._name


def test_serialize_image_with_all_options(
    askui_serializer: AskUiLocatorSerializer,
) -> None:
    image = Image(
        TEST_IMAGE,
        threshold=0.8,
        stop_threshold=0.9,
        mask=[(0.1, 0.1), (0.5, 0.5), (0.9, 0.9)],
        rotation_degree_per_step=5,
        image_compare_format="RGB",
        name="test_image",
    )
    result = askui_serializer.serialize(image)
    assert (
        result["instruction"]
        == "custom element with text <|string|>test_image<|string|>"
    )
    assert len(result["customElements"]) == 1
    custom_element = result["customElements"][0]
    assert custom_element["customImage"] == f"data:image/png;base64,{TEST_IMAGE_BASE64}"
    assert custom_element["threshold"] == 0.8
    assert custom_element["stopThreshold"] == 0.9
    assert custom_element["mask"] == [(0.1, 0.1), (0.5, 0.5), (0.9, 0.9)]
    assert custom_element["rotationDegreePerStep"] == 5
    assert custom_element["imageCompareFormat"] == "RGB"
    assert custom_element["name"] == "test_image"


def test_serialize_above_relation(askui_serializer: AskUiLocatorSerializer) -> None:
    text = Text("hello")
    text.above_of(Text("world"), index=1, reference_point="center")
    result = askui_serializer.serialize(text)
    assert (
        result["instruction"]
        == "text <|string|>hello<|string|> index 1 above intersection_area element_center_line text <|string|>world<|string|>"
    )
    assert result["customElements"] == []


def test_serialize_below_relation(askui_serializer: AskUiLocatorSerializer) -> None:
    text = Text("hello")
    text.below_of(Text("world"))
    result = askui_serializer.serialize(text)
    assert (
        result["instruction"]
        == "text <|string|>hello<|string|> index 0 below intersection_area element_edge_area text <|string|>world<|string|>"
    )
    assert result["customElements"] == []


def test_serialize_right_relation(askui_serializer: AskUiLocatorSerializer) -> None:
    text = Text("hello")
    text.right_of(Text("world"))
    result = askui_serializer.serialize(text)
    assert (
        result["instruction"]
        == "text <|string|>hello<|string|> index 0 right of intersection_area element_center_line text <|string|>world<|string|>"
    )
    assert result["customElements"] == []


def test_serialize_left_relation(askui_serializer: AskUiLocatorSerializer) -> None:
    text = Text("hello")
    text.left_of(Text("world"))
    result = askui_serializer.serialize(text)
    assert (
        result["instruction"]
        == "text <|string|>hello<|string|> index 0 left of intersection_area element_center_line text <|string|>world<|string|>"
    )
    assert result["customElements"] == []


def test_serialize_containing_relation(
    askui_serializer: AskUiLocatorSerializer,
) -> None:
    text = Text("hello")
    text.containing(Text("world"))
    result = askui_serializer.serialize(text)
    assert (
        result["instruction"]
        == "text <|string|>hello<|string|> contains text <|string|>world<|string|>"
    )
    assert result["customElements"] == []


def test_serialize_inside_relation(askui_serializer: AskUiLocatorSerializer) -> None:
    text = Text("hello")
    text.inside_of(Text("world"))
    result = askui_serializer.serialize(text)
    assert (
        result["instruction"]
        == "text <|string|>hello<|string|> in text <|string|>world<|string|>"
    )
    assert result["customElements"] == []


def test_serialize_nearest_to_relation(
    askui_serializer: AskUiLocatorSerializer,
) -> None:
    text = Text("hello")
    text.nearest_to(Text("world"))
    result = askui_serializer.serialize(text)
    assert (
        result["instruction"]
        == "text <|string|>hello<|string|> nearest to text <|string|>world<|string|>"
    )
    assert result["customElements"] == []


def test_serialize_and_relation(askui_serializer: AskUiLocatorSerializer) -> None:
    text = Text("hello")
    text.and_(Text("world"))
    result = askui_serializer.serialize(text)
    assert (
        result["instruction"]
        == "text <|string|>hello<|string|> and text <|string|>world<|string|>"
    )
    assert result["customElements"] == []


def test_serialize_or_relation(askui_serializer: AskUiLocatorSerializer) -> None:
    text = Text("hello")
    text.or_(Text("world"))
    result = askui_serializer.serialize(text)
    assert (
        result["instruction"]
        == "text <|string|>hello<|string|> or text <|string|>world<|string|>"
    )
    assert result["customElements"] == []


def test_serialize_multiple_relations_raises(
    askui_serializer: AskUiLocatorSerializer,
) -> None:
    text = Text("hello")
    text.above_of(Text("world"))
    text.below_of(Text("earth"))
    with pytest.raises(
        NotImplementedError,
        match="Serializing locators with multiple relations is not yet supported by AskUI",
    ):
        askui_serializer.serialize(text)


def test_serialize_relations_chain(askui_serializer: AskUiLocatorSerializer) -> None:
    text = Text("hello")
    text.above_of(Text("world").below_of(Text("earth")))
    result = askui_serializer.serialize(text)
    assert (
        result["instruction"]
        == "text <|string|>hello<|string|> index 0 above intersection_area element_edge_area text <|string|>world<|string|> index 0 below intersection_area element_edge_area text <|string|>earth<|string|>"
    )
    assert result["customElements"] == []


def test_serialize_unsupported_locator_type(
    askui_serializer: AskUiLocatorSerializer,
) -> None:
    class UnsupportedLocator(Locator):
        pass

    with pytest.raises(TypeError, match="Unsupported locator type:.*"):
        askui_serializer.serialize(UnsupportedLocator())


def test_serialize_simple_cycle_raises(
    askui_serializer: AskUiLocatorSerializer,
) -> None:
    text1 = Text("hello")
    text2 = Text("world")
    text1.above_of(text2)
    text2.above_of(text1)
    with pytest.raises(CircularDependencyError):
        askui_serializer.serialize(text1)


def test_serialize_self_reference_cycle_raises(
    askui_serializer: AskUiLocatorSerializer,
) -> None:
    text = Text("hello")
    text.above_of(text)
    with pytest.raises(CircularDependencyError):
        askui_serializer.serialize(text)


def test_serialize_deep_cycle_raises(askui_serializer: AskUiLocatorSerializer) -> None:
    text1 = Text("hello")
    text2 = Text("world")
    text3 = Text("earth")
    text1.above_of(text2)
    text2.above_of(text3)
    text3.above_of(text1)
    with pytest.raises(CircularDependencyError):
        askui_serializer.serialize(text1)


def test_serialize_cycle_detection_called_once(
    askui_serializer: AskUiLocatorSerializer, mocker: MockerFixture
) -> None:
    text1 = Text("hello")
    mocked_text1 = mocker.patch.object(text1, "_has_cycle")
    text2 = Text("world")
    mocked_text2 = mocker.patch.object(text2, "_has_cycle")
    text1.above_of(text2)
    text2.above_of(text1)
    with pytest.raises(CircularDependencyError):
        askui_serializer.serialize(text1)
    mocked_text1.assert_called_once()
    mocked_text2.assert_not_called()


def test_serialize_image_with_cycle_raises(
    askui_serializer: AskUiLocatorSerializer,
) -> None:
    image1 = Image(TEST_IMAGE, name="image1")
    image2 = Image(TEST_IMAGE, name="image2")
    image1.above_of(image2)
    image2.above_of(image1)
    with pytest.raises(CircularDependencyError):
        askui_serializer.serialize(image1)


def test_serialize_mixed_locator_types_cycle_raises(
    askui_serializer: AskUiLocatorSerializer,
) -> None:
    text = Text("hello")
    image = Image(TEST_IMAGE, name="image")
    text.above_of(image)
    image.above_of(text)
    with pytest.raises(CircularDependencyError):
        askui_serializer.serialize(text)


def test_serialize_image_with_relation(
    askui_serializer: AskUiLocatorSerializer,
) -> None:
    image = Image(TEST_IMAGE, name="image")
    image.above_of(Text("world"))
    result = askui_serializer.serialize(image)
    assert (
        result["instruction"]
        == "custom element with text <|string|>image<|string|> index 0 above intersection_area element_edge_area text <|string|>world<|string|>"
    )
    assert len(result["customElements"]) == 1
    custom_element = result["customElements"][0]
    assert custom_element["customImage"] == f"data:image/png;base64,{TEST_IMAGE_BASE64}"


def test_serialize_text_with_image_relation(
    askui_serializer: AskUiLocatorSerializer,
) -> None:
    text = Text("hello")
    text.above_of(Image(TEST_IMAGE, name="image"))
    result = askui_serializer.serialize(text)
    assert (
        result["instruction"]
        == "text <|string|>hello<|string|> index 0 above intersection_area element_edge_area custom element with text <|string|>image<|string|>"
    )
    assert len(result["customElements"]) == 1
    custom_element = result["customElements"][0]
    assert custom_element["customImage"] == f"data:image/png;base64,{TEST_IMAGE_BASE64}"


def test_serialize_multiple_images_with_relation(
    askui_serializer: AskUiLocatorSerializer,
) -> None:
    image1 = Image(TEST_IMAGE, name="image1")
    image2 = Image(TEST_IMAGE, name="image2")
    image1.above_of(image2)
    result = askui_serializer.serialize(image1)
    assert (
        result["instruction"]
        == "custom element with text <|string|>image1<|string|> index 0 above intersection_area element_edge_area custom element with text <|string|>image2<|string|>"
    )
    assert len(result["customElements"]) == 2
    assert result["customElements"][0]["name"] == "image1"
    assert result["customElements"][1]["name"] == "image2"
    assert (
        result["customElements"][0]["customImage"]
        == f"data:image/png;base64,{TEST_IMAGE_BASE64}"
    )
    assert (
        result["customElements"][1]["customImage"]
        == f"data:image/png;base64,{TEST_IMAGE_BASE64}"
    )


def test_serialize_images_with_non_neighbor_relation(
    askui_serializer: AskUiLocatorSerializer,
) -> None:
    image1 = Image(TEST_IMAGE, name="image1")
    image2 = Image(TEST_IMAGE, name="image2")
    image1.and_(image2)
    result = askui_serializer.serialize(image1)
    assert (
        result["instruction"]
        == "custom element with text <|string|>image1<|string|> and custom element with text <|string|>image2<|string|>"
    )
    assert len(result["customElements"]) == 2
    assert result["customElements"][0]["name"] == "image1"
    assert result["customElements"][1]["name"] == "image2"
    assert (
        result["customElements"][0]["customImage"]
        == f"data:image/png;base64,{TEST_IMAGE_BASE64}"
    )
    assert (
        result["customElements"][1]["customImage"]
        == f"data:image/png;base64,{TEST_IMAGE_BASE64}"
    )
