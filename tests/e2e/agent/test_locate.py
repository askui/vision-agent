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
class TestVisionAgentLocate:
    """Test class for VisionAgent.locate() method."""

    def test_locate_with_string_locator(self, vision_agent: VisionAgent, github_login_screenshot: Image.Image, model_name: str) -> None:
        """Test locating elements using a simple string locator."""
        locator = "Forgot password?"
        x, y = vision_agent.locate(locator, github_login_screenshot, model_name=model_name)
        assert 450 <= x <= 570
        assert 190 <= y <= 260

    def test_locate_with_textfield_class_locator(self, vision_agent: VisionAgent, github_login_screenshot: Image.Image, model_name: str) -> None:
        """Test locating elements using a class locator."""
        locator = Class("textfield")
        x, y = vision_agent.locate(locator, github_login_screenshot, model_name=model_name)
        assert 50 <= x <= 860 or 350 <= x <= 570 or 350 <= x <= 570
        assert 0 <= y <= 80 or 210 <= y <= 280 or 160 <= y <= 230
        
    def test_locate_with_unspecified_class_locator(self, vision_agent: VisionAgent, github_login_screenshot: Image.Image, model_name: str) -> None:
        """Test locating elements using a class locator."""
        locator = Class()
        x, y = vision_agent.locate(locator, github_login_screenshot, model_name=model_name)
        assert 0 <= x <= github_login_screenshot.width
        assert 0 <= y <= github_login_screenshot.height

    def test_locate_with_description_locator(self, vision_agent: VisionAgent, github_login_screenshot: Image.Image, model_name: str) -> None:
        """Test locating elements using a description locator."""
        locator = Description("Username textfield")
        x, y = vision_agent.locate(locator, github_login_screenshot, model_name=model_name)
        assert 350 <= x <= 570
        assert 160 <= y <= 230

    def test_locate_with_similar_text_locator(self, vision_agent: VisionAgent, github_login_screenshot: Image.Image, model_name: str) -> None:
        """Test locating elements using a text locator."""
        locator = Text("Forgot password?")
        x, y = vision_agent.locate(locator, github_login_screenshot, model_name=model_name)
        assert 450 <= x <= 570
        assert 190 <= y <= 260
        
    def test_locate_with_typo_text_locator(self, vision_agent: VisionAgent, github_login_screenshot: Image.Image, model_name: str) -> None:
        """Test locating elements using a text locator with a typo."""
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


