from typing import Any, Literal, TypedDict

from anthropic.types.beta import BetaToolComputerUse20241022Param

from askui.tools.agent_os import AgentOs
from askui.utils.image_utils import (
    image_to_base64,
    scale_coordinates_back,
    scale_image_with_padding,
)

from .base import BaseAnthropicTool, ToolError, ToolResult

Action = Literal[
    "key",
    "type",
    "mouse_move",
    "left_click",
    "left_click_drag",
    "right_click",
    "middle_click",
    "double_click",
    "screenshot",
    "cursor_position",
]


PC_KEY = [
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


KEYSYM_MAP = {
    "BackSpace": "backspace",
    "Delete": "delete",
    "Return": "enter",
    "Enter": "enter",
    "Tab": "tab",
    "Escpage": "escape",
    "Up": "up",
    "Down": "down",
    "Right": "right",
    "Left": "left",
    "Home": "home",
    "End": "end",
    "Page_Up": "pageup",
    "Page_Down": "pagedown",
    "F1": "f1",
    "F2": "f2",
    "F3": "f3",
    "F4": "f4",
    "F5": "f5",
    "F6": "f6",
    "F7": "f7",
    "F8": "f8",
    "F9": "f9",
    "F10": "f10",
    "F11": "f11",
    "F12": "f12",
}


class Resolution(TypedDict):
    width: int
    height: int


# sizes above XGA/WXGA are not recommended (see README.md)
# scale down to one of these targets if ComputerTool._scaling_enabled is set
MAX_SCALING_TARGETS: dict[str, Resolution] = {
    "XGA": Resolution(width=1024, height=768),  # 4:3
    "WXGA": Resolution(width=1280, height=800),  # 16:10
    "FWXGA": Resolution(width=1366, height=768),  # ~16:9
}


class ComputerToolOptions(TypedDict):
    display_height_px: int
    display_width_px: int
    display_number: int | None


class ComputerTool(BaseAnthropicTool):
    """
    A tool that allows the agent to interact with the screen, keyboard, and mouse of
    the current computer.
    The tool parameters are defined by Anthropic and are not editable.
    """

    name: Literal["computer"] = "computer"
    api_type: Literal["computer_20241022"] = "computer_20241022"
    width: int
    height: int

    _screenshot_delay = 2.0
    _scaling_enabled = True

    @property
    def options(self) -> ComputerToolOptions:
        return {
            "display_width_px": self.width,
            "display_height_px": self.height,
        }

    def to_params(self) -> BetaToolComputerUse20241022Param:
        return {"name": self.name, "type": self.api_type, **self.options}

    def __init__(self, controller_client: AgentOs) -> None:
        super().__init__()
        self.controller_client = controller_client

        self.width = 1280
        self.height = 800

        self.real_screen_width = None
        self.real_screen_height = None

    def __call__(  # noqa: C901
        self,
        *,
        action: Action | None = None,
        text: str | None = None,
        coordinate: tuple[int, int] | None = None,
        **kwargs: Any,  # noqa: ARG002
    ) -> ToolResult:
        """Execute computer action."""
        if action is None:
            error_msg = "Action is missing"
            raise ToolError(error_msg)

        if action in ("mouse_move", "left_click_drag"):
            if coordinate is None:
                error_msg = f"coordinate is required for {action}"
                raise ToolError(error_msg)
            if text is not None:
                error_msg = f"text is not accepted for {action}"
                raise ToolError(error_msg)
            if not isinstance(coordinate, list) or len(coordinate) != 2:
                error_msg = f"{coordinate} must be a tuple of length 2"
                raise ToolError(error_msg)
            if not all(isinstance(i, int) and i >= 0 for i in coordinate):
                error_msg = f"{coordinate} must be a tuple of non-negative ints"
                raise ToolError(error_msg)

            x, y = scale_coordinates_back(
                coordinate[0],
                coordinate[1],
                self.real_screen_width,
                self.real_screen_height,
                self.width,
                self.height,
            )
            x, y = int(x), int(y)

            if action == "mouse_move":
                self.controller_client.mouse(x, y)
                return ToolResult()
            if action == "left_click_drag":
                self.controller_client.mouse_down("left")
                self.controller_client.mouse(x, y)
                self.controller_client.mouse_up("left")
                return ToolResult()

        if action in ("key", "type"):
            if text is None:
                error_msg = f"text is required for {action}"
                raise ToolError(error_msg)
            if coordinate is not None:
                error_msg = f"coordinate is not accepted for {action}"
                raise ToolError(error_msg)
            if not isinstance(text, str):
                error_msg = f"{text} must be a string"
                raise ToolError(error_msg)

            if action == "key":
                if text in KEYSYM_MAP.keys():
                    text = KEYSYM_MAP[text]

                if text not in PC_KEY:
                    error_msg = (
                        f"Key {text} is not a valid PC_KEY from {', '.join(PC_KEY)}"
                    )
                    raise ToolError(error_msg)
                self.controller_client.keyboard_pressed(text)
                self.controller_client.keyboard_release(text)
                return ToolResult()
            if action == "type":
                self.controller_client.type(text)
                return ToolResult()

        if action in (
            "left_click",
            "right_click",
            "double_click",
            "middle_click",
            "screenshot",
            "cursor_position",
        ):
            if text is not None:
                error_msg = f"text is not accepted for {action}"
                raise ToolError(error_msg)
            if coordinate is not None:
                error_msg = f"coordinate is not accepted for {action}"
                raise ToolError(error_msg)

            if action == "screenshot":
                return self.screenshot()
            if action == "cursor_position":
                error_msg = "cursor_position is not implemented by this agent"
                raise ToolError(error_msg)
            if action == "left_click":
                self.controller_client.click("left")
                return ToolResult()
            if action == "right_click":
                self.controller_client.click("right")
                return ToolResult()
            if action == "middle_click":
                self.controller_client.click("middle")
                return ToolResult()
            if action == "double_click":
                self.controller_client.click("left", 2)
                return ToolResult()

        error_msg = f"Invalid action: {action}"
        raise ToolError(error_msg)

    def screenshot(self) -> ToolResult:
        """
        Take a screenshot of the current screen, scale it and return the base64
        encoded image.
        """
        screenshot = self.controller_client.screenshot()
        self.real_screen_width = screenshot.width
        self.real_screen_height = screenshot.height
        scaled_screenshot = scale_image_with_padding(screenshot, 1280, 800)
        base64_image = image_to_base64(scaled_screenshot)
        return ToolResult(base64_image=base64_image)
