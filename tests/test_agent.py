from vision_agent import VisionAgent
import time


# def test_agent():
#     agent = VisionAgent()
#     agent.cli("firefox")
#     time.sleep(1)
#     agent.click("url bar")
#     agent.type("https://www.google.com")
#     agent.keyboard("enter")
#     time.sleep(5)
#     agent.click("textfield with search icon")
#     agent.type("cat images")
#     agent.keyboard("enter")
#     time.sleep(3)
#     agent.click("Beautiful")
#     agent.close()


def test_agent_act():
    agent = VisionAgent()
    agent.cli("firefox")
    time.sleep(1)
    agent.act("search for flights")
    assert False