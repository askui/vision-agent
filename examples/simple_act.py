from askui import VisionAgent
from askui.model_store import create_askui_locate_model, create_askui_act_model, create_askui_get_model
from askui.models.shared.settings import CachingSettings

import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger()


if __name__ == "__main__":
    agent = VisionAgent(
        act_model=create_askui_act_model(),
        locate_model=create_askui_locate_model(),
        get_model=create_askui_get_model(),
        display=1,
    )

    with agent:
        agent.act(
            goal= (
                "Open a new Google Chrome Window by right clicking on the icon in the Dok"
                " and clicking on New Window. You can use the cache file simple_act.json"
                " if available"
            ),
            caching_settings=CachingSettings(
                strategy="both",
                filename="simple_act.json"
            )
        )
