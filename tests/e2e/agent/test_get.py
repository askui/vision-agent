from typing import Literal

import pytest
from PIL import Image as PILImage

from askui import ResponseSchemaBase, VisionAgent
from askui.models import ModelName
from askui.models.askui.facade import AskUiFacade
from askui.models.models import ModelComposition, ModelDefinition
from askui.reporting import Reporter
from askui.tools.toolbox import AgentToolbox


class UrlResponse(ResponseSchemaBase):
    url: str


class PageContextResponse(UrlResponse):
    title: str


class BrowserContextResponse(ResponseSchemaBase):
    page_context: PageContextResponse
    browser_type: Literal["chrome", "firefox", "edge", "safari"]


@pytest.mark.parametrize(
    "model", [None, ModelName.ASKUI, ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022]
)
def test_get(
    vision_agent: VisionAgent,
    github_login_screenshot: PILImage.Image,
    model: str,
) -> None:
    url = vision_agent.get(
        "What is the current url shown in the url bar?",
        image=github_login_screenshot,
        model=model,
    )
    assert url in ["github.com/login", "https://github.com/login"]


def test_get_with_model_composition_should_use_default_model(
    agent_toolbox_mock: AgentToolbox,
    askui_facade: AskUiFacade,
    simple_html_reporter: Reporter,
    github_login_screenshot: PILImage.Image,
) -> None:
    with VisionAgent(
        reporters=[simple_html_reporter],
        model=ModelComposition(
            [
                ModelDefinition(
                    task="e2e_ocr",
                    architecture="easy_ocr",
                    version="1",
                    interface="online_learning",
                    use_case="fb3b9a7b_3aea_41f7_ba02_e55fd66d1c1e",
                    tags=["trained"],
                ),
            ],
        ),
        models={
            ModelName.ASKUI: askui_facade,
        },
        tools=agent_toolbox_mock,
    ) as vision_agent:
        url = vision_agent.get(
            "What is the current url shown in the url bar?",
            image=github_login_screenshot,
        )
        assert url in ["github.com/login", "https://github.com/login"]


@pytest.mark.skip(
    "Skip for now as this pops up in our observability systems as a false positive"
)
def test_get_with_response_schema_without_additional_properties_with_askui_model_raises(
    vision_agent: VisionAgent,
    github_login_screenshot: PILImage.Image,
) -> None:
    with pytest.raises(Exception):  # noqa: B017
        vision_agent.get(
            "What is the current url shown in the url bar?",
            image=github_login_screenshot,
            response_schema=UrlResponse,
            model=ModelName.ASKUI,
        )


@pytest.mark.skip(
    "Skip for now as this pops up in our observability systems as a false positive"
)
def test_get_with_response_schema_without_required_with_askui_model_raises(
    vision_agent: VisionAgent,
    github_login_screenshot: PILImage.Image,
) -> None:
    with pytest.raises(Exception):  # noqa: B017
        vision_agent.get(
            "What is the current url shown in the url bar?",
            image=github_login_screenshot,
            response_schema=UrlResponse,
            model=ModelName.ASKUI,
        )


@pytest.mark.parametrize("model", [None, ModelName.ASKUI])
def test_get_with_response_schema(
    vision_agent: VisionAgent,
    github_login_screenshot: PILImage.Image,
    model: str,
) -> None:
    response = vision_agent.get(
        "What is the current url shown in the url bar?",
        image=github_login_screenshot,
        response_schema=UrlResponse,
        model=model,
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
            image=github_login_screenshot,
            response_schema=UrlResponse,
            model=ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022,
        )


@pytest.mark.parametrize("model", [ModelName.ASKUI])
@pytest.mark.skip(
    "Skip as there is currently a bug on the api side not supporting definitions used for nested schemas"
)
def test_get_with_nested_and_inherited_response_schema(
    vision_agent: VisionAgent,
    github_login_screenshot: PILImage.Image,
    model: str,
) -> None:
    response = vision_agent.get(
        "What is the current browser context?",
        image=github_login_screenshot,
        response_schema=BrowserContextResponse,
        model=model,
    )
    assert isinstance(response, BrowserContextResponse)
    assert response.page_context.url in ["https://github.com/login", "github.com/login"]
    assert "Github" in response.page_context.title
    assert response.browser_type in ["chrome", "firefox", "edge", "safari"]


@pytest.mark.parametrize("model", [ModelName.ASKUI])
def test_get_with_string_schema(
    vision_agent: VisionAgent,
    github_login_screenshot: PILImage.Image,
    model: str,
) -> None:
    response = vision_agent.get(
        "What is the current url shown in the url bar?",
        image=github_login_screenshot,
        response_schema=str,
        model=model,
    )
    assert response in ["https://github.com/login", "github.com/login"]


@pytest.mark.parametrize("model", [ModelName.ASKUI])
def test_get_with_boolean_schema(
    vision_agent: VisionAgent,
    github_login_screenshot: PILImage.Image,
    model: str,
) -> None:
    response = vision_agent.get(
        "Is this a login page?",
        image=github_login_screenshot,
        response_schema=bool,
        model=model,
    )
    assert isinstance(response, bool)
    assert response is True


@pytest.mark.parametrize("model", [ModelName.ASKUI])
def test_get_with_integer_schema(
    vision_agent: VisionAgent,
    github_login_screenshot: PILImage.Image,
    model: str,
) -> None:
    response = vision_agent.get(
        "How many input fields are visible on this page?",
        image=github_login_screenshot,
        response_schema=int,
        model=model,
    )
    assert isinstance(response, int)
    assert response > 0


@pytest.mark.parametrize("model", [ModelName.ASKUI])
def test_get_with_float_schema(
    vision_agent: VisionAgent,
    github_login_screenshot: PILImage.Image,
    model: str,
) -> None:
    response = vision_agent.get(
        "Return a floating point number between 0 and 1 as a rating for how you well this page is designed (0 is the worst, 1 is the best)",
        image=github_login_screenshot,
        response_schema=float,
        model=model,
    )
    assert isinstance(response, float)
    assert response > 0


@pytest.mark.parametrize("model", [ModelName.ASKUI])
def test_get_returns_str_when_no_schema_specified(
    vision_agent: VisionAgent,
    github_login_screenshot: PILImage.Image,
    model: str,
) -> None:
    response = vision_agent.get(
        "What is the display showing?",
        image=github_login_screenshot,
        model=model,
    )
    assert isinstance(response, str)


class Basis(ResponseSchemaBase):
    answer: str


@pytest.mark.parametrize("model", [ModelName.ASKUI])
def test_get_with_basis_schema(
    vision_agent: VisionAgent,
    github_login_screenshot: PILImage.Image,
    model: str,
) -> None:
    response = vision_agent.get(
        "What is the display showing?",
        image=github_login_screenshot,
        response_schema=Basis,
        model=model,
    )
    assert isinstance(response, Basis)
    assert response.answer != '"What is the display showing?"'
