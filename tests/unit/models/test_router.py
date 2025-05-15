"""Unit tests for the ModelRouter class."""

import os
import uuid
from typing import cast
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image
from pydantic import ValidationError
from pytest_mock import MockerFixture

from askui.exceptions import ModelNotFoundError
from askui.models.anthropic.claude import ClaudeHandler
from askui.models.anthropic.claude_agent import ClaudeComputerAgent
from askui.models.askui.api import AskUiInferenceApi
from askui.models.huggingface.spaces_api import HFSpacesHandler
from askui.models.models import ModelName
from askui.models.router import ModelRouter
from askui.models.types.response_schemas import ResponseSchemaBase
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
def mock_askui_inference_api(mocker: MockerFixture) -> AskUiInferenceApi:
    """Fixture providing a mock AskUI inference API."""
    mock = cast("AskUiInferenceApi", mocker.MagicMock(spec=AskUiInferenceApi))
    mock.predict.return_value = (50, 50)  # type: ignore[attr-defined]
    mock.get_inference.return_value = "Mock response"  # type: ignore[attr-defined]
    return mock


@pytest.fixture
def mock_claude(mocker: MockerFixture) -> ClaudeHandler:
    """Fixture providing a mock Claude handler."""
    mock = cast("ClaudeHandler", mocker.MagicMock(spec=ClaudeHandler))
    mock.locate_inference.return_value = (50, 50)  # type: ignore[attr-defined]
    mock.get_inference.return_value = "Mock response"  # type: ignore[attr-defined]
    return mock


@pytest.fixture
def mock_claude_agent(mocker: MockerFixture) -> ClaudeComputerAgent:
    """Fixture providing a mock Claude computer agent."""
    mock = cast("ClaudeComputerAgent", mocker.MagicMock(spec=ClaudeComputerAgent))
    mock.act = MagicMock(return_value=None)  # type: ignore[method-assign]
    return mock


@pytest.fixture
def mock_tars(mocker: MockerFixture) -> UiTarsApiHandler:
    """Fixture providing a mock TARS API handler."""
    mock = cast("UiTarsApiHandler", mocker.MagicMock(spec=UiTarsApiHandler))
    mock.locate_prediction.return_value = (50, 50)  # type: ignore[attr-defined]
    mock.get_inference.return_value = "Mock response"  # type: ignore[attr-defined]
    mock.act = MagicMock(return_value=None)  # type: ignore[method-assign]
    return mock


@pytest.fixture
def mock_hf_spaces(mocker: MockerFixture) -> HFSpacesHandler:
    """Fixture providing a mock HuggingFace spaces handler."""
    mock = cast("HFSpacesHandler", mocker.MagicMock(spec=HFSpacesHandler))
    mock.predict.return_value = (50, 50)  # type: ignore[attr-defined]
    mock.get_spaces_names.return_value = ["hf-space-1", "hf-space-2"]  # type: ignore[attr-defined]
    return mock


@pytest.fixture
def model_router(
    agent_toolbox_mock: AgentToolbox,
    mock_askui_inference_api: AskUiInferenceApi,
    mock_claude: ClaudeHandler,
    mock_claude_agent: ClaudeComputerAgent,
    mock_tars: UiTarsApiHandler,
    mock_hf_spaces: HFSpacesHandler,
    mocker: MockerFixture,
) -> ModelRouter:
    """Fixture providing a ModelRouter instance with mocked dependencies."""
    return ModelRouter(
        tools=agent_toolbox_mock,
        reporter=CompositeReporter(),
        askui_inference_api=mock_askui_inference_api,
        claude=mock_claude,
        claude_computer_agent=mock_claude_agent,
        tars=mock_tars,
        huggingface_spaces=mock_hf_spaces,
        askui_settings=mocker.MagicMock(workspace_id=TEST_WORKSPACE_ID),
    )


