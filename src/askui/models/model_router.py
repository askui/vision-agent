import functools
import logging
from typing import Type, overload

from typing_extensions import Literal

from askui.locators.locators import Locator
from askui.locators.serializers import AskUiLocatorSerializer, VlmLocatorSerializer
from askui.models.anthropic.factory import AnthropicApiProvider, create_api_client
from askui.models.anthropic.messages_api import AnthropicMessagesApi
from askui.models.anthropic.models import AnthropicModel, AnthropicModelSettings
from askui.models.askui.ai_element_utils import AiElementCollection
from askui.models.askui.google_genai_api import AskUiGoogleGenAiApi
from askui.models.askui.inference_api_settings import AskUiInferenceApiSettings
from askui.models.askui.models import AskUiGetModel, AskUiLocateModel
from askui.models.exceptions import ModelNotFoundError, ModelTypeMismatchError
from askui.models.huggingface.spaces_api import HFSpacesHandler
from askui.models.models import (
    MODEL_TYPES,
    ActModel,
    DetectedElement,
    GetModel,
    LocateModel,
    Model,
    ModelComposition,
    ModelName,
    ModelRegistry,
)
from askui.models.shared.agent import Agent
from askui.models.shared.agent_message_param import MessageParam
from askui.models.shared.agent_on_message_cb import OnMessageCb
from askui.models.shared.facade import ModelFacade
from askui.models.shared.settings import ActSettings
from askui.models.shared.tools import ToolCollection
from askui.models.types.geometry import PointList
from askui.models.types.response_schemas import ResponseSchema
from askui.reporting import NULL_REPORTER, CompositeReporter, Reporter
from askui.utils.image_utils import ImageSource
from askui.utils.source_utils import Source

from .askui.inference_api import AskUiInferenceApi
from .ui_tars_ep.ui_tars_api import UiTarsApiHandler, UiTarsApiHandlerSettings

logger = logging.getLogger(__name__)


def initialize_default_model_registry(  # noqa: C901
    reporter: Reporter = NULL_REPORTER,
) -> ModelRegistry:
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
        act_model = Agent(
            messages_api=messages_api,
            reporter=reporter,
        )
        model = AnthropicModel(
            settings=AnthropicModelSettings(),
            messages_api=messages_api,
            locator_serializer=vlm_locator_serializer(),
        )
        return ModelFacade(
            act_model=act_model,
            get_model=model,
            locate_model=model,
        )

    @functools.cache
    def askui_google_genai_api() -> AskUiGoogleGenAiApi:
        return AskUiGoogleGenAiApi()

    @functools.cache
    def askui_inference_api() -> AskUiInferenceApi:
        return AskUiInferenceApi(
            settings=AskUiInferenceApiSettings(),
        )

    @functools.cache
    def askui_locate_model() -> AskUiLocateModel:
        return AskUiLocateModel(
            locator_serializer=AskUiLocatorSerializer(
                ai_element_collection=AiElementCollection(),
                reporter=reporter,
            ),
            inference_api=askui_inference_api(),
        )

    @functools.cache
    def askui_get_model() -> AskUiGetModel:
        return AskUiGetModel(
            google_genai_api=askui_google_genai_api(),
            inference_api=askui_inference_api(),
        )

    @functools.cache
    def askui_facade() -> ModelFacade:
        act_model = Agent(
            messages_api=anthropic_messages_api("askui"),
            reporter=reporter,
        )
        return ModelFacade(
            act_model=act_model,
            get_model=askui_get_model(),
            locate_model=askui_locate_model(),
        )

    @functools.cache
    def hf_spaces_handler() -> HFSpacesHandler:
        return HFSpacesHandler(
            locator_serializer=vlm_locator_serializer(),
        )

    @functools.cache
    def tars_handler() -> UiTarsApiHandler:
        try:
            settings = UiTarsApiHandlerSettings()
            locator_serializer = VlmLocatorSerializer()
            return UiTarsApiHandler(
                reporter=reporter,
                settings=settings,
                locator_serializer=locator_serializer,
            )
        except Exception as e:  # noqa: BLE001
            error_msg = f"Failed to initialize TARS model: {e}"
            raise ValueError(error_msg)  # noqa: B904

    return {
        ModelName.CLAUDE__SONNET__4__20250514: lambda: anthropic_facade("anthropic"),
        ModelName.ASKUI: askui_facade,
        ModelName.ASKUI__GEMINI__2_5__FLASH: askui_google_genai_api,
        ModelName.ASKUI__GEMINI__2_5__PRO: askui_google_genai_api,
        ModelName.ASKUI__AI_ELEMENT: askui_locate_model,
        ModelName.ASKUI__COMBO: askui_locate_model,
        ModelName.ASKUI__OCR: askui_locate_model,
        ModelName.ASKUI__PTA: askui_locate_model,
        ModelName.HF__SPACES__ASKUI__PTA_1: hf_spaces_handler,
        ModelName.HF__SPACES__QWEN__QWEN2_VL_2B_INSTRUCT: hf_spaces_handler,
        ModelName.HF__SPACES__QWEN__QWEN2_VL_7B_INSTRUCT: hf_spaces_handler,
        ModelName.HF__SPACES__OS_COPILOT__OS_ATLAS_BASE_7B: hf_spaces_handler,
        ModelName.HF__SPACES__SHOWUI__2B: hf_spaces_handler,
        ModelName.TARS: tars_handler,
        "anthropic/": lambda: anthropic_facade("anthropic"),
        "askui/": askui_facade,
        "bedrock/": lambda: anthropic_facade("bedrock"),
        "vertex/": lambda: anthropic_facade("vertex"),
    }


