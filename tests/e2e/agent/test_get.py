import pathlib
from typing import Literal

import pytest
from PIL import Image as PILImage
from pydantic import BaseModel, RootModel
from pytest_mock import MockerFixture

from askui import ResponseSchemaBase, VisionAgent
from askui.model_store.get_models import AnthropicGetModel
from askui.model_store.get_models.gemini_get_model import AskUiGeminiGetModel
from askui.models import ModelName
from askui.models.anthropic.factory import create_api_client
from askui.models.anthropic.messages_api import AnthropicMessagesApi
from askui.models.askui.inference_api import AskUiInferenceApiSettings
from askui.models.models import GetModel
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
    "get_model",
    [
        pytest.param(None, id="default"),
        pytest.param(
            AskUiGeminiGetModel(
                model_id=ModelName.GEMINI__2_5__FLASH,
                inference_api_settings=AskUiInferenceApiSettings(),
            ),
            id="askui",
        ),
        pytest.param(
            AskUiGeminiGetModel(
                model_id=ModelName.GEMINI__2_5__FLASH,
                inference_api_settings=AskUiInferenceApiSettings(),
            ),
            id="gemini_flash",
        ),
        pytest.param(
            AskUiGeminiGetModel(
                model_id=ModelName.GEMINI__2_5__PRO,
                inference_api_settings=AskUiInferenceApiSettings(),
            ),
            id="gemini_pro",
        ),
        pytest.param(
            AnthropicGetModel(
                model_id=ModelName.CLAUDE__SONNET__4__20250514,
                messages_api=AnthropicMessagesApi(
                    client=create_api_client(api_provider="anthropic"),
                ),
            ),
            id="claude",
        ),
    ],
)
def test_get(
    vision_agent: VisionAgent,
    github_login_screenshot: PILImage.Image,
    get_model: GetModel | None,
) -> None:
    url = vision_agent.get(
        "What is the current url shown in the url bar?\nUrl: ",
        source=github_login_screenshot,
        get_model=get_model,
    )
    assert url in ["github.com/login", "https://github.com/login"]


def test_get_with_pdf_with_non_gemini_model_raises_not_implemented(
    vision_agent: VisionAgent, path_fixtures_dummy_pdf: pathlib.Path
) -> None:
    with pytest.raises(NotImplementedError):
        vision_agent.get("What is in the PDF?", source=path_fixtures_dummy_pdf)


@pytest.mark.parametrize(
    "get_model",
    [
        pytest.param(
            AskUiGeminiGetModel(
                model_id=ModelName.GEMINI__2_5__FLASH,
                inference_api_settings=AskUiInferenceApiSettings(),
            ),
            id="gemini_flash",
        ),
        pytest.param(
            AskUiGeminiGetModel(
                model_id=ModelName.GEMINI__2_5__PRO,
                inference_api_settings=AskUiInferenceApiSettings(),
            ),
            id="gemini_pro",
        ),
    ],
)
def test_get_with_pdf_with_gemini_model(
    vision_agent: VisionAgent,
    get_model: GetModel,
    path_fixtures_dummy_pdf: pathlib.Path,
) -> None:
    response = vision_agent.get(
        "What is in the PDF? explain in 1 sentence",
        source=path_fixtures_dummy_pdf,
        get_model=get_model,
    )
    assert isinstance(response, str)
    assert "is a test " in response.lower()


@pytest.mark.parametrize(
    "get_model",
    [
        pytest.param(
            AskUiGeminiGetModel(
                model_id=ModelName.GEMINI__2_5__FLASH,
                inference_api_settings=AskUiInferenceApiSettings(),
            ),
            id="gemini_flash",
        ),
        pytest.param(
            AskUiGeminiGetModel(
                model_id=ModelName.GEMINI__2_5__PRO,
                inference_api_settings=AskUiInferenceApiSettings(),
            ),
            id="gemini_pro",
        ),
    ],
)
def test_get_with_pdf_too_large(
    vision_agent: VisionAgent,
    get_model: GetModel,
    path_fixtures_dummy_pdf: pathlib.Path,
    mocker: MockerFixture,
) -> None:
    mocker.patch("askui.models.askui.google_genai_api.MAX_FILE_SIZE_BYTES", 1)
    with pytest.raises(ValueError, match="PDF file size exceeds the limit"):
        vision_agent.get(
            "What is in the PDF?",
            source=path_fixtures_dummy_pdf,
            get_model=get_model,
        )


