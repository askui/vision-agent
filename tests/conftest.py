import pathlib
from typing import cast

import pytest
from PIL import Image
from pytest_mock import MockerFixture

from askui.models.model_router import ModelRouter
from askui.tools.agent_os import AgentOs, Display, DisplaySize
from askui.tools.toolbox import AgentToolbox


@pytest.fixture
def path_fixtures() -> pathlib.Path:
    """Fixture providing the path to the fixtures directory."""
    return pathlib.Path().absolute() / "tests" / "fixtures"


@pytest.fixture
def path_fixtures_images(path_fixtures: pathlib.Path) -> pathlib.Path:
    """Fixture providing the path to the images directory."""
    return path_fixtures / "images"


@pytest.fixture
def path_fixtures_screenshots(path_fixtures: pathlib.Path) -> pathlib.Path:
    """Fixture providing the path to the screenshots directory."""
    return path_fixtures / "screenshots"


@pytest.fixture
def path_fixtures_pdf(path_fixtures: pathlib.Path) -> pathlib.Path:
    """Fixture providing the path to the pdf directory."""
    return path_fixtures / "pdf"


@pytest.fixture
def path_fixtures_dummy_pdf(path_fixtures_pdf: pathlib.Path) -> pathlib.Path:
    """Fixture providing the path to the dummy pdf."""
    return path_fixtures_pdf / "dummy.pdf"


@pytest.fixture
def path_fixtures_excel(path_fixtures: pathlib.Path) -> pathlib.Path:
    """Fixture providing the path to the excel directory."""
    return path_fixtures / "excel"


@pytest.fixture
def path_fixtures_dummy_excel(path_fixtures_excel: pathlib.Path) -> pathlib.Path:
    """Fixture providing the path to the dummy excel."""
    return path_fixtures_excel / "dummy.xlsx"


@pytest.fixture
def path_fixtures_docs(path_fixtures: pathlib.Path) -> pathlib.Path:
    """Fixture providing the path to the docs directory."""
    return path_fixtures / "docs"


@pytest.fixture
def path_fixtures_dummy_doc(path_fixtures_docs: pathlib.Path) -> pathlib.Path:
    """Fixture providing the path to the dummy doc."""
    return path_fixtures_docs / "dummy.docx"


@pytest.fixture
def github_login_screenshot(path_fixtures_screenshots: pathlib.Path) -> Image.Image:
    """Fixture providing the GitHub login screenshot."""
    screenshot_path = path_fixtures_screenshots / "macos__chrome__github_com__login.png"
    return Image.open(screenshot_path)


@pytest.fixture
def path_fixtures_github_com__icon(path_fixtures_images: pathlib.Path) -> pathlib.Path:
    """Fixture providing the path to the github com icon image."""
    return path_fixtures_images / "github_com__icon.png"


@pytest.fixture
def agent_os_mock(mocker: MockerFixture) -> AgentOs:
    """Fixture providing a mock agent os."""
    mock = mocker.MagicMock(spec=AgentOs)
    mock.retrieve_active_display.return_value = Display(
        id=1,
        size=DisplaySize(width=100, height=100),
    )
    mock.screenshot.return_value = Image.new("RGB", (100, 100), color="white")
    return cast("AgentOs", mock)


@pytest.fixture
def agent_toolbox_mock(agent_os_mock: AgentOs) -> AgentToolbox:
    """Fixture providing a mock agent toolbox."""
    return AgentToolbox(agent_os=agent_os_mock)


@pytest.fixture
def model_router_mock(mocker: MockerFixture) -> ModelRouter:
    """Fixture providing a mock model router."""
    mock = mocker.MagicMock(spec=ModelRouter)
    mock.locate.return_value = (100, 100)  # Return fixed point for all locate calls
    mock.get_inference.return_value = (
        "Mock response"  # Return fixed response for all get_inference calls
    )
    return cast("ModelRouter", mock)


@pytest.fixture(autouse=True)
def disable_telemetry() -> None:
    from askui.container import telemetry

    telemetry.set_processors([])


@pytest.fixture
def askui_logo_bmp(path_fixtures: pathlib.Path) -> Image.Image:
    """Fixture providing askui logo as BMP."""
    screenshot_path = path_fixtures / "images" / "logo.bmp"
    return Image.open(screenshot_path)
