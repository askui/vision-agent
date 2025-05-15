from abc import ABC, abstractmethod
from functools import cached_property
from typing import Type

from PIL import Image
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
from askui.models.models import ModelComposition, ModelName
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

Point = tuple[int, int]
"""
A tuple of two integers representing the coordinates of a point on the screen.
"""


def handle_response(
    response: tuple[int | None, int | None], locator: str | Locator
) -> tuple[int, int]:
    x, y = response
    if x is None or y is None:
        error_msg = f"Element not found: {locator}"
        raise ElementNotFoundError(error_msg)
    return x, y


class GroundingModelRouter(ABC):
    @abstractmethod
    def locate(
        self,
        screenshot: Image.Image,
        locator: str | Locator,
        model: ModelComposition | str | None = None,
    ) -> Point:
        pass

    @abstractmethod
    def is_responsible(self, model: ModelComposition | str | None = None) -> bool:
        pass


class AskUiModelRouter(GroundingModelRouter):
    def __init__(self, inference_api: AskUiInferenceApi):
        self._inference_api = inference_api

    def _locate_with_askui_ocr(
        self, screenshot: Image.Image, locator: str | Text
    ) -> Point:
        locator = Text(locator) if isinstance(locator, str) else locator
        x, y = self._inference_api.predict(screenshot, locator)
        return handle_response((x, y), locator)

    @override
    def locate(
        self,
        screenshot: Image.Image,
        locator: str | Locator,
        model: ModelComposition | str | None = None,
    ) -> Point:
        if not isinstance(model, str) or model == ModelName.ASKUI:
            logger.debug("Routing locate prediction to askui")
            locator = Text(locator) if isinstance(locator, str) else locator
            _model = model if not isinstance(model, str) else None
            x, y = self._inference_api.predict(screenshot, locator, _model)
            return handle_response((x, y), locator)
        if not isinstance(locator, str):
            error_msg = (
                f"Locators of type `{type(locator)}` are not supported for models "
                '"askui-pta", "askui-ocr" and "askui-combo" and "askui-ai-element". '
                "Please provide a `str`."
            )
            raise AutomationError(error_msg)
        if model == ModelName.ASKUI__PTA:
            logger.debug("Routing locate prediction to askui-pta")
            x, y = self._inference_api.predict(screenshot, Prompt(locator))
            return handle_response((x, y), locator)
        if model == ModelName.ASKUI__OCR:
            logger.debug("Routing locate prediction to askui-ocr")
            return self._locate_with_askui_ocr(screenshot, locator)
        if model == ModelName.ASKUI__COMBO or model is None:
            logger.debug("Routing locate prediction to askui-combo")
            prompt_locator = Prompt(locator)
            x, y = self._inference_api.predict(screenshot, prompt_locator)
            if x is None or y is None:
                return self._locate_with_askui_ocr(screenshot, locator)
            return handle_response((x, y), prompt_locator)
        if model == ModelName.ASKUI__AI_ELEMENT:
            logger.debug("Routing click prediction to askui-ai-element")
            _locator = AiElement(locator)
            x, y = self._inference_api.predict(screenshot, _locator)
            return handle_response((x, y), _locator)
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

    @cached_property
    def _anthropic_settings(self) -> AnthropicSettings:
        if self._anthropic_settings_base is not None:
            return self._anthropic_settings_base
        return AnthropicSettings()

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
        return AskUiSettings()

    @cached_property
    def _claude(self) -> ClaudeHandler:
        if self._claude_base is not None:
            return self._claude_base
        claude_settings = ClaudeSettings(
            anthropic=self._anthropic_settings,
        )
        return ClaudeHandler(settings=claude_settings)

    @cached_property
    def _claude_computer_agent(self) -> ClaudeComputerAgent:
        if self._claude_computer_agent_base is not None:
            return self._claude_computer_agent_base
        claude_computer_agent_settings = ClaudeComputerAgentSettings(
            anthropic=self._anthropic_settings,
        )
        return ClaudeComputerAgent(
            agent_os=self._tools.agent_os,
            reporter=self._reporter,
            settings=claude_computer_agent_settings,
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
        tars_settings = UiTarsApiHandlerSettings()
        return UiTarsApiHandler(
            agent_os=self._tools.agent_os,
            reporter=self._reporter,
            settings=tars_settings,
        )

    def act(self, goal: str, model: str | None = None) -> None:
        if model == ModelName.TARS:
            logger.debug(f"Routing act prediction to {ModelName.TARS}")
            return self._tars.act(goal)
        if model == ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022 or model is None:
            logger.debug(
                f"Routing act prediction to {ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022}"  # noqa: E501
            )
            return self._claude_computer_agent.act(goal)
        raise ModelNotFoundError(model, "Act")

    def get_inference(
        self,
        query: str,
        image: ImageSource,
        response_schema: Type[ResponseSchema] | None = None,
        model: str | None = None,
    ) -> ResponseSchema | str:
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
            return self._tars.get_inference(image=image, query=query)
        if model == ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022:
            logger.debug(
                f"Routing get inference to {ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022}"  # noqa: E501
            )
            return self._claude.get_inference(image=image, query=query)
        if model == ModelName.ASKUI or model is None:
            logger.debug(f"Routing get inference to {ModelName.ASKUI}")
            return self._askui_inference_api.get_inference(
                image=image,
                query=query,
                response_schema=response_schema,
            )
        raise ModelNotFoundError(model, "Query (get/extract)")

    def _serialize_locator(self, locator: str | Locator) -> str:
        if isinstance(locator, Locator):
            return self._locator_serializer.serialize(locator=locator)
        return locator

    @telemetry.record_call(exclude={"locator", "screenshot"})
    def locate(  # noqa: C901
        self,
        screenshot: Image.Image,
        locator: str | Locator,
        model: ModelComposition | str | None = None,
    ) -> Point:
        point: tuple[int | None, int | None] | None = None
        if model in self._huggingface_spaces.get_spaces_names():
            logger.debug(f"Routing locate prediction to {model}")
            point = self._huggingface_spaces.predict(
                screenshot=screenshot,
                locator=self._serialize_locator(locator),
                model_name=model,  # type: ignore
            )
            return handle_response(point, locator)
        if model == ModelName.TARS:
            logger.debug(f"Routing locate prediction to {ModelName.TARS}")
            point = self._tars.locate_prediction(
                screenshot, self._serialize_locator(locator)
            )
            return handle_response(point, locator)
        if model == ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022:
            logger.debug(
                f"Routing locate prediction to {ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022}"  # noqa: E501
            )
            point = self._claude.locate_inference(
                screenshot, self._serialize_locator(locator)
            )
            return handle_response(point, locator)
        point = self._try_locating_using_grounding_model(screenshot, locator, model)
        if point:
            return handle_response(point, locator)
        if not point and model is None:
            logger.debug(
                f"Routing locate prediction to {ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022}"  # noqa: E501
            )
            point = self._claude.locate_inference(
                screenshot, self._serialize_locator(locator)
            )
            return handle_response(point, locator)
        raise ModelNotFoundError(model, "Grounding (locate)")

    def _try_locating_using_grounding_model(
        self,
        screenshot: Image.Image,
        locator: str | Locator,
        model: ModelComposition | str | None = None,
    ) -> Point | None:
        try:
            for grounding_model_router in self._grounding_model_routers:
                if grounding_model_router.is_responsible(model):
                    return grounding_model_router.locate(screenshot, locator, model)
        except (ModelNotFoundError, ValueError):
            if model is not None:
                raise
        return None
