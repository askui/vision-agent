import logging

import pytest
from PIL import Image

from askui import locators as loc
from askui.agent import VisionAgent
from askui.container import telemetry
from askui.telemetry.processors import Segment, SegmentSettings
from askui.tools.toolbox import AgentToolbox


@pytest.mark.timeout(60)
def test_telemetry_with_nonexistent_domain_should_not_block(
    github_login_screenshot: Image.Image,
    agent_toolbox_mock: AgentToolbox,
) -> None:
    telemetry.set_processors(
        [
            Segment(
                SegmentSettings(
                    api_url="https://this-domain-does-not-exist-123456789.com",
                    write_key="1234567890",
                )
            )
        ]
    )
    with VisionAgent(tools=agent_toolbox_mock, log_level=logging.DEBUG) as agent:
        agent.locate(loc.Text(), screenshot=github_login_screenshot)
    assert True
