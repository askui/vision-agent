"""Tests for VisionAgent.locate() with different locator types and models"""

import pathlib

import pytest
from PIL import Image as PILImage

from askui.agent import VisionAgent
from askui.exceptions import ElementNotFoundError
from askui.locators import (
    AiElement,
    Element,
    Prompt,
    Text,
)
from askui.locators.locators import Image
from askui.models import ModelName


@pytest.mark.parametrize(
    "model",
    [
        ModelName.ASKUI,
        ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022,
    ],
)
class TestVisionAgentLocate:
    """Test class for VisionAgent.locate() method."""

    def test_locate_with_string_locator(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test locating elements using a simple string locator."""
        locator = "Forgot password?"
        x, y = vision_agent.locate(locator, github_login_screenshot, model=model)
        assert 450 <= x <= 570
        assert 190 <= y <= 260

    def test_locate_with_textfield_class_locator(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test locating elements using a class locator."""
        locator = Element("textfield")
        x, y = vision_agent.locate(locator, github_login_screenshot, model=model)
        assert 50 <= x <= 860 or 350 <= x <= 570
        assert 0 <= y <= 80 or 160 <= y <= 280

    def test_locate_with_unspecified_class_locator(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test locating elements using a class locator."""
        locator = Element()
        x, y = vision_agent.locate(locator, github_login_screenshot, model=model)
        assert 0 <= x <= github_login_screenshot.width
        assert 0 <= y <= github_login_screenshot.height

    def test_locate_with_description_locator(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test locating elements using a description locator."""
        locator = Prompt("Username textfield")
        x, y = vision_agent.locate(locator, github_login_screenshot, model=model)
        assert 350 <= x <= 570
        assert 160 <= y <= 230

    def test_locate_with_similar_text_locator(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test locating elements using a text locator."""
        locator = Text("Forgot password?")
        x, y = vision_agent.locate(locator, github_login_screenshot, model=model)
        assert 450 <= x <= 570
        assert 190 <= y <= 260

    def test_locate_with_typo_text_locator(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test locating elements using a text locator with a typo."""
        locator = Text("Forgot pasword", similarity_threshold=90)
        x, y = vision_agent.locate(locator, github_login_screenshot, model=model)
        assert 450 <= x <= 570
        assert 190 <= y <= 260

    def test_locate_with_exact_text_locator(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test locating elements using a text locator."""
        locator = Text("Forgot password?", match_type="exact")
        x, y = vision_agent.locate(locator, github_login_screenshot, model=model)
        assert 450 <= x <= 570
        assert 190 <= y <= 260

    def test_locate_with_regex_text_locator(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test locating elements using a text locator."""
        locator = Text(r"F.*?", match_type="regex")
        x, y = vision_agent.locate(locator, github_login_screenshot, model=model)
        assert 450 <= x <= 570
        assert 190 <= y <= 260

    def test_locate_with_contains_text_locator(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test locating elements using a text locator."""
        locator = Text("Forgot", match_type="contains")
        x, y = vision_agent.locate(locator, github_login_screenshot, model=model)
        assert 450 <= x <= 570
        assert 190 <= y <= 260

    def test_locate_with_image(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
        path_fixtures: pathlib.Path,
    ) -> None:
        """Test locating elements using image locator."""
        if model in [ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022]:
            pytest.skip("Skipping test for Anthropic model because not supported yet")
        image_path = path_fixtures / "images" / "github_com__signin__button.png"
        image = PILImage.open(image_path)
        locator = Image(image=image)
        x, y = vision_agent.locate(locator, github_login_screenshot, model=model)
        assert 350 <= x <= 570
        assert 240 <= y <= 320

    def test_locate_with_image_and_custom_params(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
        path_fixtures: pathlib.Path,
    ) -> None:
        """Test locating elements using image locator with custom parameters."""
        if model in [ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022]:
            pytest.skip("Skipping test for Anthropic model because not supported yet")
        image_path = path_fixtures / "images" / "github_com__signin__button.png"
        image = PILImage.open(image_path)
        locator = Image(
            image=image,
            threshold=0.7,
            stop_threshold=0.95,
            rotation_degree_per_step=45,
            image_compare_format="RGB",
            name="Sign in button",
        )
        x, y = vision_agent.locate(locator, github_login_screenshot, model=model)
        assert 350 <= x <= 570
        assert 240 <= y <= 320

    def test_locate_with_image_should_fail_when_threshold_is_too_high(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
        path_fixtures: pathlib.Path,
    ) -> None:
        """Test locating elements using image locator with custom parameters."""
        if model in [ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022]:
            pytest.skip("Skipping test for Anthropic model because not supported yet")
        image_path = path_fixtures / "images" / "github_com__icon.png"
        image = PILImage.open(image_path)
        locator = Image(image=image, threshold=1.0, stop_threshold=1.0)
        with pytest.raises(ElementNotFoundError):
            vision_agent.locate(locator, github_login_screenshot, model=model)

    def test_locate_with_ai_element_locator(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test locating elements using an AI element locator."""
        if model in [ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022]:
            pytest.skip("Skipping test for Anthropic model because not supported yet")
        locator = AiElement("github_com__icon")
        x, y = vision_agent.locate(locator, github_login_screenshot, model=model)
        assert 350 <= x <= 570
        assert 50 <= y <= 130

    def test_locate_with_ai_element_locator_should_fail_when_threshold_is_too_high(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test locating elements using image locator with custom parameters."""
        if model in [ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022]:
            pytest.skip("Skipping test for Anthropic model because not supported yet")
        locator = AiElement("github_com__icon", threshold=1.0)
        with pytest.raises(ElementNotFoundError):
            vision_agent.locate(locator, github_login_screenshot, model=model)
