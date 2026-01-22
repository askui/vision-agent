"""Shared pytest fixtures for e2e tests."""

import functools
import pathlib
from typing import Any, Generator, Optional, Union

import pytest
from PIL import Image as PILImage
from typing_extensions import override

from askui.agent import VisionAgent
from askui.locators.serializers import AskUiLocatorSerializer, VlmLocatorSerializer
from askui.model_store.act_models.agent import AskUIAgent
from askui.model_store.get_models import AnthropicGetModel, AskUiGeminiGetModel
from askui.model_store.locate_models import (
    AnthropicLocateModel,
    AskUiAiElementLocateModel,
    AskUiComboLocateModel,
    AskUiLocateModel,
    AskUiOcrLocateModel,
    AskUiPtaLocateModel,
)
from askui.models.anthropic.factory import AnthropicApiProvider, create_api_client
from askui.models.anthropic.messages_api import AnthropicMessagesApi
from askui.models.anthropic.settings import AnthropicModelSettings
from askui.models.askui.ai_element_utils import AiElementCollection
from askui.models.askui.inference_api import (
    AskUiInferenceApi,
    AskUiInferenceApiSettings,
)
from askui.models.models import ActModel, GetModel, LocateModel, ModelName
from askui.reporting import NULL_REPORTER, Reporter, SimpleHtmlReporter
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
def askui_act_model() -> ActModel:
    reporter = SimpleHtmlReporter()
    return AskUIAgent(
        model_id=ModelName.CLAUDE__SONNET__4__20250514,
        messages_api=AnthropicMessagesApi(
            client=create_api_client(api_provider="askui")
        ),
        reporter=reporter,
    )


@pytest.fixture
def askui_get_model() -> GetModel:
    return AskUiGeminiGetModel(
        model_id=ModelName.GEMINI__2_5__FLASH,
        settings=AskUiInferenceApiSettings(),
    )


@pytest.fixture
def gemini_flash_get_model() -> GetModel:
    return AskUiGeminiGetModel(
        model_id=ModelName.GEMINI__2_5__FLASH,
        settings=AskUiInferenceApiSettings(),
    )


@pytest.fixture
def gemini_pro_get_model() -> GetModel:
    return AskUiGeminiGetModel(
        model_id=ModelName.GEMINI__2_5__PRO,
        settings=AskUiInferenceApiSettings(),
    )


@pytest.fixture
def claude_get_model() -> GetModel:
    return AnthropicGetModel(
        model_id=ModelName.CLAUDE__SONNET__4__20250514,
        settings=AnthropicModelSettings(),
        messages_api=AnthropicMessagesApi(
            client=create_api_client(api_provider="anthropic"),
        ),
    )


@pytest.fixture
def askui_locate_model(path_fixtures: pathlib.Path) -> LocateModel:
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
    return AskUiLocateModel(
        locator_serializer=locator_serializer,
        inference_api=askui_inference_api,
    )


@pytest.fixture
def pta_locate_model(path_fixtures: pathlib.Path) -> LocateModel:
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
    return AskUiPtaLocateModel(
        locator_serializer=locator_serializer,
        inference_api=askui_inference_api,
    )


@pytest.fixture
def ocr_locate_model(path_fixtures: pathlib.Path) -> LocateModel:
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
    return AskUiOcrLocateModel(
        locator_serializer=locator_serializer,
        inference_api=askui_inference_api,
    )


@pytest.fixture
def ai_element_locate_model(path_fixtures: pathlib.Path) -> LocateModel:
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
    return AskUiAiElementLocateModel(
        locator_serializer=locator_serializer,
        inference_api=askui_inference_api,
    )


@pytest.fixture
def combo_locate_model(path_fixtures: pathlib.Path) -> LocateModel:
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
    return AskUiComboLocateModel(
        locator_serializer=locator_serializer,
        inference_api=askui_inference_api,
    )


@functools.cache
def vlm_locator_serializer() -> VlmLocatorSerializer:
    return VlmLocatorSerializer()


@functools.cache
def anthropic_messages_api(
    api_provider: AnthropicApiProvider,
) -> AnthropicMessagesApi:
    return AnthropicMessagesApi(client=create_api_client(api_provider=api_provider))


@functools.cache
def anthropic_act_model(api_provider: AnthropicApiProvider) -> ActModel:
    messages_api = anthropic_messages_api(api_provider)
    return AskUIAgent(
        model_id=ModelName.CLAUDE__SONNET__4__20250514,
        messages_api=messages_api,
        reporter=NULL_REPORTER,
    )


@functools.cache
def anthropic_get_model(api_provider: AnthropicApiProvider) -> GetModel:
    messages_api = anthropic_messages_api(api_provider)
    return AnthropicGetModel(
        model_id=ModelName.CLAUDE__SONNET__4__20250514,
        settings=AnthropicModelSettings(),
        messages_api=messages_api,
    )


@functools.cache
def anthropic_locate_model(api_provider: AnthropicApiProvider) -> LocateModel:
    messages_api = anthropic_messages_api(api_provider)
    return AnthropicLocateModel(
        model_id=ModelName.CLAUDE__SONNET__4__20250514,
        settings=AnthropicModelSettings(),
        messages_api=messages_api,
        locator_serializer=vlm_locator_serializer(),
    )


@pytest.fixture
def vision_agent(
    agent_toolbox_mock: AgentToolbox,
    simple_html_reporter: Reporter,
    askui_act_model: ActModel,
    askui_get_model: GetModel,
    askui_locate_model: LocateModel,
) -> Generator[VisionAgent, None, None]:
    """Fixture providing a VisionAgent instance."""
    with VisionAgent(
        reporters=[simple_html_reporter],
        act_model=askui_act_model,
        get_model=askui_get_model,
        locate_model=askui_locate_model,
        tools=agent_toolbox_mock,
    ) as agent:
        yield agent
