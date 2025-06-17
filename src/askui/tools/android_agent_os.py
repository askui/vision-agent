from abc import ABC, abstractmethod
from typing import List, Literal

from PIL import Image

ANDROID_KEY = Literal[  # pylint: disable=C0103
    "home",
    "back",
    "call",
    "endcall",
    "0",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "star",
    "pound",
    "dpad_up",
    "dpad_down",
    "dpad_left",
    "dpad_right",
    "dpad_center",
    "volume_up",
    "volume_down",
    "power",
    "camera",
    "clear",
    "a",
    "b",
    "c",
    "d",
    "e",
    "f",
    "g",
    "h",
    "i",
    "j",
    "k",
    "l",
    "m",
    "n",
    "o",
    "p",
    "q",
    "r",
    "s",
    "t",
    "u",
    "v",
    "w",
    "x",
    "y",
    "z",
    "comma",
    "period",
    "alt_left",
    "alt_right",
    "shift_left",
    "shift_right",
    "tab",
    "space",
    "sym",
    "explorer",
    "envelope",
    "enter",
    "del",
    "grave",
    "minus",
    "equals",
    "left_bracket",
    "right_bracket",
    "backslash",
    "semicolon",
    "apostrophe",
    "slash",
    "at",
    "num",
    "headsethook",
    "focus",
    "plus",
    "menu",
    "notification",
    "search",
    "media_play_pause",
    "media_stop",
    "media_next",
    "media_previous",
    "media_rewind",
    "media_fast_forward",
    "mute",
    "page_up",
    "page_down",
    "switch_charset",
    "escape",
    "forward_del",
    "ctrl_left",
    "ctrl_right",
    "caps_lock",
    "scroll_lock",
    "function",
    "break",
    "move_home",
    "move_end",
    "insert",
    "forward",
    "media_play",
    "media_pause",
    "media_close",
    "media_eject",
    "media_record",
    "f1",
    "f2",
    "f3",
    "f4",
    "f5",
    "f6",
    "f7",
    "f8",
    "f9",
    "f10",
    "f11",
    "f12",
    "num_lock",
    "numpad_0",
    "numpad_1",
    "numpad_2",
    "numpad_3",
    "numpad_4",
    "numpad_5",
    "numpad_6",
    "numpad_7",
    "numpad_8",
    "numpad_9",
    "numpad_divide",
    "numpad_multiply",
    "numpad_subtract",
    "numpad_add",
    "numpad_dot",
    "numpad_comma",
    "numpad_enter",
    "numpad_equals",
    "numpad_left_paren",
    "numpad_right_paren",
    "volume_mute",
    "info",
    "channel_up",
    "channel_down",
    "zoom_in",
    "zoom_out",
    "window",
    "guide",
    "bookmark",
    "captions",
    "settings",
    "app_switch",
    "language_switch",
    "contacts",
    "calendar",
    "music",
    "calculator",
    "assist",
    "brightness_down",
    "brightness_up",
    "media_audio_track",
    "sleep",
    "wakeup",
    "pairing",
    "media_top_menu",
    "last_channel",
    "tv_data_service",
    "voice_assist",
    "help",
    "navigate_previous",
    "navigate_next",
    "navigate_in",
    "navigate_out",
    "dpad_up_left",
    "dpad_down_left",
    "dpad_up_right",
    "dpad_down_right",
    "media_skip_forward",
    "media_skip_backward",
    "media_step_forward",
    "media_step_backward",
    "soft_sleep",
    "cut",
    "copy",
    "paste",
    "all_apps",
    "refresh",
]


class AndroidDisplay:
    def __init__(
        self, unique_display_id: int, display_name: str, display_index: int
    ) -> None:
        self.unique_display_id: int = unique_display_id
        self.display_name: str = display_name
        self.display_index: int = display_index

    def __repr__(self) -> str:
        return (
            f"AndroidDisplay(unique_display_id={self.unique_display_id}, "
            f"display_name={self.display_name}, display_index={self.display_index})"
        )


