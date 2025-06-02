"""Shared pytest fixtures for e2e tests."""

import pathlib
from typing import Any, Generator, Optional, Union

import pytest
from PIL import Image as PILImage
from typing_extensions import override

from askui.agent import VisionAgent
from askui.locators.serializers import AskUiLocatorSerializer
from askui.models.askui.ai_element_utils import AiElementCollection
from askui.models.askui.computer_agent import AskUiComputerAgent
from askui.models.askui.facade import AskUiFacade
from askui.models.askui.inference_api import AskUiInferenceApi, AskUiSettings
from askui.models.askui.model_router import AskUiModelRouter
from askui.models.askui.settings import AskUiComputerAgentSettings
from askui.models.models import ModelName
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
def askui_settings() -> AskUiSettings:
    return AskUiSettings()


@pytest.fixture
def askui_inference_api(
    askui_settings: AskUiSettings,
    path_fixtures: pathlib.Path,
) -> AskUiInferenceApi:
    ai_element_collection = AiElementCollection(
        additional_ai_element_locations=[path_fixtures / "images"]
    )
    reporter = SimpleHtmlReporter()
    serializer = AskUiLocatorSerializer(
        ai_element_collection=ai_element_collection, reporter=reporter
    )
    return AskUiInferenceApi(
        locator_serializer=serializer,
        settings=askui_settings,
    )


@pytest.fixture
def askui_computer_agent(
    agent_toolbox_mock: AgentToolbox,
    askui_settings: AskUiSettings,
    simple_html_reporter: Reporter,
) -> AskUiComputerAgent:
    return AskUiComputerAgent(
        agent_os=agent_toolbox_mock.os,
        reporter=simple_html_reporter,
        settings=AskUiComputerAgentSettings(
            askui=askui_settings,
        ),
    )


@pytest.fixture
def askui_facade(
    askui_computer_agent: AskUiComputerAgent,
    askui_inference_api: AskUiInferenceApi,
) -> AskUiFacade:
    return AskUiFacade(
        computer_agent=askui_computer_agent,
        inference_api=askui_inference_api,
        model_router=AskUiModelRouter(inference_api=askui_inference_api),
    )


@pytest.fixture
def vision_agent(
    agent_toolbox_mock: AgentToolbox,
    simple_html_reporter: Reporter,
    askui_facade: AskUiFacade,
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
