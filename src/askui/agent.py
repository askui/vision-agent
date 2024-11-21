import logging
import webbrowser
import subprocess
from typing import Literal
from .tools.askui.askui_controller import AskUiControllerClient, AskUiControllerServer
from .models.anthropic.claude import ClaudeHandler
from .models.anthropic.claude_agent import ClaudeComputerAgent
from .logging import logger, configure_logging
from .tools.toolbox import AgentToolbox
from .models.router import ModelRouter


PC_KEY = Literal['backspace', 'delete', 'enter', 'tab', 'escape', 'up', 'down', 'right', 'left', 'home', 'end', 'pageup', 'pagedown', 'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12', 'space', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '!', '"', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',', '-', '.', '/', ':', ';', '<', '=', '>', '?', '@', '[', '\\', ']', '^', '_', '`', '{', '|', '}', '~']


class VisionAgent:
    def __init__(self, log_level=logging.INFO, display: int = 1):
        configure_logging(level=log_level)

        self.controller = AskUiControllerServer()
        self.controller.start(True)
        self.client = AskUiControllerClient(display)
        self.client.connect()
        self.client.set_display(display)
        self.model_router = ModelRouter(log_level)
        self.claude = ClaudeHandler(log_level=log_level)
        self.tools = AgentToolbox(os_controller=self.client)

    def click(self, instruction: str, model_name: str = None):
        logger.debug("VisionAgent received instruction to click '%s'", instruction)
        screenshot = self.client.screenshot()
        x, y = self.model_router.click(screenshot, instruction, model_name)
        self.client.mouse(x, y)
        self.client.click("left")

    def type(self, text: str):
        logger.debug("VisionAgent received instruction to type '%s'", text)
        self.client.type(text)

    def get(self, instruction: str) -> str:
        logger.debug("VisionAgent received instruction to get '%s'", instruction)
        screenshot = self.client.screenshot()
        reponse = self.claude.get_inference(screenshot, instruction)
        return reponse

    def act(self, goal: str):
        logger.debug("VisionAgent received instruction to act towards the goal '%s'", goal)
        agent = ClaudeComputerAgent(self.client)
        agent.run(goal)
    
    def keyboard(self, key: PC_KEY):
        logger.debug("VisionAgent received instruction to press '%s'", key)
        self.client.keyboard_pressed(key)
        self.client.keyboard_release(key)
    
    def cli(self, command: str):
        logger.debug("VisionAgent received instruction to execute '%s' on cli", command)
        subprocess.run(command.split(" "))

    def close(self):
        self.client.disconnect()
        self.controller.stop(True)

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