class TestModelRouter:
    """Test class for ModelRouter."""

    def test_locate_with_askui_model(
        self,
        model_router: ModelRouter,
        mock_image: Image.Image,
        mock_askui_inference_api: AskUiInferenceApi,
    ) -> None:
        """Test locating elements using AskUI model."""
        locator = "test locator"
        x, y = model_router.locate(mock_image, locator, ModelName.ASKUI)
        assert x == 50
        assert y == 50
        mock_askui_inference_api.predict.assert_called_once()  # type: ignore

    def test_locate_with_askui_pta_model(
        self,
        model_router: ModelRouter,
        mock_image: Image.Image,
        mock_askui_inference_api: AskUiInferenceApi,
    ) -> None:
        """Test locating elements using AskUI PTA model."""
        locator = "test locator"
        x, y = model_router.locate(mock_image, locator, ModelName.ASKUI__PTA)
        assert x == 50
        assert y == 50
        mock_askui_inference_api.predict.assert_called_once()  # type: ignore

    def test_locate_with_askui_ocr_model(
        self,
        model_router: ModelRouter,
        mock_image: Image.Image,
        mock_askui_inference_api: AskUiInferenceApi,
    ) -> None:
        """Test locating elements using AskUI OCR model."""
        locator = "test locator"
        x, y = model_router.locate(mock_image, locator, ModelName.ASKUI__OCR)
        assert x == 50
        assert y == 50
        mock_askui_inference_api.predict.assert_called_once()  # type: ignore

    def test_locate_with_askui_combo_model(
        self,
        model_router: ModelRouter,
        mock_image: Image.Image,
        mock_askui_inference_api: AskUiInferenceApi,
    ) -> None:
        """Test locating elements using AskUI combo model."""
        locator = "test locator"
        x, y = model_router.locate(mock_image, locator, ModelName.ASKUI__COMBO)
        assert x == 50
        assert y == 50
        mock_askui_inference_api.predict.assert_called_once()  # type: ignore

    def test_locate_with_askui_ai_element_model(
        self,
        model_router: ModelRouter,
        mock_image: Image.Image,
        mock_askui_inference_api: AskUiInferenceApi,
    ) -> None:
        """Test locating elements using AskUI AI element model."""
        locator = "test locator"
        x, y = model_router.locate(mock_image, locator, ModelName.ASKUI__AI_ELEMENT)
        assert x == 50
        assert y == 50
        mock_askui_inference_api.predict.assert_called_once()  # type: ignore

    def test_locate_with_tars_model(
        self,
        model_router: ModelRouter,
        mock_image: Image.Image,
        mock_tars: UiTarsApiHandler,
    ) -> None:
        """Test locating elements using TARS model."""
        locator = "test locator"
        x, y = model_router.locate(mock_image, locator, ModelName.TARS)
        assert x == 50
        assert y == 50
        mock_tars.locate_prediction.assert_called_once()  # type: ignore

    def test_locate_with_claude_model(
        self,
        model_router: ModelRouter,
        mock_image: Image.Image,
        mock_claude: ClaudeHandler,
    ) -> None:
        """Test locating elements using Claude model."""
        locator = "test locator"
        x, y = model_router.locate(
            mock_image, locator, ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022
        )
        assert x == 50
        assert y == 50
        mock_claude.locate_inference.assert_called_once()  # type: ignore

    def test_locate_with_hf_space_model(
        self,
        model_router: ModelRouter,
        mock_image: Image.Image,
        mock_hf_spaces: HFSpacesHandler,
    ) -> None:
        """Test locating elements using HuggingFace space model."""
        locator = "test locator"
        x, y = model_router.locate(mock_image, locator, "hf-space-1")
        assert x == 50
        assert y == 50
        mock_hf_spaces.predict.assert_called_once()  # type: ignore

    def test_locate_with_invalid_model(
        self, model_router: ModelRouter, mock_image: Image.Image
    ) -> None:
        """Test that locating with invalid model raises InvalidModelError."""
        with pytest.raises(ModelNotFoundError):
            model_router.locate(mock_image, "test locator", "invalid-model")

    def test_get_inference_with_askui_model(
        self,
        model_router: ModelRouter,
        mock_image_source: ImageSource,
        mock_askui_inference_api: AskUiInferenceApi,
    ) -> None:
        """Test getting inference using AskUI model."""
        response = model_router.get_inference(
            "test query", mock_image_source, model=ModelName.ASKUI
        )
        assert response == "Mock response"
        mock_askui_inference_api.get_inference.assert_called_once()  # type: ignore

    def test_get_inference_with_tars_model(
        self,
        model_router: ModelRouter,
        mock_image_source: ImageSource,
        mock_tars: UiTarsApiHandler,
    ) -> None:
        """Test getting inference using TARS model."""
        response = model_router.get_inference(
            "test query", mock_image_source, model=ModelName.TARS
        )
        assert response == "Mock response"
        mock_tars.get_inference.assert_called_once()  # type: ignore

    def test_get_inference_with_claude_model(
        self,
        model_router: ModelRouter,
        mock_image_source: ImageSource,
        mock_claude: ClaudeHandler,
    ) -> None:
        """Test getting inference using Claude model."""
        response = model_router.get_inference(
            "test query",
            mock_image_source,
            model=ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022,
        )
        assert response == "Mock response"
        mock_claude.get_inference.assert_called_once()  # type: ignore

    def test_get_inference_with_invalid_model(
        self, model_router: ModelRouter, mock_image_source: ImageSource
    ) -> None:
        """Test that getting inference with invalid model raises InvalidModelError."""
        with pytest.raises(ModelNotFoundError):
            model_router.get_inference(
                "test query", mock_image_source, model="invalid-model"
            )

    def test_get_inference_with_response_schema_not_implemented(
        self, model_router: ModelRouter, mock_image_source: ImageSource
    ) -> None:
        """
        Test that getting inference with response schema for non-AskUI models raises
        NotImplementedError.
        """

        class TestSchema(ResponseSchemaBase):
            pass

        with pytest.raises(NotImplementedError):
            model_router.get_inference(
                "test query",
                mock_image_source,
                response_schema=TestSchema,
                model=ModelName.TARS,
            )

    def test_act_with_tars_model(
        self, model_router: ModelRouter, mock_tars: UiTarsApiHandler
    ) -> None:
        """Test acting using TARS model."""
        model_router.act("test goal", ModelName.TARS)
        mock_tars.act.assert_called_once_with("test goal")  # type: ignore

    def test_act_with_claude_model(
        self, model_router: ModelRouter, mock_claude_agent: ClaudeComputerAgent
    ) -> None:
        """Test acting using Claude model."""
        model_router.act(
            "test goal", ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022
        )
        mock_claude_agent.act.assert_called_once_with("test goal")  # type: ignore

    def test_act_with_invalid_model(self, model_router: ModelRouter) -> None:
        """Test that acting with invalid model raises InvalidModelError."""
        with pytest.raises(ModelNotFoundError):
            model_router.act("test goal", "invalid-model")

    def test_act_with_missing_anthropic_credentials(
        self, model_router: ModelRouter
    ) -> None:
        """
        Test that acting with Claude model raises ValidationError when credentials are
        missing.
        """
        with patch.dict(os.environ, {}, clear=True):
            router = ModelRouter(
                tools=model_router._tools, reporter=model_router._reporter
            )
            with pytest.raises(ValidationError, match="ANTHROPIC_API_KEY"):
                router.act(
                    "test goal", ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022
                )

    def test_act_with_default_missing_credentials(
        self, model_router: ModelRouter
    ) -> None:
        """
        Test that acting with default model raises ValidationError when credentials are
        missing.
        """
        with patch.dict(os.environ, {}, clear=True):
            router = ModelRouter(
                tools=model_router._tools, reporter=model_router._reporter
            )
            with pytest.raises(ValidationError, match="ANTHROPIC_API_KEY"):
                router.act("test goal")

    def test_locate_with_missing_askui_credentials(
        self, model_router: ModelRouter, mock_image: Image.Image
    ) -> None:
        with patch.dict(os.environ, {}, clear=True):
            router = ModelRouter(
                tools=model_router._tools,
                reporter=model_router._reporter,
            )
            with pytest.raises(ValueError, match="ASKUI_WORKSPACE_ID"):
                router.locate(mock_image, "test locator", ModelName.ASKUI)

    def test_locate_with_missing_askui_credentials_only_token(
        self, model_router: ModelRouter, mock_image: Image.Image
    ) -> None:
        with patch.dict(
            os.environ, {"ASKUI_WORKSPACE_ID": str(uuid.uuid4())}, clear=True
        ):
            router = ModelRouter(
                tools=model_router._tools,
                reporter=model_router._reporter,
            )
            with pytest.raises(ValueError, match="ASKUI_TOKEN"):
                router.locate(mock_image, "test locator", ModelName.ASKUI)

    def test_get_inference_with_missing_askui_credentials(
        self,
        model_router: ModelRouter,
        mock_image_source: ImageSource,
    ) -> None:
        with patch.dict(os.environ, {}, clear=True):
            router = ModelRouter(
                tools=model_router._tools,
                reporter=model_router._reporter,
            )
            with pytest.raises(ValueError, match="ASKUI_WORKSPACE_ID"):
                router.get_inference(
                    "test query", mock_image_source, model=ModelName.ASKUI
                )

    def test_get_inference_with_default_missing_credentials(
        self,
        model_router: ModelRouter,
        mock_image_source: ImageSource,
    ) -> None:
        with patch.dict(os.environ, {}, clear=True):
            router = ModelRouter(
                tools=model_router._tools,
                reporter=model_router._reporter,
            )
            with pytest.raises(ValueError, match="ASKUI_WORKSPACE_ID"):
                router.get_inference("test query", mock_image_source)

    def test_locate_with_missing_anthropic_credentials(
        self, model_router: ModelRouter, mock_image: Image.Image
    ) -> None:
        with patch.dict(os.environ, {}, clear=True):
            router = ModelRouter(
                tools=model_router._tools,
                reporter=model_router._reporter,
            )
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
                router.locate(
                    mock_image,
                    "test locator",
                    ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022,
                )

    def test_locate_with_default_missing_credentials(
        self, model_router: ModelRouter, mock_image: Image.Image
    ) -> None:
        with patch.dict(os.environ, {}, clear=True):
            router = ModelRouter(
                tools=model_router._tools,
                reporter=model_router._reporter,
            )
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
                router.locate(mock_image, "test locator")
