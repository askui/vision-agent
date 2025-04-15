"""Tests for VisionAgent.locate() with different AskUI models"""

import pytest
from PIL import Image as PILImage

from askui.agent import VisionAgent
from askui.locators import (
    Description,
    Text,
    AiElement,
)
from askui.exceptions import AutomationError


class TestVisionAgentLocateWithDifferentModels:
    """Test class for VisionAgent.locate() method with different AskUI models."""

    @pytest.mark.parametrize("model_name", ["askui-pta"])
    def test_locate_with_pta_model(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model_name: str,
    ) -> None:
        """Test locating elements using PTA model with description locator."""
        locator = "Username textfield"
        x, y = vision_agent.locate(
            locator, github_login_screenshot, model_name=model_name
        )
        assert 350 <= x <= 570
        assert 160 <= y <= 230

    @pytest.mark.parametrize("model_name", ["askui-pta"])
    def test_locate_with_pta_model_fails_with_wrong_locator(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model_name: str,
    ) -> None:
        """Test that PTA model fails with wrong locator type."""
        locator = Text("Username textfield")
        with pytest.raises(AutomationError):
            vision_agent.locate(locator, github_login_screenshot, model_name=model_name)

    @pytest.mark.parametrize("model_name", ["askui-ocr"])
    def test_locate_with_ocr_model(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model_name: str,
    ) -> None:
        """Test locating elements using OCR model with text locator."""
        locator = "Forgot password?"
        x, y = vision_agent.locate(
            locator, github_login_screenshot, model_name=model_name
        )
        assert 450 <= x <= 570
        assert 190 <= y <= 260

    @pytest.mark.parametrize("model_name", ["askui-ocr"])
    def test_locate_with_ocr_model_fails_with_wrong_locator(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model_name: str,
    ) -> None:
        """Test that OCR model fails with wrong locator type."""
        locator = Description("Forgot password?")
        with pytest.raises(AutomationError):
            vision_agent.locate(locator, github_login_screenshot, model_name=model_name)

    @pytest.mark.parametrize("model_name", ["askui-ai-element"])
    def test_locate_with_ai_element_model(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model_name: str,
    ) -> None:
        """Test locating elements using AI element model."""
        locator = "github_com__signin__button"
        x, y = vision_agent.locate(
            locator, github_login_screenshot, model_name=model_name
        )
        assert 350 <= x <= 570
        assert 240 <= y <= 320

    @pytest.mark.parametrize("model_name", ["askui-ai-element"])
    def test_locate_with_ai_element_model_fails_with_wrong_locator(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model_name: str,
    ) -> None:
        """Test that AI element model fails with wrong locator type."""
        locator = Text("Sign in")
        with pytest.raises(AutomationError):
            vision_agent.locate(locator, github_login_screenshot, model_name=model_name)

    @pytest.mark.parametrize("model_name", ["askui-combo"])
    def test_locate_with_combo_model_description_first(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model_name: str,
    ) -> None:
        """Test locating elements using combo model with description locator."""
        locator = "Username textfield"
        x, y = vision_agent.locate(
            locator, github_login_screenshot, model_name=model_name
        )
        assert 350 <= x <= 570
        assert 160 <= y <= 230

    @pytest.mark.parametrize("model_name", ["askui-combo"])
    def test_locate_with_combo_model_text_fallback(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model_name: str,
    ) -> None:
        """Test locating elements using combo model with text locator as fallback."""
        locator = "Forgot password?"
        x, y = vision_agent.locate(
            locator, github_login_screenshot, model_name=model_name
        )
        assert 450 <= x <= 570
        assert 190 <= y <= 260

    @pytest.mark.parametrize("model_name", ["askui-combo"])
    def test_locate_with_combo_model_fails_with_wrong_locator(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model_name: str,
    ) -> None:
        """Test that combo model fails with wrong locator type."""
        locator = AiElement("github_com__signin__button")
        with pytest.raises(AutomationError):
            vision_agent.locate(locator, github_login_screenshot, model_name=model_name)
