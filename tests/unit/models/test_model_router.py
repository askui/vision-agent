"""Unit tests for the ModelRouter class."""

import uuid
from typing import cast
from unittest.mock import MagicMock

import pytest
from PIL import Image
from pytest_mock import MockerFixture

from askui.exceptions import ModelNotFoundError
from askui.models.anthropic.facade import AnthropicFacade
from askui.models.askui.facade import AskUiFacade
from askui.models.huggingface.spaces_api import HFSpacesHandler
from askui.models.model_router import ModelRouter
from askui.models.models import ModelName
from askui.models.ui_tars_ep.ui_tars_api import UiTarsApiHandler
from askui.reporting import CompositeReporter
from askui.tools.toolbox import AgentToolbox
from askui.utils.image_utils import ImageSource

# Test UUID for workspace_id
TEST_WORKSPACE_ID = uuid.uuid4()


@pytest.fixture
def mock_image() -> Image.Image:
    """Fixture providing a mock PIL Image."""
    return Image.new("RGB", (100, 100))


@pytest.fixture
def mock_image_source(mock_image: Image.Image) -> ImageSource:
    """Fixture providing a mock ImageSource."""
    return ImageSource(root=mock_image)


@pytest.fixture
def mock_tars(mocker: MockerFixture) -> UiTarsApiHandler:
    """Fixture providing a mock TARS API handler."""
    mock = cast("UiTarsApiHandler", mocker.MagicMock(spec=UiTarsApiHandler))
    mock.locate.return_value = (50, 50)  # type: ignore[attr-defined]
    mock.get.return_value = "Mock response"  # type: ignore[attr-defined]
    mock.act = MagicMock(return_value=None)  # type: ignore[method-assign]
    return mock


@pytest.fixture
def mock_hf_spaces(mocker: MockerFixture) -> HFSpacesHandler:
    """Fixture providing a mock HuggingFace spaces handler."""
    mock = cast("HFSpacesHandler", mocker.MagicMock(spec=HFSpacesHandler))
    mock.locate.return_value = (50, 50)  # type: ignore[attr-defined]
    mock.get_spaces_names.return_value = ["hf-space-1", "hf-space-2"]  # type: ignore[attr-defined]
    return mock


@pytest.fixture
def mock_anthropic_facade(mocker: MockerFixture) -> AnthropicFacade:
    """Fixture providing a mock Anthropic facade."""
    mock = cast("AnthropicFacade", mocker.MagicMock(spec=AnthropicFacade))
    mock.act.return_value = None  # type: ignore[attr-defined]
    mock.get.return_value = "Mock response"  # type: ignore[attr-defined]
    mock.locate.return_value = (50, 50)  # type: ignore[attr-defined]
    return mock


@pytest.fixture
def mock_askui_facade(mocker: MockerFixture) -> AskUiFacade:
    """Fixture providing a mock AskUI facade."""
    mock = cast("AskUiFacade", mocker.MagicMock(spec=AskUiFacade))
    mock.act.return_value = None  # type: ignore[attr-defined]
    mock.get.return_value = "Mock response"  # type: ignore[attr-defined]
    mock.locate.return_value = (50, 50)  # type: ignore[attr-defined]
    return mock


@pytest.fixture
def model_router(
    agent_toolbox_mock: AgentToolbox,
    mock_anthropic_facade: AnthropicFacade,
    mock_askui_facade: AskUiFacade,
    mock_tars: UiTarsApiHandler,
    mock_hf_spaces: HFSpacesHandler,
) -> ModelRouter:
    """Fixture providing a ModelRouter instance with mocked dependencies."""
    return ModelRouter(
        tools=agent_toolbox_mock,
        reporter=CompositeReporter(),
        models={
            ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022: mock_anthropic_facade,
            ModelName.ASKUI: mock_askui_facade,
            ModelName.ASKUI__AI_ELEMENT: mock_askui_facade,
            ModelName.ASKUI__COMBO: mock_askui_facade,
            ModelName.ASKUI__OCR: mock_askui_facade,
            ModelName.ASKUI__PTA: mock_askui_facade,
            ModelName.HF__SPACES__ASKUI__PTA_1: mock_hf_spaces,
            ModelName.HF__SPACES__OS_COPILOT__OS_ATLAS_BASE_7B: mock_hf_spaces,
            ModelName.HF__SPACES__QWEN__QWEN2_VL_2B_INSTRUCT: mock_hf_spaces,
            ModelName.HF__SPACES__QWEN__QWEN2_VL_7B_INSTRUCT: mock_hf_spaces,
            ModelName.HF__SPACES__SHOWUI__2B: mock_hf_spaces,
            ModelName.TARS: mock_tars,
        },
    )


