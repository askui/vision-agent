from typing import Type
from typing_extensions import override
from PIL import Image

from askui.container import telemetry
from askui.locators.locators import AiElement, Prompt, Text
from askui.locators.serializers import AskUiLocatorSerializer, VlmLocatorSerializer
from askui.locators.locators import Locator
from askui.models.askui.ai_element_utils import AiElementCollection
from askui.models.models import ModelComposition, ModelName
from askui.models.types.response_schemas import ResponseSchema
from askui.reporting import CompositeReporter, Reporter
from askui.tools.toolbox import AgentToolbox
from askui.utils.image_utils import ImageSource
from .askui.api import AskUiInferenceApi
from .anthropic.claude import ClaudeHandler
from .huggingface.spaces_api import HFSpacesHandler
from ..exceptions import AutomationError, ElementNotFoundError
from ..logger import logger
from .ui_tars_ep.ui_tars_api import UITarsAPIHandler
from .anthropic.claude_agent import ClaudeComputerAgent
from abc import ABC, abstractmethod


Point = tuple[int, int]
"""
A tuple of two integers representing the coordinates of a point on the screen.
"""


def handle_response(response: tuple[int | None, int | None], locator: str | Locator):
    if response[0] is None or response[1] is None:
        raise ElementNotFoundError(f"Element not found: {locator}")
    return response


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

    @abstractmethod
    def is_authenticated(self) -> bool:
        pass


class AskUiModelRouter(GroundingModelRouter):
    def __init__(self, inference_api: AskUiInferenceApi):
        self._inference_api = inference_api
        
    def _locate_with_askui_ocr(self, screenshot: Image.Image, locator: str | Text) -> Point:
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
        if not self._inference_api.authenticated:
            raise AutomationError(
                "NoAskUIAuthenticationSet! Please set 'AskUI ASKUI_WORKSPACE_ID' or 'ASKUI_TOKEN' as env variables!"
            )
        if not isinstance(model, str) or model == ModelName.ASKUI:
            logger.debug("Routing locate prediction to askui")
            locator = Text(locator) if isinstance(locator, str) else locator
            _model = model if not isinstance(model, str) else None
            x, y = self._inference_api.predict(screenshot, locator, _model)
            return handle_response((x, y), locator)
        if not isinstance(locator, str):
            raise AutomationError(
                f'Locators of type `{type(locator)}` are not supported for models "askui-pta", "askui-ocr" and "askui-combo" and "askui-ai-element". Please provide a `str`.'
            )
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
        raise AutomationError(f'Invalid model: "{model}"')

    @override
    def is_responsible(self, model: ModelComposition | str | None = None) -> bool:
        return not isinstance(model, str) or model.startswith(ModelName.ASKUI)

    @override
    def is_authenticated(self) -> bool:
        return self._inference_api.authenticated


class ModelRouter:
    def __init__(
        self,
        tools: AgentToolbox,
        grounding_model_routers: list[GroundingModelRouter] | None = None,
        reporter: Reporter | None = None,
    ):
        _reporter = reporter or CompositeReporter()
        self._askui = AskUiInferenceApi(
            locator_serializer=AskUiLocatorSerializer(
                ai_element_collection=AiElementCollection(),
                reporter=_reporter,
            ),
        )
        self._grounding_model_routers = grounding_model_routers or [AskUiModelRouter(inference_api=self._askui)]
        self._claude = ClaudeHandler()
        self._huggingface_spaces = HFSpacesHandler()
        self._tars = UITarsAPIHandler(agent_os=tools.agent_os, reporter=_reporter)
        self._claude_computer_agent = ClaudeComputerAgent(agent_os=tools.agent_os, reporter=_reporter)
        self._locator_serializer = VlmLocatorSerializer()

    def act(self, goal: str, model: ModelComposition | str | None = None):
        if self._tars.authenticated and model == ModelName.TARS:
            return self._tars.act(goal)
        if self._claude.authenticated and (model is None or isinstance(model, str) and model.startswith(ModelName.ANTHROPIC)):
            return self._claude_computer_agent.run(goal)
        raise AutomationError(f"Invalid model for act: {model}")

    def get_inference(
        self,
        query: str,
        image: ImageSource,
        response_schema: Type[ResponseSchema] | None = None,
        model: ModelComposition | str | None = None,
    ) -> ResponseSchema | str:
        if self._tars.authenticated and model == ModelName.TARS:
            if response_schema not in [str, None]:
                raise NotImplementedError("(Non-String) Response schema is not yet supported for UI-TARS models.")
            return self._tars.get_inference(image=image, query=query)
        if self._claude.authenticated and (
            isinstance(model, str) and model.startswith(ModelName.ANTHROPIC)
        ):
            if response_schema not in [str, None]:
                raise NotImplementedError("(Non-String) Response schema is not yet supported for Anthropic models.")
            return self._claude.get_inference(image=image, query=query)
        if self._askui.authenticated and (model == ModelName.ASKUI or model is None):
            return self._askui.get_inference(
                image=image,
                query=query,
                response_schema=response_schema,
            )
        raise AutomationError(
            f"Executing get commands requires to authenticate with an Automation Model Provider supporting it: {model}"
        )

    def _serialize_locator(self, locator: str | Locator) -> str:
        if isinstance(locator, Locator):
            return self._locator_serializer.serialize(locator=locator)
        return locator

    @telemetry.record_call(exclude={"locator", "screenshot"})
    def locate(
        self,
        screenshot: Image.Image,
        locator: str | Locator,
        model: ModelComposition | str | None = None,
    ) -> Point:
        if (
            isinstance(model, str)
            and model in self._huggingface_spaces.get_spaces_names()
        ):
            x, y = self._huggingface_spaces.predict(
                screenshot=screenshot,
                locator=self._serialize_locator(locator),
                model_name=model,
            )
            return handle_response((x, y), locator)
        if isinstance(model, str):
            if model.startswith(ModelName.ANTHROPIC) and not self._claude.authenticated:
                raise AutomationError(
                    "You need to provide Anthropic credentials to use Anthropic models."
                )
            if model.startswith(ModelName.TARS) and not self._tars.authenticated:
                raise AutomationError(
                    "You need to provide UI-TARS HF Endpoint credentials to use UI-TARS models."
                )
        if self._tars.authenticated and model == ModelName.TARS:
            x, y = self._tars.locate_prediction(
                screenshot, self._serialize_locator(locator)
            )
            return handle_response((x, y), locator)
        if (
            self._claude.authenticated
            and isinstance(model, str) and model.startswith(ModelName.ANTHROPIC)
        ):
            logger.debug("Routing locate prediction to Anthropic")
            x, y = self._claude.locate_inference(
                screenshot, self._serialize_locator(locator)
            )
            return handle_response((x, y), locator)

        for grounding_model_router in self._grounding_model_routers:
            if (
                grounding_model_router.is_responsible(model)
                and grounding_model_router.is_authenticated()
            ):
                return grounding_model_router.locate(screenshot, locator, model)

        if model is None:
            if self._claude.authenticated:
                logger.debug("Routing locate prediction to Anthropic")
                x, y = self._claude.locate_inference(
                    screenshot, self._serialize_locator(locator)
                )
                return handle_response((x, y), locator)

        raise AutomationError(
            "Executing locate commands requires to authenticate with an Automation Model Provider."
        )
