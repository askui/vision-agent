from dataclasses import dataclass
from typing import Literal
import pytest
from PIL import Image as PILImage

from askui.locators import Class, Description, Locator, Text, Image
from askui.locators.relatable import RelationBase
from askui.locators.serializers import AskUiLocatorSerializer
from askui.utils import image_to_base64


TEST_IMAGE = PILImage.new("RGB", (100, 100), color="red")
TEST_IMAGE_BASE64 = image_to_base64(TEST_IMAGE)


@pytest.fixture
def askui_serializer() -> AskUiLocatorSerializer:
    return AskUiLocatorSerializer()


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
    class_ = Class()
    result = askui_serializer.serialize(class_)
    assert result["instruction"] == "element"
    assert result["customElements"] == []


def test_serialize_description(askui_serializer: AskUiLocatorSerializer) -> None:
    desc = Description("a big red button")
    result = askui_serializer.serialize(desc)
    assert result["instruction"] == "pta <|string|>a big red button<|string|>"
    assert result["customElements"] == []


def test_serialize_image(askui_serializer: AskUiLocatorSerializer) -> None:
    image = Image(TEST_IMAGE)
    result = askui_serializer.serialize(image)
    assert result["instruction"] == "custom element"
    assert len(result["customElements"]) == 1
    custom_element = result["customElements"][0]
    assert custom_element["customImage"] == f"data:image/png;base64,{TEST_IMAGE_BASE64}"
    assert custom_element["threshold"] == image.threshold
    assert custom_element["stopThreshold"] == image.stop_threshold
    assert "mask" not in custom_element
    assert custom_element["rotationDegreePerStep"] == image.rotation_degree_per_step
    assert custom_element["imageCompareFormat"] == image.image_compare_format
    assert custom_element["name"] == image.name


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
    assert result["instruction"] == "custom element"
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
        == "text with text <|string|>hello<|string|> that matches to 70 % index 1 above intersection_area element_center_line text with text <|string|>world<|string|> that matches to 70 %"
    )
    assert result["customElements"] == []


def test_serialize_below_relation(askui_serializer: AskUiLocatorSerializer) -> None:
    text = Text("hello")
    text.below_of(Text("world"))
    result = askui_serializer.serialize(text)
    assert (
        result["instruction"]
        == "text with text <|string|>hello<|string|> that matches to 70 % index 0 below intersection_area element_edge_area text with text <|string|>world<|string|> that matches to 70 %"
    )
    assert result["customElements"] == []


def test_serialize_right_relation(askui_serializer: AskUiLocatorSerializer) -> None:
    text = Text("hello")
    text.right_of(Text("world"))
    result = askui_serializer.serialize(text)
    assert (
        result["instruction"]
        == "text with text <|string|>hello<|string|> that matches to 70 % index 0 right of intersection_area element_edge_area text with text <|string|>world<|string|> that matches to 70 %"
    )
    assert result["customElements"] == []


def test_serialize_left_relation(askui_serializer: AskUiLocatorSerializer) -> None:
    text = Text("hello")
    text.left_of(Text("world"))
    result = askui_serializer.serialize(text)
    assert (
        result["instruction"]
        == "text with text <|string|>hello<|string|> that matches to 70 % index 0 left of intersection_area element_edge_area text with text <|string|>world<|string|> that matches to 70 %"
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
        == "text with text <|string|>hello<|string|> that matches to 70 % contains text with text <|string|>world<|string|> that matches to 70 %"
    )
    assert result["customElements"] == []


def test_serialize_inside_relation(askui_serializer: AskUiLocatorSerializer) -> None:
    text = Text("hello")
    text.inside_of(Text("world"))
    result = askui_serializer.serialize(text)
    assert (
        result["instruction"]
        == "text with text <|string|>hello<|string|> that matches to 70 % in text with text <|string|>world<|string|> that matches to 70 %"
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
        == "text with text <|string|>hello<|string|> that matches to 70 % nearest to text with text <|string|>world<|string|> that matches to 70 %"
    )
    assert result["customElements"] == []


def test_serialize_and_relation(askui_serializer: AskUiLocatorSerializer) -> None:
    text = Text("hello")
    text.and_(Text("world"))
    result = askui_serializer.serialize(text)
    assert (
        result["instruction"]
        == "text with text <|string|>hello<|string|> that matches to 70 % and text with text <|string|>world<|string|> that matches to 70 %"
    )
    assert result["customElements"] == []


