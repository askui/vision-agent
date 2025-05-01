import re
from pathlib import Path

import pytest
from PIL import Image as PILImage

from askui.locators import AiElement, Element, Image, Prompt, Text

TEST_IMAGE_PATH = Path("tests/fixtures/images/github_com__icon.png")


class TestDescriptionLocator:
    def test_initialization_with_description(self) -> None:
        desc = Prompt(prompt="test")
        assert desc._prompt == "test"
        assert str(desc) == 'element with prompt "test"'

    def test_initialization_without_description_raises(self) -> None:
        with pytest.raises(ValueError):
            Prompt()  # type: ignore

    def test_initialization_with_empty_description_raises(self) -> None:
        with pytest.raises(ValueError):
            Prompt("")

    def test_initialization_with_positional_arg(self) -> None:
        desc = Prompt("test")
        assert desc._prompt == "test"

    def test_initialization_with_invalid_args_raises(self) -> None:
        with pytest.raises(ValueError):
            Prompt(prompt=123)  # type: ignore

        with pytest.raises(ValueError):
            Prompt(123)  # type: ignore


class TestClassLocator:
    def test_initialization_with_class_name(self) -> None:
        cls = Element(class_name="text")
        assert cls._class_name == "text"
        assert str(cls) == 'element with class "text"'

    def test_initialization_without_class_name(self) -> None:
        cls = Element()
        assert cls._class_name is None
        assert str(cls) == "element"

    def test_initialization_with_positional_arg(self) -> None:
        cls = Element("text")
        assert cls._class_name == "text"

    def test_initialization_with_invalid_args_raises(self) -> None:
        with pytest.raises(ValueError):
            Element(class_name="button")  # type: ignore

        with pytest.raises(ValueError):
            Element(class_name=123)  # type: ignore

        with pytest.raises(ValueError):
            Element(123)  # type: ignore


class TestTextLocator:
    def test_initialization_with_positional_text(self) -> None:
        text = Text("Hello")
        assert text._text == "Hello"
        assert text._match_type == "similar"
        assert text._similarity_threshold == 70
        assert str(text) == 'text similar to "Hello" (similarity >= 70%)'

    def test_initialization_with_named_text(self) -> None:
        text = Text(text="hello", match_type="exact")
        assert text._text == "hello"
        assert text._match_type == "exact"
        assert str(text) == 'text "hello"'

    def test_initialization_with_similarity(self) -> None:
        text = Text(text="hello", match_type="similar", similarity_threshold=80)
        assert text._similarity_threshold == 80
        assert str(text) == 'text similar to "hello" (similarity >= 80%)'

    def test_initialization_with_contains(self) -> None:
        text = Text(text="hello", match_type="contains")
        assert str(text) == 'text containing text "hello"'

    def test_initialization_with_regex(self) -> None:
        text = Text(text="hello.*", match_type="regex")
        assert str(text) == 'text matching regex "hello.*"'

    def test_initialization_without_text(self) -> None:
        text = Text()
        assert text._text is None
        assert str(text) == "text"

    def test_initialization_with_invalid_args(self) -> None:
        with pytest.raises(ValueError):
            Text(text=123)  # type: ignore

        with pytest.raises(ValueError):
            Text(123)  # type: ignore

        with pytest.raises(ValueError):
            Text(text="hello", match_type="invalid")  # type: ignore

        with pytest.raises(ValueError):
            Text(text="hello", similarity_threshold=-1)

        with pytest.raises(ValueError):
            Text(text="hello", similarity_threshold=101)


