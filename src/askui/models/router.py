import logging
from typing import Optional
from PIL import Image

from askui.container import telemetry
from askui.locators.locators import AiElement, Description, Text
from askui.locators.serializers import AskUiLocatorSerializer, VlmLocatorSerializer
from askui.locators.locators import Locator
from askui.models.askui.ai_element_utils import AiElementCollection
from askui.reporting.report import SimpleReportGenerator
from .askui.api import AskUiInferenceApi
from .anthropic.claude import ClaudeHandler
from .huggingface.spaces_api import HFSpacesHandler
from ..logger import logger
from ..utils import AutomationError, LocatingError
from .ui_tars_ep.ui_tars_api import UITarsAPIHandler
from .anthropic.claude_agent import ClaudeComputerAgent
from abc import ABC, abstractmethod


Point = tuple[int, int]


def handle_response(response: tuple[int | None, int | None], locator: str | Locator):
    if response[0] is None or response[1] is None:
        raise LocatingError(f"Could not locate\n{locator}")
    return response


class GroundingModelRouter(ABC):

    @abstractmethod
    def locate(
        self,
        screenshot: Image.Image,
        locator: str | Locator,
        model_name: str | None = None,
    ) -> Point:
        pass

    @abstractmethod
    def is_responsible(self, model_name: Optional[str]) -> bool:
        pass

    @abstractmethod
    def is_authenticated(self) -> bool:
        pass


class AskUiModelRouter(GroundingModelRouter):
    def __init__(self, inference_api: AskUiInferenceApi):
        self._inference_api = inference_api

    def locate(
        self,
        screenshot: Image.Image,
        locator: str | Locator,
        model_name: str | None = None,
    ) -> Point:
        if not self._inference_api.authenticated:
            raise AutomationError(
                "NoAskUIAuthenticationSet! Please set 'AskUI ASKUI_WORKSPACE_ID' or 'ASKUI_TOKEN' as env variables!"
            )
        if model_name == "askui":
            logger.debug("Routing locate prediction to askui")
            locator = Text(locator) if isinstance(locator, str) else locator
            x, y = self._inference_api.predict(screenshot, locator)
            return handle_response((x, y), locator)
        if model_name == "askui-pta":
            logger.debug("Routing locate prediction to askui-pta")
            locator = Description(locator) if isinstance(locator, str) else locator
            if not isinstance(locator, Description):
                raise AutomationError(
                    f'Invalid locator type `{type(locator)}` for model "askui-pta". Please provide a `Description` or a `str`.'
                )
            x, y = self._inference_api.predict(screenshot, locator)
            return handle_response((x, y), locator)
        if model_name == "askui-ocr":
            logger.debug("Routing locate prediction to askui-ocr")
            locator = Text(locator) if isinstance(locator, str) else locator
            if not isinstance(locator, Text):
                raise AutomationError(
                    f'Invalid locator type `{type(locator)}` for model "askui-ocr". Please provide a `Text` or a `str`.'
                )
            x, y = self._inference_api.predict(screenshot, locator)
            return handle_response((x, y), locator)
        if model_name == "askui-combo" or model_name is None:
            logger.debug("Routing locate prediction to askui-combo")
            if not isinstance(locator, str):
                raise AutomationError(
                    f'Invalid locator type `{type(locator)}` for model "askui-combo". Please provide a `str`.'
                )
            x, y = self._inference_api.predict(screenshot, Description(locator))
            if x is None or y is None:
                x, y = self._inference_api.predict(screenshot, Text(locator))
            return handle_response((x, y), locator)
        if model_name == "askui-ai-element":
            logger.debug("Routing click prediction to askui-ai-element")
            locator = AiElement(locator) if isinstance(locator, str) else locator
            if not isinstance(locator, AiElement):
                raise AutomationError(
                    f'Invalid locator type `{type(locator)}` for model "askui-ai-element". Please provide an `AiElement` or a `str`.'
                )
            x, y = self._inference_api.predict(screenshot, locator)
            return handle_response((x, y), locator)
        raise AutomationError(f'Invalid model name: "{model_name}"')

    def is_responsible(self, model_name: Optional[str]):
        return model_name is None or model_name.startswith("askui")

    def is_authenticated(self) -> bool:
        return self._inference_api.authenticated


class ModelRouter:
    def __init__(
        self,
        log_level: int = logging.INFO,
        report: SimpleReportGenerator | None = None,
        grounding_model_routers: list[GroundingModelRouter] | None = None,
    ):
        self.report = report
        self.grounding_model_routers = grounding_model_routers or [
            AskUiModelRouter(
                inference_api=AskUiInferenceApi(
                    locator_serializer=AskUiLocatorSerializer(
                        ai_element_collection=AiElementCollection(),
                    )
                )
            )
        ]
        self.claude = ClaudeHandler(log_level)
        self.huggingface_spaces = HFSpacesHandler()
        self.tars = UITarsAPIHandler(self.report)
        self._locator_serializer = VlmLocatorSerializer()

    def act(self, controller_client, goal: str, model_name: str | None = None):
        if self.tars.authenticated and model_name == "tars":
            return self.tars.act(controller_client, goal)
        if self.claude.authenticated and (model_name == "claude" or model_name is None):
            agent = ClaudeComputerAgent(controller_client, self.report)
            return agent.run(goal)
        raise AutomationError("Invalid model name for act")

    def get_inference(
        self, screenshot: Image.Image, locator: str, model_name: str | None = None
    ):
        if self.tars.authenticated and model_name == "tars":
            return self.tars.get_prediction(screenshot, locator)
        if self.claude.authenticated and (
            model_name == "anthropic-claude-3-5-sonnet-20241022" or model_name is None
        ):
            return self.claude.get_inference(screenshot, locator)
        raise AutomationError(
            "Executing get commands requires to authenticate with an Automation Model Provider supporting it."
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
        model_name: str | None = None,
    ) -> Point:
        if (
            model_name is not None
            and model_name in self.huggingface_spaces.get_spaces_names()
        ):
            x, y = self.huggingface_spaces.predict(
                screenshot, self._serialize_locator(locator), model_name
            )
            return handle_response((x, y), locator)
        if model_name is not None:
            if model_name.startswith("anthropic") and not self.claude.authenticated:
                raise AutomationError(
                    "You need to provide Anthropic credentials to use Anthropic models."
                )
            if model_name.startswith("tars") and not self.tars.authenticated:
                raise AutomationError(
                    "You need to provide UI-TARS HF Endpoint credentials to use UI-TARS models."
                )
        if self.tars.authenticated and model_name == "tars":
            x, y = self.tars.locate_prediction(
                screenshot, self._serialize_locator(locator)
            )
            return handle_response((x, y), locator)
        if (
            self.claude.authenticated
            and model_name == "anthropic-claude-3-5-sonnet-20241022"
        ):
            logger.debug("Routing locate prediction to Anthropic")
            x, y = self.claude.locate_inference(
                screenshot, self._serialize_locator(locator)
            )
            return handle_response((x, y), locator)

        for grounding_model_router in self.grounding_model_routers:
            if (
                grounding_model_router.is_responsible(model_name)
                and grounding_model_router.is_authenticated()
            ):
                return grounding_model_router.locate(screenshot, locator, model_name)

        if model_name is None:
            if self.claude.authenticated:
                logger.debug("Routing locate prediction to Anthropic")
                x, y = self.claude.locate_inference(
                    screenshot, self._serialize_locator(locator)
                )
                return handle_response((x, y), locator)

        raise AutomationError(
            "Executing locate commands requires to authenticate with an Automation Model Provider."
        )