class TestModelRouter:
    """Test class for ModelRouter."""

    def test_locate_with_askui_model(
        self,
        model_router: ModelRouter,
        mock_image: Image.Image,
        mock_askui_facade: AskUiFacade,
    ) -> None:
        """Test locating elements using AskUI model."""
        locator = "test locator"
        x, y = model_router.locate(ImageSource(mock_image), locator, ModelName.ASKUI)
        assert x == 50
        assert y == 50
        mock_askui_facade.locate.assert_called_once()  # type: ignore

    def test_locate_with_askui_pta_model(
        self,
        model_router: ModelRouter,
        mock_image: Image.Image,
        mock_askui_facade: AskUiFacade,
    ) -> None:
        """Test locating elements using AskUI PTA model."""
        locator = "test locator"
        x, y = model_router.locate(
            ImageSource(mock_image), locator, ModelName.ASKUI__PTA
        )
        assert x == 50
        assert y == 50
        mock_askui_facade.locate.assert_called_once()  # type: ignore

    def test_locate_with_askui_ocr_model(
        self,
        model_router: ModelRouter,
        mock_image: Image.Image,
        mock_askui_facade: AskUiFacade,
    ) -> None:
        """Test locating elements using AskUI OCR model."""
        locator = "test locator"
        x, y = model_router.locate(
            ImageSource(mock_image), locator, ModelName.ASKUI__OCR
        )
        assert x == 50
        assert y == 50
        mock_askui_facade.locate.assert_called_once()  # type: ignore

    def test_locate_with_askui_combo_model(
        self,
        model_router: ModelRouter,
        mock_image: Image.Image,
        mock_askui_facade: AskUiFacade,
    ) -> None:
        """Test locating elements using AskUI combo model."""
        locator = "test locator"
        x, y = model_router.locate(
            ImageSource(mock_image), locator, ModelName.ASKUI__COMBO
        )
        assert x == 50
        assert y == 50
        mock_askui_facade.locate.assert_called_once()  # type: ignore

    def test_locate_with_askui_ai_element_model(
        self,
        model_router: ModelRouter,
        mock_image: Image.Image,
        mock_askui_facade: AskUiFacade,
    ) -> None:
        """Test locating elements using AskUI AI element model."""
        locator = "test locator"
        x, y = model_router.locate(
            ImageSource(mock_image), locator, ModelName.ASKUI__AI_ELEMENT
        )
        assert x == 50
        assert y == 50
        mock_askui_facade.locate.assert_called_once()  # type: ignore

    def test_locate_with_tars_model(
        self,
        model_router: ModelRouter,
        mock_image: Image.Image,
        mock_tars: UiTarsApiHandler,
    ) -> None:
        """Test locating elements using TARS model."""
        locator = "test locator"
        x, y = model_router.locate(ImageSource(mock_image), locator, ModelName.TARS)
        assert x == 50
        assert y == 50
        mock_tars.locate.assert_called_once()  # type: ignore

    def test_locate_with_claude_model(
        self,
        model_router: ModelRouter,
        mock_image: Image.Image,
        mock_anthropic_facade: AnthropicFacade,
    ) -> None:
        """Test locating elements using Claude model."""
        locator = "test locator"
        x, y = model_router.locate(
            ImageSource(mock_image),
            locator,
            ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022,
        )
        assert x == 50
        assert y == 50
        mock_anthropic_facade.locate.assert_called_once()  # type: ignore

    def test_locate_with_hf_space_model(
        self,
        model_router: ModelRouter,
        mock_image: Image.Image,
        mock_hf_spaces: HFSpacesHandler,
    ) -> None:
        """Test locating elements using HuggingFace space model."""
        locator = "test locator"
        x, y = model_router.locate(
            ImageSource(mock_image),
            locator,
            model_choice=ModelName.HF__SPACES__OS_COPILOT__OS_ATLAS_BASE_7B,
        )
        assert x == 50
        assert y == 50
        mock_hf_spaces.locate.assert_called_once()  # type: ignore

    def test_locate_with_invalid_model(
        self, model_router: ModelRouter, mock_image: Image.Image
    ) -> None:
        """Test that locating with invalid model raises InvalidModelError."""
        with pytest.raises(ModelNotFoundError):
            model_router.locate(
                ImageSource(mock_image), "test locator", "invalid-model"
            )

    def test_get_with_askui_model(
        self,
        model_router: ModelRouter,
        mock_image_source: ImageSource,
        mock_askui_facade: AskUiFacade,
    ) -> None:
        """Test getting inference using AskUI model."""
        response = model_router.get(
            "test query", mock_image_source, model_choice=ModelName.ASKUI
        )
        assert response == "Mock response"
        mock_askui_facade.get.assert_called_once()  # type: ignore

    def test_get_with_tars_model(
        self,
        model_router: ModelRouter,
        mock_image_source: ImageSource,
        mock_tars: UiTarsApiHandler,
    ) -> None:
        """Test getting inference using TARS model."""
        response = model_router.get(
            "test query", mock_image_source, model_choice=ModelName.TARS
        )
        assert response == "Mock response"
        mock_tars.get.assert_called_once()  # type: ignore

    def test_get_with_claude_model(
        self,
        model_router: ModelRouter,
        mock_image_source: ImageSource,
        mock_anthropic_facade: AnthropicFacade,
    ) -> None:
        """Test getting inference using Claude model."""
        response = model_router.get(
            "test query",
            mock_image_source,
            model_choice=ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022,
        )
        assert response == "Mock response"
        mock_anthropic_facade.get.assert_called_once()  # type: ignore

    def test_get_with_invalid_model(
        self, model_router: ModelRouter, mock_image_source: ImageSource
    ) -> None:
        """Test that getting inference with invalid model raises InvalidModelError."""
        with pytest.raises(ModelNotFoundError):
            model_router.get(
                "test query", mock_image_source, model_choice="invalid-model"
            )

    def test_act_with_tars_model(
        self, model_router: ModelRouter, mock_tars: UiTarsApiHandler
    ) -> None:
        """Test acting using TARS model."""
        model_router.act("test goal", ModelName.TARS)
        mock_tars.act.assert_called_once_with("test goal", ModelName.TARS)  # type: ignore

    def test_act_with_claude_model(
        self, model_router: ModelRouter, mock_anthropic_facade: AnthropicFacade
    ) -> None:
        """Test acting using Claude model."""
        model_router.act(
            "test goal", ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022
        )
        mock_anthropic_facade.act.assert_called_once_with(  # type: ignore
            "test goal", ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022
        )

    def test_act_with_invalid_model(self, model_router: ModelRouter) -> None:
        """Test that acting with invalid model raises InvalidModelError."""
        with pytest.raises(ModelNotFoundError):
            model_router.act("test goal", "invalid-model")
