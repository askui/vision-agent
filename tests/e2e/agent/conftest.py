"""Shared pytest fixtures for e2e tests."""

import pathlib
from typing import Any, Generator, Optional, Union

import pytest
from PIL import Image as PILImage
from typing_extensions import override

from askui.agent import VisionAgent
from askui.locators.serializers import AskUiLocatorSerializer
from askui.models.askui.ai_element_utils import AiElementCollection
from askui.models.askui.inference_api import (
    AskUiInferenceApi,
    AskUiInferenceApiSettings,
)
from askui.models.askui.model_router import AskUiModelRouter
from askui.models.models import ModelName
from askui.models.shared.agent import Agent
from askui.models.shared.facade import ModelFacade
from askui.models.shared.settings import (
    COMPUTER_USE_20250124_BETA_FLAG,
    ActSettings,
    MessageSettings,
)
from askui.reporting import Reporter, SimpleHtmlReporter
from askui.tools.toolbox import AgentToolbox


class ReporterMock(Reporter):
    @override
    def add_message(
        self,
        role: str,
        content: Union[str, dict[str, Any], list[Any]],
        image: Optional[PILImage.Image | list[PILImage.Image]] = None,
    ) -> None:
        pass

    @override
    def generate(self) -> None:
        pass


@pytest.fixture
def simple_html_reporter() -> Reporter:
    return SimpleHtmlReporter()


@pytest.fixture
def askui_facade(
    path_fixtures: pathlib.Path,
) -> ModelFacade:
    settings = ActSettings(
        messages=MessageSettings(betas=[COMPUTER_USE_20250124_BETA_FLAG])
    )
    reporter = SimpleHtmlReporter()
    askui_inference_api = AskUiInferenceApi(
        locator_serializer=AskUiLocatorSerializer(
            ai_element_collection=AiElementCollection(
                additional_ai_element_locations=[path_fixtures / "images"]
            ),
            reporter=reporter,
        ),
        settings=AskUiInferenceApiSettings(
            messages=settings.messages,
        ),
    )
    agent = Agent(
        messages_api=askui_inference_api,
        reporter=reporter,
    )
    return ModelFacade(
        act_model=agent,
        get_model=askui_inference_api,
        locate_model=AskUiModelRouter(inference_api=askui_inference_api),
    )


@pytest.fixture
def vision_agent(
    agent_toolbox_mock: AgentToolbox,
    simple_html_reporter: Reporter,
    askui_facade: ModelFacade,
) -> Generator[VisionAgent, None, None]:
    """Fixture providing a VisionAgent instance."""
    with VisionAgent(
        reporters=[simple_html_reporter],
        models={
            ModelName.ASKUI: askui_facade,
            ModelName.ASKUI__AI_ELEMENT: askui_facade,
            ModelName.ASKUI__COMBO: askui_facade,
            ModelName.ASKUI__OCR: askui_facade,
            ModelName.ASKUI__PTA: askui_facade,
        },
        tools=agent_toolbox_mock,
    ) as agent:
        yield agent
