import os
import logging

from askui import AgentSettings, ComputerAgent
from askui.model_providers import (
    AskUIVlmProvider,
    AskUIImageQAProvider,
    AskUIDetectionProvider,
    AnthropicVlmProvider,
    AnthropicImageQAProvider
)


from askui.models.shared.settings import CachingSettings

logging.basicConfig(
    level=logging.INFO, format=(
        "[%(levelname)s] %(asctime)s "
        "%(pathname)s:%(lineno)d | "
        "%(message)s"
    )
)
logger = logging.getLogger()

def try_act(agent: ComputerAgent) -> None:
    agent.act(
        goal=(
            "Open a new Google Chrome Window by right clicking on the icon in the"
            " Dok and clicking on New Window. Then navgate to askui.com."
            #" You can use the cache file simple_act.json if available"
        ),
        # caching_settings=CachingSettings(
        #     strategy="no", filename="simple_act.json"
        # ),
    )

def try_locate(agent: ComputerAgent) -> None:
    point = agent.locate("Accept All")
    print(point)

def try_get(agent: ComputerAgent) -> None:
    name = agent.get("The name of the website")
    print(name)

if __name__ == "__main__":

    askui_sonnet = AskUIVlmProvider(
        model_id="claude-sonnet-4-5",
    )
    askui_qa = AskUIImageQAProvider(model_id="gemini-2.5-flash")
    askui_detection = AskUIDetectionProvider()

    anthropic_haiku = AnthropicVlmProvider(
        api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        model_id="claude-haiku-4-5"
    )
    anthropic_haiku_image_qa = AnthropicImageQAProvider(
        api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        model_id="claude-haiku-4-5"
    )

    default_settings = AgentSettings(
        vlm_provider=askui_sonnet,
        image_qa_provider=askui_qa,
        detection_provider=askui_detection
    )
    anthropic_settings = AgentSettings(
        vlm_provider=anthropic_haiku,
        image_qa_provider=anthropic_haiku_image_qa,
    )

    default_agent = ComputerAgent(
        settings=default_settings,
        display=1,
    )
    anthropic_agent = ComputerAgent(
        settings=anthropic_settings,
        display=1,
    )

    with default_agent as agent:
        try_act(default_agent)
        try_locate(default_agent)
        try_get(default_agent)

    with anthropic_agent:
        try_act(anthropic_agent)
        try_get(anthropic_agent)


