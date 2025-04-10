"""Shared pytest fixtures for e2e tests."""

import pathlib
import pytest
from PIL import Image as PILImage

from askui.agent import VisionAgent
from askui.models.askui.ai_element_utils import AiElementCollection
from askui.models.askui.api import AskUiInferenceApi
from askui.locators.serializers import AskUiLocatorSerializer
from askui.models.router import ModelRouter, AskUiModelRouter


@pytest.fixture
def vision_agent(path_fixtures: pathlib.Path) -> VisionAgent:
    """Fixture providing a VisionAgent instance."""
    ai_element_collection = AiElementCollection(additional_ai_element_locations=[path_fixtures / "images"])
    serializer = AskUiLocatorSerializer(ai_element_collection=ai_element_collection)
    inference_api = AskUiInferenceApi(locator_serializer=serializer)
    model_router = ModelRouter(
        grounding_model_routers=[AskUiModelRouter(inference_api=inference_api)]
    )
    return VisionAgent(enable_askui_controller=False, enable_report=False, model_router=model_router)


@pytest.fixture
def github_login_screenshot(path_fixtures: pathlib.Path) -> PILImage.Image:
    """Fixture providing the GitHub login screenshot."""
    screenshot_path = (
        path_fixtures / "screenshots" / "macos__chrome__github_com__login.png"
    )
    return PILImage.open(screenshot_path)
