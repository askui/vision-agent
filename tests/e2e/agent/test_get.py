from typing import Literal
import pytest
from PIL import Image as PILImage
from askui import models
from askui import VisionAgent
from askui.utils.image_utils import ImageSource
from askui import JsonSchemaBase


class UrlResponse(JsonSchemaBase):
    url: str


class PageContextResponse(UrlResponse):
    title: str


class BrowserContextResponse(JsonSchemaBase):
    page_context: PageContextResponse
    browser_type: Literal["chrome", "firefox", "edge", "safari"]


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


@pytest.mark.skip("Skip for now as this pops up in our observability systems as a false positive")
def test_get_with_response_schema_without_additional_properties_with_askui_model_raises(
    vision_agent: VisionAgent,
    github_login_screenshot: PILImage.Image,
) -> None:
    with pytest.raises(Exception):
        vision_agent.get(
            "What is the current url shown in the url bar?",
            ImageSource(github_login_screenshot),
            response_schema=UrlResponse,
            model_name=models.ASKUI,
        )


@pytest.mark.skip("Skip for now as this pops up in our observability systems as a false positive")
def test_get_with_response_schema_without_required_with_askui_model_raises(
    vision_agent: VisionAgent,
    github_login_screenshot: PILImage.Image,
) -> None:
    with pytest.raises(Exception):
        vision_agent.get(
            "What is the current url shown in the url bar?",
            ImageSource(github_login_screenshot),
            response_schema=UrlResponse,
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
        response_schema=UrlResponse,
        model_name=model_name,
    )
    assert isinstance(response, UrlResponse)
    assert response.url in ["https://github.com/login", "github.com/login"]


def test_get_with_response_schema_with_anthropic_model_raises_not_implemented(
    vision_agent: VisionAgent,
    github_login_screenshot: PILImage.Image,
) -> None:
    with pytest.raises(NotImplementedError):
        vision_agent.get(
            "What is the current url shown in the url bar?",
            ImageSource(github_login_screenshot),
            response_schema=UrlResponse,
            model_name=models.ANTHROPIC,
        )


@pytest.mark.parametrize("model_name", [None, models.ASKUI])
@pytest.mark.skip("Skip as there is currently a bug on the api side not supporting definitions used for nested schemas")
def test_get_with_nested_and_inherited_response_schema(
    vision_agent: VisionAgent,
    github_login_screenshot: PILImage.Image,
    model_name: str,
) -> None:
    response = vision_agent.get(
        "What is the current browser context?",
        ImageSource(github_login_screenshot),
        response_schema=BrowserContextResponse,
        model_name=model_name,
    )
    assert isinstance(response, BrowserContextResponse)
    assert response.page_context.url in ["https://github.com/login", "github.com/login"]
    assert "Github" in response.page_context.title
    assert response.browser_type in ["chrome", "firefox", "edge", "safari"]
