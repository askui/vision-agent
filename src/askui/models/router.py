from PIL import Image
from .askui.api import AskUIHandler
from .anthropic.claude import ClaudeHandler
from ..logging import logger
from ..utils import AutomationError


class ModelRouter:
    def __init__(self, log_level):
        self.askui = AskUIHandler()
        self.claude = ClaudeHandler(log_level)

    def handle_response(self, response: tuple[int, int], instruction: str):
        if response[0] is None or response[1] is None:
            raise AutomationError(f'Could not locate "{instruction}"')
        return response

    def click(self, screenshot: Image.Image, instruction: str):
        if self.askui.authenticated:
            logger.debug("Routing click prediction to AskUI")
            x, y = self.askui.click_prediction(screenshot, instruction)
            return self.handle_response((x, y), instruction)
        else:
            logger.debug("Routing click prediction to Anthropic")
            x, y = self.claude.click_inference(screenshot, instruction)
            return self.handle_response((x, y), instruction)
