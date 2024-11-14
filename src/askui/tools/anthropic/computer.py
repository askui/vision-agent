from typing import Literal, TypedDict

from anthropic.types.beta import BetaToolComputerUse20241022Param

from .base import BaseAnthropicTool, ToolError, ToolResult

from ..utils import image_to_base64, scale_image_with_padding, scale_coordinates_back


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


PC_KEY = Literal['backspace', 'delete', 'enter', 'tab', 'escape', 'up', 'down', 'right', 'left', 'home', 'end', 'pageup', 'pagedown', 'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12', 'space', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '!', '"', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',', '-', '.', '/', ':', ';', '<', '=', '>', '?', '@', '[', '\\', ']', '^', '_', '`', '{', '|', '}', '~']


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
    "Page_Up": 'pageup',
    "Page_Down": 'pagedown',
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
    "F12": "f12"
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
    A tool that allows the agent to interact with the screen, keyboard, and mouse of the current computer.
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
        width = self.width
        height = self.height
        return {
            "display_width_px": width,
            "display_height_px": height,
        }

    def to_params(self) -> BetaToolComputerUse20241022Param:
        return {"name": self.name, "type": self.api_type, **self.options}

    def __init__(self, controller_client):
        super().__init__()
        self.controller_client = controller_client

        self.width = 1280
        self.height = 800

        self.real_screen_width = None
        self.real_screen_height = None

    def __call__(
        self,
        *,
        action: Action | None = None,
        text: str | None = None,
        coordinate: tuple[int, int] | None = None,
        **kwargs,
    ):
        if action is None:
            raise ToolError("Action is missing")
        
        if action in ("mouse_move", "left_click_drag"):
            if coordinate is None:
                raise ToolError(f"coordinate is required for {action}")
            if text is not None:
                raise ToolError(f"text is not accepted for {action}")
            if not isinstance(coordinate, list) or len(coordinate) != 2:
                raise ToolError(f"{coordinate} must be a tuple of length 2")
            if not all(isinstance(i, int) and i >= 0 for i in coordinate):
                raise ToolError(f"{coordinate} must be a tuple of non-negative ints")

            x, y = scale_coordinates_back(coordinate[0], coordinate[1], self.real_screen_width, self.real_screen_height, self.width, self.height)
            x, y = int(x), int(y)

            if action == "mouse_move":
                self.controller_client.mouse(x, y)
                return ToolResult()
            elif action == "left_click_drag":
                self.controller_client.mouse_down("left")
                self.controller_client.mouse(x, y)
                self.controller_client.mouse_up("left")
                return ToolResult()

        if action in ("key", "type"):
            if text is None:
                raise ToolError(f"text is required for {action}")
            if coordinate is not None:
                raise ToolError(f"coordinate is not accepted for {action}")
            if not isinstance(text, str):
                raise ToolError(output=f"{text} must be a string")

            if action == "key":
                if text in KEYSYM_MAP.keys():
                    text = KEYSYM_MAP[text]

                if text not in PC_KEY.__args__:
                    raise ToolError(f"Key {text} is not a valid PC_KEY from {', '.join(list(PC_KEY.__args__))}")
                self.controller_client.keyboard_pressed(text)
                self.controller_client.keyboard_release(text)
                return ToolResult()
            elif action == "type":
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
                raise ToolError(f"text is not accepted for {action}")
            if coordinate is not None:
                raise ToolError(f"coordinate is not accepted for {action}")

            if action == "screenshot":
                return self.screenshot()
            elif action == "cursor_position":
                # TODO: Implement in the future
                return ToolError("cursor_position is not implemented by this agent")
            elif action == "left_click":
                self.controller_client.click("left")
                return ToolResult()
            elif action == "right_click":
                self.controller_client.click("right")
                return ToolResult()
            elif action == "middle_click":
                self.controller_client.click("middle")
                return ToolResult()
            elif action == "double_click":
                self.controller_client.click("left", 2)
                return ToolResult()

        raise ToolError(f"Invalid action: {action}")

    def screenshot(self):
        """Take a screenshot of the current screen, scale it and return the base64 encoded image."""
        screenshot = self.controller_client.screenshot()
        self.real_screen_width = screenshot.width
        self.real_screen_height = screenshot.height
        scaled_screenshot = scale_image_with_padding(screenshot, 1280, 800)
        base64_image = image_to_base64(scaled_screenshot)
        return ToolResult(base64_image=base64_image)
