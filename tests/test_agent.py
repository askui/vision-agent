from vision_agent import VisionAgent
import time


def test_agent():
    agent = VisionAgent()
    time.sleep(2)
    agent.click("url bar")
    agent.type("http://www.google.com")
    agent.close()
