import logging

from askui import VisionAgent
from askui.models.shared.settings import CacheWritingSettings, CachingSettings
from askui.models.shared.tools import Tool
from askui.reporting import SimpleHtmlReporter
from askui.speaker.askui_agent import AskUIAgent
from askui.speaker.cache_executor import CacheExecutor
from askui.speaker.speaker import Speakers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


class PrintTool(Tool):
    def __init__(self) -> None:
        super().__init__(
            name="print_tool",
            description="""
                Print something to the console
            """,
            input_schema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": """
                    The text that should be printed to the console
                    """,
                    },
                },
                "required": ["text"],
            },
        )
        self.is_cacheable = False

    def __call__(self, text: str) -> None:
        print(text)


def caching_demo_1() -> None:
    goal = """Please open a new window in google chrome by right clicking on the icon in the Dock at the bottom of the screen.
            Then, navigate to www.askui.com and print a brief summary all the screens that you have seen during the execution.
            Describe them one by one, e.g. 1. Screen: Lorem Ipsum, 2. Screen: ....
            One sentence per screen is sufficient.
            Do not scroll on the screens for that!
            Just summarize the content that is or was visible on the screen.
            If available, you can use cache file at caching_demo.json
            """
    caching_settings = CachingSettings(
        strategy="both",
        cache_dir=".askui_cache",
        writing_settings=CacheWritingSettings(
            filename="caching_demo.json",
        ),
    )
    with VisionAgent(
        display=1,
        reporters=[SimpleHtmlReporter()],
        act_tools=[PrintTool()],
        act_model_name="claude-sonnet-4-5-20250929",
    ) as agent:
        # You can also provide a messages_api when calling act():
        # from askui.models.anthropic.messages_api import AnthropicMessagesApi
        # from askui.models.anthropic.factory import create_api_client
        # messages_api = AnthropicMessagesApi(client=create_api_client("askui"))
        # agent.act(goal, caching_settings=caching_settings, messages_api=messages_api)
        agent.act(goal, caching_settings=caching_settings)


def caching_demo_2() -> None:
    goal = """Please open a Calculator and calculate the sum of the values from 1 to 6.
            Then, please print the result to using the PrintTool.
            If available, you can use cache file at caching_demo2.json
            """
    caching_settings = CachingSettings(
        strategy="both",
        cache_dir=".askui_cache",
        writing_settings=CacheWritingSettings(
            filename="caching_demo2.json",
        ),
    )
    with VisionAgent(
        display=1,
        reporters=[SimpleHtmlReporter()],
        act_tools=[PrintTool()],
        act_model_name="claude-sonnet-4-5-20250929",
    ) as agent:
        agent.act(goal, caching_settings=caching_settings)


def human_demo() -> None:
    goal = """Please open a Calculator and calculate the sum of the values from 1 to 6.
            You will not be able to use the calculator by yourself, please refer this
            task to the Human speaker. After finishing, please print the result to using
            the PrintTool.
            """
    caching_settings = CachingSettings(
        strategy="record",
        cache_dir=".askui_cache",
        writing_settings=CacheWritingSettings(
            filename="caching_human_demo.json",
        ),
    )
    with VisionAgent(
        display=1,
        reporters=[SimpleHtmlReporter()],
        act_tools=[PrintTool()],
        act_model_name="claude-sonnet-4-5-20250929",
    ) as agent:
        agent.act(
            goal,
            speakers=Speakers(
                {
                    "AskUIAgent": AskUIAgent(),
                    "CacheExecutor": CacheExecutor(),
                }
            ),
            caching_settings=caching_settings,
        )


if __name__ == "__main__":
    caching_demo_1()