def test_get_with_pdf_too_large_with_default_model(
    vision_agent: VisionAgent,
    path_fixtures_dummy_pdf: pathlib.Path,
    mocker: MockerFixture,
) -> None:
    mocker.patch("askui.models.askui.google_genai_api.MAX_FILE_SIZE_BYTES", 1)

    # This should raise a ValueError because the default model is Gemini and it falls
    # back to inference askui which does not support pdfs
    with pytest.raises(ValueError, match="PDF file size exceeds the limit"):
        vision_agent.get("What is in the PDF?", source=path_fixtures_dummy_pdf)


def test_get_with_xlsx_with_non_gemini_model_raises_not_implemented(
    vision_agent: VisionAgent, path_fixtures_dummy_excel: pathlib.Path
) -> None:
    with pytest.raises(NotImplementedError):
        vision_agent.get("What is in the xlsx?", source=path_fixtures_dummy_excel)


@pytest.mark.parametrize(
    "get_model",
    [
        pytest.param(
            AskUiGeminiGetModel(
                model_id=ModelName.GEMINI__2_5__FLASH,
                inference_api_settings=AskUiInferenceApiSettings(),
            ),
            id="gemini_flash",
        ),
        pytest.param(
            AskUiGeminiGetModel(
                model_id=ModelName.GEMINI__2_5__PRO,
                inference_api_settings=AskUiInferenceApiSettings(),
            ),
            id="gemini_pro",
        ),
    ],
)
def test_get_with_xlsx_with_gemini_model(
    vision_agent: VisionAgent,
    get_model: GetModel,
    path_fixtures_dummy_excel: pathlib.Path,
) -> None:
    response = vision_agent.get(
        "What is the salary of Doe?",
        source=path_fixtures_dummy_excel,
        get_model=get_model,
    )
    assert isinstance(response, str)
    assert "20000" in response.lower()


class Salary(ResponseSchemaBase):
    salary: int
    name: str


class SalaryResponse(ResponseSchemaBase):
    salaries: list[Salary]


@pytest.mark.parametrize(
    "get_model",
    [
        pytest.param(
            AskUiGeminiGetModel(
                model_id=ModelName.GEMINI__2_5__FLASH,
                inference_api_settings=AskUiInferenceApiSettings(),
            ),
            id="gemini_flash",
        ),
        pytest.param(
            AskUiGeminiGetModel(
                model_id=ModelName.GEMINI__2_5__PRO,
                inference_api_settings=AskUiInferenceApiSettings(),
            ),
            id="gemini_pro",
        ),
    ],
)
def test_get_with_xlsx_with_gemini_model_with_response_schema(
    vision_agent: VisionAgent,
    get_model: GetModel,
    path_fixtures_dummy_excel: pathlib.Path,
) -> None:
    response = vision_agent.get(
        "What is the salary of Everyone?",
        source=path_fixtures_dummy_excel,
        response_schema=SalaryResponse,
        get_model=get_model,
    )
    assert isinstance(response, SalaryResponse)
    # sort salaries by name for easier assertion
    response.salaries.sort(key=lambda x: x.name)
    assert response.salaries[0].name == "Doe"
    assert response.salaries[0].salary == 20000
    assert response.salaries[1].name == "John"
    assert response.salaries[1].salary == 10000


