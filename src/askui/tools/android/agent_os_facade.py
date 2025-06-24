from typing import List, Optional, Tuple

from PIL import Image

from askui.reporting import Reporter
from askui.tools.android.agent_os import ANDROID_KEY, AndroidAgentOs, AndroidDisplay
from askui.utils.image_utils import scale_coordinates_back, scale_image_with_padding


class AndroidAgentOsFacade(AndroidAgentOs):
    """
    This class is a facade for the AndroidAgentOs class.
    It is used to scale the coordinates to the target resolution
    and back to the real screen resolution.
    """

    def __init__(self, agent_os: AndroidAgentOs, reporter: Reporter) -> None:
        self._agent_os: AndroidAgentOs = agent_os
        self._reporter: Reporter = reporter
        self._target_resolution: Tuple[int, int] = (1280, 800)
        self._real_screen_resolution: Optional[Tuple[int, int]] = None

    def connect(self) -> None:
        self._agent_os.connect()
        self._reporter.add_message("AndroidAgentOS", "Connected to device")
        self._real_screen_resolution = self._agent_os.screenshot().size

    def disconnect(self) -> None:
        self._agent_os.disconnect()
        self._real_screen_resolution = None

    def screenshot(self) -> Image.Image:
        screenshot = self._agent_os.screenshot()
        self._real_screen_resolution = screenshot.size
        scaled_image = scale_image_with_padding(
            screenshot,
            self._target_resolution[0],
            self._target_resolution[1],
        )

        self._reporter.add_message("AndroidAgentOS", "Screenshot taken", screenshot)
        return scaled_image

    def _scale_coordinates_back(self, x: int, y: int) -> Tuple[int, int]:
        if self._real_screen_resolution is None:
            self._real_screen_resolution = self._agent_os.screenshot().size

        scaled_x, scaled_y = scale_coordinates_back(
            x,
            y,
            self._real_screen_resolution[0],
            self._real_screen_resolution[1],
            self._target_resolution[0],
            self._target_resolution[1],
        )
        return int(scaled_x), int(scaled_y)

    def tap(self, x: int, y: int) -> None:
        scaled_x, scaled_y = self._scale_coordinates_back(x, y)
        self._agent_os.tap(scaled_x, scaled_y)
        self._reporter.add_message("AndroidAgentOS", f"Tapped on {x}, {y}")

    def swipe(
        self, x1: int, y1: int, x2: int, y2: int, duration_in_ms: int = 1000
    ) -> None:
        scaled_x1, scaled_y1 = self._scale_coordinates_back(x1, y1)
        scaled_x2, scaled_y2 = self._scale_coordinates_back(x2, y2)
        self._agent_os.swipe(scaled_x1, scaled_y1, scaled_x2, scaled_y2, duration_in_ms)
        self._reporter.add_message(
            "AndroidAgentOS", f"Swiped from {x1}, {y1} to {x2}, {y2}"
        )

    def drag_and_drop(
        self, x1: int, y1: int, x2: int, y2: int, duration_in_ms: int = 1000
    ) -> None:
        scaled_x1, scaled_y1 = self._scale_coordinates_back(x1, y1)
        scaled_x2, scaled_y2 = self._scale_coordinates_back(x2, y2)
        self._agent_os.drag_and_drop(
            scaled_x1, scaled_y1, scaled_x2, scaled_y2, duration_in_ms
        )
        self._reporter.add_message(
            "AndroidAgentOS",
            f"Dragged and dropped from {x1}, {y1} to {x2}, {y2}",
        )

    def type(self, text: str) -> None:
        self._agent_os.type(text)
        self._reporter.add_message("AndroidAgentOS", f"Typed {text}")

    def key_tap(self, key: ANDROID_KEY) -> None:
        self._agent_os.key_tap(key)
        self._reporter.add_message("AndroidAgentOS", f"Tapped on {key}")

    def key_combination(
        self, keys: List[ANDROID_KEY], duration_in_ms: int = 100
    ) -> None:
        self._agent_os.key_combination(keys, duration_in_ms)
        self._reporter.add_message(
            "AndroidAgentOS",
            f"Tapped on Keys: {keys}",
        )

    def shell(self, command: str) -> str:
        shell_output = self._agent_os.shell(command)
        self._reporter.add_message("AndroidAgentOS", f"Ran shell command: {command}")
        return shell_output

    def get_connected_displays(self) -> list[AndroidDisplay]:
        displays = self._agent_os.get_connected_displays()
        self._reporter.add_message(
            "AndroidAgentOS",
            f"Retrieved connected displays, length: {len(displays)}",
        )
        return displays

    def set_display_by_index(self, display_index: int = 0) -> None:
        self._agent_os.set_display_by_index(display_index)
        self._real_screen_resolution = None
        self._reporter.add_message(
            "AndroidAgentOS", f"Set display by index: {display_index}"
        )

    def set_display_by_id(self, display_id: int) -> None:
        self._agent_os.set_display_by_id(display_id)
        self._real_screen_resolution = None
        self._reporter.add_message("AndroidAgentOS", f"Set display by id: {display_id}")

    def set_display_by_name(self, display_name: str) -> None:
        self._agent_os.set_display_by_name(display_name)
        self._real_screen_resolution = None
        self._reporter.add_message(
            "AndroidAgentOS", f"Set display by name: {display_name}"
        )

    def set_device_by_index(self, device_index: int = 0) -> None:
        self._agent_os.set_device_by_index(device_index)
        self._real_screen_resolution = None
        self._reporter.add_message(
            "AndroidAgentOS", f"Set device by index: {device_index}"
        )

    def set_device_by_serial_number(self, device_sn: str) -> None:
        self._agent_os.set_device_by_serial_number(device_sn)
        self._real_screen_resolution = None
        self._reporter.add_message(
            "AndroidAgentOS", f"Set device by serial number: {device_sn}"
        )