class ModelRouter:
    def __init__(
        self,
        reporter: Reporter | None = None,
        models: ModelRegistry | None = None,
    ):
        self._reporter = reporter or CompositeReporter()
        self._models = {
            key: value for key, value in (models or {}).items() if not key.endswith("/")
        }
        self._model_prefixes = {
            key: value for key, value in (models or {}).items() if key.endswith("/")
        }

    @overload
    def _get_model(
        self, model_name: str, model_type: Literal["act"]
    ) -> tuple[ActModel, str]: ...

    @overload
    def _get_model(
        self, model_name: str, model_type: Literal["get"]
    ) -> tuple[GetModel, str]: ...

    @overload
    def _get_model(
        self, model_name: str, model_type: Literal["locate"]
    ) -> tuple[LocateModel, str]: ...

    def _get_model(
        self, model_name: str, model_type: Literal["act", "get", "locate"]
    ) -> tuple[Model, str]:
        _model_name = model_name
        model_or_model_factory = self._models.get(model_name)
        if model_or_model_factory is None:
            for prefix, _model_or_model_factory in self._model_prefixes.items():
                if model_name.startswith(prefix):
                    model_or_model_factory = _model_or_model_factory
                    _model_name = model_name[len(prefix) :]
                    break
        if model_or_model_factory is None:
            raise ModelNotFoundError(model_name)

        if not isinstance(model_or_model_factory, (ActModel, GetModel, LocateModel)):
            model = model_or_model_factory()
        else:
            model = model_or_model_factory

        if not isinstance(model, MODEL_TYPES[model_type]):
            raise ModelTypeMismatchError(
                model_name,
                MODEL_TYPES[model_type],
                type(model),
            )

        return (model, _model_name)

    def act(
        self,
        messages: list[MessageParam],
        model: str,
        on_message: OnMessageCb | None = None,
        tools: ToolCollection | None = None,
        settings: ActSettings | None = None,
    ) -> None:
        m, _model = self._get_model(model, "act")
        logger.debug(
            'Routing "act" to model',
            extra={"model": model},
        )
        return m.act(
            messages=messages,
            model=_model,
            on_message=on_message,
            settings=settings,
            tools=tools,
        )

    def get(
        self,
        query: str,
        source: Source,
        model: str,
        response_schema: Type[ResponseSchema] | None = None,
    ) -> ResponseSchema | str:
        m, _model = self._get_model(model, "get")
        logger.debug(
            'Routing "get" to model',
            extra={"model": model},
        )
        return m.get(query, source, response_schema, _model)

    def locate(
        self,
        screenshot: ImageSource,
        locator: str | Locator,
        model: ModelComposition | str,
    ) -> PointList:
        _model = ModelName.ASKUI if isinstance(model, ModelComposition) else model
        _model_composition = model if isinstance(model, ModelComposition) else None
        m, _model = self._get_model(_model, "locate")
        logger.debug(
            "Routing locate prediction to",
            extra={"model": _model},
        )
        return m.locate(locator, screenshot, _model_composition or _model)

    def locate_all_elements(
        self,
        image: ImageSource,
        model: ModelComposition | str,
    ) -> list[DetectedElement]:
        _model = ModelName.ASKUI if isinstance(model, ModelComposition) else model
        _model_composition = model if isinstance(model, ModelComposition) else None
        m, _model = self._get_model(_model, "locate")
        logger.debug(
            "Routing locate_all_elements prediction to",
            extra={"model": _model},
        )
        return m.locate_all_elements(image, model=_model_composition or _model)
