from time import sleep

import pytest

from askui.reporting import CompositeReporter
from askui.tools.askui.askui_controller import (
    AskUiControllerClient,
    AskUiControllerServer,
)
from askui.tools.askui.render_objects import create_style


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


def test_demo(controller_client: AskUiControllerClient) -> None:
    with controller_client:
        text_array = [
            "Locating search bar",
            "Search bar located",
            "Moving cursor to search bar",
            "Left clicked (400, 100)",
        ]

        while True:
            box_style = create_style(
                top=1.0,
                left=0.0,
                width=0.2,
                height=1.0,
                color="#fafafa",
                opacity=0.9,
                visible=True,
            )

            box_id = controller_client.add_quad_render_object(box_style)

            font_size = 18
            line_height = font_size * 1.5
            start_y = 30
            start_x = 10

            text_object_ids = []

            # Locating search bar
            y_position = start_y + (0 * line_height)
            text_style = create_style(
                top=f"{y_position}px",
                left=start_x,
                color="#404040",
                font_size=font_size,
                opacity=1.0,
                visible=True,
            )
            text_id = controller_client.add_text_render_object(
                text_style, text_array[0]
            )
            text_object_ids.append(text_id)
            sleep(2)

            # search bar located
            y_position = start_y + (1 * line_height)
            text_style = create_style(
                top=f"{y_position}px",
                left=start_x,
                color="#404040",
                font_size=font_size,
                opacity=1.0,
                visible=True,
            )
            text_id = controller_client.add_text_render_object(
                text_style, text_array[1]
            )
            text_object_ids.append(text_id)

            # draw search box overlay
            box_style = create_style(
                top=477,
                left=525,
                width=750,
                height=50,
                color="#c026d3",
                opacity=0.5,
                visible=True,
            )
            box_id = controller_client.add_quad_render_object(box_style)
            sleep(2)

            # moving cursor
            y_position = start_y + (2 * line_height)
            text_style = create_style(
                top=f"{y_position}px",
                left=start_x,
                color="#404040",
                font_size=font_size,
                opacity=1.0,
                visible=True,
            )
            text_id = controller_client.add_text_render_object(
                text_style, text_array[2]
            )
            text_object_ids.append(text_id)

            # move cursor
            cursor = controller_client.create_mouse_cursor(x=0, y=0, color="#00d492")
            controller_client.animate_cursor_to(650, 455, 500)
            sleep(1)
            cursor.update_cursor_color(color="#00bcff")
            sleep(2)

            # clicked
            y_position = start_y + (3 * line_height)
            text_style = create_style(
                top=f"{y_position}px",
                left=start_x,
                color="#404040",
                font_size=font_size,
                opacity=1.0,
                visible=True,
            )
            text_id = controller_client.add_text_render_object(
                text_style, text_array[3]
            )
            text_object_ids.append(text_id)
            sleep(2)

            for text_id in text_object_ids:
                controller_client.delete_render_object(text_id)

            controller_client.delete_render_object(box_id)
            controller_client.clear_render_objects()

