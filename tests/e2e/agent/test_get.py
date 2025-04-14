import pytest
from PIL import Image as PILImage
from askui import models
from askui import VisionAgent
from askui.utils.image_utils import ImageSource


@pytest.mark.parametrize("model_name", [None, models.ASKUI, models.ANTHROPIC])
def test_get(
    vision_agent: VisionAgent,
    github_login_screenshot: PILImage.Image,
    model_name: str,
) -> None:
    url = vision_agent.get(
        "What is the current url shown in the url bar?", ImageSource(github_login_screenshot), model_name=model_name
    )
    assert url == "github.com/login"
