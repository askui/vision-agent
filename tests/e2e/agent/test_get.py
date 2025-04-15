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
        "What is the current url shown in the url bar?",
        ImageSource(github_login_screenshot),
        model_name=model_name,
    )
    assert url == "github.com/login"


def test_get_with_response_schema_without_additional_properties_with_askui_model_raises(
    vision_agent: VisionAgent,
    github_login_screenshot: PILImage.Image,
) -> None:
    with pytest.raises(Exception):
        vision_agent.get(
            "What is the current url shown in the url bar?",
            ImageSource(github_login_screenshot),
            response_schema={
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
            },
            model_name=models.ASKUI,
        )


def test_get_with_response_schema_without_required_with_askui_model_raises(
    vision_agent: VisionAgent,
    github_login_screenshot: PILImage.Image,
) -> None:
    with pytest.raises(Exception):
        vision_agent.get(
            "What is the current url shown in the url bar?",
            ImageSource(github_login_screenshot),
            response_schema={
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "additionalProperties": False,
            },
            model_name=models.ASKUI,
        )


@pytest.mark.parametrize("model_name", [None, models.ASKUI])
def test_get_with_response_schema(
    vision_agent: VisionAgent,
    github_login_screenshot: PILImage.Image,
    model_name: str,
) -> None:
    response = vision_agent.get(
        "What is the current url shown in the url bar?",
        ImageSource(github_login_screenshot),
        response_schema={
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "additionalProperties": False,
            "required": ["url"],
        },
        model_name=model_name,
    )
    assert response == {"url": "https://github.com/login"} or response == {"url": "github.com/login"}


def test_get_with_response_schema_with_anthropic_model_raises_not_implemented(
    vision_agent: VisionAgent,
    github_login_screenshot: PILImage.Image,
) -> None:
    with pytest.raises(NotImplementedError):
        vision_agent.get(
            "What is the current url shown in the url bar?",
            ImageSource(github_login_screenshot),
            response_schema={
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "additionalProperties": False,
            },
            model_name=models.ANTHROPIC,
        )
