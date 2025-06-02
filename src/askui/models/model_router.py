import functools
from typing import Type, overload

from typing_extensions import Literal

from askui.exceptions import ModelNotFoundError, ModelTypeMismatchError
from askui.locators.locators import Locator
from askui.locators.serializers import AskUiLocatorSerializer, VlmLocatorSerializer
from askui.models.anthropic.facade import AnthropicFacade
from askui.models.anthropic.settings import (
    AnthropicSettings,
    ClaudeComputerAgentSettings,
    ClaudeSettings,
)
from askui.models.askui.ai_element_utils import AiElementCollection
from askui.models.askui.computer_agent import AskUiComputerAgent
from askui.models.askui.facade import AskUiFacade
from askui.models.askui.model_router import AskUiModelRouter
from askui.models.askui.settings import AskUiComputerAgentSettings
from askui.models.huggingface.spaces_api import HFSpacesHandler
from askui.models.models import (
    MODEL_TYPES,
    ActModel,
    GetModel,
    LocateModel,
    Model,
    ModelComposition,
    ModelName,
    ModelRegistry,
    Point,
)
from askui.models.types.response_schemas import ResponseSchema
from askui.reporting import CompositeReporter, Reporter
from askui.tools.toolbox import AgentToolbox
from askui.utils.image_utils import ImageSource

from ..logger import logger
from .anthropic.computer_agent import ClaudeComputerAgent
from .anthropic.handler import ClaudeHandler
from .askui.inference_api import AskUiInferenceApi, AskUiSettings
from .ui_tars_ep.ui_tars_api import UiTarsApiHandler, UiTarsApiHandlerSettings


def _initialize_default_model_registry(  # noqa: C901
    tools: AgentToolbox,
    reporter: Reporter,
) -> ModelRegistry:
    @functools.cache
    def askui_settings() -> AskUiSettings:
        return AskUiSettings()

    @functools.cache
    def askui_inference_api() -> AskUiInferenceApi:
        return AskUiInferenceApi(
            locator_serializer=AskUiLocatorSerializer(
                ai_element_collection=AiElementCollection(),
                reporter=reporter,
            ),
            settings=askui_settings(),
        )

    @functools.cache
    def askui_model_router() -> AskUiModelRouter:
        return AskUiModelRouter(
            inference_api=askui_inference_api(),
        )

    @functools.cache
    def vlm_locator_serializer() -> VlmLocatorSerializer:
        return VlmLocatorSerializer()

    @functools.cache
    def anthropic_facade() -> AnthropicFacade:
        settings = AnthropicSettings()
        computer_agent = ClaudeComputerAgent(
            agent_os=tools.os,
            reporter=reporter,
            settings=ClaudeComputerAgentSettings(
                anthropic=settings,
            ),
        )
        handler = ClaudeHandler(
            settings=ClaudeSettings(
                anthropic=settings,
            ),
            locator_serializer=vlm_locator_serializer(),
        )
        return AnthropicFacade(
            computer_agent=computer_agent,
            handler=handler,
        )

    @functools.cache
    def askui_facade() -> AskUiFacade:
        computer_agent = AskUiComputerAgent(
            agent_os=tools.os,
            reporter=reporter,
            settings=AskUiComputerAgentSettings(
                askui=askui_settings(),
            ),
        )
        return AskUiFacade(
            computer_agent=computer_agent,
            inference_api=askui_inference_api(),
            model_router=askui_model_router(),
        )

    @functools.cache
    def hf_spaces_handler() -> HFSpacesHandler:
        return HFSpacesHandler(
            locator_serializer=vlm_locator_serializer(),
        )

    @functools.cache
    def ui_tars_api_handler() -> UiTarsApiHandler:
        return UiTarsApiHandler(
            locator_serializer=vlm_locator_serializer(),
            agent_os=tools.os,
            reporter=reporter,
            settings=UiTarsApiHandlerSettings(),
        )

    return {
        ModelName.ASKUI: askui_facade,
        ModelName.ASKUI__AI_ELEMENT: askui_model_router,
        ModelName.ASKUI__COMBO: askui_model_router,
        ModelName.ASKUI__OCR: askui_model_router,
        ModelName.ASKUI__PTA: askui_model_router,
        ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022: anthropic_facade,
        ModelName.HF__SPACES__ASKUI__PTA_1: hf_spaces_handler,
        ModelName.HF__SPACES__QWEN__QWEN2_VL_2B_INSTRUCT: hf_spaces_handler,
        ModelName.HF__SPACES__QWEN__QWEN2_VL_7B_INSTRUCT: hf_spaces_handler,
        ModelName.HF__SPACES__OS_COPILOT__OS_ATLAS_BASE_7B: hf_spaces_handler,
        ModelName.HF__SPACES__SHOWUI__2B: hf_spaces_handler,
        ModelName.TARS: ui_tars_api_handler,
    }


class ModelRouter:
    def __init__(
        self,
        tools: AgentToolbox,
        reporter: Reporter | None = None,
        models: ModelRegistry | None = None,
    ):
        self._tools = tools
        self._reporter = reporter or CompositeReporter()
        self._models = _initialize_default_model_registry(tools, self._reporter)
        self._models.update(models or {})

    @overload
    def _get_model(self, model_choice: str, model_type: Literal["act"]) -> ActModel: ...

    @overload
    def _get_model(self, model_choice: str, model_type: Literal["get"]) -> GetModel: ...

    @overload
    def _get_model(
        self, model_choice: str, model_type: Literal["locate"]
    ) -> LocateModel: ...

    def _get_model(
        self, model_choice: str, model_type: Literal["act", "get", "locate"]
    ) -> Model:
        if model_choice not in self._models:
            raise ModelNotFoundError(model_choice)

        model_or_model_factory = self._models[model_choice]
        if not isinstance(model_or_model_factory, (ActModel, GetModel, LocateModel)):
            model = model_or_model_factory()
        else:
            model = model_or_model_factory

        if not isinstance(model, MODEL_TYPES[model_type]):
            raise ModelTypeMismatchError(
                model_choice,
                MODEL_TYPES[model_type],
                type(model),
            )

        return model

    def act(self, goal: str, model_choice: str) -> None:
        m = self._get_model(model_choice, "act")
        logger.debug(f'Routing "act" to model "{model_choice}"')
        return m.act(goal, model_choice)

    def get(
        self,
        query: str,
        image: ImageSource,
        model_choice: str,
        response_schema: Type[ResponseSchema] | None = None,
    ) -> ResponseSchema | str:
        m = self._get_model(model_choice, "get")
        logger.debug(f'Routing "get" to model "{model_choice}"')
        return m.get(query, image, response_schema, model_choice)

    def locate(
        self,
        screenshot: ImageSource,
        locator: str | Locator,
        model_choice: ModelComposition | str,
    ) -> Point:
        _model_choice = (
            ModelName.ASKUI
            if isinstance(model_choice, ModelComposition)
            else model_choice
        )
        _model_composition = (
            model_choice if isinstance(model_choice, ModelComposition) else None
        )
        m = self._get_model(_model_choice, "locate")
        logger.debug(f"Routing locate prediction to {_model_choice}")
        return m.locate(locator, screenshot, _model_composition or _model_choice)
