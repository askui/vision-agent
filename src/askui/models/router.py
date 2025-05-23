from abc import ABC, abstractmethod
from functools import cached_property
from typing import Type

from typing_extensions import override

from askui.container import telemetry
from askui.exceptions import ModelNotFoundError
from askui.locators.locators import AiElement, Locator, Prompt, Text
from askui.locators.serializers import AskUiLocatorSerializer, VlmLocatorSerializer
from askui.models.anthropic.settings import (
    AnthropicSettings,
    ClaudeComputerAgentSettings,
    ClaudeSettings,
)
from askui.models.askui.ai_element_utils import AiElementCollection
from askui.models.askui.askui_computer_agent import AskUiComputerAgent
from askui.models.askui.settings import AskUiComputerAgentSettings
from askui.models.models import (
    ActModel,
    GetModel,
    LocateModel,
    Model,
    ModelComposition,
    ModelName,
    Point,
)
from askui.models.types.response_schemas import ResponseSchema
from askui.reporting import CompositeReporter, Reporter
from askui.tools.toolbox import AgentToolbox
from askui.utils.image_utils import ImageSource

from ..exceptions import AutomationError, ElementNotFoundError
from ..logger import logger
from .anthropic.claude import ClaudeHandler
from .anthropic.claude_agent import ClaudeComputerAgent
from .askui.api import AskUiInferenceApi, AskUiSettings
from .huggingface.spaces_api import HFSpacesHandler
from .ui_tars_ep.ui_tars_api import UiTarsApiHandler, UiTarsApiHandlerSettings


class GroundingModelRouter(LocateModel, ABC):
    @abstractmethod
    def is_responsible(self, model: ModelComposition | str | None = None) -> bool:
        pass


class AskUiModelRouter(GroundingModelRouter):
    def __init__(self, inference_api: AskUiInferenceApi):
        self._inference_api = inference_api

    def _locate_with_askui_ocr(
        self, screenshot: ImageSource, locator: str | Text
    ) -> Point:
        locator = Text(locator) if isinstance(locator, str) else locator
        return self._inference_api.locate(
            locator, screenshot, model=ModelName.ASKUI__OCR
        )

    @override
    def locate(
        self,
        locator: str | Locator,
        image: ImageSource,
        model: ModelComposition | str,
    ) -> Point:
        if isinstance(model, ModelComposition) or model == ModelName.ASKUI:
            logger.debug("Routing locate prediction to askui")
            locator = Text(locator) if isinstance(locator, str) else locator
            _model = model if not isinstance(model, str) else None
            return self._inference_api.locate(locator, image, _model or ModelName.ASKUI)
        if not isinstance(locator, str):
            error_msg = (
                f"Locators of type `{type(locator)}` are not supported for models "
                '"askui-pta", "askui-ocr" and "askui-combo" and "askui-ai-element". '
                "Please provide a `str`."
            )
            raise AutomationError(error_msg)
        if model == ModelName.ASKUI__PTA:
            logger.debug("Routing locate prediction to askui-pta")
            return self._inference_api.locate(Prompt(locator), image, model)
        if model == ModelName.ASKUI__OCR:
            logger.debug("Routing locate prediction to askui-ocr")
            return self._locate_with_askui_ocr(image, locator)
        if model == ModelName.ASKUI__COMBO:
            logger.debug("Routing locate prediction to askui-combo")
            prompt_locator = Prompt(locator)
            try:
                return self._inference_api.locate(prompt_locator, image, model)
            except ElementNotFoundError:
                return self._locate_with_askui_ocr(image, locator)
        if model == ModelName.ASKUI__AI_ELEMENT:
            logger.debug("Routing click prediction to askui-ai-element")
            _locator = AiElement(locator)
            return self._inference_api.locate(_locator, image, model)
        raise ModelNotFoundError(model, "Grounding (locate)")

    @override
    def is_responsible(self, model: ModelComposition | str | None = None) -> bool:
        return not isinstance(model, str) or model in [
            ModelName.ASKUI,
            ModelName.ASKUI__AI_ELEMENT,
            ModelName.ASKUI__OCR,
            ModelName.ASKUI__COMBO,
            ModelName.ASKUI__PTA,
        ]


