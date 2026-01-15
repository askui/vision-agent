from PIL import Image

from askui.models.shared.tool_tags import ToolTags
from askui.tools.agent_os import (
    AgentOs,
    Coordinate,
    Display,
    DisplaySize,
    DisplaysListResponse,
    InputEvent,
    ModifierKey,
    MouseButton,
    PcKey,
)
from askui.tools.askui.askui_controller import RenderObjectStyle  # noqa: TC001
from askui.utils.image_utils import scale_coordinates, scale_image_to_fit


class ComputerAgentOsFacade(AgentOs):
    """
    Facade for AgentOs that adds coordinate scaling functionality.

    This class is used to scale the coordinates to the target resolution
    and back to the real screen resolution.
    """

    def __init__(self, agent_os: AgentOs) -> None:
        self._agent_os = agent_os
        self._target_resolution: tuple[int, int] = (1024, 768)
        self._real_screen_resolution: DisplaySize | None = None
        self.tags = self._agent_os.tags + [ToolTags.SCALED_AGENT_OS.value]

    def connect(self) -> None:
        self._agent_os.connect()
        self._real_screen_resolution = self._agent_os.retrieve_active_display().size

    def disconnect(self) -> None:
        self._agent_os.disconnect()
        self._real_screen_resolution = None

    def screenshot(self, report: bool = True) -> Image.Image:
        screenshot = self._agent_os.screenshot(report=report)
        self._real_screen_resolution = DisplaySize(
            width=screenshot.width, height=screenshot.height
        )
        return scale_image_to_fit(screenshot, self._target_resolution)

    def mouse_move(self, x: int, y: int) -> None:
        scaled_x, scaled_y = self._scale_coordinates_back(x, y)
        self._agent_os.mouse_move(scaled_x, scaled_y)

    def get_mouse_position(self) -> Coordinate:
        mouse_position = self._agent_os.get_mouse_position()
        scaled_x, scaled_y = self._scale_coordinates_back(
            mouse_position.x, mouse_position.y, from_agent=False
        )
        return Coordinate(x=scaled_x, y=scaled_y)

    def set_mouse_position(self, x: int, y: int) -> None:
        scaled_x, scaled_y = self._scale_coordinates_back(x, y)
        self._agent_os.set_mouse_position(scaled_x, scaled_y)

    def type(self, text: str, typing_speed: int = 50) -> None:
        self._agent_os.type(text, typing_speed)

    def click(self, button: MouseButton = "left", count: int = 1) -> None:
        self._agent_os.click(button, count)

    def mouse_down(self, button: MouseButton = "left") -> None:
        self._agent_os.mouse_down(button)

    def mouse_up(self, button: MouseButton = "left") -> None:
        self._agent_os.mouse_up(button)

    def mouse_scroll(self, x: int, y: int) -> None:
        scaled_x, scaled_y = self._scale_coordinates_back(x, y)
        self._agent_os.mouse_scroll(scaled_x, scaled_y)

    def keyboard_pressed(
        self, key: PcKey | ModifierKey, modifier_keys: list[ModifierKey] | None = None
    ) -> None:
        self._agent_os.keyboard_pressed(key, modifier_keys)

    def keyboard_release(
        self, key: PcKey | ModifierKey, modifier_keys: list[ModifierKey] | None = None
    ) -> None:
        self._agent_os.keyboard_release(key, modifier_keys)

    def keyboard_tap(
        self,
        key: PcKey | ModifierKey,
        modifier_keys: list[ModifierKey] | None = None,
        count: int = 1,
    ) -> None:
        self._agent_os.keyboard_tap(key, modifier_keys, count)

    def list_displays(self) -> DisplaysListResponse:
        return self._agent_os.list_displays()

    def retrieve_active_display(self) -> Display:
        return self._agent_os.retrieve_active_display()

    def set_display(self, display: int = 1) -> None:
        self._agent_os.set_display(display)
        self._real_screen_resolution = None

    def run_command(self, command: str, timeout_ms: int = 30000) -> None:
        self._agent_os.run_command(command, timeout_ms)

    def start_listening(self) -> None:
        self._agent_os.start_listening()

    def poll_event(self) -> InputEvent | None:
        return self._agent_os.poll_event()

    def stop_listening(self) -> None:
        self._agent_os.stop_listening()

    def render_quad(self, style: "RenderObjectStyle") -> int:
        return self._agent_os.render_quad(style)

    def render_line(self, style: "RenderObjectStyle", points: list[Coordinate]) -> int:
        return self._agent_os.render_line(style, points)

    def render_image(self, style: "RenderObjectStyle", image_data: str) -> int:
        return self._agent_os.render_image(style, image_data)

    def render_text(self, style: "RenderObjectStyle", content: str) -> int:
        return self._agent_os.render_text(style, content)

    def update_render_object(self, object_id: int, style: "RenderObjectStyle") -> None:
        self._agent_os.update_render_object(object_id, style)

    def delete_render_object(self, object_id: int) -> None:
        self._agent_os.delete_render_object(object_id)

    def clear_render_objects(self) -> None:
        self._agent_os.clear_render_objects()

    def _scale_coordinates_back(
        self,
        x: int,
        y: int,
        from_agent: bool = True,
    ) -> tuple[int, int]:
        if self._real_screen_resolution is None:
            self._real_screen_resolution = self._agent_os.retrieve_active_display().size
        return scale_coordinates(
            (x, y),
            (self._real_screen_resolution.width, self._real_screen_resolution.height),
            self._target_resolution,
            inverse=from_agent,
        )
