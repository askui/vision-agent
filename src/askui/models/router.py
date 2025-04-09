from typing import Optional
from PIL import Image

from askui.container import telemetry
from askui.locators.serializers import VlmLocatorSerializer
from askui.locators import Locator
from .askui.api import AskUIHandler
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
        raise LocatingError(f'Could not locate\n{locator}')
    return response


class GroundingModelRouter(ABC):

    @abstractmethod
    def locate(self, screenshot: Image.Image, locator: str | Locator, model_name: str | None = None) -> Point:
        pass

    @abstractmethod
    def is_responsible(self, model_name: Optional[str]) -> bool:
        pass
    
    @abstractmethod
    def is_authenticated(self) -> bool:
        pass


class AskUIModelRouter(GroundingModelRouter):
    
    def __init__(self):
        self.askui = AskUIHandler()

    def locate(self, screenshot: Image.Image, locator: str | Locator, model_name: str | None = None) -> Point:
        if not self.askui.authenticated:
            raise AutomationError(f"NoAskUIAuthenticationSet! Please set 'AskUI ASKUI_WORKSPACE_ID' or 'ASKUI_TOKEN' as env variables!")
        if model_name == "askui":
            logger.debug(f"Routing locate prediction to askui")
            if isinstance(locator, str):
                x, y = self.askui.locate_ocr_prediction(screenshot, locator)
            else:
                x, y = self.askui.predict(screenshot, locator)
            return handle_response((x, y), locator)
        if  model_name == "askui-pta":
            logger.debug(f"Routing locate prediction to askui-pta")
            x, y = self.askui.locate_pta_prediction(screenshot, locator)
            return handle_response((x, y), locator)
        if model_name == "askui-ocr":
            logger.debug(f"Routing locate prediction to askui-ocr")
            x, y = self.askui.locate_ocr_prediction(screenshot, locator)
            return handle_response((x, y), locator)
        if model_name == "askui-combo" or model_name is None:
            logger.debug(f"Routing locate prediction to askui-combo")
            x, y = self.askui.locate_pta_prediction(screenshot, locator)
            if x is None or y is None:
                x, y = self.askui.locate_ocr_prediction(screenshot, locator)
            return handle_response((x, y), locator)
        if model_name == "askui-ai-element":
            logger.debug(f"Routing click prediction to askui-ai-element")
            x, y = self.askui.locate_ai_element_prediction(screenshot, locator)
            return handle_response((x, y), locator)
        raise AutomationError(f"Invalid model name {model_name} for click")
        
    def is_responsible(self, model_name: Optional[str]):
        return model_name is None or model_name.startswith("askui")
    
    def is_authenticated(self) -> bool:
        return self.askui.authenticated

    

class ModelRouter:
    def __init__(self, log_level, report, 
                 grounding_model_routers: list[GroundingModelRouter] | None = None):
        self.report = report

        self.grounding_model_routers = grounding_model_routers or [AskUIModelRouter()]

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
    
    def get_inference(self, screenshot: Image.Image, locator: str, model_name: str | None = None):
        if self.tars.authenticated and model_name == "tars":
            return self.tars.get_prediction(screenshot, locator)
        if self.claude.authenticated and (model_name == "anthropic-claude-3-5-sonnet-20241022"  or model_name is None):
            return self.claude.get_inference(screenshot, locator)
        raise AutomationError("Executing get commands requires to authenticate with an Automation Model Provider supporting it.")

    def _serialize_locator(self, locator: str | Locator) -> str:
        if isinstance(locator, Locator):
            return self._locator_serializer.serialize(locator=locator)
        return locator

    @telemetry.record_call(exclude={"locator", "screenshot"})
    def locate(self, screenshot: Image.Image, locator: str | Locator, model_name: str | None = None) -> Point:
        if model_name is not None and model_name in self.huggingface_spaces.get_spaces_names():
            x, y = self.huggingface_spaces.predict(screenshot, self._serialize_locator(locator), model_name)
            return handle_response((x, y), locator)
        if model_name is not None:
            if model_name.startswith("anthropic") and not self.claude.authenticated:
                raise AutomationError("You need to provide Anthropic credentials to use Anthropic models.")
            if model_name.startswith("tars") and not self.tars.authenticated:
                raise AutomationError("You need to provide UI-TARS HF Endpoint credentials to use UI-TARS models.")
        if self.tars.authenticated and model_name == "tars":
            x, y = self.tars.locate_prediction(screenshot, self._serialize_locator(locator))
            return handle_response((x, y), locator)
        if self.claude.authenticated and model_name == "anthropic-claude-3-5-sonnet-20241022":
            logger.debug("Routing locate prediction to Anthropic")
            x, y = self.claude.locate_inference(screenshot, self._serialize_locator(locator))
            return handle_response((x, y), locator)
        
        for grounding_model_router in self.grounding_model_routers:
            if grounding_model_router.is_responsible(model_name) and grounding_model_router.is_authenticated():
                return grounding_model_router.locate(screenshot, locator, model_name)

        if model_name is None:
            if self.claude.authenticated:
                logger.debug("Routing locate prediction to Anthropic")
                x, y = self.claude.locate_inference(screenshot, self._serialize_locator(locator))
                return handle_response((x, y), locator)
            
        raise AutomationError("Executing locate commands requires to authenticate with an Automation Model Provider.")
