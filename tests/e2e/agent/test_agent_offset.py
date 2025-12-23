"""Tests for VisionAgent offset functionality with different locator types and models"""

from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest
from PIL import Image as PILImage

from askui.agent import VisionAgent
from askui.locators import Element
from askui.models.askui.models import AskUiLocateModel, LocateModel

if TYPE_CHECKING:
    from askui.models.models import Point


class TestVisionAgentOffset:
    """Test class for VisionAgent offset functionality."""

    def _setup_mocks(
        self, vision_agent: VisionAgent, github_login_screenshot: PILImage.Image
    ) -> tuple[Mock, Mock, Mock, Mock]:
        """Helper method to setup common mocks."""
        mock_mouse_move = Mock()
        mock_click = Mock()
        mock_type = Mock()
        mock_screenshot = Mock(return_value=github_login_screenshot)

        vision_agent.tools.os.mouse_move = mock_mouse_move  # type: ignore[method-assign]
        vision_agent.tools.os.click = mock_click  # type: ignore[method-assign]
        vision_agent.tools.os.type = mock_type  # type: ignore[method-assign]
        vision_agent.tools.os.screenshot = mock_screenshot  # type: ignore[method-assign]

        return mock_mouse_move, mock_click, mock_type, mock_screenshot

    def test_click_with_positive_offset(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        askui_locate_model_factory,
    ) -> None:
        """Test clicking with positive offset (right and down)."""
        locator = "Forgot password?"
        offset: Point = (10, 5)
        locate_model = askui_locate_model_factory()

        mock_mouse_move, mock_click, _, mock_screenshot = self._setup_mocks(
            vision_agent, github_login_screenshot
        )

        # Get original position
        x, y = vision_agent.locate(
            locator, github_login_screenshot, locate_model=locate_model
        )

        # Click with offset should work without error
        vision_agent.click(locator, offset=offset, locate_model=locate_model)

        # Verify calls
        mock_screenshot.assert_called()
        expected_x, expected_y = x + offset[0], y + offset[1]
        mock_mouse_move.assert_called_once_with(expected_x, expected_y)
        mock_click.assert_called_once_with("left", 1)

    def test_click_with_negative_offset(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        askui_locate_model_factory,
    ) -> None:
        """Test clicking with negative offset (left and up)."""
        locator = "Forgot password?"
        offset: Point = (-10, -5)
        locate_model = askui_locate_model_factory()

        mock_mouse_move, mock_click, _, mock_screenshot = self._setup_mocks(
            vision_agent, github_login_screenshot
        )

        # Get original position
        x, y = vision_agent.locate(
            locator, github_login_screenshot, locate_model=locate_model
        )

        # Click with negative offset should work without error
        vision_agent.click(locator, offset=offset, locate_model=locate_model)

        # Verify calls
        mock_screenshot.assert_called()
        expected_x, expected_y = x + offset[0], y + offset[1]
        mock_mouse_move.assert_called_once_with(expected_x, expected_y)
        mock_click.assert_called_once_with("left", 1)

    def test_click_with_zero_offset(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        askui_locate_model_factory,
    ) -> None:
        """Test clicking with zero offset (same as no offset)."""
        locate_model = askui_locate_model_factory()

        locator = "Forgot password?"
        offset: Point = (0, 0)

        mock_mouse_move, mock_click, _, mock_screenshot = self._setup_mocks(
            vision_agent, github_login_screenshot
        )

        # Get original position
        x, y = vision_agent.locate(
            locator, github_login_screenshot, locate_model=locate_model
        )

        # Click with zero offset should work without error
        vision_agent.click(locator, offset=offset, locate_model=locate_model)

        # Verify calls
        mock_screenshot.assert_called()
        mock_mouse_move.assert_called_once_with(x, y)
        mock_click.assert_called_once_with("left", 1)

    def test_click_with_point_locator_and_offset(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        askui_locate_model_factory,
    ) -> None:
        """Test clicking with Point locator and offset."""
        locate_model = askui_locate_model_factory()

        point_locator: Point = (100, 100)
        offset: Point = (20, 15)

        mock_mouse_move, mock_click, _, mock_screenshot = self._setup_mocks(
            vision_agent, github_login_screenshot
        )

        # Click with Point locator and offset should work
        vision_agent.click(point_locator, offset=offset, locate_model=locate_model)

        # Verify calls
        mock_screenshot.assert_not_called()
        expected_x, expected_y = (
            point_locator[0] + offset[0],
            point_locator[1] + offset[1],
        )
        mock_mouse_move.assert_called_once_with(expected_x, expected_y)
        mock_click.assert_called_once_with("left", 1)

    def test_mouse_move_with_positive_offset(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        askui_locate_model_factory,
    ) -> None:
        """Test mouse movement with positive offset."""
        locate_model = askui_locate_model_factory()

        locator = "Forgot password?"
        offset: Point = (15, 10)

        mock_mouse_move, _, _, mock_screenshot = self._setup_mocks(
            vision_agent, github_login_screenshot
        )

        # Get original position
        x, y = vision_agent.locate(
            locator, github_login_screenshot, locate_model=locate_model
        )

        # Mouse move with offset should work without error
        vision_agent.mouse_move(locator, offset=offset, locate_model=locate_model)

        # Verify calls
        mock_screenshot.assert_called()
        expected_x, expected_y = x + offset[0], y + offset[1]
        mock_mouse_move.assert_called_once_with(expected_x, expected_y)

    def test_mouse_move_with_negative_offset(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        askui_locate_model_factory,
    ) -> None:
        """Test mouse movement with negative offset."""
        locate_model = askui_locate_model_factory()

        locator = "Forgot password?"
        offset: Point = (-15, -10)

        mock_mouse_move, _, _, mock_screenshot = self._setup_mocks(
            vision_agent, github_login_screenshot
        )

        # Get original position
        x, y = vision_agent.locate(
            locator, github_login_screenshot, locate_model=locate_model
        )

        # Mouse move with negative offset should work without error
        vision_agent.mouse_move(locator, offset=offset, locate_model=locate_model)

        # Verify calls
        mock_screenshot.assert_called()
        expected_x, expected_y = x + offset[0], y + offset[1]
        mock_mouse_move.assert_called_once_with(expected_x, expected_y)

    def test_mouse_move_with_point_locator_and_offset(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        askui_locate_model_factory,
    ) -> None:
        """Test mouse movement with Point locator and offset."""
        locate_model = askui_locate_model_factory()

        point_locator: Point = (200, 150)
        offset: Point = (25, -10)

        mock_mouse_move, _, _, mock_screenshot = self._setup_mocks(
            vision_agent, github_login_screenshot
        )

        # Mouse move with Point locator and offset should work
        vision_agent.mouse_move(point_locator, offset=offset, locate_model=locate_model)

        # Verify calls
        mock_screenshot.assert_not_called()
        expected_x, expected_y = (
            point_locator[0] + offset[0],
            point_locator[1] + offset[1],
        )
        mock_mouse_move.assert_called_once_with(expected_x, expected_y)

    def test_type_with_positive_offset(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        askui_locate_model_factory,
    ) -> None:
        """Test typing with positive offset."""
        locate_model = askui_locate_model_factory()

        locator = Element("textfield")
        offset: Point = (5, 3)
        text = "test@example.com"

        mock_mouse_move, mock_click, mock_type, mock_screenshot = self._setup_mocks(
            vision_agent, github_login_screenshot
        )

        # Get original position
        x, y = vision_agent.locate(
            locator, github_login_screenshot, locate_model=locate_model
        )

        # Type with offset should work without error
        vision_agent.type(text, locator=locator, offset=offset, locate_model=locate_model)

        # Verify calls
        mock_screenshot.assert_called()
        expected_x, expected_y = x + offset[0], y + offset[1]
        mock_mouse_move.assert_called_once_with(expected_x, expected_y)
        mock_click.assert_called_once_with("left", 3)
        mock_type.assert_called_once_with(text)

    def test_type_with_negative_offset(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        askui_locate_model_factory,
    ) -> None:
        """Test typing with negative offset."""
        locate_model = askui_locate_model_factory()

        locator = Element("textfield")
        offset: Point = (-5, -3)
        text = "test@example.com"

        mock_mouse_move, mock_click, mock_type, mock_screenshot = self._setup_mocks(
            vision_agent, github_login_screenshot
        )

        # Get original position
        x, y = vision_agent.locate(
            locator, github_login_screenshot, locate_model=locate_model
        )

        # Type with negative offset should work without error
        vision_agent.type(text, locator=locator, offset=offset, locate_model=locate_model)

        # Verify calls
        mock_screenshot.assert_called()
        expected_x, expected_y = x + offset[0], y + offset[1]
        mock_mouse_move.assert_called_once_with(expected_x, expected_y)
        mock_click.assert_called_once_with("left", 3)
        mock_type.assert_called_once_with(text)

    def test_type_with_point_locator_and_offset(
        self,
        vision_agent: VisionAgent,
        github_login_screenshot: PILImage.Image,
        askui_locate_model_factory,
    ) -> None:
        """Test typing with Point locator and offset."""
        locate_model = askui_locate_model_factory()

        point_locator: Point = (460, 195)  # Approximate textfield location
        offset: Point = (10, 5)
        text = "username"

        mock_mouse_move, mock_click, mock_type, mock_screenshot = self._setup_mocks(
            vision_agent, github_login_screenshot
        )

        # Type with Point locator and offset should work
        vision_agent.type(
            text, locator=point_locator, offset=offset, locate_model=locate_model
        )

        # Verify calls
        mock_screenshot.assert_not_called()
        expected_x, expected_y = (
            point_locator[0] + offset[0],
            point_locator[1] + offset[1],
        )
        mock_mouse_move.assert_called_once_with(expected_x, expected_y)
        mock_click.assert_called_once_with("left", 3)
        mock_type.assert_called_once_with(text)
