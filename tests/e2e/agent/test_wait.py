"""Tests for VisionAgent wait functionality."""

import time
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest
from PIL import Image as PILImage

from askui.agent import VisionAgent
from askui.locators import Element
from askui.models import ModelName
from askui.models.exceptions import WaitUntilError



@pytest.mark.parametrize(
    "model",
    [
        ModelName.ASKUI,
    ],
)
class TestVisionAgentWait:
    """Test class for VisionAgent wait functionality."""

    def test_wait_duration_float(self, vision_agent: VisionAgent, model: str) -> None:
        """Test waiting for a specific duration (float)."""
        start_time = time.time()
        wait_duration = 0.5

        vision_agent.wait(wait_duration)

        elapsed_time = time.time() - start_time
        # Allow small tolerance for timing
        assert elapsed_time >= wait_duration - 0.1
        assert elapsed_time <= wait_duration + 0.2

    def test_wait_duration_int(self, vision_agent: VisionAgent, model: str) -> None:
        """Test waiting for a specific duration (int)."""
        start_time = time.time()
        wait_duration = 1

        vision_agent.wait(wait_duration)

        elapsed_time = time.time() - start_time
        # Allow small tolerance for timing
        assert elapsed_time >= wait_duration - 0.1
        assert elapsed_time <= wait_duration + 0.2

    def test_wait_for_element_appear_success(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test waiting for an element to appear (successful case)."""
        locator = "Forgot password?"

        # Mock screenshot to return the image
        mock_screenshot = Mock(return_value=github_login_screenshot)
        vision_agent._agent_os.screenshot = mock_screenshot  # type: ignore[method-assign]

        # Should not raise an exception since element exists
        vision_agent.wait(locator, retries=3, delay=1, until_condition="appear", model=model)

        # Verify screenshot was called
        mock_screenshot.assert_called()

    def test_wait_for_element_appear_failure(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test waiting for an element to appear (failure case)."""
        locator = "Non-existent element"

        # Mock screenshot to return the image
        mock_screenshot = Mock(return_value=github_login_screenshot)
        vision_agent._agent_os.screenshot = mock_screenshot  # type: ignore[method-assign]

        # Should raise WaitUntilError since element doesn't exist
        with pytest.raises(WaitUntilError) as exc_info:
            vision_agent.wait(locator, retries=2, delay=1, until_condition="appear", model=model)

        assert "appear" in str(exc_info.value)
        mock_screenshot.assert_called()

    def test_wait_for_element_disappear_success(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test waiting for an element to disappear (successful case)."""
        locator = "Non-existent element"

        # Mock screenshot to return the image
        mock_screenshot = Mock(return_value=github_login_screenshot)
        vision_agent._agent_os.screenshot = mock_screenshot  # type: ignore[method-assign]

        # Should not raise an exception since element doesn't exist (already "disappeared")
        vision_agent.wait(locator, retries=2, delay=1, until_condition="disappear", model=model)

        mock_screenshot.assert_called()

    def test_wait_for_element_disappear_failure(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test waiting for an element to disappear (failure case)."""
        locator = "Forgot password?"

        # Mock screenshot to return the image
        mock_screenshot = Mock(return_value=github_login_screenshot)
        vision_agent._agent_os.screenshot = mock_screenshot  # type: ignore[method-assign]

        # Should raise WaitUntilError since element exists and won't disappear
        with pytest.raises(WaitUntilError) as exc_info:
            vision_agent.wait(locator, retries=2, delay=1, until_condition="disappear", model=model)

        assert "disappear" in str(exc_info.value)
        mock_screenshot.assert_called()

    def test_wait_with_locator_object(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test waiting with a Locator object."""
        locator = Element("textfield")

        # Mock screenshot to return the image
        mock_screenshot = Mock(return_value=github_login_screenshot)
        vision_agent._agent_os.screenshot = mock_screenshot  # type: ignore[method-assign]

        # Should not raise an exception since textfield exists
        vision_agent.wait(locator, retries=2, delay=1, until_condition="appear", model=model)

        mock_screenshot.assert_called()

    def test_wait_with_default_parameters(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test waiting with default parameters."""
        locator = "Forgot password?"

        # Mock screenshot to return the image
        mock_screenshot = Mock(return_value=github_login_screenshot)
        vision_agent._agent_os.screenshot = mock_screenshot  # type: ignore[method-assign]

        # Should use default retries=3, delay=1, until_condition="appear"
        vision_agent.wait(locator, model=model)

        mock_screenshot.assert_called()

    def test_wait_with_custom_retries_and_delay(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test waiting with custom retries and delay values."""
        locator = "Forgot password?"

        # Mock screenshot to return the image
        mock_screenshot = Mock(return_value=github_login_screenshot)
        vision_agent._agent_os.screenshot = mock_screenshot  # type: ignore[method-assign]

        start_time = time.time()
        vision_agent.wait(locator, retries=1, delay=2, until_condition="appear", model=model)
        elapsed_time = time.time() - start_time

        # Should complete quickly since element exists on first try
        assert elapsed_time < 1.0
        mock_screenshot.assert_called()

    def test_wait_with_custom_model(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test waiting with a custom model parameter."""
        locator = "Forgot password?"
        custom_model = "custom_model_name"

        # Mock screenshot to return the image
        mock_screenshot = Mock(return_value=github_login_screenshot)
        vision_agent._agent_os.screenshot = mock_screenshot  # type: ignore[method-assign]

        # Should not raise an exception
        vision_agent.wait(
            locator,
            retries=1,
            delay=1,
            until_condition="appear",
            model=custom_model
        )

        mock_screenshot.assert_called()

    @patch("time.sleep")
    def test_wait_disappear_timing(
        self,
        mock_sleep: Mock,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test that wait for disappear calls sleep with correct delay."""
        locator = "Forgot password?"
        delay = 2

        # Mock screenshot to return the image
        mock_screenshot = Mock(return_value=github_login_screenshot)
        vision_agent._agent_os.screenshot = mock_screenshot  # type: ignore[method-assign]

        # Should raise WaitUntilError and call sleep with correct delay
        with pytest.raises(WaitUntilError):
            vision_agent.wait(
                locator,
                retries=2,
                delay=delay,
                until_condition="disappear",
                model=model
            )

        # Verify sleep was called with the correct delay
        expected_calls = delay * (2 - 1)  # (retries - 1) * delay
        assert mock_sleep.call_count == 1
        mock_sleep.assert_called_with(delay)

    def test_wait_until_error_contains_correct_info(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test that WaitUntilError contains correct information."""
        locator = "Non-existent element"
        retries = 3
        delay = 1
        until_condition = "appear"

        # Mock screenshot to return the image
        mock_screenshot = Mock(return_value=github_login_screenshot)
        vision_agent._agent_os.screenshot = mock_screenshot  # type: ignore[method-assign]

        with pytest.raises(WaitUntilError) as exc_info:
            vision_agent.wait(
                locator,
                retries=retries,
                delay=delay,
                until_condition=until_condition,
                model=model
            )

        error = exc_info.value
        # Verify error contains the expected information
        assert locator in str(error)
        assert until_condition in str(error)

    def test_wait_zero_retries(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        model: str,
    ) -> None:
        """Test waiting with zero retries."""
        locator = "Non-existent element"

        # Mock screenshot to return the image
        mock_screenshot = Mock(return_value=github_login_screenshot)
        vision_agent._agent_os.screenshot = mock_screenshot  # type: ignore[method-assign]

        # Should fail immediately with 0 retries
        with pytest.raises(WaitUntilError):
            vision_agent.wait(
                locator,
                retries=0,
                delay=1,
                until_condition="appear",
                model=model
            )
