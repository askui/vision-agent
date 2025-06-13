from typing import cast
from unittest.mock import MagicMock

import pytest
from PIL import Image as PILImage
from pytest_mock import MockerFixture

from askui.models.openrouter.model import OpenRouterModel
from askui.models.openrouter.settings import OpenRouterSettings
from askui.utils.image_utils import ImageSource


@pytest.fixture(autouse=True)
def set_env_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPEN_ROUTER_API_KEY", "test_openrouter_api_key")


@pytest.fixture
def settings() -> OpenRouterSettings:
    return OpenRouterSettings(
        model="test-model",
    )


@pytest.fixture
def mock_openai_client(mocker: MockerFixture) -> MagicMock:
    return cast("MagicMock", mocker.MagicMock())


@pytest.fixture
def openrouter_model(
    settings: OpenRouterSettings, mock_openai_client: MagicMock
) -> OpenRouterModel:
    return OpenRouterModel(settings=settings, client=mock_openai_client)


@pytest.fixture
def image_source_github_login_screenshot(
    github_login_screenshot: PILImage.Image,
) -> ImageSource:
    return ImageSource(root=github_login_screenshot)
