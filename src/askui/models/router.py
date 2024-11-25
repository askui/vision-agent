from PIL import Image
from .askui.api import AskUIHandler
from .anthropic.claude import ClaudeHandler
from .huggingface.spaces_api import HFSpacesHandler
from ..logging import logger
from ..utils import AutomationError


class ModelRouter:
    def __init__(self, log_level):
        self.askui = AskUIHandler()
        self.claude = ClaudeHandler(log_level)
        self.huggingface_spaces = HFSpacesHandler()

    def handle_response(self, response: tuple[int, int], instruction: str):
        if response[0] is None or response[1] is None:
            raise AutomationError(f'Could not locate "{instruction}"')
        return response

    def click(self, screenshot: Image.Image, instruction: str, model_name: str = None):
        if model_name is not None and model_name in self.huggingface_spaces.get_spaces_names():
            x, y = self.huggingface_spaces.predict(screenshot, instruction, model_name)
            return self.handle_response((x, y), instruction)
        if model_name is not None:
            if model_name.startswith("askui") and not self.askui.authenticated:
                raise AutomationError("You need to provide AskUI credentials to use AskUI models.")
            if model_name.startswith("anthropic") and not self.claude.authenticated:
                raise AutomationError("You need to provide Anthropic credentials to use Anthropic models.")
        if self.askui.authenticated and model_name == "askui-pta":
            logger.debug(f"Routing click prediction to askui-pta")
            x, y = self.askui.click_pta_prediction(screenshot, instruction)
            return self.handle_response((x, y), instruction)
        if self.askui.authenticated and model_name == "askui-ocr":
            logger.debug(f"Routing click prediction to askui-ocr")
            x, y = self.askui.click_ocr_prediction(screenshot, instruction)
            return self.handle_response((x, y), instruction)
        if self.askui.authenticated and model_name == "askui-combo":
            logger.debug(f"Routing click prediction to askui-combo")
            x, y = self.askui.click_pta_prediction(screenshot, instruction)
            if x is None or y is None:
                x, y = self.askui.click_ocr_prediction(screenshot, instruction)
            return self.handle_response((x, y), instruction)
        if self.claude.authenticated and model_name == "anthropic-claude-3-5-sonnet-20241022":
            logger.debug("Routing click prediction to Anthropic")
            x, y = self.claude.click_inference(screenshot, instruction)
            return self.handle_response((x, y), instruction)
        if model_name is None:
            if self.askui.authenticated:
                logger.debug(f"Routing click prediction to askui-combo")
                x, y = self.askui.click_pta_prediction(screenshot, instruction)
                if x is None or y is None:
                    x, y = self.askui.click_ocr_prediction(screenshot, instruction)
                return self.handle_response((x, y), instruction)
            if self.claude.authenticated:
                logger.debug("Routing click prediction to Anthropic")
                x, y = self.claude.click_inference(screenshot, instruction)
                return self.handle_response((x, y), instruction)
        raise AutomationError("Executing click commands requires to authenticate with an Automation Model Provider.")
