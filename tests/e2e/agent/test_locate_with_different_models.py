"""Tests for Agent.locate() with different AskUI models"""

import pytest
from PIL import Image as PILImage

from askui.agent import ComputerAgent
from askui.exceptions import AutomationError
from askui.locators import AiElement, Prompt, Text


class TestAgentLocateWithDifferentModels:
    """Test class for Agent.locate() method with different AskUI models."""

    def test_locate_with_pta_model(
        self,
        agent_with_pta_model: ComputerAgent,
        github_login_screenshot: PILImage.Image,
    ) -> None:
        """Test locating elements using PTA model with description locator."""
        locator = "Username textfield"
        x, y = agent_with_pta_model.locate(
            locator,
            github_login_screenshot,
        )
        assert 350 <= x <= 570
        assert 160 <= y <= 230

    def test_locate_with_pta_model_fails_with_wrong_locator(
        self,
        agent_with_pta_model: ComputerAgent,
        github_login_screenshot: PILImage.Image,
    ) -> None:
        """Test that PTA model fails with wrong locator type."""
        locator = Text("Username textfield")
        with pytest.raises(AutomationError):
            agent_with_pta_model.locate(locator, github_login_screenshot)

    def test_locate_with_ocr_model(
        self,
        agent_with_ocr_model: ComputerAgent,
        github_login_screenshot: PILImage.Image,
    ) -> None:
        """Test locating elements using OCR model with text locator."""
        locator = "Forgot password?"
        x, y = agent_with_ocr_model.locate(locator, github_login_screenshot)
        assert 450 <= x <= 570
        assert 190 <= y <= 260

    def test_locate_with_ocr_model_fails_with_wrong_locator(
        self,
        agent_with_ocr_model: ComputerAgent,
        github_login_screenshot: PILImage.Image,
    ) -> None:
        """Test that OCR model fails with wrong locator type."""
        locator = Prompt("Forgot password?")
        with pytest.raises(AutomationError):
            agent_with_ocr_model.locate(locator, github_login_screenshot)

    def test_locate_with_ai_element_model(
        self,
        agent_with_ai_element_model: ComputerAgent,
        github_login_screenshot: PILImage.Image,
    ) -> None:
        """Test locating elements using AI element model."""
        locator = "github_com__signin__button"
        x, y = agent_with_ai_element_model.locate(locator, github_login_screenshot)
        assert 350 <= x <= 570
        assert 240 <= y <= 320

    def test_locate_with_ai_element_model_fails_with_wrong_locator(
        self,
        agent_with_ai_element_model: ComputerAgent,
        github_login_screenshot: PILImage.Image,
    ) -> None:
        """Test that AI element model fails with wrong locator type."""
        locator = Text("Sign in")
        with pytest.raises(AutomationError):
            agent_with_ai_element_model.locate(locator, github_login_screenshot)

    def test_locate_with_combo_model_description_first(
        self,
        agent_with_combo_model: ComputerAgent,
        github_login_screenshot: PILImage.Image,
    ) -> None:
        """Test locating elements using combo model with description locator."""
        locator = "Username textfield"
        x, y = agent_with_combo_model.locate(locator, github_login_screenshot)
        assert 350 <= x <= 570
        assert 160 <= y <= 230

    def test_locate_with_combo_model_text_fallback(
        self,
        agent_with_combo_model: ComputerAgent,
        github_login_screenshot: PILImage.Image,
    ) -> None:
        """Test locating elements using combo model with text locator as fallback."""
        locator = "Forgot password?"
        x, y = agent_with_combo_model.locate(locator, github_login_screenshot)
        assert 450 <= x <= 570
        assert 190 <= y <= 260

    def test_locate_with_combo_model_fails_with_wrong_locator(
        self,
        agent_with_combo_model: ComputerAgent,
        github_login_screenshot: PILImage.Image,
    ) -> None:
        """Test that combo model fails with wrong locator type."""
        locator = AiElement("github_com__signin__button")
        with pytest.raises(AutomationError):
            agent_with_combo_model.locate(locator, github_login_screenshot)
