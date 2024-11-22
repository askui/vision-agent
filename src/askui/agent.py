import logging
import subprocess
from .tools.askui.askui_controller import AskUiControllerClient, AskUiControllerServer, PC_AND_MODIFIER_KEY, MODIFIER_KEY
from .models.anthropic.claude import ClaudeHandler
from .models.anthropic.claude_agent import ClaudeComputerAgent
from .logging import logger, configure_logging
from .tools.toolbox import AgentToolbox
from .models.router import ModelRouter


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
    
    def keyboard(self, key: PC_AND_MODIFIER_KEY, modifier_keys: list[MODIFIER_KEY] = None):
        logger.debug("VisionAgent received instruction to press '%s'", key)
        self.client.keyboard_tap(key, modifier_keys)
    
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