def test_get_with_xlsx_with_default_model_with_chart_data(
    vision_agent: VisionAgent, path_fixtures_dummy_excel: pathlib.Path
) -> None:
    response = vision_agent.get(
        "What is the salary of John?", source=path_fixtures_dummy_excel
    )
    assert isinstance(response, str)
    assert "10000" in response.lower()


def test_get_with_docs_with_default_model(
    vision_agent: VisionAgent, path_fixtures_dummy_doc: pathlib.Path
) -> None:
    response = vision_agent.get(
        "At what time in 24h format does the person sleeps?",
        source=path_fixtures_dummy_doc,
    )
    assert isinstance(response, str)
    assert "22:00" in response.lower()


def test_get_with_fallback_model(
    agent_toolbox_mock: AgentToolbox,
    askui_get_model: GetModel,
    simple_html_reporter: Reporter,
    github_login_screenshot: PILImage.Image,
) -> None:
    with VisionAgent(
        reporters=[simple_html_reporter],
        get_model=askui_get_model,
        tools=agent_toolbox_mock,
    ) as vision_agent:
        url = vision_agent.get(
            "What is the current url shown in the url bar?",
            source=github_login_screenshot,
        )
        assert url in ["github.com/login", "https://github.com/login"]


class UrlResponseBaseModel(BaseModel):
    url: str


def test_get_with_response_schema_without_additional_properties_with_askui_model_raises(
    vision_agent: VisionAgent, github_login_screenshot: PILImage.Image
) -> None:
    with pytest.raises(Exception):  # noqa: B017
        vision_agent.get(
            "What is the current url shown in the url bar?",
            source=github_login_screenshot,
            response_schema=UrlResponseBaseModel,  # type: ignore[type-var]
        )


class OptionalUrlResponse(ResponseSchemaBase):
    url: str = "github.com"


def test_get_with_response_schema_with_default_value(
    vision_agent: VisionAgent, github_login_screenshot: PILImage.Image
) -> None:
    response = vision_agent.get(
        "What is the current url shown in the url bar?",
        source=github_login_screenshot,
        response_schema=OptionalUrlResponse,
    )
    assert isinstance(response, OptionalUrlResponse)
    assert "github.com" in response.url


@pytest.mark.parametrize(
    "get_model",
    [
        pytest.param(None, id="default"),
        pytest.param(
            AskUiGeminiGetModel(
                model_id=ModelName.GEMINI__2_5__FLASH,
                inference_api_settings=AskUiInferenceApiSettings(),
            ),
            id="askui",
        ),
    ],
)
def test_get_with_response_schema(
    vision_agent: VisionAgent,
    github_login_screenshot: PILImage.Image,
    get_model: GetModel | None,
) -> None:
    response = vision_agent.get(
        "What is the current url shown in the url bar?",
        source=github_login_screenshot,
        response_schema=UrlResponse,
        get_model=get_model,
    )
    assert isinstance(response, UrlResponse)
    assert response.url in ["https://github.com/login", "github.com/login"]


def test_get_with_response_schema_with_anthropic_model_raises_not_implemented(
    vision_agent: VisionAgent, github_login_screenshot: PILImage.Image
) -> None:
    with pytest.raises(NotImplementedError):
        vision_agent.get(
            "What is the current url shown in the url bar?",
            source=github_login_screenshot,
            response_schema=UrlResponse,
        )


@pytest.mark.parametrize(
    "get_model",
    [
        pytest.param(
            AskUiGeminiGetModel(
                model_id=ModelName.GEMINI__2_5__FLASH,
                inference_api_settings=AskUiInferenceApiSettings(),
            ),
            id="askui",
        ),
    ],
)
def test_get_with_nested_and_inherited_response_schema(
    vision_agent: VisionAgent,
    github_login_screenshot: PILImage.Image,
    get_model: GetModel,
) -> None:
    response = vision_agent.get(
        "What is the current browser context?",
        source=github_login_screenshot,
        response_schema=BrowserContextResponse,
        get_model=get_model,
    )
    assert isinstance(response, BrowserContextResponse)
    assert response.page_context.url in ["https://github.com/login", "github.com/login"]
    assert "GitHub" in response.page_context.title
    assert response.browser_type in ["chrome", "firefox", "edge", "safari"]


