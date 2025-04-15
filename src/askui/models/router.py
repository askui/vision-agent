import logging
from typing import Type
from typing_extensions import override
from PIL import Image

from askui.container import telemetry
from askui.locators.locators import AiElement, Description, Text
from askui.locators.serializers import AskUiLocatorSerializer, VlmLocatorSerializer
from askui.locators.locators import Locator
from askui.models.askui.ai_element_utils import AiElementCollection
from askui.models.types import JsonSchema
from askui.reporting import Reporter
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


def handle_response(response: tuple[int | None, int | None], locator: str | Locator):
    if response[0] is None or response[1] is None:
        raise ElementNotFoundError(f"Could not locate\n{locator}")
    return response


class GroundingModelRouter(ABC):
    @abstractmethod
    def locate(
        self,
        screenshot: Image.Image,
        locator: str | Locator,
        model: str | None = None,
    ) -> Point:
        pass

    @abstractmethod
    def is_responsible(self, model: str | None = None) -> bool:
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
        model: str | None = None,
    ) -> Point:
        if not self._inference_api.authenticated:
            raise AutomationError(
                "NoAskUIAuthenticationSet! Please set 'AskUI ASKUI_WORKSPACE_ID' or 'ASKUI_TOKEN' as env variables!"
            )
        if model == "askui" or model is None:
            logger.debug("Routing locate prediction to askui")
            locator = Text(locator) if isinstance(locator, str) else locator
            x, y = self._inference_api.predict(screenshot, locator)
            return handle_response((x, y), locator)
        if not isinstance(locator, str):
            raise AutomationError(
                f'Locators of type `{type(locator)}` are not supported for models "askui-pta", "askui-ocr" and "askui-combo" and "askui-ai-element". Please provide a `str`.'
            )
        if model == "askui-pta":
            logger.debug("Routing locate prediction to askui-pta")
            x, y = self._inference_api.predict(screenshot, Description(locator))
            return handle_response((x, y), locator)
        if model == "askui-ocr":
            logger.debug("Routing locate prediction to askui-ocr")
            return self._locate_with_askui_ocr(screenshot, locator)
        if model == "askui-combo" or model is None:
            logger.debug("Routing locate prediction to askui-combo")
            description_locator = Description(locator)
            x, y = self._inference_api.predict(screenshot, description_locator)
            if x is None or y is None:
                return self._locate_with_askui_ocr(screenshot, locator)
            return handle_response((x, y), description_locator)
        if model == "askui-ai-element":
            logger.debug("Routing click prediction to askui-ai-element")
            _locator = AiElement(locator)
            x, y = self._inference_api.predict(screenshot, _locator)
            return handle_response((x, y), _locator)
        raise AutomationError(f'Invalid model: "{model}"')

    @override
    def is_responsible(self, model: str | None = None) -> bool:
        return model is None or model.startswith("askui")

    @override
    def is_authenticated(self) -> bool:
        return self._inference_api.authenticated


class ModelRouter:
    def __init__(
        self,
        reporter: Reporter,
        log_level: int = logging.INFO,
        grounding_model_routers: list[GroundingModelRouter] | None = None,
    ):
        self._reporter = reporter
        self.askui = AskUiInferenceApi(
            locator_serializer=AskUiLocatorSerializer(
                ai_element_collection=AiElementCollection(),
            ),
        )
        self.grounding_model_routers = grounding_model_routers or [AskUiModelRouter(inference_api=self.askui)]
        self.claude = ClaudeHandler(log_level)
        self.huggingface_spaces = HFSpacesHandler()
        self.tars = UITarsAPIHandler(self._reporter)
        self._locator_serializer = VlmLocatorSerializer()

    def act(self, controller_client, goal: str, model: str | None = None):
        if self.tars.authenticated and model == "tars":
            return self.tars.act(controller_client, goal)
        if self.claude.authenticated and (model == "claude" or model is None):
            agent = ClaudeComputerAgent(controller_client, self._reporter)
            return agent.run(goal)
        raise AutomationError(f"Invalid model for act: {model}")

    def get_inference(
        self,
        query: str,
        image: ImageSource,
        response_schema: Type[JsonSchema] | None = None,
        model: str | None = None,
    ) -> JsonSchema | str:
        if self.tars.authenticated and model == "tars":
            if response_schema is not None:
                raise NotImplementedError("Response schema is not yet supported for UI-TARS models.")
            return self.tars.get_inference(image=image, query=query)
        if self.claude.authenticated and (
            model == "anthropic-claude-3-5-sonnet-20241022"
        ):
            if response_schema is not None:
                raise NotImplementedError("Response schema is not yet supported for Anthropic models.")
            return self.claude.get_inference(image=image, query=query)
        if self.askui.authenticated and (model == "askui" or model is None):
            return self.askui.get_inference(
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
        model: str | None = None,
    ) -> Point:
        if (
            model is not None
            and model in self.huggingface_spaces.get_spaces_names()
        ):
            x, y = self.huggingface_spaces.predict(
                screenshot=screenshot,
                locator=self._serialize_locator(locator),
                model_name=model,
            )
            return handle_response((x, y), locator)
        if model is not None:
            if model.startswith("anthropic") and not self.claude.authenticated:
                raise AutomationError(
                    "You need to provide Anthropic credentials to use Anthropic models."
                )
            if model.startswith("tars") and not self.tars.authenticated:
                raise AutomationError(
                    "You need to provide UI-TARS HF Endpoint credentials to use UI-TARS models."
                )
        if self.tars.authenticated and model == "tars":
            x, y = self.tars.locate_prediction(
                screenshot, self._serialize_locator(locator)
            )
            return handle_response((x, y), locator)
        if (
            self.claude.authenticated
            and model == "anthropic-claude-3-5-sonnet-20241022"
        ):
            logger.debug("Routing locate prediction to Anthropic")
            x, y = self.claude.locate_inference(
                screenshot, self._serialize_locator(locator)
            )
            return handle_response((x, y), locator)

        for grounding_model_router in self.grounding_model_routers:
            if (
                grounding_model_router.is_responsible(model)
                and grounding_model_router.is_authenticated()
            ):
                return grounding_model_router.locate(screenshot, locator, model)

        if model is None:
            if self.claude.authenticated:
                logger.debug("Routing locate prediction to Anthropic")
                x, y = self.claude.locate_inference(
                    screenshot, self._serialize_locator(locator)
                )
                return handle_response((x, y), locator)

        raise AutomationError(
            "Executing locate commands requires to authenticate with an Automation Model Provider."
        )