class AndroidAgentOs(ABC):
    """
    Abstract base class for Android Agent OS. Cannot be instantiated directly.

    This class defines the interface for operating system interactions including
    mouse control, keyboard input, and screen capture functionality.
    Implementations should provide concrete functionality for these abstract
    methods.
    """

    @abstractmethod
    def connect(self) -> None:
        """
        Establishes a connection to the Agent OS.

        This method is called before performing any OS-level operations.
        It handles any necessary setup or initialization required for the OS
        interaction.
        """
        raise NotImplementedError

    @abstractmethod
    def disconnect(self) -> None:
        """
        Terminates the connection to the Agent OS.

        This method is called after all OS-level operations are complete.
        It handles any necessary cleanup or resource release.
        """
        raise NotImplementedError

    @abstractmethod
    def screenshot(self) -> Image.Image:
        """
        Captures a screenshot of the current display.

        Returns:
            Image.Image: A PIL Image object containing the screenshot.
        """
        raise NotImplementedError

    @abstractmethod
    def mouse_move(self, x: int, y: int) -> None:
        """
        Moves the mouse cursor to specified screen coordinates.

        Args:
            x (int): The horizontal coordinate (in pixels) to move to.
            y (int): The vertical coordinate (in pixels) to move to.
        """
        raise NotImplementedError

    @abstractmethod
    def type(self, text: str) -> None:
        """
        Simulates typing text as if entered on a keyboard.

        Args:
            text (str): The text to be typed.
        """
        raise NotImplementedError

    @abstractmethod
    def tap(self, x: int, y: int) -> None:
        """
        Simulates tapping a screen at specified coordinates.

        Args:
            button (Literal["left", "middle", "right"], optional): The mouse
                button to click. Defaults to `"left"`.
            count (int, optional): Number of times to click. Defaults to `1`.
        """
        raise NotImplementedError

    @abstractmethod
    def swipe(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        duration_in_ms: int = 1000,
    ) -> None:
        """
        Simulates swiping a screen from one point to another.

        Args:
            x1 (int): The horizontal coordinate of the start point.
            y1 (int): The vertical coordinate of the start point.
            x2 (int): The horizontal coordinate of the end point.
            y2 (int): The vertical coordinate of the end point.
            duration_in_ms (int, optional): The duration of the swipe in
                milliseconds. Defaults to `1000`.
        """
        raise NotImplementedError

    @abstractmethod
    def drag_and_drop(self, x1: int, y1: int, x2: int, y2: int) -> None:
        """
        Simulates dragging and dropping an object from one point to another.

        Args:
            x1 (int): The horizontal coordinate of the start point.
            y1 (int): The vertical coordinate of the start point.
            x2 (int): The horizontal coordinate of the end point.
            y2 (int): The vertical coordinate of the end point.
            duration_in_ms (int, optional): The duration of the drag and drop in
                milliseconds. Defaults to `1000`.
        """
        raise NotImplementedError

    @abstractmethod
    def shell(self, command: str) -> str:
        """
        Executes a shell command on the Android device.
        """
        raise NotImplementedError

    @abstractmethod
    def key_event(self, key: ANDROID_KEY) -> None:
        """
        Simulates a key event on the Android device.
        """
        raise NotImplementedError

    @abstractmethod
    def key_combination(
        self, keys: List[ANDROID_KEY], duration_in_ms: int = 100
    ) -> None:
        """
        Simulates a key combination on the Android device.

        Args:
            keys (List[ANDROID_KEY]): The keys to be pressed.
            duration_in_ms (int, optional): The duration of the key combination in
                milliseconds. Defaults to `100`.
        """
        raise NotImplementedError

    @abstractmethod
    def set_display_by_index(self, display_index: int = 0) -> None:
        """
        Sets the active display for screen interactions by index.
        """
        raise NotImplementedError

    @abstractmethod
    def set_display_by_id(self, display_id: int) -> None:
        """
        Sets the active display for screen interactions by id.
        """
        raise NotImplementedError

    @abstractmethod
    def set_display_by_name(self, display_name: str) -> None:
        """
        Sets the active display for screen interactions by name.
        """
        raise NotImplementedError

    @abstractmethod
    def set_device_by_index(self, device_index: int = 0) -> None:
        """
        Sets the active device for screen interactions by index.
        """
        raise NotImplementedError

    @abstractmethod
    def set_device_by_name(self, device_name: str) -> None:
        """
        Sets the active device for screen interactions by name.
        """
        raise NotImplementedError

    @abstractmethod
    def get_connected_displays(self) -> list[AndroidDisplay]:
        """
        Gets the connected displays for screen interactions.
        """
        raise NotImplementedError
