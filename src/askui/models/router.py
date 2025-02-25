from typing import Optional
from PIL import Image
from .askui.api import AskUIHandler
from .anthropic.claude import ClaudeHandler
from .huggingface.spaces_api import HFSpacesHandler
from ..logging import logger
from ..utils import AutomationError
from .ui_tars_ep.ui_tars_api import UITarsAPIHandler
from .anthropic.claude_agent import ClaudeComputerAgent
from abc import ABC, abstractmethod

def handle_response(response: tuple[int | None, int | None], instruction: str):
    if response[0] is None or response[1] is None:
        raise AutomationError(f'Could not locate "{instruction}"')
    return response

class GroundingModelRouter(ABC):

    @abstractmethod
    def click(self, screenshot: Image.Image, instruction: str, model_name: str | None = None):
        pass

    @abstractmethod
    def is_responsible(self, model_nam: Optional[str]):
        pass
    
    @abstractmethod
    def is_authenticated(self) -> bool:
        pass


class AskUIModelRouter(GroundingModelRouter):
    
    def __init__(self):
        self.askui = AskUIHandler()

    def click(self, screenshot: Image.Image, instruction: str, model_name: str | None = None):
        if not self.askui.authenticated:
            raise AutomationError(f"NoAskUIAuthenticationSet! Please set 'AskUI ASKUI_WORKSPACE_ID' or 'ASKUI_TOKEN' as env variables!")

        if  model_name == "askui-pta":
            logger.debug(f"Routing click prediction to askui-pta")
            x, y = self.askui.click_pta_prediction(screenshot, instruction)
            return handle_response((x, y), instruction)
        if model_name == "askui-ocr":
            logger.debug(f"Routing click prediction to askui-ocr")
            x, y = self.askui.click_ocr_prediction(screenshot, instruction)
            return handle_response((x, y), instruction)
        if model_name == "askui-combo" or model_name is None:
            logger.debug(f"Routing click prediction to askui-combo")
            x, y = self.askui.click_pta_prediction(screenshot, instruction)
            if x is None or y is None:
                x, y = self.askui.click_ocr_prediction(screenshot, instruction)
            return handle_response((x, y), instruction)
        raise AutomationError(f"Invalid model name {model_name} for click")
        
    def is_responsible(self, model_name: Optional[str]):
        return model_name is None or model_name.startswith("askui")
    
    def is_authenticated(self) -> bool:
        return self.askui.authenticated

    

class ModelRouter:
    def __init__(self, log_level, report, 
                 grounding_model_routers: list[GroundingModelRouter] = None):
        self.report = report

        self.grounding_model_routers = grounding_model_routers or [AskUIModelRouter()]

        self.claude = ClaudeHandler(log_level)
        self.huggingface_spaces = HFSpacesHandler()
        self.tars = UITarsAPIHandler(self.report)
    
    def act(self, controller_client, instruction: str, model_name: str | None = None):
        if self.tars.authenticated and model_name == "tars":
            return self.tars.act(controller_client, instruction)
        if self.claude.authenticated and model_name == "claude":
            agent = ClaudeComputerAgent(controller_client, self.report)
            agent.run(instruction)
        raise AutomationError("Invalid model name for act")
    
    def get_inference(self, screenshot: Image.Image, instruction: str, model_name: str | None = None):
        if self.tars.authenticated and model_name == "tars":
            return self.tars.get_prediction(screenshot, instruction)
        if self.claude.authenticated and model_name == "anthropic-claude-3-5-sonnet-20241022":
            return self.claude.get_inference(screenshot, instruction)
        raise AutomationError("Executing get commands requires to authenticate with an Automation Model Provider supporting it.")
    
    def click(self, screenshot: Image.Image, instruction: str, model_name: str | None = None):
        if model_name is not None and model_name in self.huggingface_spaces.get_spaces_names():
            x, y = self.huggingface_spaces.predict(screenshot, instruction, model_name)
            return handle_response((x, y), instruction)
        if model_name is not None:
            if model_name.startswith("anthropic") and not self.claude.authenticated:
                raise AutomationError("You need to provide Anthropic credentials to use Anthropic models.")
            if model_name.startswith("tars") and not self.tars.authenticated:
                raise AutomationError("You need to provide UI-TARS HF Endpoint credentials to use UI-TARS models.")
        if self.tars.authenticated and model_name == "tars":
            x, y = self.tars.click_pta_prediction(screenshot, instruction)
            return handle_response((x, y), instruction)
        if self.claude.authenticated and model_name == "anthropic-claude-3-5-sonnet-20241022":
            logger.debug("Routing click prediction to Anthropic")
            x, y = self.claude.click_inference(screenshot, instruction)
            return handle_response((x, y), instruction)
        
        for grounding_model_router in self.grounding_model_routers:
            if grounding_model_router.is_responsible(model_name) and grounding_model_router.is_authenticated():
                return grounding_model_router.click(screenshot, instruction, model_name)

        if model_name is None:
            if self.claude.authenticated:
                logger.debug("Routing click prediction to Anthropic")
                x, y = self.claude.click_inference(screenshot, instruction)
                return handle_response((x, y), instruction)
            
        raise AutomationError("Executing click commands requires to authenticate with an Automation Model Provider.")
