import os
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


def chunks(s: str, chunk_size: int) -> list[str]:
    return [s[i : i + chunk_size] for i in range(0, len(s), chunk_size)]


class ComputerTool(BaseAnthropicTool):
    """
    A tool that allows the agent to interact with the screen, keyboard, and mouse of the current computer.
    The tool parameters are defined by Anthropic and are not editable.
    """

    name: Literal["computer"] = "computer"
    api_type: Literal["computer_20241022"] = "computer_20241022"
    width: int
    height: int
    display_num: int | None

    _screenshot_delay = 2.0
    _scaling_enabled = True

    @property
    def options(self) -> ComputerToolOptions:
        # width, height = self.scale_coordinates(
        #     ScalingSource.COMPUTER, self.width, self.height
        # )
        width = self.width
        height = self.height
        return {
            "display_width_px": width,
            "display_height_px": height,
            "display_number": self.display_num,
        }

    def to_params(self) -> BetaToolComputerUse20241022Param:
        return {"name": self.name, "type": self.api_type, **self.options}

    def __init__(self, controller_client):
        super().__init__()
        self.controller_client = controller_client

        #self.width = int(os.getenv("WIDTH") or 0)
        #self.height = int(os.getenv("HEIGHT") or 0)
        self.width = 1280
        self.height = 800

        self.real_screen_width = None
        self.real_screen_height = None

        assert self.width and self.height, "WIDTH, HEIGHT must be set"
        if (display_num := os.getenv("DISPLAY_NUM")) is not None:
            self.display_num = int(display_num)
            self._display_prefix = f"DISPLAY=:{self.display_num} "
        else:
            self.display_num = None
            self._display_prefix = ""

        self.xdotool = f"{self._display_prefix}xdotool"

    def __call__(
        self,
        *,
        action: Action,
        text: str | None = None,
        coordinate: tuple[int, int] | None = None,
        **kwargs,
    ):
        if action in ("mouse_move", "left_click_drag"):
            if coordinate is None:
                raise ToolError(f"coordinate is required for {action}")
            if text is not None:
                raise ToolError(f"text is not accepted for {action}")
            if not isinstance(coordinate, list) or len(coordinate) != 2:
                raise ToolError(f"{coordinate} must be a tuple of length 2")
            if not all(isinstance(i, int) and i >= 0 for i in coordinate):
                raise ToolError(f"{coordinate} must be a tuple of non-negative ints")

            x, y = scale_coordinates_back(coordinate[0], coordinate[1], self.real_screen_width, self.real_screen_height, 1280, 800)
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
                # TODO: claude has other names for keys
                if text == "Return":
                    text = "enter"

                if text not in PC_KEY.__args__:
                    raise ToolError(f"Key {text} is not a valid PC_KEY")
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
