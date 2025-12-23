"""Shared pytest fixtures for e2e tests."""

from collections.abc import Callable
from typing import Any, Generator, Optional, Union

import pytest
from PIL import Image as PILImage
from typing_extensions import override

from askui.agent import VisionAgent
from askui.locators.serializers import AskUiLocatorSerializer, VlmLocatorSerializer
from askui.models.anthropic.factory import create_api_client
from askui.models.anthropic.messages_api import AnthropicMessagesApi
from askui.models.anthropic.models import AnthropicModel, AnthropicModelSettings
from askui.models.askui.google_genai_api import AskUiGoogleGenAiApi
from askui.models.askui.inference_api import AskUiInferenceApi
from askui.models.askui.inference_api_settings import AskUiInferenceApiSettings
from askui.models.askui.models import AskUiGetModel, AskUiLocateModel
from askui.models.models import GetModel, LocateModel
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
    def add_usage_summary(self, usage: dict[str, int | None]) -> None:
        pass

    @override
    def generate(self) -> None:
        pass


@pytest.fixture
def simple_html_reporter() -> Reporter:
    return SimpleHtmlReporter()


@pytest.fixture
def vision_agent(
    agent_toolbox_mock: AgentToolbox,
    simple_html_reporter: Reporter,
) -> Generator[VisionAgent, None, None]:
    """Fixture providing a VisionAgent instance.

    Note: Custom models are no longer supported via the models parameter.
    The agent will use default AskUI models for get/locate operations.
    """
    with VisionAgent(
        reporters=[simple_html_reporter],
        tools=agent_toolbox_mock,
    ) as agent:
        yield agent


@pytest.fixture
def askui_locate_model_factory() -> Callable[[str | None], LocateModel]:
    """Factory for creating AskUiLocateModel instances with custom model_name."""

    def _create_model(model_name: str | None = None) -> LocateModel:
        from askui.models.askui.ai_element_utils import AiElementCollection

        # Create dependencies for AskUiLocatorSerializer
        ai_element_collection = AiElementCollection(additional_ai_element_locations=[])
        reporter = ReporterMock()

        locator_serializer = AskUiLocatorSerializer(
            ai_element_collection=ai_element_collection,
            reporter=reporter,
        )
        inference_api = AskUiInferenceApi(settings=AskUiInferenceApiSettings())
        return AskUiLocateModel(
            locator_serializer=locator_serializer,
            inference_api=inference_api,
            model_name=model_name,
        )

    return _create_model


@pytest.fixture
def askui_get_model_factory() -> Callable[[str | None], GetModel]:
    """Factory for creating AskUiGetModel instances with custom model_name."""

    def _create_model(model_name: str | None = None) -> GetModel:
        google_genai_api = AskUiGoogleGenAiApi()
        inference_api = AskUiInferenceApi(settings=AskUiInferenceApiSettings())
        return AskUiGetModel(
            google_genai_api=google_genai_api,
            inference_api=inference_api,
            model_name=model_name,
        )

    return _create_model


@pytest.fixture
def anthropic_model() -> AnthropicModel:
    """Fixture providing an AnthropicModel instance."""
    client = create_api_client("askui")  # Use askui proxy for tests
    locator_serializer = VlmLocatorSerializer()
    messages_api = AnthropicMessagesApi(
        client=client,
        locator_serializer=locator_serializer,
    )
    settings = AnthropicModelSettings()
    return AnthropicModel(
        settings=settings,
        messages_api=messages_api,
        locator_serializer=locator_serializer,
    )
