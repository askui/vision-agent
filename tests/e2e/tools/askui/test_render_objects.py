from time import sleep
import time

import pytest

from askui.reporting import CompositeReporter
from askui.tools.askui.askui_controller import (
    AskUiControllerClient,
    AskUiControllerServer,
)
from askui.tools.askui.render_objects import create_location, create_style


@pytest.fixture
def controller_server() -> AskUiControllerServer:
    """Fixture providing an AskUI controller server."""
    return AskUiControllerServer()


@pytest.fixture
def controller_client(
    controller_server: AskUiControllerServer,
) -> AskUiControllerClient:
    """Fixture providing an AskUI controller client."""
    return AskUiControllerClient(
        reporter=CompositeReporter(),
        display=1,
        controller_server=controller_server,
    )


def test_add_quad_render_object(controller_client: AskUiControllerClient) -> None:
    """Test adding a quad render object."""
    style = create_style(
        top=100,
        left=200,
        width=50,
        height=50,
        color="#FF0000",
        opacity=0.8
    )
    
    with controller_client:
        object_id = controller_client.add_quad_render_object(style)
        assert isinstance(object_id, int)
        assert object_id > 0


def test_add_line_render_object(controller_client: AskUiControllerClient) -> None:
    """Test adding a line render object."""
    style = create_style(
        color="#00FF00",
        line_width=3,
        opacity=1.0
    )
    points = [
        create_location(100, 100),
        create_location(200, 150),
        create_location(150, 200)
    ]
    
    with controller_client:
        object_id = controller_client.add_line_render_object(style, points)
        assert isinstance(object_id, int)
        assert object_id > 0


def test_add_image_render_object(controller_client: AskUiControllerClient) -> None:
    """Test adding an image render object."""
    style = create_style(
        top=50,
        left=50,
        width=100,
        height=100,
        opacity=0.9
    )
    # Simple 1x1 pixel red image as base64
    bitmap_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    
    with controller_client:
        object_id = controller_client.add_image_render_object(style, bitmap_data)
        assert isinstance(object_id, int)
        assert object_id > 0


def test_add_text_render_object(controller_client: AskUiControllerClient) -> None:
    """Test adding a text render object."""
    style = create_style(
        top=300,
        left=100,
        color="#0000FF",
        font_size=16,
        opacity=1.0
    )
    text = "Test Text"
    
    with controller_client:
        object_id = controller_client.add_text_render_object(style, text)
        assert isinstance(object_id, int)
        assert object_id > 0


def test_get_mouse_position(controller_client: AskUiControllerClient) -> None:
    """Test getting mouse position."""
    with controller_client:
        position = controller_client.get_mouse_position()
        assert "x" in position
        assert "y" in position
        assert isinstance(position["x"], (int, float))
        assert isinstance(position["y"], (int, float))


def test_set_mouse_position(controller_client: AskUiControllerClient) -> None:
    """Test setting mouse position."""
    target_x, target_y = 400, 300
    
    with controller_client:
        controller_client.set_mouse_position(target_x, target_y)
        
        current_position = controller_client.get_mouse_position()
        assert current_position["x"] == target_x
        assert current_position["y"] == target_y


def test_create_mouse_cursor(controller_client: AskUiControllerClient) -> None:
    """Test creating a mouse cursor."""
    x, y = 100, 200
    color = "#FF0000"
    
    with controller_client:
        cursor = controller_client.create_mouse_cursor(x, y, color)
        assert cursor is not None
        assert controller_client.cursor is cursor


def test_update_cursor_position(controller_client: AskUiControllerClient) -> None:
    """Test updating cursor position."""
    initial_x, initial_y = 100, 200
    new_x, new_y = 300, 400
    
    with controller_client:
        controller_client.create_mouse_cursor(initial_x, initial_y)
        controller_client.update_cursor_position(new_x, new_y)
        assert controller_client.cursor is not None
        assert controller_client.cursor.position["x"] == new_x
        assert controller_client.cursor.position["y"] == new_y

