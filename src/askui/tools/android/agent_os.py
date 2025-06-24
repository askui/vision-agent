from abc import ABC, abstractmethod
from typing import List, Literal

from PIL import Image

ANDROID_KEY = Literal[  # pylint: disable=C0103
    "HOME",
    "BACK",
    "CALL",
    "ENDCALL",
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
    "STAR",
    "POUND",
    "DPAD_UP",
    "DPAD_DOWN",
    "DPAD_LEFT",
    "DPAD_RIGHT",
    "DPAD_CENTER",
    "VOLUME_UP",
    "VOLUME_DOWN",
    "POWER",
    "CAMERA",
    "CLEAR",
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "J",
    "K",
    "L",
    "M",
    "N",
    "O",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "U",
    "V",
    "W",
    "X",
    "Y",
    "Z",
    "COMMA",
    "PERIOD",
    "ALT_LEFT",
    "ALT_RIGHT",
    "SHIFT_LEFT",
    "SHIFT_RIGHT",
    "TAB",
    "SPACE",
    "SYM",
    "EXPLORER",
    "ENVELOPE",
    "ENTER",
    "DEL",
    "GRAVE",
    "MINUS",
    "EQUALS",
    "LEFT_BRACKET",
    "RIGHT_BRACKET",
    "BACKSLASH",
    "SEMICOLON",
    "APOSTROPHE",
    "SLASH",
    "AT",
    "NUM",
    "HEADSETHOOK",
    "FOCUS",
    "PLUS",
    "MENU",
    "NOTIFICATION",
    "SEARCH",
    "MEDIA_PLAY_PAUSE",
    "MEDIA_STOP",
    "MEDIA_NEXT",
    "MEDIA_PREVIOUS",
    "MEDIA_REWIND",
    "MEDIA_FAST_FORWARD",
    "MUTE",
    "PAGE_UP",
    "PAGE_DOWN",
    "SWITCH_CHARSET",
    "ESCAPE",
    "FORWARD_DEL",
    "CTRL_LEFT",
    "CTRL_RIGHT",
    "CAPS_LOCK",
    "SCROLL_LOCK",
    "FUNCTION",
    "BREAK",
    "MOVE_HOME",
    "MOVE_END",
    "INSERT",
    "FORWARD",
    "MEDIA_PLAY",
    "MEDIA_PAUSE",
    "MEDIA_CLOSE",
    "MEDIA_EJECT",
    "MEDIA_RECORD",
    "F1",
    "F2",
    "F3",
    "F4",
    "F5",
    "F6",
    "F7",
    "F8",
    "F9",
    "F10",
    "F11",
    "F12",
    "NUM_LOCK",
    "NUMPAD_0",
    "NUMPAD_1",
    "NUMPAD_2",
    "NUMPAD_3",
    "NUMPAD_4",
    "NUMPAD_5",
    "NUMPAD_6",
    "NUMPAD_7",
    "NUMPAD_8",
    "NUMPAD_9",
    "NUMPAD_DIVIDE",
    "NUMPAD_MULTIPLY",
    "NUMPAD_SUBTRACT",
    "NUMPAD_ADD",
    "NUMPAD_DOT",
    "NUMPAD_COMMA",
    "NUMPAD_ENTER",
    "NUMPAD_EQUALS",
    "NUMPAD_LEFT_PAREN",
    "NUMPAD_RIGHT_PAREN",
    "VOLUME_MUTE",
    "INFO",
    "CHANNEL_UP",
    "CHANNEL_DOWN",
    "ZOOM_IN",
    "ZOOM_OUT",
    "WINDOW",
    "GUIDE",
    "BOOKMARK",
    "CAPTIONS",
    "SETTINGS",
    "APP_SWITCH",
    "LANGUAGE_SWITCH",
    "CONTACTS",
    "CALENDAR",
    "MUSIC",
    "CALCULATOR",
    "ASSIST",
    "BRIGHTNESS_DOWN",
    "BRIGHTNESS_UP",
    "MEDIA_AUDIO_TRACK",
    "SLEEP",
    "WAKEUP",
    "PAIRING",
    "MEDIA_TOP_MENU",
    "LAST_CHANNEL",
    "TV_DATA_SERVICE",
    "VOICE_ASSIST",
    "HELP",
    "NAVIGATE_PREVIOUS",
    "NAVIGATE_NEXT",
    "NAVIGATE_IN",
    "NAVIGATE_OUT",
    "DPAD_UP_LEFT",
    "DPAD_DOWN_LEFT",
    "DPAD_UP_RIGHT",
    "DPAD_DOWN_RIGHT",
    "MEDIA_SKIP_FORWARD",
    "MEDIA_SKIP_BACKWARD",
    "MEDIA_STEP_FORWARD",
    "MEDIA_STEP_BACKWARD",
    "SOFT_SLEEP",
    "CUT",
    "COPY",
    "PASTE",
    "ALL_APPS",
    "REFRESH",
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
    def drag_and_drop(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        duration_in_ms: int = 1000,
    ) -> None:
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
    def key_tap(self, key: ANDROID_KEY) -> None:
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
    def set_device_by_serial_number(self, device_sn: str) -> None:
        """
        Sets the active device for screen interactions by serial number.
        """
        raise NotImplementedError

    @abstractmethod
    def get_connected_displays(self) -> list[AndroidDisplay]:
        """
        Gets the connected displays for screen interactions.
        """
        raise NotImplementedError
