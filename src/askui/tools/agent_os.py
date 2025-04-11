from abc import ABC, abstractmethod
from typing import Literal
from PIL import Image

ModifierKey = Literal["command", "alt", "control", "shift", "right_shift"]
PcKey = Literal[
    "backspace",
    "delete",
    "enter",
    "tab",
    "escape",
    "up",
    "down",
    "right",
    "left",
    "home",
    "end",
    "pageup",
    "pagedown",
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
    "space",
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
    "!",
    '"',
    "#",
    "$",
    "%",
    "&",
    "'",
    "(",
    ")",
    "*",
    "+",
    ",",
    "-",
    ".",
    "/",
    ":",
    ";",
    "<",
    "=",
    ">",
    "?",
    "@",
    "[",
    "\\",
    "]",
    "^",
    "_",
    "`",
    "{",
    "|",
    "}",
    "~",
]


class AgentOs(ABC):
    @abstractmethod
    def connect(self) -> None:
        """Connect to the Agent OS."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the Agent OS."""
        pass
    
    @abstractmethod
    def screenshot(self, report: bool = True) -> Image.Image:
        """Take a screenshot of the current display."""
        raise NotImplementedError()

    @abstractmethod
    def mouse(self, x: int, y: int) -> None:
        """Move mouse to specified coordinates."""
        raise NotImplementedError()

    @abstractmethod
    def type(self, text: str, typing_speed: int = 50) -> None:
        """Type text."""
        raise NotImplementedError()

    @abstractmethod
    def click(
        self, button: Literal["left", "middle", "right"] = "left", count: int = 1
    ) -> None:
        """Click mouse button (repeatedly)."""
        raise NotImplementedError()

    @abstractmethod
    def mouse_down(self, button: Literal["left", "middle", "right"] = "left") -> None:
        """Press and hold mouse button."""
        raise NotImplementedError()

    @abstractmethod
    def mouse_up(self, button: Literal["left", "middle", "right"] = "left") -> None:
        """Release mouse button."""
        raise NotImplementedError()

    @abstractmethod
    def mouse_scroll(self, x: int, y: int) -> None:
        """Scroll mouse wheel horizontally and vertically."""
        raise NotImplementedError()

    @abstractmethod
    def keyboard_pressed(
        self, key: PcKey | ModifierKey, modifier_keys: list[ModifierKey] | None = None
    ) -> None:
        """Press and hold keyboard key."""
        raise NotImplementedError()

    @abstractmethod
    def keyboard_release(
        self, key: PcKey | ModifierKey, modifier_keys: list[ModifierKey] | None = None
    ) -> None:
        """Release keyboard key."""
        raise NotImplementedError()

    @abstractmethod
    def keyboard_tap(
        self, key: PcKey | ModifierKey, modifier_keys: list[ModifierKey] | None = None
    ) -> None:
        """Press and release keyboard key."""
        raise NotImplementedError()

    @abstractmethod
    def set_display(self, displayNumber: int = 1) -> None:
        """Set active display, e.g., when using multiple displays."""
        raise NotImplementedError()
