import io
import re
import shlex
import string
from pathlib import Path
from typing import List, Optional, get_args

from PIL import Image
from ppadb.client import Client as AdbClient
from ppadb.device import Device as AndroidDevice

from askui.reporting import NULL_REPORTER, Reporter
from askui.tools.android.agent_os import (
    ANDROID_KEY,
    AndroidAgentOs,
    AndroidDisplay,
    UnknownAndroidDisplay,
)
from askui.utils.annotated_image import AnnotatedImage


class PpadbAgentOs(AndroidAgentOs):
    """
    This class is used to control the Android device.
    """

    def __init__(
        self, reporter: Reporter = NULL_REPORTER, device_sn: str | None = None
    ) -> None:
        self._client: Optional[AdbClient] = None
        self._device: Optional[AndroidDevice] = None
        self._mouse_position: tuple[int, int] = (0, 0)
        self._displays: list[AndroidDisplay] = []
        self._selected_display: Optional[AndroidDisplay] = None
        self._reporter: Reporter = reporter
        self._device_sn: str | None = device_sn

    def connect_adb_client(self) -> None:
        if self._client is not None:
            msg = "Adb client is already connected"
            raise RuntimeError(msg)
        try:
            self._client = AdbClient()
            self._reporter.add_message("AndroidAgentOS", "Connected to adb client")
        except Exception as e:  # noqa: BLE001
            msg = f""" Failed to connect the adb client to the server.
            Make sure the adb server is running.
            IF you are using a real device, make sure the device is connected.
            And listed after executiing the 'adb devices' command.
            If you are using an emulator, make sure the emulator is running.
            The error message: {e}
            """
            raise RuntimeError(msg)  # noqa: B904

    def connect(self) -> None:
        self.connect_adb_client()
        if self._device_sn:
            self.set_device_by_serial_number(self._device_sn)
        else:
            self.set_device_by_index(0)
        assert self._device is not None
        self._device.wait_boot_complete()

    def disconnect(self) -> None:
        self._client = None
        self._device = None
        self._reporter.add_message("AndroidAgentOS", "Disconnected from adb client")

    def _set_display(self, display: AndroidDisplay) -> None:
        self._selected_display = display
        self._mouse_position = (0, 0)
        self._reporter.add_message(
            "AndroidAgentOS",
            f"Display'{str(display)}' set as active",
            AnnotatedImage(self._screenshot_without_reporting),
        )

    def get_connected_displays(self) -> list[AndroidDisplay]:
        self._check_if_device_is_selected()
        assert self._device is not None
        displays: list[AndroidDisplay] = []
        output: str = self._device.shell(
            "dumpsys SurfaceFlinger --display-id",
        )

        for line in output.splitlines():
            if line.startswith("Display"):
                match = re.match(
                    r"Display (\d+) .* port=(\d+) .* displayName=\"([^\"]*?)\"",
                    line,
                )
                if match:
                    unique_display_id: int = int(match.group(1))
                    port: int = int(match.group(2))
                    display_id = port + 1
                    if port == 0:
                        display_id = 0
                    display_name: str = match.group(3)
                    displays.append(
                        AndroidDisplay(unique_display_id, display_name, display_id)
                    )
        if not displays:
            return [UnknownAndroidDisplay()]
        return displays

    def set_display_by_index(self, display_index: int = 0) -> None:
        self._displays = self.get_connected_displays()
        if not self._displays:
            self._displays = [AndroidDisplay(0, "Default", 0)]
        if display_index >= len(self._displays):
            msg = (
                f"Display index {display_index} out of range it must be less than "
                f"{len(self._displays)}."
            )
            raise RuntimeError(msg)
        self._set_display(self._displays[display_index])

    def set_display_by_id(self, display_id: int) -> None:
        self._displays = self.get_connected_displays()
        if not self._displays:
            msg = "No displays connected"
            raise RuntimeError(msg)
        for display in self._displays:
            if display.display_id == display_id:
                self._set_display(display)
                return
        msg = f"Display ID {display_id} not found"
        raise RuntimeError(msg)

    def set_display_by_unique_id(self, display_unique_id: int) -> None:
        self._displays = self.get_connected_displays()
        if not self._displays:
            msg = "No displays connected"
            raise RuntimeError(msg)
        for display in self._displays:
            if display.unique_display_id == display_unique_id:
                self._set_display(display)
                return
        msg = f"Display unique ID {display_unique_id} not found"
        raise RuntimeError(msg)

    def set_display_by_name(self, display_name: str) -> None:
        self._displays = self.get_connected_displays()
        if not self._displays:
            msg = "No displays connected"
            raise RuntimeError(msg)
        for display in self._displays:
            if display.display_name == display_name:
                self._set_display(display)
                return
        msg = f"Display name {display_name} not found"
        raise RuntimeError(msg)

    def set_device_by_index(self, device_index: int = 0) -> None:
        devices = self._get_connected_devices()
        if device_index >= len(devices):
            msg = (
                f"Device index {device_index} out of range it must be less than "
                f"{len(devices)}."
            )
            raise RuntimeError(msg)
        self._device = devices[device_index]
        self.set_display_by_index(0)
        self._reporter.add_message(
            "AndroidAgentOS",
            f"Device {self._device.serial} set as active",
            AnnotatedImage(self._screenshot_without_reporting),
        )

    def set_device_by_serial_number(self, device_sn: str) -> None:
        devices = self._get_connected_devices()
        for device in devices:
            if device.serial == device_sn:
                self._device = device
                self.set_display_by_index(0)
                self._reporter.add_message(
                    "AndroidAgentOS",
                    f"Device {self._device.serial} set as active",
                    AnnotatedImage(self._screenshot_without_reporting),
                )
                return
        msg = f"Device name {device_sn} not found"
        raise RuntimeError(msg)

    def _screenshot_without_reporting(self) -> Image.Image:
        self._check_if_device_is_selected()
        self._check_if_display_is_selected()
        assert self._device is not None
        assert self._selected_display is not None
        connection_to_device = self._device.create_connection()
        unique_display_id_flag = self._selected_display.get_display_unique_id_flag()
        connection_to_device.send(
            f"shell:/system/bin/screencap -p {unique_display_id_flag}"
        )
        response = connection_to_device.read_all()
        if response and len(response) > 5 and response[5] == 0x0D:
            response = response.replace(b"\r\n", b"\n")
        return Image.open(io.BytesIO(response))

    def screenshot(self) -> Image.Image:
        screenshot = self._screenshot_without_reporting()
        self._reporter.add_message("AndroidAgentOS", "screenshot()", screenshot)
        return screenshot

    def shell(self, command: str) -> str:
        self._check_if_device_is_selected()
        self._check_if_display_is_selected()
        assert self._device is not None
        response: str = self._device.shell(command)
        self._reporter.add_message(
            "AndroidAgentOS",
            f"shell(command='{command}') -> '{response}'",
        )
        return response

    def tap(self, x: int, y: int) -> None:
        self._check_if_device_is_selected()
        self._check_if_display_is_selected()
        assert self._device is not None
        assert self._selected_display is not None
        display_flag = self._selected_display.get_display_id_flag()
        self._reporter.add_message(
            "AndroidAgentOS",
            f"tap(x={x}, y={y})",
            AnnotatedImage(self._screenshot_without_reporting, [(x, y)]),
        )
        self._device.shell(f"input {display_flag} tap {x} {y}")
        self._mouse_position = (x, y)
        self._reporter.add_message(
            "AndroidAgentOS",
            f"After tap(x={x}, y={y})",
            AnnotatedImage(self._screenshot_without_reporting, [(x, y)]),
        )

    def swipe(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        duration_in_ms: int = 1000,
    ) -> None:
        self._check_if_device_is_selected()
        self._check_if_display_is_selected()
        assert self._device is not None
        assert self._selected_display is not None
        display_flag = self._selected_display.get_display_id_flag()
        self._reporter.add_message(
            "AndroidAgentOS",
            (
                f"Swiping from (x1={x1}, y1={y1}) to (x2={x2}, y2={y2}) "
                f"in {duration_in_ms}ms"
            ),
            AnnotatedImage(self._screenshot_without_reporting, [(x1, y1)]),
        )
        self._device.shell(
            f"input {display_flag} swipe {x1} {y1} {x2} {y2} {duration_in_ms}"
        )
        self._mouse_position = (x2, y2)
        self._reporter.add_message(
            "AndroidAgentOS",
            f"After swiping from (x1={x1}, y1={y1}) to (x2={x2}, y2={y2})",
            AnnotatedImage(self._screenshot_without_reporting, [(x2, y2)]),
        )

    def drag_and_drop(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        duration_in_ms: int = 1000,
    ) -> None:
        self._check_if_device_is_selected()
        self._check_if_display_is_selected()
        assert self._device is not None
        assert self._selected_display is not None
        display_flag = self._selected_display.get_display_id_flag()
        self._reporter.add_message(
            "AndroidAgentOS",
            f"Dragging and dropping from (x1={x1}, y1={y1}) to (x2={x2}, y2={y2})",
            AnnotatedImage(self._screenshot_without_reporting, [(x1, y1)]),
        )

        self._device.shell(
            f"input {display_flag} draganddrop {x1} {y1} {x2} {y2} {duration_in_ms}"
        )
        self._mouse_position = (x2, y2)

        self._reporter.add_message(
            "AndroidAgentOS",
            f"After drag and drop from (x1={x1}, y1={y1}) to (x2={x2}, y2={y2})",
            AnnotatedImage(self._screenshot_without_reporting, [(x2, y2)]),
        )

    def type(self, text: str) -> None:
        if any(c not in string.printable or ord(c) < 32 or ord(c) > 126 for c in text):
            error_msg_nonprintable: str = (
                f"Text contains non-printable characters: {text} "
                + "or special characters which are not supported by the device"
            )
            raise RuntimeError(error_msg_nonprintable)
        self._check_if_device_is_selected()
        self._check_if_display_is_selected()
        assert self._device is not None
        assert self._selected_display is not None
        display_flag = self._selected_display.get_display_id_flag()
        escaped_text = shlex.quote(text)
        shell_safe_text = escaped_text.replace(" ", "%s")
        self._reporter.add_message(
            "AndroidAgentOS",
            f"Typing text: '{text}'",
            AnnotatedImage(self._screenshot_without_reporting),
        )
        self._device.shell(f"input {display_flag} text {shell_safe_text}")

        self._reporter.add_message(
            "AndroidAgentOS",
            f"After typing text: '{text}'",
            AnnotatedImage(self._screenshot_without_reporting),
        )

    def key_tap(self, key: ANDROID_KEY) -> None:
        if key not in get_args(ANDROID_KEY):
            error_msg_invalid_key: str = f"Invalid key: {key}"
            raise RuntimeError(error_msg_invalid_key)
        self._check_if_device_is_selected()
        self._check_if_display_is_selected()
        assert self._device is not None
        assert self._selected_display is not None
        display_flag = self._selected_display.get_display_id_flag()
        self._reporter.add_message(
            "AndroidAgentOS",
            f"Tapping key: '{key}'",
            AnnotatedImage(self._screenshot_without_reporting),
        )
        self._device.shell(f"input {display_flag} keyevent {key}")
        self._reporter.add_message(
            "AndroidAgentOS",
            f"After tapping key: '{key}'",
            AnnotatedImage(self._screenshot_without_reporting),
        )

    def key_combination(
        self, keys: List[ANDROID_KEY], duration_in_ms: int = 100
    ) -> None:
        if any(key not in get_args(ANDROID_KEY) for key in keys):
            error_msg_invalid_keys: str = f"Invalid key: {keys}"
            raise RuntimeError(error_msg_invalid_keys)

        if len(keys) < 2:
            error_msg_too_few: str = "Key combination must contain at least 2 keys"
            raise RuntimeError(error_msg_too_few)

        keys_string = " ".join(keys)
        self._check_if_device_is_selected()
        self._check_if_display_is_selected()
        assert self._device is not None
        assert self._selected_display is not None
        display_flag = self._selected_display.get_display_id_flag()
        self._reporter.add_message(
            "AndroidAgentOS",
            f"Performing key combination: '{keys_string}'",
            AnnotatedImage(self._screenshot_without_reporting),
        )
        self._device.shell(
            f"input {display_flag} keycombination -t {duration_in_ms} {keys_string}"
        )
        self._reporter.add_message(
            "AndroidAgentOS",
            f"key_combination(keys=[{', '.join(keys)}], duration_in_ms={duration_in_ms})",  # noqa: E501
            AnnotatedImage(self._screenshot_without_reporting),
        )

    def _check_if_device_is_selected(self) -> None:
        devices: list[AndroidDevice] = self._get_connected_devices()

        if not self._device:
            msg = "No device is selected, did you call on of the set_device methods?"
            raise RuntimeError(msg)

        for device in devices:
            if device.serial == self._device.serial:
                return
        msg = f"Device {self._device.serial} not found in connected devices"
        raise RuntimeError(msg)

    def _check_if_display_is_selected(self) -> None:
        if self._selected_display is None:
            msg = "No display is selected, did you call on of  the set_display methods?"
            raise RuntimeError(msg)

    def _get_connected_devices(self) -> list[AndroidDevice]:
        """
        Get the connected devices.
        """
        if not self._client:
            msg = "No adb client is connected, did you call the connect method?"
            raise RuntimeError(msg)
        devices: list[AndroidDevice] = self._client.devices()
        if not devices:
            msg = """No devices are connected,
            If you are using an emulator, make sure the emulator is running.
            If you are using a real device, make sure the device is connected.
            """
            raise RuntimeError(msg)
        return devices

    def get_connected_devices_serial_numbers(self) -> list[str]:
        """
        Get the connected devices serial numbers.
        """
        devices: list[AndroidDevice] = self._get_connected_devices()
        device_serial_numbers: list[str] = [device.serial for device in devices]
        self._reporter.add_message(
            "AndroidAgentOS",
            f"get_connected_devices_serial_numbers() -> {device_serial_numbers}",
        )
        return device_serial_numbers

    def get_selected_device_infos(self) -> tuple[str, AndroidDisplay]:
        """
        Get the selected device infos.
        """
        self._check_if_device_is_selected()
        self._check_if_display_is_selected()
        assert self._device is not None
        assert self._selected_display is not None
        self._reporter.add_message(
            "AndroidAgentOS",
            (
                "get_selected_device_infos() -> "
                f"Selected device serial number: '{self._device.serial}' "
                f"and selected display: '{self._selected_display}'"
            ),
        )
        return (self._device.serial, self._selected_display)

    def push(self, local_path: str, remote_path: str) -> None:
        """
        Push a file to the device.
        """
        self._check_if_device_is_selected()
        assert self._device is not None
        if not Path.exists(Path(local_path)):
            msg = f"Local path {local_path} does not exist"
            raise FileNotFoundError(msg)
        self._device.push(local_path, remote_path)
        self._reporter.add_message(
            "AndroidAgentOS",
            f"push(local_path='{local_path}', remote_path='{remote_path}')",
        )

    def pull(self, remote_path: str, local_path: str) -> None:
        """
        Pull a file from the device.
        """
        self._check_if_device_is_selected()
        assert self._device is not None
        Path.mkdir(Path.absolute(Path(local_path).parent), exist_ok=True)
        self._device.pull(remote_path, local_path)
        self._reporter.add_message(
            "AndroidAgentOS",
            f"pull(remote_path='{remote_path}', local_path='{local_path}')",
        )
