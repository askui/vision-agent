"""Shared pytest fixtures for e2e tests."""

import pathlib
from typing import Generator, Optional, Union
from typing_extensions import override
import pytest
from PIL import Image as PILImage

from askui.agent import VisionAgent
from askui.models.askui.ai_element_utils import AiElementCollection
from askui.models.askui.api import AskUiInferenceApi
from askui.locators.serializers import AskUiLocatorSerializer
from askui.models.router import ModelRouter, AskUiModelRouter
from askui.reporting import Reporter, SimpleHtmlReporter
from askui.tools.toolbox import AgentToolbox


class ReporterMock(Reporter):
    @override
    def add_message(self, role: str, content: Union[str, dict, list], image: Optional[PILImage.Image | list[PILImage.Image]] = None) -> None:
        pass
    
    @override
    def generate(self) -> None:
        pass


@pytest.fixture
def vision_agent(
    path_fixtures: pathlib.Path, agent_toolbox_mock: AgentToolbox
) -> Generator[VisionAgent, None, None]:
    """Fixture providing a VisionAgent instance."""
    ai_element_collection = AiElementCollection(
        additional_ai_element_locations=[path_fixtures / "images"]
    )
    reporter = SimpleHtmlReporter()
    serializer = AskUiLocatorSerializer(ai_element_collection=ai_element_collection, reporter=reporter)
    inference_api = AskUiInferenceApi(locator_serializer=serializer)
    model_router = ModelRouter(
        tools=agent_toolbox_mock,
        reporter=reporter,
        grounding_model_routers=[AskUiModelRouter(inference_api=inference_api)]
    )
    with VisionAgent(
        reporters=[reporter], model_router=model_router, tools=agent_toolbox_mock
    ) as agent:
        yield agent


@pytest.fixture
def github_login_screenshot(path_fixtures: pathlib.Path) -> PILImage.Image:
    """Fixture providing the GitHub login screenshot."""
    screenshot_path = (
        path_fixtures / "screenshots" / "macos__chrome__github_com__login.png"
    )
    return PILImage.open(screenshot_path)
