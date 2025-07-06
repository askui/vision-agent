from typing import Literal

import pytest
from PIL import Image as PILImage
from pydantic import BaseModel, RootModel

from askui import ResponseSchemaBase, VisionAgent
from askui.models import ModelName
from askui.models.models import ModelComposition, ModelDefinition
from askui.models.shared.facade import ModelFacade
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
    "model",
    [
        None,
        ModelName.ASKUI,
        ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022,
        ModelName.CLAUDE__SONNET__4__20250514,
    ],
)
def test_get(
    vision_agent: VisionAgent,
    github_login_screenshot: PILImage.Image,
    model: str,
) -> None:
    url = vision_agent.get(
        "What is the current url shown in the url bar?\nUrl: ",
        image=github_login_screenshot,
        model=model,
    )
    assert url in ["github.com/login", "https://github.com/login"]


def test_get_with_model_composition_should_use_default_model(
    agent_toolbox_mock: AgentToolbox,
    askui_facade: ModelFacade,
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


class UrlResponseBaseModel(BaseModel):
    url: str


def test_get_with_response_schema_without_additional_properties_with_askui_model_raises(
    vision_agent: VisionAgent,
    github_login_screenshot: PILImage.Image,
) -> None:
    with pytest.raises(Exception):  # noqa: B017
        vision_agent.get(
            "What is the current url shown in the url bar?",
            image=github_login_screenshot,
            response_schema=UrlResponseBaseModel,  # type: ignore[type-var]
            model=ModelName.ASKUI,
        )


class OptionalUrlResponse(ResponseSchemaBase):
    url: str = "github.com"


def test_get_with_response_schema_with_default_value_with_askui_model_raises(
    vision_agent: VisionAgent,
    github_login_screenshot: PILImage.Image,
) -> None:
    with pytest.raises(Exception):  # noqa: B017
        vision_agent.get(
            "What is the current url shown in the url bar?",
            image=github_login_screenshot,
            response_schema=OptionalUrlResponse,
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
            model=ModelName.CLAUDE__SONNET__4__20250514,
        )


@pytest.mark.parametrize("model", [ModelName.ASKUI])
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
    assert "GitHub" in response.page_context.title
    assert response.browser_type in ["chrome", "firefox", "edge", "safari"]


class LinkedListNode(ResponseSchemaBase):
    value: str
    next: "LinkedListNode | None"


@pytest.mark.parametrize("model", [ModelName.ASKUI])
def test_get_with_recursive_response_schema(
    vision_agent: VisionAgent,
    github_login_screenshot: PILImage.Image,
    model: str,
) -> None:
    response = vision_agent.get(
        "Can you extract all segments (domain, path etc.) from the url as a linked list, "
        "e.g. 'https://google.com/test' -> 'google.com->test->None'?",
        image=github_login_screenshot,
        response_schema=LinkedListNode,
        model=model,
    )
    assert isinstance(response, LinkedListNode)
    assert response.value == "github.com"
    assert response.next is not None
    assert response.next.value == "login"
    assert (
        response.next.next is None
        or response.next.next.value == ""
        and response.next.next.next is None
    )


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
    assert isinstance(response.answer, str)


class Answer(ResponseSchemaBase):
    answer: str


class BasisWithNestedRootModel(ResponseSchemaBase):
    answer: RootModel[Answer]


@pytest.mark.parametrize("model", [ModelName.ASKUI])
def test_get_with_nested_root_model(
    vision_agent: VisionAgent,
    github_login_screenshot: PILImage.Image,
    model: str,
) -> None:
    response = vision_agent.get(
        "What is the display showing?",
        image=github_login_screenshot,
        response_schema=BasisWithNestedRootModel,
        model=model,
    )
    assert isinstance(response, BasisWithNestedRootModel)
    assert isinstance(response.answer.root.answer, str)