class TestImageLocator:
    @pytest.fixture
    def test_image(self) -> PILImage.Image:
        return PILImage.open(TEST_IMAGE_PATH)

    _STR_PATTERN = re.compile(
        r'^element ".*" located by image \(threshold: \d+\.\d+, stop_threshold: \d+\.\d+, rotation_degree_per_step: \d+, image_compare_format: \w+, mask: None\)$'
    )

    def test_initialization_with_basic_params(self, test_image: PILImage.Image) -> None:
        locator = Image(image=test_image)
        assert locator._image.root == test_image
        assert locator._threshold == 0.5
        assert locator._stop_threshold == 0.5
        assert locator._mask is None
        assert locator._rotation_degree_per_step == 0
        assert locator._image_compare_format == "grayscale"
        assert re.match(self._STR_PATTERN, str(locator))

    def test_initialization_with_name(self, test_image: PILImage.Image) -> None:
        locator = Image(image=test_image, name="test")
        assert (
            str(locator)
            == 'element "test" located by image (threshold: 0.5, stop_threshold: 0.5, rotation_degree_per_step: 0, image_compare_format: grayscale, mask: None)'
        )

    def test_initialization_with_custom_params(
        self, test_image: PILImage.Image
    ) -> None:
        locator = Image(
            image=test_image,
            threshold=0.7,
            stop_threshold=0.95,
            mask=[(0, 0), (1, 0), (1, 1)],
            rotation_degree_per_step=45,
            image_compare_format="RGB",
        )
        assert locator._threshold == 0.7
        assert locator._stop_threshold == 0.95
        assert locator._mask == [(0, 0), (1, 0), (1, 1)]
        assert locator._rotation_degree_per_step == 45
        assert locator._image_compare_format == "RGB"
        assert re.match(
            r'^element "anonymous image [a-f0-9-]+" located by image \(threshold: 0.7, stop_threshold: 0.95, rotation_degree_per_step: 45, image_compare_format: RGB, mask: \[\(0.0, 0.0\), \(1.0, 0.0\), \(1.0, 1.0\)\]\)$',
            str(locator),
        )

    def test_initialization_with_invalid_args(self, test_image: PILImage.Image) -> None:
        with pytest.raises(ValueError):
            Image(image="not_an_image")

        with pytest.raises(ValueError):
            Image(image=test_image, threshold=-0.1)

        with pytest.raises(ValueError):
            Image(image=test_image, threshold=1.1)

        with pytest.raises(ValueError):
            Image(image=test_image, stop_threshold=-0.1)

        with pytest.raises(ValueError):
            Image(image=test_image, stop_threshold=1.1)

        with pytest.raises(ValueError):
            Image(image=test_image, rotation_degree_per_step=-1)

        with pytest.raises(ValueError):
            Image(image=test_image, rotation_degree_per_step=361)

        with pytest.raises(ValueError):
            Image(image=test_image, image_compare_format="invalid")  # type: ignore

        with pytest.raises(ValueError):
            Image(image=test_image, mask=[(0, 0), (1)])  # type: ignore


class TestAiElementLocator:
    def test_initialization_with_name(self) -> None:
        locator = AiElement("github_com__icon")
        assert locator._name == "github_com__icon"
        assert (
            str(locator)
            == 'ai element named "github_com__icon" (threshold: 0.5, stop_threshold: 0.5, rotation_degree_per_step: 0, image_compare_format: grayscale, mask: None)'
        )

    def test_initialization_without_name_raises(self) -> None:
        with pytest.raises(ValueError):
            AiElement()  # type: ignore

    def test_initialization_with_invalid_args_raises(self) -> None:
        with pytest.raises(ValueError):
            AiElement(123)  # type: ignore

    def test_initialization_with_custom_params(self) -> None:
        locator = AiElement(
            name="test_element",
            threshold=0.7,
            stop_threshold=0.95,
            mask=[(0, 0), (1, 0), (1, 1)],
            rotation_degree_per_step=45,
            image_compare_format="RGB",
        )
        assert locator._name == "test_element"
        assert locator._threshold == 0.7
        assert locator._stop_threshold == 0.95
        assert locator._mask == [(0, 0), (1, 0), (1, 1)]
        assert locator._rotation_degree_per_step == 45
        assert locator._image_compare_format == "RGB"
        assert (
            str(locator)
            == 'ai element named "test_element" (threshold: 0.7, stop_threshold: 0.95, rotation_degree_per_step: 45, image_compare_format: RGB, mask: [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)])'
        )

    def test_initialization_with_invalid_threshold(self) -> None:
        with pytest.raises(ValueError):
            AiElement(name="test", threshold=-0.1)

        with pytest.raises(ValueError):
            AiElement(name="test", threshold=1.1)

    def test_initialization_with_invalid_stop_threshold(self) -> None:
        with pytest.raises(ValueError):
            AiElement(name="test", stop_threshold=-0.1)

        with pytest.raises(ValueError):
            AiElement(name="test", stop_threshold=1.1)

    def test_initialization_with_invalid_rotation(self) -> None:
        with pytest.raises(ValueError):
            AiElement(name="test", rotation_degree_per_step=-1)

        with pytest.raises(ValueError):
            AiElement(name="test", rotation_degree_per_step=361)

    def test_initialization_with_invalid_image_format(self) -> None:
        with pytest.raises(ValueError):
            AiElement(name="test", image_compare_format="invalid")  # type: ignore

    def test_initialization_with_invalid_mask(self) -> None:
        with pytest.raises(ValueError):
            AiElement(name="test", mask=[(0, 0), (1)])  # type: ignore

        with pytest.raises(ValueError):
            AiElement(name="test", mask=[(0, 0)])