@pytest.mark.parametrize("model_name", [
    "askui",
    pytest.param("anthropic-claude-3-5-sonnet-20241022", marks=pytest.mark.skip(reason="Relations not supported by this model")),
])
class TestVisionAgentLocateWithRelations:
    """Test class for VisionAgent.locate() method with relations."""

    def test_locate_with_above_relation(self, vision_agent: VisionAgent, github_login_screenshot: Image.Image, model_name: str) -> None:
        """Test locating elements using above_of relation."""
        locator = Text("Sign in").above_of(Text("Password"))
        x, y = vision_agent.locate(locator, github_login_screenshot, model_name=model_name)
        assert 350 <= x <= 570
        assert 120 <= y <= 150

    def test_locate_with_below_relation(self, vision_agent: VisionAgent, github_login_screenshot: Image.Image, model_name: str) -> None:
        """Test locating elements using below_of relation."""
        locator = Text("Password").below_of(Text("Username"))
        x, y = vision_agent.locate(locator, github_login_screenshot, model_name=model_name)
        assert 350 <= x <= 450
        assert 190 <= y <= 220

    def test_locate_with_right_relation(self, vision_agent: VisionAgent, github_login_screenshot: Image.Image, model_name: str) -> None:
        """Test locating elements using right_of relation."""
        locator = Text("Forgot password?").right_of(Text("Password"))
        x, y = vision_agent.locate(locator, github_login_screenshot, model_name=model_name)
        assert 450 <= x <= 570
        assert 190 <= y <= 260
        
    def test_locate_with_left_relation(self, vision_agent: VisionAgent, github_login_screenshot: Image.Image, model_name: str) -> None:
        """Test locating elements using left_of relation."""
        locator = Text("Username").left_of(Text("Forgot password?"))
        x, y = vision_agent.locate(locator, github_login_screenshot, model_name=model_name)
        assert 350 <= x <= 450
        assert 150 <= y <= 180
        
    def test_locate_with_containing_relation(self, vision_agent: VisionAgent, github_login_screenshot: Image.Image, model_name: str) -> None:
        """Test locating elements using containing relation."""
        locator = Class().containing(Text("Sign in"))
        x, y = vision_agent.locate(locator, github_login_screenshot, model_name=model_name)
        assert 350 <= x <= 570
        assert 280 <= y <= 330
        
    def test_locate_with_inside_relation(self, vision_agent: VisionAgent, github_login_screenshot: Image.Image, model_name: str) -> None:
        """Test locating elements using inside_of relation."""
        locator = Text("Sign in").inside_of(Class())
        x, y = vision_agent.locate(locator, github_login_screenshot, model_name=model_name)
        assert 430 <= x <= 490
        assert 300 <= y <= 320
        
    def test_locate_with_nearest_to_relation(self, vision_agent: VisionAgent, github_login_screenshot: Image.Image, model_name: str) -> None:
        """Test locating elements using nearest_to relation."""
        locator = Class("textfield").nearest_to(Text("Password"))
        x, y = vision_agent.locate(locator, github_login_screenshot, model_name=model_name)
        assert 350 <= x <= 570
        assert 210 <= y <= 280
        
    def test_locate_with_and_relation(self, vision_agent: VisionAgent, github_login_screenshot: Image.Image, model_name: str) -> None:
        """Test locating elements using and_ relation."""
        locator = Text("Sign in").and_(Class())
        x, y = vision_agent.locate(locator, github_login_screenshot, model_name=model_name)
        assert 430 <= x <= 490
        assert 300 <= y <= 320
        
    def test_locate_with_or_relation(self, vision_agent: VisionAgent, github_login_screenshot: Image.Image, model_name: str) -> None:
        """Test locating elements using or_ relation."""
        locator = Text("Sign in").or_(Text("Sign up"))
        x, y = vision_agent.locate(locator, github_login_screenshot, model_name=model_name)
        assert 430 <= x <= 570
        assert 300 <= y <= 350
        
    def test_locate_with_relation_index(self, vision_agent: VisionAgent, github_login_screenshot: Image.Image, model_name: str) -> None:
        """Test locating elements using relation with index."""
        locator = Class("textfield").below_of(Text("Username"), index=1)
        x, y = vision_agent.locate(locator, github_login_screenshot, model_name=model_name)
        assert 350 <= x <= 570
        assert 210 <= y <= 280
        
    def test_locate_with_relation_reference_point(self, vision_agent: VisionAgent, github_login_screenshot: Image.Image, model_name: str) -> None:
        """Test locating elements using relation with reference point."""
        locator = Class("textfield").right_of(Text("Username"), reference_point="center")
        x, y = vision_agent.locate(locator, github_login_screenshot, model_name=model_name)
        assert 480 <= x <= 570
        assert 160 <= y <= 230
        
    def test_locate_with_chained_relations(self, vision_agent: VisionAgent, github_login_screenshot: Image.Image, model_name: str) -> None:
        """Test locating elements using chained relations."""
        locator = Text("Sign in").below_of(Text("Password")).below_of(Text("Username"))
        x, y = vision_agent.locate(locator, github_login_screenshot, model_name=model_name)
        assert 430 <= x <= 490
        assert 300 <= y <= 320
        
    def test_locate_with_complex_chained_relations(self, vision_agent: VisionAgent, github_login_screenshot: Image.Image, model_name: str) -> None:
        """Test locating elements using complex chained relations."""
        locator = Text("Forgot password?").right_of(Text("Password").below_of(Text("Username")))
        x, y = vision_agent.locate(locator, github_login_screenshot, model_name=model_name)
        assert 450 <= x <= 570
        assert 190 <= y <= 260
        
    def test_locate_with_relation_different_locator_types(self, vision_agent: VisionAgent, github_login_screenshot: Image.Image, model_name: str) -> None:
        """Test locating elements using relation with different locator types."""
        locator = Text("Sign in").below_of(Class("textfield"))
        x, y = vision_agent.locate(locator, github_login_screenshot, model_name=model_name)
        assert 430 <= x <= 490
        assert 300 <= y <= 320
        
    def test_locate_with_description_and_relation(self, vision_agent: VisionAgent, github_login_screenshot: Image.Image, model_name: str) -> None:
        """Test locating elements using description with relation."""
        locator = Description("Sign in button").below_of(Description("Password field"))
        x, y = vision_agent.locate(locator, github_login_screenshot, model_name=model_name)
        assert 430 <= x <= 490
        assert 300 <= y <= 320
