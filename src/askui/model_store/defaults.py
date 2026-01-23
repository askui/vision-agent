"""Default model factory functions.

This module provides cached factory functions for creating default model instances.
These are used by AgentBase when no custom models are provided.
"""

from functools import cache

from askui.locators.serializers import AskUiLocatorSerializer
from askui.model_store.act_models.agent import AskUIAgent
from askui.model_store.get_models.gemini_get_model import AskUiGeminiGetModel
from askui.model_store.locate_models import AskUiLocateModel
from askui.models.askui.ai_element_utils import AiElementCollection
from askui.models.askui.inference_api import AskUiInferenceApi
from askui.models.askui.inference_api_settings import AskUiInferenceApiSettings
from askui.models.askui.locate_api import AskUiInferenceLocateApi
from askui.models.models import ActModel, GetModel, LocateModel, ModelName
from askui.reporting import NULL_REPORTER


@cache
def _get_askui_inference_api_settings() -> AskUiInferenceApiSettings:
    """Get shared AskUI inference API settings instance."""
    return AskUiInferenceApiSettings()


@cache
def _get_askui_inference_api() -> AskUiInferenceApi:
    """Get shared AskUI inference API client instance."""
    return AskUiInferenceApi(_get_askui_inference_api_settings())


@cache
def _get_askui_locator_serializer() -> AskUiLocatorSerializer:
    """Get shared AskUI locator serializer instance."""
    ai_element_collection = AiElementCollection()
    return AskUiLocatorSerializer(
        ai_element_collection=ai_element_collection,
        reporter=NULL_REPORTER,
    )


@cache
def default_act_model() -> ActModel:
    """Returns the default ActModel (Claude Sonnet via AskUI).

    The model is cached as a singleton for efficiency.

    Returns:
        ActModel: Default ActModel instance using Claude Sonnet 4.
    """
    from askui.models.anthropic.factory import create_api_client
    from askui.models.anthropic.messages_api import AnthropicMessagesApi

    client = create_api_client(api_provider="askui")
    messages_api = AnthropicMessagesApi(
        client=client,
    )

    return AskUIAgent(
        model_id=ModelName.CLAUDE__SONNET__4__20250514,
        messages_api=messages_api,
    )


@cache
def default_get_model() -> GetModel:
    """Returns the default GetModel (AskUI Gemini).

    The model is cached as a singleton for efficiency.

    Returns:
        GetModel: Default GetModel instance using Google Gemini 2.5 Flash.
    """
    return AskUiGeminiGetModel(
        model_id=ModelName.GEMINI__2_5__FLASH,
        inference_api_settings=AskUiInferenceApiSettings(),
    )


@cache
def default_locate_model() -> LocateModel:
    """Returns the default LocateModel (AskUI).

    The model is cached as a singleton for efficiency.

    Returns:
        LocateModel: Default LocateModel instance.
    """
    locator_serializer = _get_askui_locator_serializer()
    inference_api = _get_askui_inference_api()
    locate_api = AskUiInferenceLocateApi(
        locator_serializer=locator_serializer,
        inference_api=inference_api,
    )

    return AskUiLocateModel(locate_api=locate_api)