class ModelRouter:
    def __init__(
        self,
        tools: AgentToolbox,
        grounding_model_routers: list[GroundingModelRouter] | None = None,
        reporter: Reporter | None = None,
        anthropic_settings: AnthropicSettings | None = None,
        askui_inference_api: AskUiInferenceApi | None = None,
        askui_settings: AskUiSettings | None = None,
        claude: ClaudeHandler | None = None,
        claude_computer_agent: ClaudeComputerAgent | None = None,
        huggingface_spaces: HFSpacesHandler | None = None,
        tars: UiTarsApiHandler | None = None,
        askui_computer_agent: AskUiComputerAgent | None = None,
        models: dict[str, Model] | None = None,
    ):
        self._tools = tools
        self._reporter = reporter or CompositeReporter()
        self._grounding_model_routers_base = grounding_model_routers
        self._anthropic_settings_base = anthropic_settings
        self._askui_inference_api_base = askui_inference_api
        self._askui_settings_base = askui_settings
        self._claude_base = claude
        self._claude_computer_agent_base = claude_computer_agent
        self._huggingface_spaces = huggingface_spaces or HFSpacesHandler()
        self._tars_base = tars
        self._locator_serializer = VlmLocatorSerializer()
        self._askui_computer_agent_base = askui_computer_agent
        _models = models or {}
        self._act_models = {k: v for k, v in _models.items() if isinstance(v, ActModel)}
        self._locate_models = {
            k: v for k, v in _models.items() if isinstance(v, LocateModel)
        }
        self._get_models = {k: v for k, v in _models.items() if isinstance(v, GetModel)}

    @cached_property
    def _anthropic_settings(self) -> AnthropicSettings:
        if self._anthropic_settings_base is not None:
            return self._anthropic_settings_base
        return AnthropicSettings()  # type: ignore

    @cached_property
    def _askui_inference_api(self) -> AskUiInferenceApi:
        if self._askui_inference_api_base is not None:
            return self._askui_inference_api_base
        return AskUiInferenceApi(
            locator_serializer=AskUiLocatorSerializer(
                ai_element_collection=AiElementCollection(),
                reporter=self._reporter,
            ),
            settings=self._askui_settings,
        )

    @cached_property
    def _askui_settings(self) -> AskUiSettings:
        if self._askui_settings_base is not None:
            return self._askui_settings_base
        return AskUiSettings()  # type: ignore

    @cached_property
    def _claude(self) -> ClaudeHandler:
        if self._claude_base is not None:
            return self._claude_base
        claude_settings = ClaudeSettings(
            anthropic=self._anthropic_settings,
        )
        return ClaudeHandler(
            settings=claude_settings,
            locator_serializer=self._locator_serializer,
        )

    @cached_property
    def _claude_computer_agent(self) -> ClaudeComputerAgent:
        if self._claude_computer_agent_base is not None:
            return self._claude_computer_agent_base
        claude_computer_agent_settings = ClaudeComputerAgentSettings(
            anthropic=self._anthropic_settings,
        )
        return ClaudeComputerAgent(
            agent_os=self._tools.os,
            reporter=self._reporter,
            settings=claude_computer_agent_settings,
        )

    @cached_property
    def _askui_computer_agent(self) -> AskUiComputerAgent:
        if self._askui_computer_agent_base is not None:
            return self._askui_computer_agent_base
        askui_computer_agent_settings = AskUiComputerAgentSettings(
            askui=self._askui_settings,
        )
        return AskUiComputerAgent(
            agent_os=self._tools.os,
            reporter=self._reporter,
            settings=askui_computer_agent_settings,
        )

    @cached_property
    def _grounding_model_routers(self) -> list[GroundingModelRouter]:
        return self._grounding_model_routers_base or [
            AskUiModelRouter(inference_api=self._askui_inference_api)
        ]

    @cached_property
    def _tars(self) -> UiTarsApiHandler:
        if self._tars_base is not None:
            return self._tars_base
        tars_settings = UiTarsApiHandlerSettings()  # type: ignore
        return UiTarsApiHandler(
            locator_serializer=self._locator_serializer,
            agent_os=self._tools.os,
            reporter=self._reporter,
            settings=tars_settings,
        )

    def act(self, goal: str, model: str | None = None) -> None:
        if model in self._act_models:
            logger.debug(f"Routing act prediction to {model}")
            return self._act_models[model].act(goal, model)
        if model == ModelName.TARS:
            logger.debug(f"Routing act prediction to {ModelName.TARS}")
            return self._tars.act(goal, model)
        if model == ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022:
            logger.debug(
                f"Routing act prediction to {ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022}"  # noqa: E501
            )
            return self._claude_computer_agent.act(goal, model)
        if model == ModelName.ASKUI or model is None:
            logger.debug(f"Routing act prediction to {ModelName.ASKUI} (default)")
            return self._askui_computer_agent.act(goal, model)
        raise ModelNotFoundError(model, "Act")

    def get_inference(
        self,
        query: str,
        image: ImageSource,
        response_schema: Type[ResponseSchema] | None = None,
        model: str | None = None,
    ) -> ResponseSchema | str:
        if model in self._get_models:
            logger.debug(f"Routing get inference to {model}")
            return self._get_models[model].get(query, image, response_schema, model)
        if model in [
            ModelName.TARS,
            ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022,
        ] and response_schema not in [str, None]:
            error_msg = (
                "(Non-String) Response schema is not yet supported for "
                f'"{model}" model.'
            )
            raise NotImplementedError(error_msg)
        if model == ModelName.TARS:
            logger.debug(f"Routing get inference to {ModelName.TARS}")
            return self._tars.get(query, image, response_schema, model)
        if model == ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022:
            logger.debug(
                f"Routing get inference to {ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022}"  # noqa: E501
            )
            return self._claude.get(query, image, response_schema, model)
        if model == ModelName.ASKUI or model is None:
            logger.debug(f"Routing get inference to {ModelName.ASKUI}")
            return self._askui_inference_api.get(
                query=query,
                image=image,
                response_schema=response_schema,
                model=ModelName.ASKUI,
            )
        raise ModelNotFoundError(model, "Query (get/extract)")

    def _serialize_locator(self, locator: str | Locator) -> str:
        if isinstance(locator, Locator):
            return self._locator_serializer.serialize(locator=locator)
        return locator

    @telemetry.record_call(exclude={"locator", "screenshot"})
    def locate(  # noqa: C901
        self,
        screenshot: ImageSource,
        locator: str | Locator,
        model: ModelComposition | str | None = None,
    ) -> Point:
        point: tuple[int | None, int | None] | None = None
        if model in self._locate_models:
            logger.debug(f"Routing locate prediction to {model}")
            return self._locate_models[model].locate(locator, screenshot, model)
        if model in self._huggingface_spaces.get_spaces_names():
            logger.debug(f"Routing locate prediction to {model}")
            return self._huggingface_spaces.locate(
                locator=locator,
                image=screenshot,
                model=model,
            )
        if model == ModelName.TARS:
            logger.debug(f"Routing locate prediction to {ModelName.TARS}")
            return self._tars.locate(locator, screenshot, model)
        if model == ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022:
            logger.debug(
                f"Routing locate prediction to {ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022}"  # noqa: E501
            )
            return self._claude.locate(locator, screenshot, model)
        point = self._try_locating_using_grounding_model(screenshot, locator, model)
        if point:
            return point
        if model is None:
            logger.debug(
                f"Routing locate prediction to {ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022}"  # noqa: E501
            )
            return self._claude.locate(
                locator, screenshot, ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022
            )
        raise ModelNotFoundError(model, "Grounding (locate)")

    def _try_locating_using_grounding_model(
        self,
        image: ImageSource,
        locator: str | Locator,
        model: ModelComposition | str | None = None,
    ) -> Point | None:
        try:
            for grounding_model_router in self._grounding_model_routers:
                if grounding_model_router.is_responsible(model):
                    return grounding_model_router.locate(
                        locator=locator, image=image, model=(model or ModelName.ASKUI)
                    )
        except (ModelNotFoundError, ValueError):
            if model is not None:
                raise
        return None
