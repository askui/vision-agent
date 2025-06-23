"""Integration tests for Holo-1 model implementation."""

import pytest
from PIL import Image
from pytest_mock import MockerFixture

from askui.locators.locators import Button, Locator
from askui.locators.serializers import VlmLocatorSerializer
from askui.models.huggingface.holo1 import Holo1LocateModel
from askui.models.huggingface.settings import Holo1Settings
from askui.utils.image_utils import Img


class TestHolo1Integration:
    """Integration tests for Holo-1 model."""

    @pytest.fixture
    def mock_settings(self) -> Holo1Settings:
        """Create mock settings for testing."""
        return Holo1Settings(
            model_name="Hcompany/Holo1-7B",
            device="cpu",
            max_new_tokens=50,
            temperature=0.1,
        )

    @pytest.fixture
    def mock_locator_serializer(self) -> VlmLocatorSerializer:
        """Create a mock locator serializer."""
        return VlmLocatorSerializer()

    @pytest.fixture
    def sample_image(self) -> Img:
        """Create a sample image for testing."""
        # Create a simple test image
        img = Image.new("RGB", (800, 600), color="white")
        return Img(img)

    def test_holo1_initialization(
        self,
        mock_locator_serializer: VlmLocatorSerializer,
        mock_settings: Holo1Settings,
    ) -> None:
        """Test Holo-1 model initialization."""
        model = Holo1LocateModel(
            locator_serializer=mock_locator_serializer,
            model_name=mock_settings.model_name,
            device=mock_settings.device,
        )

        assert model._model_name == "Hcompany/Holo1-7B"
        assert model._device == "cpu"
        assert model._model is None  # Lazy loading
        assert model._processor is None

    def test_holo1_locate_with_string(
        self,
        mocker: MockerFixture,
        mock_locator_serializer: VlmLocatorSerializer,
        sample_image: Img,
    ) -> None:
        """Test locating an element with a string description."""
        # Mock the model loading and inference
        mock_processor = mocker.MagicMock()
        mock_model = mocker.MagicMock()

        mocker.patch(
            "transformers.AutoProcessor.from_pretrained", return_value=mock_processor
        )
        mocker.patch(
            "transformers.AutoModelForImageTextToText.from_pretrained",
            return_value=mock_model,
        )

        # Mock the model output
        mock_processor.batch_decode.return_value = ['{"bbox": [100, 200, 150, 250]}']
        mock_model.generate.return_value = [[1, 2, 3]]  # Mock token output

        model = Holo1LocateModel(
            locator_serializer=mock_locator_serializer,
            model_name="Hcompany/Holo1-7B",
            device="cpu",
        )

        result = model.locate(
            locator="Submit button",
            image=sample_image,
            model_choice="holo-1",
        )

        assert result == (125, 225)  # Center of bbox [100, 200, 150, 250]

    def test_holo1_locate_with_locator_object(
        self,
        mocker: MockerFixture,
        mock_locator_serializer: VlmLocatorSerializer,
        sample_image: Img,
    ) -> None:
        """Test locating an element with a Locator object."""
        # Mock the model loading and inference
        mock_processor = mocker.MagicMock()
        mock_model = mocker.MagicMock()

        mocker.patch(
            "transformers.AutoProcessor.from_pretrained", return_value=mock_processor
        )
        mocker.patch(
            "transformers.AutoModelForImageTextToText.from_pretrained",
            return_value=mock_model,
        )

        # Mock the model output with coordinate format
        mock_processor.batch_decode.return_value = ["Element at (300, 400)"]
        mock_model.generate.return_value = [[1, 2, 3]]

        model = Holo1LocateModel(
            locator_serializer=mock_locator_serializer,
            model_name="Hcompany/Holo1-7B",
            device="cpu",
        )

        locator = Locator(Button("Submit"))
        result = model.locate(
            locator=locator,
            image=sample_image,
            model_choice="holo-1",
        )

        assert result == (300, 400)

    def test_holo1_model_composition_not_supported(
        self,
        mock_locator_serializer: VlmLocatorSerializer,
        sample_image: Img,
    ) -> None:
        """Test that model composition raises NotImplementedError."""
        from askui.models import ModelComposition, ModelDefinition

        model = Holo1LocateModel(
            locator_serializer=mock_locator_serializer,
            model_name="Hcompany/Holo1-7B",
            device="cpu",
        )

        composition = ModelComposition(
            [
                ModelDefinition(
                    task="locate",
                    architecture="holo1",
                    version="1",
                    interface="test",
                )
            ]
        )

        with pytest.raises(
            NotImplementedError, match="Model composition is not supported"
        ):
            model.locate(
                locator="button",
                image=sample_image,
                model_choice=composition,
            )

    def test_holo1_element_not_found(
        self,
        mocker: MockerFixture,
        mock_locator_serializer: VlmLocatorSerializer,
        sample_image: Img,
    ) -> None:
        """Test handling when element cannot be found."""
        from askui.exceptions import ElementNotFoundError

        # Mock the model loading and inference
        mock_processor = mocker.MagicMock()
        mock_model = mocker.MagicMock()

        mocker.patch(
            "transformers.AutoProcessor.from_pretrained", return_value=mock_processor
        )
        mocker.patch(
            "transformers.AutoModelForImageTextToText.from_pretrained",
            return_value=mock_model,
        )

        # Mock the model output without valid coordinates
        mock_processor.batch_decode.return_value = ["No element found"]
        mock_model.generate.return_value = [[1, 2, 3]]

        model = Holo1LocateModel(
            locator_serializer=mock_locator_serializer,
            model_name="Hcompany/Holo1-7B",
            device="cpu",
        )

        with pytest.raises(ElementNotFoundError):
            model.locate(
                locator="Submit button",
                image=sample_image,
                model_choice="holo-1",
            )

    def test_holo1_model_loading_error(
        self,
        mocker: MockerFixture,
        mock_locator_serializer: VlmLocatorSerializer,
        sample_image: Img,
    ) -> None:
        """Test handling of model loading errors."""
        from askui.exceptions import AutomationError

        # Mock model loading to fail
        mocker.patch(
            "transformers.AutoProcessor.from_pretrained",
            side_effect=Exception("Model not found"),
        )

        model = Holo1LocateModel(
            locator_serializer=mock_locator_serializer,
            model_name="invalid-model",
            device="cpu",
        )

        with pytest.raises(AutomationError, match="Failed to load Holo-1 model"):
            model.locate(
                locator="button",
                image=sample_image,
                model_choice="holo-1",
            )
