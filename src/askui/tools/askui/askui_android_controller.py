from PIL import Image
from askui.models.utils import scale_image_with_padding
from ppadb.client import Client as AdbClient
import io
from typing import Optional, Union

from PIL import Image, ImageDraw

from askui.reporting.report import SimpleReportGenerator
from askui.utils import ANDROID_KEY, draw_point_on_image


class AskUiAndroidControllerClient:
    def __init__(
        self, report: SimpleReportGenerator | None = None
    ) -> None:
        self._client = None
        self._device = None
        self._mouse_position = (0, 0)
        self.report = report

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

    def disconnect(self) -> None:
        self._client = None
        self._device = None

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
        screencap = self._device.screencap()
        image = Image.open(io.BytesIO(screencap))
        if report:
            self._add_report_message("AgentOS", "screenshot()", image)
        return image

    def get_cursor_position(self) -> tuple[int, int]:
        self._add_report_message(
            "AgentOS", f"get_cursor_position() = {self._mouse_position}"
        )
        return self._mouse_position

    def tap(self, x: int, y: int) -> None:
        self._check_if_device_is_connected()
        self._device.shell(f"input tap {x} {y}")
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
        self._device.shell(f"input swipe {x1} {y1} {x2} {y2} {duration_in_ms}")
        self._mouse_position = (x2, y2)
        self._add_report_message(
            "AgentOS", f"swipe({x1}, {y1}, {x2}, {y2}, {duration_in_ms})"
        )

    def drag_and_drop(
        self, x1: int, y1: int, x2: int, y2: int, duration_in_ms: int = 1000
    ) -> None:
        self._check_if_device_is_connected()
        self._device.shell(f"input draganddrop {x1} {y1} {x2} {y2} {duration_in_ms}")
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
        self._device.shell(f"input roll {dx} {dy}")
        self._mouse_position = (
            self._mouse_position[0] + dx,
            self._mouse_position[1] + dy,
        )
        self._add_report_message("AgentOS", f"roll({dx}, {dy})")

    def key_event(self, key: ANDROID_KEY) -> None:
        self._check_if_device_is_connected()
        self._device.shell(f"input keyevent {key}")
        self._add_report_message("AgentOS", f"key_event({key})")

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
