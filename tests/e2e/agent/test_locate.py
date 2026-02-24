"""Tests for Agent.locate() with different locator types"""

import pathlib

import pytest
from PIL import Image as PILImage

from askui.agent import ComputerAgent
from askui.locators import AiElement, Element, Prompt, Text
from askui.locators.locators import Image
from askui.models.exceptions import ElementNotFoundError


class TestAgentLocate:
    """Test class for Agent.locate() method."""

    def test_locate_with_string_locator(
        self,
        vision_agent: ComputerAgent,
        github_login_screenshot: PILImage.Image,
    ) -> None:
        """Test locating elements using a simple string locator."""
        locator = "Forgot password?"
        x, y = vision_agent.locate(locator, github_login_screenshot)
        assert 450 <= x <= 570
        assert 190 <= y <= 260

    def test_locate_with_switch_class_locator(
        self, vision_agent: ComputerAgent, path_fixtures: pathlib.Path
    ) -> None:
        """Test locating elements using a class locator."""
        locator = Element("switch")
        x, y = vision_agent.locate(locator, path_fixtures / "images" / "switch.png")
        assert 340 <= x <= 400
        assert 270 <= y <= 460

    def test_locate_with_textfield_class_locator(
        self,
        vision_agent: ComputerAgent,
        github_login_screenshot: PILImage.Image,
    ) -> None:
        """Test locating elements using a class locator."""
        locator = Element("textfield")
        x, y = vision_agent.locate(locator, github_login_screenshot)
        assert 50 <= x <= 860 or 350 <= x <= 570
        assert 0 <= y <= 80 or 160 <= y <= 280

    def test_locate_with_unspecified_class_locator(
        self,
        vision_agent: ComputerAgent,
        github_login_screenshot: PILImage.Image,
    ) -> None:
        """Test locating elements using a class locator."""
        locator = Element()
        x, y = vision_agent.locate(locator, github_login_screenshot)
        assert 0 <= x <= github_login_screenshot.width
        assert 0 <= y <= github_login_screenshot.height

    def test_locate_with_description_locator(
        self,
        vision_agent: ComputerAgent,
        github_login_screenshot: PILImage.Image,
    ) -> None:
        """Test locating elements using a description locator."""
        locator = Prompt("Username textfield")
        x, y = vision_agent.locate(locator, github_login_screenshot)
        assert 350 <= x <= 570
        assert 160 <= y <= 230

    def test_locate_with_similar_text_locator(
        self,
        vision_agent: ComputerAgent,
        github_login_screenshot: PILImage.Image,
    ) -> None:
        """Test locating elements using a text locator."""
        locator = Text("Forgot password?")
        x, y = vision_agent.locate(locator, github_login_screenshot)
        assert 450 <= x <= 570
        assert 190 <= y <= 260

    def test_locate_with_typo_text_locator(
        self,
        vision_agent: ComputerAgent,
        github_login_screenshot: PILImage.Image,
    ) -> None:
        """Test locating elements using a text locator with a typo."""
        locator = Text("Forgot pasword", similarity_threshold=90)
        x, y = vision_agent.locate(locator, github_login_screenshot)
        assert 450 <= x <= 570
        assert 190 <= y <= 260

    def test_locate_with_exact_text_locator(
        self,
        vision_agent: ComputerAgent,
        github_login_screenshot: PILImage.Image,
    ) -> None:
        """Test locating elements using a text locator."""
        locator = Text("Forgot password?", match_type="exact")
        x, y = vision_agent.locate(locator, github_login_screenshot)
        assert 450 <= x <= 570
        assert 190 <= y <= 260

    def test_locate_with_regex_text_locator(
        self,
        vision_agent: ComputerAgent,
        github_login_screenshot: PILImage.Image,
    ) -> None:
        """Test locating elements using a text locator."""
        locator = Text(r"F.*?", match_type="regex")
        x, y = vision_agent.locate(locator, github_login_screenshot)
        assert 450 <= x <= 570
        assert 190 <= y <= 260

    def test_locate_with_contains_text_locator(
        self,
        vision_agent: ComputerAgent,
        github_login_screenshot: PILImage.Image,
    ) -> None:
        """Test locating elements using a text locator."""
        locator = Text("Forgot", match_type="contains")
        x, y = vision_agent.locate(locator, github_login_screenshot)
        assert 450 <= x <= 570
        assert 190 <= y <= 260

    def test_locate_with_image(
        self,
        vision_agent: ComputerAgent,
        github_login_screenshot: PILImage.Image,
        path_fixtures: pathlib.Path,
    ) -> None:
        """Test locating elements using image locator."""
        image_path = path_fixtures / "images" / "github_com__signin__button.png"
        image = PILImage.open(image_path)
        locator = Image(image=image)
        x, y = vision_agent.locate(locator, github_login_screenshot)
        assert 350 <= x <= 570
        assert 240 <= y <= 320

    def test_locate_with_image_and_custom_params(
        self,
        vision_agent: ComputerAgent,
        github_login_screenshot: PILImage.Image,
        path_fixtures: pathlib.Path,
    ) -> None:
        """Test locating elements using image locator with custom parameters."""
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
        x, y = vision_agent.locate(locator, github_login_screenshot)
        assert 350 <= x <= 570
        assert 240 <= y <= 320

    def test_locate_with_image_should_fail_when_threshold_is_too_high(
        self,
        vision_agent: ComputerAgent,
        github_login_screenshot: PILImage.Image,
        path_fixtures: pathlib.Path,
    ) -> None:
        """Test locating elements using image locator with custom parameters."""
        image_path = path_fixtures / "images" / "github_com__icon.png"
        image = PILImage.open(image_path)
        locator = Image(image=image, threshold=1.0, stop_threshold=1.0)
        with pytest.raises(ElementNotFoundError):
            vision_agent.locate(locator, github_login_screenshot)

    def test_locate_with_ai_element_locator(
        self,
        vision_agent: ComputerAgent,
        github_login_screenshot: PILImage.Image,
    ) -> None:
        """Test locating elements using an AI element locator."""
        locator = AiElement("github_com__icon")
        x, y = vision_agent.locate(locator, github_login_screenshot)
        assert 350 <= x <= 570
        assert 50 <= y <= 130

    def test_locate_with_ai_element_locator_should_fail_when_threshold_is_too_high(
        self,
        vision_agent: ComputerAgent,
        github_login_screenshot: PILImage.Image,
    ) -> None:
        """Test locating elements using image locator with custom parameters."""
        locator = AiElement("github_com__icon", threshold=1.0)
        with pytest.raises(ElementNotFoundError):
            vision_agent.locate(locator, github_login_screenshot)
