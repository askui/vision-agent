"""Tests for VisionAgent.locate() with different AskUI models"""

import pytest
from PIL import Image as PILImage

from askui.agent import VisionAgent
from askui.exceptions import AutomationError
from askui.locators import AiElement, Prompt, Text
from askui.models.models import LocateModel


class TestVisionAgentLocateWithDifferentModels:
    """Test class for VisionAgent.locate() method with different AskUI models."""

    def test_locate_with_pta_model(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        pta_locate_model: LocateModel,
    ) -> None:
        """Test locating elements using PTA model with description locator."""
        locator = "Username textfield"
        x, y = vision_agent.locate(
            locator,
            github_login_screenshot,
            locate_model=pta_locate_model,
        )
        assert 350 <= x <= 570
        assert 160 <= y <= 230

    def test_locate_with_pta_model_fails_with_wrong_locator(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        pta_locate_model: LocateModel,
    ) -> None:
        """Test that PTA model fails with wrong locator type."""
        locator = Text("Username textfield")
        with pytest.raises(AutomationError):
            vision_agent.locate(
                locator, github_login_screenshot, locate_model=pta_locate_model
            )

    def test_locate_with_ocr_model(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        ocr_locate_model: LocateModel,
    ) -> None:
        """Test locating elements using OCR model with text locator."""
        locator = "Forgot password?"
        x, y = vision_agent.locate(
            locator, github_login_screenshot, locate_model=ocr_locate_model
        )
        assert 450 <= x <= 570
        assert 190 <= y <= 260

    def test_locate_with_ocr_model_fails_with_wrong_locator(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        ocr_locate_model: LocateModel,
    ) -> None:
        """Test that OCR model fails with wrong locator type."""
        locator = Prompt("Forgot password?")
        with pytest.raises(AutomationError):
            vision_agent.locate(
                locator, github_login_screenshot, locate_model=ocr_locate_model
            )

    def test_locate_with_ai_element_model(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        ai_element_locate_model: LocateModel,
    ) -> None:
        """Test locating elements using AI element model."""
        locator = "github_com__signin__button"
        x, y = vision_agent.locate(
            locator, github_login_screenshot, locate_model=ai_element_locate_model
        )
        assert 350 <= x <= 570
        assert 240 <= y <= 320

    def test_locate_with_ai_element_model_fails_with_wrong_locator(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        ai_element_locate_model: LocateModel,
    ) -> None:
        """Test that AI element model fails with wrong locator type."""
        locator = Text("Sign in")
        with pytest.raises(AutomationError):
            vision_agent.locate(
                locator, github_login_screenshot, locate_model=ai_element_locate_model
            )

    def test_locate_with_combo_model_description_first(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        combo_locate_model: LocateModel,
    ) -> None:
        """Test locating elements using combo model with description locator."""
        locator = "Username textfield"
        x, y = vision_agent.locate(
            locator, github_login_screenshot, locate_model=combo_locate_model
        )
        assert 350 <= x <= 570
        assert 160 <= y <= 230

    def test_locate_with_combo_model_text_fallback(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        combo_locate_model: LocateModel,
    ) -> None:
        """Test locating elements using combo model with text locator as fallback."""
        locator = "Forgot password?"
        x, y = vision_agent.locate(
            locator, github_login_screenshot, locate_model=combo_locate_model
        )
        assert 450 <= x <= 570
        assert 190 <= y <= 260

    def test_locate_with_combo_model_fails_with_wrong_locator(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        combo_locate_model: LocateModel,
    ) -> None:
        """Test that combo model fails with wrong locator type."""
        locator = AiElement("github_com__signin__button")
        with pytest.raises(AutomationError):
            vision_agent.locate(
                locator, github_login_screenshot, locate_model=combo_locate_model
            )
