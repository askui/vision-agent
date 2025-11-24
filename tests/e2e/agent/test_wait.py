# mypy: disable-error-code="method-assign"
"""Tests for VisionAgent wait functionality."""

import time
from unittest.mock import Mock

import pytest
from PIL import Image as PILImage
from pydantic import ValidationError

from askui.agent import VisionAgent
from askui.locators import Element
from askui.models.exceptions import WaitUntilError


class TestVisionAgentWait:
    """Test class for VisionAgent wait functionality."""

    def test_wait_duration_float(self, vision_agent: VisionAgent) -> None:
        """Test waiting for a specific duration (float)."""
        start_time = time.time()
        wait_duration = 0.5

        vision_agent.wait(wait_duration)

        elapsed_time = time.time() - start_time
        # Allow small tolerance for timing
        assert elapsed_time >= wait_duration - 0.1
        assert elapsed_time <= wait_duration + 0.2

    def test_wait_duration_int(self, vision_agent: VisionAgent) -> None:
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
        white_page_screenshot: PILImage.Image,
    ) -> None:
        """Test waiting for an element to appear (successful case)."""
        locator = "Forgot password?"

        # Mock screenshot to return the image where element exists
        mock_screenshot = Mock(
            side_effect=[white_page_screenshot, github_login_screenshot]
        )
        vision_agent._agent_os.screenshot = mock_screenshot
        vision_agent._model_router.locate = Mock(
            wraps=vision_agent._model_router.locate
        )

        # Should not raise an exception since element exists
        vision_agent.wait(locator, retry_count=3, delay=0.1, until_condition="appear")

        # Verify locate was called
        assert vision_agent._model_router.locate.call_count == 2

    def test_wait_for_element_appear_failure(
        self, vision_agent: VisionAgent, white_page_screenshot: PILImage.Image
    ) -> None:
        """Test waiting for an element to appear (failure case)."""
        locator = "Forgot password?"

        # Mock screenshot to return white page where element doesn't exist
        mock_screenshot = Mock(return_value=white_page_screenshot)
        vision_agent._agent_os.screenshot = mock_screenshot
        vision_agent._model_router.locate = Mock(
            wraps=vision_agent._model_router.locate
        )

        # Should raise WaitUntilError since element doesn't exist
        with pytest.raises(WaitUntilError) as exc_info:
            vision_agent.wait(
                locator, retry_count=2, delay=0.1, until_condition="appear"
            )

        assert (
            "Wait until condition 'appear' not met for locator: 'text similar to "
            '"Forgot password?" (similarity >= 70%)\' after 2 retries with 0.1 '
            "seconds delay" == str(exc_info.value)
        )
        assert vision_agent._model_router.locate.call_count == 2

    def test_wait_for_element_disappear_success(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        white_page_screenshot: PILImage.Image,
    ) -> None:
        """Test waiting for an element to disappear (successful case)."""
        locator = "Forgot password?"

        # Mock screenshot to first show element exists, then show it's gone
        mock_screenshot = Mock(
            side_effect=[github_login_screenshot, white_page_screenshot]
        )
        vision_agent._agent_os.screenshot = mock_screenshot
        vision_agent._model_router.locate = Mock(
            wraps=vision_agent._model_router.locate
        )

        # Should not raise an exception since element disappears
        vision_agent.wait(
            locator, retry_count=2, delay=0.1, until_condition="disappear"
        )

        assert vision_agent._model_router.locate.call_count == 2

    def test_wait_for_element_disappear_failure(
        self, vision_agent: VisionAgent, github_login_screenshot: PILImage.Image
    ) -> None:
        """Test waiting for an element to disappear (failure case)."""
        locator = "Forgot password?"

        # Mock screenshot to always show the element exists
        mock_screenshot = Mock(return_value=github_login_screenshot)
        vision_agent._agent_os.screenshot = mock_screenshot
        vision_agent._model_router.locate = Mock(
            wraps=vision_agent._model_router.locate
        )

        # Should raise WaitUntilError since element exists and won't disappear
        with pytest.raises(WaitUntilError) as exc_info:
            vision_agent.wait(
                locator, retry_count=2, delay=0.1, until_condition="disappear"
            )

        assert (
            "Wait until condition 'disappear' not met for locator: 'Forgot password?' "
            "after 2 retries with 0.1 seconds delay" == str(exc_info.value)
        )
        assert vision_agent._model_router.locate.call_count == 2

    def test_wait_with_locator_object(
        self, vision_agent: VisionAgent, github_login_screenshot: PILImage.Image
    ) -> None:
        """Test waiting with a Locator object."""
        locator = Element("textfield")

        # Mock screenshot to return the image where textfield exists
        mock_screenshot = Mock(return_value=github_login_screenshot)
        vision_agent._agent_os.screenshot = mock_screenshot
        vision_agent._model_router.locate = Mock(
            wraps=vision_agent._model_router.locate
        )

        # Should not raise an exception since textfield exists
        vision_agent.wait(locator, retry_count=2, delay=0.1, until_condition="appear")

        assert vision_agent._model_router.locate.call_count >= 1

    def test_wait_with_default_parameters(
        self, vision_agent: VisionAgent, github_login_screenshot: PILImage.Image
    ) -> None:
        """Test waiting with default parameters."""
        locator = "Forgot password?"

        # Mock screenshot to return the image where element exists
        mock_screenshot = Mock(return_value=github_login_screenshot)
        vision_agent._agent_os.screenshot = mock_screenshot
        vision_agent._model_router.locate = Mock(
            wraps=vision_agent._model_router.locate
        )

        # Should use default retry_count=3, delay=1, until_condition="appear"
        vision_agent.wait(locator)

        assert vision_agent._model_router.locate.call_count >= 1

    def test_wait_disappear_timing(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        white_page_screenshot: PILImage.Image,
    ) -> None:
        """Test that wait for disappear calls sleep with correct delay."""
        locator = "Forgot password?"

        mock_screenshot = Mock(
            side_effect=[
                github_login_screenshot,
                github_login_screenshot,
                white_page_screenshot,
            ]
        )
        vision_agent._agent_os.screenshot = mock_screenshot
        vision_agent._model_router.locate = Mock(
            wraps=vision_agent._model_router.locate
        )

        vision_agent.wait(
            locator, until_condition="disappear", retry_count=3, delay=0.2
        )

        assert vision_agent._model_router.locate.call_count == 3

    def test_wait_zero_retries(self, vision_agent: VisionAgent) -> None:
        """Test waiting with zero retry_count."""
        # Should fail immediately with 0 retry_count
        with pytest.raises(ValidationError):
            vision_agent.wait("test", retry_count=0)
