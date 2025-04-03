"""Tests for VisionAgent.locate() with different locator types and models"""
import pathlib
import pytest
from PIL import Image

from askui.agent import VisionAgent
from askui.models.locators import (
    Description, 
    Class, 
    Text, 
)

@pytest.fixture
def vision_agent() -> VisionAgent:
    """Fixture providing a VisionAgent instance."""
    return VisionAgent(
        enable_askui_controller=False,
        enable_report=False
    )

@pytest.fixture
def path_fixtures() -> pathlib.Path:
    """Fixture providing the path to the fixtures directory."""
    return pathlib.Path().absolute() / "tests" / "fixtures"

@pytest.fixture
def github_login_screenshot(path_fixtures: pathlib.Path) -> Image.Image:
    """Fixture providing the GitHub login screenshot."""
    screenshot_path = path_fixtures / "screenshots" / "macos__chrome__github_com__login.png"
    return Image.open(screenshot_path)


@pytest.mark.parametrize("model_name", [
    "askui",
    "anthropic-claude-3-5-sonnet-20241022",
])
@pytest.mark.xfail(
    reason="Location may be inconsistent depending on the model used",
)
class TestVisionAgentLocate:
    """Test class for VisionAgent.locate() method."""

    def test_locate_with_string_locator(self, vision_agent: VisionAgent, github_login_screenshot: Image.Image, model_name: str) -> None:
        """Test locating elements using a simple string locator."""
        locator = "Forgot password?"
        x, y = vision_agent.locate(locator, github_login_screenshot, model_name=model_name)
        assert 450 <= x <= 570
        assert 190 <= y <= 260

    def test_locate_with_class_locator(self, vision_agent: VisionAgent, github_login_screenshot: Image.Image, model_name: str) -> None:
        """Test locating elements using a class locator."""
        locator = Class("textfield")
        x, y = vision_agent.locate(locator, github_login_screenshot, model_name=model_name)
        assert 50 <= x <= 860 or 350 <= x <= 570 or 350 <= x <= 570
        assert 0 <= y <= 80 or 210 <= y <= 280 or 160 <= y <= 230

    def test_locate_with_description_locator(self, vision_agent: VisionAgent, github_login_screenshot: Image.Image, model_name: str) -> None:
        """Test locating elements using a description locator."""
        locator = Description("Green sign in button")
        x, y = vision_agent.locate(locator, github_login_screenshot, model_name=model_name)
        assert 350 <= x <= 570
        assert 240 <= y <= 310

    def test_locate_with_similar_text_locator(self, vision_agent: VisionAgent, github_login_screenshot: Image.Image, model_name: str) -> None:
        """Test locating elements using a text locator."""
        locator = Text("Forgot password?")
        x, y = vision_agent.locate(locator, github_login_screenshot, model_name=model_name)
        assert 450 <= x <= 570
        assert 190 <= y <= 260
        
    def test_locate_with_similar_text_locator(self, vision_agent: VisionAgent, github_login_screenshot: Image.Image, model_name: str) -> None:
        """Test locating elements using a text locator."""
        locator = Text("Forgot pasword", similarity_threshold=90)
        x, y = vision_agent.locate(locator, github_login_screenshot, model_name=model_name)
        assert 450 <= x <= 570
        assert 190 <= y <= 260

    def test_locate_with_exact_text_locator(self, vision_agent: VisionAgent, github_login_screenshot: Image.Image, model_name: str) -> None:
        """Test locating elements using a text locator."""
        locator = Text("Forgot password?", match_type="exact")
        x, y = vision_agent.locate(locator, github_login_screenshot, model_name=model_name)
        assert 450 <= x <= 570
        assert 190 <= y <= 260

    def test_locate_with_regex_text_locator(self, vision_agent: VisionAgent, github_login_screenshot: Image.Image, model_name: str) -> None:
        """Test locating elements using a text locator."""
        locator = Text(r"F.*?", match_type="regex")
        x, y = vision_agent.locate(locator, github_login_screenshot, model_name=model_name)
        assert 450 <= x <= 570
        assert 190 <= y <= 260

    def test_locate_with_contains_text_locator(self, vision_agent: VisionAgent, github_login_screenshot: Image.Image, model_name: str) -> None:
        """Test locating elements using a text locator."""
        locator = Text("Forgot", match_type="contains")
        x, y = vision_agent.locate(locator, github_login_screenshot, model_name=model_name)
        assert 450 <= x <= 570
        assert 190 <= y <= 260
