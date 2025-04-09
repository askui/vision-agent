from pathlib import Path
import pytest
from PIL import Image

from askui.locators import Description, Class, Text, Image as ImageLocator


TEST_IMAGE_PATH = Path("tests/fixtures/images/github__icon.png")


class TestDescriptionLocator:
    def test_initialization_with_description(self) -> None:
        desc = Description(description="test")
        assert desc.description == "test"
        assert str(desc) == 'element with description "test"'

    def test_initialization_without_description_raises(self) -> None:
        with pytest.raises(TypeError):
            Description()  # type: ignore

    def test_initialization_with_positional_arg(self) -> None:
        desc = Description("test")
        assert desc.description == "test"

    def test_initialization_with_invalid_args_raises(self) -> None:
        with pytest.raises(ValueError):
            Description(description=123)  # type: ignore

        with pytest.raises(ValueError):
            Description(123)  # type: ignore


class TestClassLocator:
    def test_initialization_with_class_name(self) -> None:
        cls = Class(class_name="text")
        assert cls.class_name == "text"
        assert str(cls) == 'element with class "text"'

    def test_initialization_without_class_name(self) -> None:
        cls = Class()
        assert cls.class_name is None
        assert str(cls) == "element that has a class"

    def test_initialization_with_positional_arg(self) -> None:
        cls = Class("text")
        assert cls.class_name == "text"

    def test_initialization_with_invalid_args_raises(self) -> None:
        with pytest.raises(ValueError):
            Class(class_name="button")  # type: ignore

        with pytest.raises(ValueError):
            Class(class_name=123)  # type: ignore

        with pytest.raises(ValueError):
            Class(123)  # type: ignore


class TestTextLocator:
    def test_initialization_with_positional_text(self) -> None:
        text = Text("Hello")
        assert text.text == "Hello"
        assert text.match_type == "similar"
        assert text.similarity_threshold == 70
        assert str(text) == 'text similar to "Hello" (similarity >= 70%)'

    def test_initialization_with_named_text(self) -> None:
        text = Text(text="hello", match_type="exact")
        assert text.text == "hello"
        assert text.match_type == "exact"
        assert str(text) == 'text "hello"'

    def test_initialization_with_similarity(self) -> None:
        text = Text(text="hello", match_type="similar", similarity_threshold=80)
        assert text.similarity_threshold == 80
        assert str(text) == 'text similar to "hello" (similarity >= 80%)'

    def test_initialization_with_contains(self) -> None:
        text = Text(text="hello", match_type="contains")
        assert str(text) == 'text containing text "hello"'

    def test_initialization_with_regex(self) -> None:
        text = Text(text="hello.*", match_type="regex")
        assert str(text) == 'text matching regex "hello.*"'

    def test_initialization_without_text(self) -> None:
        text = Text()
        assert text.text is None
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
    def test_image(self) -> Image.Image:
        return Image.open(TEST_IMAGE_PATH)

    def test_initialization_with_basic_params(self, test_image: Image.Image) -> None:
        locator = ImageLocator(image=test_image)
        assert locator.image.root == test_image
        assert locator.threshold == 0.5
        assert locator.stop_threshold == 0.9
        assert locator.mask is None
        assert locator.rotation_degree_per_step == 0
        assert locator.image_compare_format == "grayscale"
        assert str(locator) == "element located by image"

    def test_initialization_with_name(self, test_image: Image.Image) -> None:
        locator = ImageLocator(image=test_image, name="test")
        assert str(locator) == 'element "test" located by image'

    def test_initialization_with_custom_params(self, test_image: Image.Image) -> None:
        locator = ImageLocator(
            image=test_image,
            threshold=0.7,
            stop_threshold=0.95,
            mask=[(0, 0), (1, 0), (1, 1)],
            rotation_degree_per_step=45,
            image_compare_format="RGB"
        )
        assert locator.threshold == 0.7
        assert locator.stop_threshold == 0.95
        assert locator.mask == [(0, 0), (1, 0), (1, 1)]
        assert locator.rotation_degree_per_step == 45
        assert locator.image_compare_format == "RGB"

    def test_initialization_with_invalid_args(self, test_image: Image.Image) -> None:
        with pytest.raises(ValueError):
            ImageLocator(image="not_an_image")  # type: ignore

        with pytest.raises(ValueError):
            ImageLocator(image=test_image, threshold=-0.1)

        with pytest.raises(ValueError):
            ImageLocator(image=test_image, threshold=1.1)

        with pytest.raises(ValueError):
            ImageLocator(image=test_image, stop_threshold=-0.1)

        with pytest.raises(ValueError):
            ImageLocator(image=test_image, stop_threshold=1.1)

        with pytest.raises(ValueError):
            ImageLocator(image=test_image, rotation_degree_per_step=-1)

        with pytest.raises(ValueError):
            ImageLocator(image=test_image, rotation_degree_per_step=361)

        with pytest.raises(ValueError):
            ImageLocator(image=test_image, image_compare_format="invalid")  # type: ignore

        with pytest.raises(ValueError):
            ImageLocator(image=test_image, mask=[(0, 0), (1)])  # type: ignore