def test_serialize_or_relation(askui_serializer: AskUiLocatorSerializer) -> None:
    text = Text("hello")
    text.or_(Text("world"))
    result = askui_serializer.serialize(text)
    assert (
        result["instruction"]
        == "text with text <|string|>hello<|string|> that matches to 70 % or text with text <|string|>world<|string|> that matches to 70 %"
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
        == "text with text <|string|>hello<|string|> that matches to 70 % index 0 above intersection_area element_edge_area text with text <|string|>world<|string|> that matches to 70 % index 0 below intersection_area element_edge_area text with text <|string|>earth<|string|> that matches to 70 %"
    )
    assert result["customElements"] == []


def test_serialize_unsupported_locator_type(
    askui_serializer: AskUiLocatorSerializer,
) -> None:
    class UnsupportedLocator(Locator):
        pass

    with pytest.raises(ValueError, match="Unsupported locator type:.*"):
        askui_serializer.serialize(UnsupportedLocator())


def test_serialize_unsupported_relation_type(
    askui_serializer: AskUiLocatorSerializer,
) -> None:
    @dataclass(kw_only=True)
    class UnsupportedRelation(RelationBase):
        type: Literal["unsupported"]  # type: ignore

    text = Text("hello")
    text.relations.append(UnsupportedRelation(type="unsupported", other_locator=Text("world")))  # type: ignore

    with pytest.raises(ValueError, match='Unsupported relation type: "unsupported"'):
        askui_serializer.serialize(text)


def test_serialize_image_with_relation(
    askui_serializer: AskUiLocatorSerializer,
) -> None:
    image = Image(TEST_IMAGE)
    image.above_of(Text("world"))
    result = askui_serializer.serialize(image)
    assert (
        result["instruction"]
        == "custom element index 0 above intersection_area element_edge_area text with text <|string|>world<|string|> that matches to 70 %"
    )
    assert len(result["customElements"]) == 1
    custom_element = result["customElements"][0]
    assert custom_element["customImage"] == f"data:image/png;base64,{TEST_IMAGE_BASE64}"


def test_serialize_text_with_image_relation(
    askui_serializer: AskUiLocatorSerializer,
) -> None:
    text = Text("hello")
    text.above_of(Image(TEST_IMAGE))
    result = askui_serializer.serialize(text)
    assert (
        result["instruction"]
        == "text with text <|string|>hello<|string|> that matches to 70 % index 0 above intersection_area element_edge_area custom element"
    )
    assert len(result["customElements"]) == 1
    custom_element = result["customElements"][0]
    assert custom_element["customImage"] == f"data:image/png;base64,{TEST_IMAGE_BASE64}"


def test_serialize_multiple_custom_elements_with_relation(
    askui_serializer: AskUiLocatorSerializer,
) -> None:
    image1 = Image(TEST_IMAGE, name="image1")
    image2 = Image(TEST_IMAGE, name="image2")
    image1.above_of(image2)
    result = askui_serializer.serialize(image1)
    assert (
        result["instruction"]
        == "custom element index 0 above intersection_area element_edge_area custom element"
    )
    assert len(result["customElements"]) == 2
    assert result["customElements"][0]["name"] == "image1"
    assert result["customElements"][1]["name"] == "image2"
    assert result["customElements"][0]["customImage"] == f"data:image/png;base64,{TEST_IMAGE_BASE64}"
    assert result["customElements"][1]["customImage"] == f"data:image/png;base64,{TEST_IMAGE_BASE64}"


def test_serialize_custom_elements_with_non_neighbor_relation(
    askui_serializer: AskUiLocatorSerializer,
) -> None:
    image1 = Image(TEST_IMAGE, name="image1")
    image2 = Image(TEST_IMAGE, name="image2")
    image1.and_(image2)
    result = askui_serializer.serialize(image1)
    assert (
        result["instruction"]
        == "custom element and custom element"
    )
    assert len(result["customElements"]) == 2
    assert result["customElements"][0]["name"] == "image1"
    assert result["customElements"][1]["name"] == "image2"
    assert result["customElements"][0]["customImage"] == f"data:image/png;base64,{TEST_IMAGE_BASE64}"
    assert result["customElements"][1]["customImage"] == f"data:image/png;base64,{TEST_IMAGE_BASE64}"
