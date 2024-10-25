from vision_agent import VisionAgent
import time


def test_agent():
    agent = VisionAgent()
    time.sleep(2)
    agent.click("AskUI durchsuchen")
    agent.close()
