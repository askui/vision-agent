from vision_agent import VisionAgent
import time


def test_agent():
    agent = VisionAgent()
    agent.cli("firefox")
    time.sleep(1)
    agent.click("url bar")
    agent.type("http://www.google.com")
    agent.keyboard("enter")
    agent.close()
