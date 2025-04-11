import re
from PIL import Image
from askui.models.utils import scale_coordinates_back, scale_image_with_padding
from ppadb.client import Client as AdbClient
import io
from typing import Optional, Union

from PIL import Image, ImageDraw

from askui.reporting.report import SimpleReportGenerator
from askui.utils import ANDROID_KEY, draw_point_on_image, resize_to_max_edge


class AndroidDisplay:
    def __init__(
        self, unique_display_id: int, display_name: str, display_index: int
    ) -> None:
        self.unique_display_id = unique_display_id
        self.display_name = display_name
        self.display_index = display_index

    def __repr__(self) -> str:
        return (
            f"AndroidDisplay(unique_display_id={self.unique_display_id}, "
            f"display_name={self.display_name}, display_index={self.display_index})"
        )


class AskUiAndroidControllerClient:
    def __init__(self, report: SimpleReportGenerator | None = None) -> None:
        self._client = None
        self._device = None
        self._mouse_position = (0, 0)
        self._displays: list[AndroidDisplay] = []
        self._selected_display: Optional[AndroidDisplay] = None
        self.report = report
        self.original_resolution = (0, 0)
        self.scaled_resolution = (0, 0)

    def _reset_screen_resolution(self) -> None:
        self.original_resolution = self.get_screen_resolution()
        self.scaled_resolution = resize_to_max_edge(self.original_resolution, 1200)

    def rescale_back_coordinates(self, x: int, y: int):
        if self.original_resolution == (0, 0):
            raise RuntimeError("Screen resolution not set")
        if self.scaled_resolution == (0, 0):
            raise RuntimeError("Scaled resolution not set")
        return scale_coordinates_back(
            x,
            y,
            self.original_resolution[0],
            self.original_resolution[1],
            self.scaled_resolution[0],
            self.scaled_resolution[1],
        )

    def get_connected_displays(self) -> list[AndroidDisplay]:
        self._check_if_device_is_connected()
        displays = []
        output = self._device.shell("dumpsys SurfaceFlinger --display-id")

        index = 0
        for line in output.splitlines():
            if line.startswith("Display"):
                match = re.match(r"Display (\d+) .* displayName=\"([^\"]+)\"", line)
                if match:
                    unique_display_id = int(match.group(1))
                    display_name = match.group(2)
                    displays.append(
                        AndroidDisplay(unique_display_id, display_name, index)
                    )
                    index += 1
        return displays

    def _check_if_device_is_connected(self) -> None:
        if not self._client or not self._device:
            raise RuntimeError("No device connected")
        devices = self._client.devices()
        if not devices:
            raise RuntimeError("No devices connected")

        for device in devices:
            if device.serial == self._device.serial:
                return
        raise Exception(f"Device {self._device.serial} not found in connected devices")

    def connect(self) -> None:
        self._client = AdbClient()
        devices = self._client.devices()
        if not devices:
            raise RuntimeError("No devices connected")
        self._device = devices[0]
        self._displays = self.get_connected_displays()
        if not self._displays:
            raise RuntimeError("No displays found")
        self.set_display_by_index(1)
        self._add_report_message("AgentOS", f"connect() to {self._device.serial}")

    def disconnect(self) -> None:
        self._client = None
        self._device = None

    def _set_display(self, display: AndroidDisplay) -> None:
        self._selected_display = display
        self._mouse_position = (0, 0)
        self._reset_screen_resolution()
        self._add_report_message("AgentOS", f"select display {str(display)}")

    def set_display_by_index(self, displayNumber: int = 0) -> None:
        if not self._displays:
            raise RuntimeError("No displays connected")
        if displayNumber >= len(self._displays):
            raise RuntimeError(f"Display number {displayNumber} out of range it must be less than {len(self._displays)}")
        self._set_display(self._displays[displayNumber])

    def set_display_by_id(self, display_id: int) -> None:
        if not self._displays:
            raise RuntimeError("No displays connected")
        for display in self._displays:
            if display.display_id == display_id:
                self._set_display(display)
                return
        raise RuntimeError(f"Display ID {display_id} not found")

    def set_display_by_name(self, display_name: str) -> None:
        if not self._displays:
            raise RuntimeError("No displays connected")
        for display in self._displays:
            if display.display_name == display_name:
                self._set_display(display)
                return
        raise RuntimeError(f"Display name {display_name} not found")

    def set_device_by_id(self, displayNumber: int = 1) -> None:
        devices = self._client.devices()
        if not devices:
            raise RuntimeError("No devices connected")
        if displayNumber > len(devices):
            raise RuntimeError(f"Display number {displayNumber} out of range")
        self._device = devices[displayNumber - 1]
        self._add_report_message("AgentOS", f"set_display({displayNumber})")

    def set_device_by_name(self, displayName: str) -> None:
        devices = self._client.devices()
        if not devices:
            raise RuntimeError("No devices connected")
        for device in devices:
            if device.serial == displayName:
                self._device = device
                self._add_report_message("AgentOS", f"set_display({displayName})")
                return
        raise RuntimeError(f"Display name {displayName} not found")

    def screenshot(self, report: bool = True) -> Image.Image:
        self._check_if_device_is_connected()
        connection_to_device = self._device.create_connection()
        connection_to_device.send(
            f"shell:/system/bin/screencap -p -d {self._selected_display.unique_display_id}"
        )
        response = connection_to_device.read_all()
        if response and len(response) > 5 and response[5] == 0x0D:
            response = response.replace(b"\r\n", b"\n")
        image = Image.open(io.BytesIO(response))
        if report:
            self._add_report_message(
                "AgentOS", f"screenshot() with size {image.size}", image
            )
        return image

    def get_cursor_position(self) -> tuple[int, int]:
        self._add_report_message(
            "AgentOS", f"get_cursor_position() = {self._mouse_position}"
        )
        return self._mouse_position

    def tap(self, x: int, y: int) -> None:
        self._check_if_device_is_connected()
        self._device.shell(
            f"input -d {self._selected_display.display_index} tap {x} {y}"
        )
        self._mouse_position = (x, y)
        self._add_report_message(
            "AgentOS",
            f"tap({x}, {y})",
            draw_point_on_image(self.screenshot(report=False), x, y, size=10),
        )

    def swipe(
        self, x1: int, y1: int, x2: int, y2: int, duration_in_ms: int = 1000
    ) -> None:
        self._check_if_device_is_connected()
        self._device.shell(
            f"input -d {self._selected_display.display_index} swipe {x1} {y1} {x2} {y2} {duration_in_ms}"
        )
        self._mouse_position = (x2, y2)
        self._add_report_message(
            "AgentOS", f"swipe({x1}, {y1}, {x2}, {y2}, {duration_in_ms})"
        )

    def drag_and_drop(
        self, x1: int, y1: int, x2: int, y2: int, duration_in_ms: int = 1000
    ) -> None:
        self._check_if_device_is_connected()
        self._device.shell(
            f"input -d {self._selected_display.display_index} draganddrop {x1} {y1} {x2} {y2} {duration_in_ms}"
        )
        self._mouse_position = (x2, y2)
        self._add_report_message(
            "AgentOS", f"drag_and_drop({x1}, {y1}, {x2}, {y2}, {duration_in_ms})"
        )

    def move_mouse(self, x: int, y: int) -> None:
        self._mouse_position = (x, y)
        self._add_report_message(
            "AgentOS",
            f"move_mouse({x}, {y})",
            draw_point_on_image(self.screenshot(report=False), x, y, size=10),
        )

    def roll(self, dx: int, dy: int) -> None:
        self._check_if_device_is_connected()
        self._device.shell(
            f"input -d {self._selected_display.display_index} roll {dx} {dy}"
        )
        self._mouse_position = (
            self._mouse_position[0] + dx,
            self._mouse_position[1] + dy,
        )
        self._add_report_message("AgentOS", f"roll({dx}, {dy})")

    def key_event(self, key: ANDROID_KEY) -> None:
        self._check_if_device_is_connected()
        self._device.shell(
            f"input -d {self._selected_display.display_index} keyevent {key.capitalize()}"
        )
        self._add_report_message("AgentOS", f"key_event({key.capitalize()})")

    def shell(self, command: str) -> str:
        self._check_if_device_is_connected()
        result = self._device.shell(command)
        self._add_report_message("AgentOS", f"shell({command})")
        return result

    def debug_draw(self, x1, y1, x2, y2) -> None:
        self._check_if_device_is_connected()
        image = self.screenshot(report=False)
        draw = ImageDraw.Draw(image)
        draw.rectangle([x1, y1, x2, y2], outline="red", width=10)
        self._add_report_message(
            "AgentOS", f"debug_draw({x1}, {y1}, {x2}, {y2})", image
        )
        return image

    def get_screen_resolution(self) -> tuple[int, int]:
        self._check_if_device_is_connected()
        image = self.screenshot(report=False)
        return image.size

    def _add_report_message(
        self,
        role: str,
        content: Union[str, dict, list],
        image: Optional[Image.Image] = None,
    ):
        if self.report is not None:
            self.report.add_message(
                role,
                content,
                scale_image_with_padding(image, 553, 1200) if image else None,
            )
