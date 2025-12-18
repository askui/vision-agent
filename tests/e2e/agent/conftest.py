"""Shared pytest fixtures for e2e tests."""

import functools
import pathlib
from typing import Any, Generator, Optional, Union

import pytest
from PIL import Image as PILImage
from typing_extensions import override

from askui.agent import VisionAgent
from askui.locators.serializers import AskUiLocatorSerializer, VlmLocatorSerializer
from askui.models.anthropic.factory import AnthropicApiProvider, create_api_client
from askui.models.anthropic.messages_api import AnthropicMessagesApi
from askui.models.anthropic.models import AnthropicModel, AnthropicModelSettings
from askui.models.askui.ai_element_utils import AiElementCollection
from askui.models.askui.google_genai_api import AskUiGoogleGenAiApi
from askui.models.askui.inference_api import (
    AskUiInferenceApi,
    AskUiInferenceApiSettings,
)
from askui.models.askui.models import AskUiGetModel, AskUiLocateModel
from askui.models.models import ModelName
from askui.models.shared.facade import ModelFacade
from askui.reporting import Reporter, SimpleHtmlReporter
from askui.tools.toolbox import AgentToolbox
from askui.utils.annotated_image import AnnotatedImage


class ReporterMock(Reporter):
    @override
    def add_message(
        self,
        role: str,
        content: Union[str, dict[str, Any], list[Any]],
        image: Optional[PILImage.Image | list[PILImage.Image] | AnnotatedImage] = None,
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
    reporter = SimpleHtmlReporter()
    locator_serializer = AskUiLocatorSerializer(
        ai_element_collection=AiElementCollection(
            additional_ai_element_locations=[path_fixtures / "images"]
        ),
        reporter=reporter,
    )
    askui_inference_api = AskUiInferenceApi(
        settings=AskUiInferenceApiSettings(),
    )
    # Act model now handled by Conversation in AgentBase
    return ModelFacade(
        act_model=None,
        get_model=AskUiGetModel(
            google_genai_api=AskUiGoogleGenAiApi(),
            inference_api=askui_inference_api,
        ),
        locate_model=AskUiLocateModel(
            locator_serializer=locator_serializer,
            inference_api=askui_inference_api,
        ),
    )


@functools.cache
def vlm_locator_serializer() -> VlmLocatorSerializer:
    return VlmLocatorSerializer()


@functools.cache
def anthropic_messages_api(
    api_provider: AnthropicApiProvider,
) -> AnthropicMessagesApi:
    return AnthropicMessagesApi(
        client=create_api_client(api_provider=api_provider),
        locator_serializer=vlm_locator_serializer(),
    )


@functools.cache
def anthropic_facade(api_provider: AnthropicApiProvider) -> ModelFacade:
    messages_api = anthropic_messages_api(api_provider)
    model = AnthropicModel(
        settings=AnthropicModelSettings(),
        messages_api=messages_api,
        locator_serializer=vlm_locator_serializer(),
    )
    # Act model now handled by Conversation in AgentBase
    return ModelFacade(
        act_model=None,
        get_model=model,
        locate_model=model,
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
            ModelName.CLAUDE__SONNET__4__20250514: lambda: anthropic_facade(
                "anthropic"
            ),
            "askui/": askui_facade,
        },
        tools=agent_toolbox_mock,
    ) as agent:
        yield agent