class LinkedListNode(ResponseSchemaBase):
    value: str
    next: "LinkedListNode | None"


@pytest.mark.parametrize(
    "get_model",
    [
        pytest.param(
            AskUiGeminiGetModel(
                model_id=ModelName.GEMINI__2_5__FLASH,
                inference_api_settings=AskUiInferenceApiSettings(),
            ),
            id="askui",
        ),
    ],
)
def test_get_with_recursive_response_schema(
    vision_agent: VisionAgent,
    github_login_screenshot: PILImage.Image,
    get_model: GetModel,
) -> None:
    response = vision_agent.get(
        "Can you extract all segments (domain, path etc.) from the url as a linked list, "
        "e.g. 'https://google.com/test' -> 'google.com->test->None'?",
        source=github_login_screenshot,
        response_schema=LinkedListNode,
        get_model=get_model,
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


@pytest.mark.parametrize(
    "get_model",
    [
        pytest.param(
            AskUiGeminiGetModel(
                model_id=ModelName.GEMINI__2_5__FLASH,
                inference_api_settings=AskUiInferenceApiSettings(),
            ),
            id="askui",
        ),
    ],
)
def test_get_with_string_schema(
    vision_agent: VisionAgent,
    github_login_screenshot: PILImage.Image,
    get_model: GetModel,
) -> None:
    response = vision_agent.get(
        "What is the current url shown in the url bar?",
        source=github_login_screenshot,
        response_schema=str,
        get_model=get_model,
    )
    assert response in ["https://github.com/login", "github.com/login"]


@pytest.mark.parametrize(
    "get_model",
    [
        pytest.param(
            AskUiGeminiGetModel(
                model_id=ModelName.GEMINI__2_5__FLASH,
                inference_api_settings=AskUiInferenceApiSettings(),
            ),
            id="askui",
        ),
        pytest.param(
            AskUiGeminiGetModel(
                model_id=ModelName.GEMINI__2_5__FLASH,
                inference_api_settings=AskUiInferenceApiSettings(),
            ),
            id="gemini_flash",
        ),
    ],
)
def test_get_with_boolean_schema(
    vision_agent: VisionAgent,
    github_login_screenshot: PILImage.Image,
    get_model: GetModel,
) -> None:
    response = vision_agent.get(
        "Is this a login page?",
        source=github_login_screenshot,
        response_schema=bool,
        get_model=get_model,
    )
    assert isinstance(response, bool)
    assert response is True


@pytest.mark.parametrize(
    "get_model",
    [
        pytest.param(
            AskUiGeminiGetModel(
                model_id=ModelName.GEMINI__2_5__FLASH,
                inference_api_settings=AskUiInferenceApiSettings(),
            ),
            id="askui",
        ),
    ],
)
def test_get_with_integer_schema(
    vision_agent: VisionAgent,
    github_login_screenshot: PILImage.Image,
    get_model: GetModel,
) -> None:
    response = vision_agent.get(
        "How many input fields are visible on this page?",
        source=github_login_screenshot,
        response_schema=int,
        get_model=get_model,
    )
    assert isinstance(response, int)
    assert response > 0


@pytest.mark.parametrize(
    "get_model",
    [
        pytest.param(
            AskUiGeminiGetModel(
                model_id=ModelName.GEMINI__2_5__FLASH,
                inference_api_settings=AskUiInferenceApiSettings(),
            ),
            id="askui",
        ),
    ],
)
def test_get_with_float_schema(
    vision_agent: VisionAgent,
    github_login_screenshot: PILImage.Image,
    get_model: GetModel,
) -> None:
    response = vision_agent.get(
        "Return a floating point number between 0 and 1 as a rating for how you well this page is designed (0 is the worst, 1 is the best)",
        source=github_login_screenshot,
        response_schema=float,
        get_model=get_model,
    )
    assert isinstance(response, float)
    assert response > 0


@pytest.mark.parametrize(
    "get_model",
    [
        pytest.param(
            AskUiGeminiGetModel(
                model_id=ModelName.GEMINI__2_5__FLASH,
                inference_api_settings=AskUiInferenceApiSettings(),
            ),
            id="askui",
        ),
    ],
)
def test_get_returns_str_when_no_schema_specified(
    vision_agent: VisionAgent,
    github_login_screenshot: PILImage.Image,
    get_model: GetModel,
) -> None:
    response = vision_agent.get(
        "What is the display showing?",
        source=github_login_screenshot,
        get_model=get_model,
    )
    assert isinstance(response, str)


class Basis(ResponseSchemaBase):
    answer: str


@pytest.mark.parametrize(
    "get_model",
    [
        pytest.param(
            AskUiGeminiGetModel(
                model_id=ModelName.GEMINI__2_5__FLASH,
                inference_api_settings=AskUiInferenceApiSettings(),
            ),
            id="askui",
        ),
    ],
)
def test_get_with_basis_schema(
    vision_agent: VisionAgent,
    github_login_screenshot: PILImage.Image,
    get_model: GetModel,
) -> None:
    response = vision_agent.get(
        "What is the display showing?",
        source=github_login_screenshot,
        response_schema=Basis,
        get_model=get_model,
    )
    assert isinstance(response, Basis)
    assert isinstance(response.answer, str)


class Answer(ResponseSchemaBase):
    answer: str


class BasisWithNestedRootModel(ResponseSchemaBase):
    answer: RootModel[Answer]


@pytest.mark.parametrize(
    "get_model",
    [
        pytest.param(
            AskUiGeminiGetModel(
                model_id=ModelName.GEMINI__2_5__FLASH,
                inference_api_settings=AskUiInferenceApiSettings(),
            ),
            id="askui",
        ),
    ],
)
def test_get_with_nested_root_model(
    vision_agent: VisionAgent,
    github_login_screenshot: PILImage.Image,
    get_model: GetModel,
) -> None:
    response = vision_agent.get(
        "What is the display showing?",
        source=github_login_screenshot,
        response_schema=BasisWithNestedRootModel,
        get_model=get_model,
    )
    assert isinstance(response, BasisWithNestedRootModel)
    assert isinstance(response.answer.root.answer, str)


class PageDomElementLevel4(ResponseSchemaBase):
    tag: str
    text: str | None = None


class PageDomElementLevel3(ResponseSchemaBase):
    tag: str
    children: list["PageDomElementLevel4"]
    text: str | None = None


class PageDomElementLevel2(ResponseSchemaBase):
    tag: str
    children: list["PageDomElementLevel3"]
    text: str | None = None


class PageDomElementLevel1(ResponseSchemaBase):
    tag: str
    children: list["PageDomElementLevel2"]
    text: str | None = None


class PageDom(ResponseSchemaBase):
    children: list[PageDomElementLevel1]


@pytest.mark.parametrize(
    "get_model",
    [
        pytest.param(
            AskUiGeminiGetModel(
                model_id=ModelName.GEMINI__2_5__PRO,
                inference_api_settings=AskUiInferenceApiSettings(),
            ),
            id="gemini_pro",
        ),
    ],
)
def test_get_with_deeply_nested_response_schema_with_model_that_does_not_support_recursion(
    vision_agent: VisionAgent,
    github_login_screenshot: PILImage.Image,
    get_model: GetModel,
) -> None:
    """Test for deeply nested structure with 4 levels of nesting.

    This test case reproduces an issue reported by a user where they encountered
    problems with a deeply nested structure containing 4 levels of nesting.
    """
    response = vision_agent.get(
        "Create a possible dom of the page that goes 4 levels deep",
        source=github_login_screenshot,
        response_schema=PageDom,
        get_model=get_model,
    )
    assert isinstance(response, PageDom)
