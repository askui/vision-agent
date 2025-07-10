import sys
import time
from abc import ABC
from dataclasses import dataclass
from typing import Annotated, Literal, TypedDict, cast, get_args

from anthropic.types.beta import (
    BetaToolComputerUse20241022Param,
    BetaToolComputerUse20250124Param,
)
from PIL import Image
from pydantic import Field, validate_call
from typing_extensions import Self, override

from askui.tools.agent_os import AgentOs, ModifierKey, PcKey
from askui.utils.image_utils import scale_coordinates_back, scale_image_with_padding

from ..models.shared.tools import InputSchema, Tool

Action20241022 = Literal[
    "cursor_position",
    "double_click",
    "key",
    "left_click",
    "left_click_drag",
    "middle_click",
    "mouse_move",
    "right_click",
    "screenshot",
    "type",
]

Action20250124 = (
    Action20241022
    | Literal[
        "hold_key",
        "left_mouse_down",
        "left_mouse_up",
        "scroll",
        "triple_click",
        "wait",
    ]
)

ScrollDirection = Literal["up", "down", "left", "right"]

XDOTOOL_TO_MODIFIER_KEY_MAP: dict[str, ModifierKey] = {
    # Aliases
    "alt": "alt",
    "ctrl": "command" if sys.platform == "darwin" else "control",
    "cmd": "command",
    "shift": "shift",
    "super": "command",
    "meta": "command",
    # Real keys
    "Control_L": "control",
    "Control_R": "control",
    "Shift_L": "shift",
    "Shift_R": "right_shift",
    "Alt_L": "alt",
    "Alt_R": "alt",
    "Super_L": "command",
    "Super_R": "command",
    "Meta_L": "command",
    "Meta_R": "command",
}

XDOTOOL_TO_PC_KEY_MAP: dict[str, PcKey] = {
    "space": "space",
    # Navigation and control
    "BackSpace": "backspace",
    "Delete": "delete",
    "Return": "enter",
    "Tab": "tab",
    "Escape": "escape",
    "Up": "up",
    "Down": "down",
    "Right": "right",
    "Left": "left",
    "Home": "home",
    "End": "end",
    "Page_Up": "pageup",
    "Page_Down": "pagedown",
    # Function keys
    **{f"F{i}": cast("PcKey", f"f{i}") for i in range(1, 13)},
    # Symbols
    "exclam": "!",
    "quotedbl": '"',
    "numbersign": "#",
    "dollar": "$",
    "percent": "%",
    "ampersand": "&",
    "apostrophe": "'",
    "parenleft": "(",
    "parenright": ")",
    "asterisk": "*",
    "plus": "+",
    "comma": ",",
    "minus": "-",
    "period": ".",
    "slash": "/",
    "colon": ":",
    "semicolon": ";",
    "less": "<",
    "equal": "=",
    "greater": ">",
    "question": "?",
    "at": "@",
    "bracketleft": "[",
    "backslash": "\\",
    "bracketright": "]",
    "asciicircum": "^",
    "underscore": "_",
    "grave": "`",
    "braceleft": "{",
    "bar": "|",
    "braceright": "}",
    "asciitilde": "~",
    # Digits and letters
    **{
        ch: cast("PcKey", ch)
        for ch in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    },
}

XDOTOOL_TO_KEY_MAP = XDOTOOL_TO_MODIFIER_KEY_MAP | XDOTOOL_TO_PC_KEY_MAP

RELATIVE_SCROLL_FACTOR = 0.1
"""
The factor by which the scroll amount is multiplied together with the real screen
resolution to get the actual scroll amount. Represents the relative height/width
of the screen (e.g., 0.1 means that 1 scroll amount equals 10% of the screen height
or width) that equals 1 scroll amount.

Example of how the scroll amount is calculated:
- real screen resolution: 1920x1080
- scroll amount: 1
- relative scroll factor: 0.1
- actual scroll amount: 1 * 0.1 * 1920 = 192 or 1 * 0.1 * 1080 = 108
"""


@dataclass
class KeyboardParam:
    key: PcKey | ModifierKey
    modifier_keys: list[ModifierKey] | None = None

    @classmethod
    def from_xdotool(cls, keystroke: str) -> Self:
        """
        Convert an xdotool keystroke (see
        [xdotool documentation](https://www.mankier.com/1/xdotool#Keyboard_Commands))
        to a `KeyboardParam`.

        Args:
            keystroke (str): The xdotool keystroke to convert.

        Example:
        `"ctrl+shift+a"` -> `KeyboardParam(key="a", modifier_keys=["control", "shift"])`
        """
        keys = keystroke.split("+")
        key = keys.pop()
        if key not in XDOTOOL_TO_KEY_MAP:
            err_msg = (
                f"Unknown key: {key} "
                f"(expected one of {list(XDOTOOL_TO_KEY_MAP.keys())})"
            )
            raise ValueError(err_msg)

        return cls(
            key=XDOTOOL_TO_KEY_MAP[key],
            modifier_keys=[XDOTOOL_TO_MODIFIER_KEY_MAP[k] for k in keys],
        )


class ActionNotImplementedError(NotImplementedError):
    def __init__(self, action: Action20250124, tool_name: str) -> None:
        self.action = action
        self.tool_name = tool_name
        super().__init__(
            f'Action "{action}" has not been implemented by tool "{tool_name}"'
        )


class BetaToolComputerUseParamBase(TypedDict):
    name: Literal["computer"]
    display_width_px: int
    display_height_px: int


class ComputerToolBase(Tool, ABC):
    def __init__(
        self,
        agent_os: AgentOs,
        input_schema: InputSchema,
    ) -> None:
        super().__init__(
            name="computer",
            description="A tool for interacting with the computer",
            input_schema=input_schema,
        )
        self._agent_os = agent_os
        self._width = 1280
        self._height = 800
        self._real_screen_width: int | None = None
        self._real_screen_height: int | None = None

    @property
    def params_base(
        self,
    ) -> BetaToolComputerUseParamBase:
        return {
            "name": self.name,  # type: ignore[typeddict-item]
            "display_width_px": self._width,
            "display_height_px": self._height,
        }

    @override
    @validate_call
    def __call__(  # noqa: C901
        self,
        action: Action20241022,
        text: str | None = None,
        coordinate: tuple[Annotated[int, Field(ge=0)], Annotated[int, Field(ge=0)]]
        | None = None,
    ) -> Image.Image | None:
        match action:
            case "cursor_position":
                raise ActionNotImplementedError(action, self.name)
            case "double_click":
                return self._agent_os.click("left", 2)
            case "key":
                return self._key(keystroke=text)  # type: ignore[arg-type]
            case "left_click":
                return self._agent_os.click("left")
            case "left_click_drag":
                return self._left_click_drag(coordinate)  # type: ignore[arg-type]
            case "middle_click":
                return self._agent_os.click("middle")
            case "mouse_move":
                return self._mouse_move(coordinate)  # type: ignore[arg-type]
            case "right_click":
                return self._agent_os.click("right")
            case "screenshot":
                return self._screenshot()
            case "type":
                return self._type(text)  # type: ignore[arg-type]

    @validate_call
    def _type(self, text: str) -> None:
        self._agent_os.type(text)

    @validate_call
    def _key(self, keystroke: str) -> None:
        keyboard_param = KeyboardParam.from_xdotool(keystroke)
        self._agent_os.keyboard_pressed(
            key=keyboard_param.key, modifier_keys=keyboard_param.modifier_keys
        )
        self._agent_os.keyboard_release(
            key=keyboard_param.key, modifier_keys=keyboard_param.modifier_keys
        )

    @validate_call
    def _keyboard_pressed(self, keystroke: str) -> None:
        keyboard_param = KeyboardParam.from_xdotool(keystroke)
        self._agent_os.keyboard_pressed(
            key=keyboard_param.key, modifier_keys=keyboard_param.modifier_keys
        )

    @validate_call
    def _keyboard_released(self, keystroke: str) -> None:
        keyboard_param = KeyboardParam.from_xdotool(keystroke)
        self._agent_os.keyboard_release(
            key=keyboard_param.key, modifier_keys=keyboard_param.modifier_keys
        )

    def _get_real_screen_resolution(self) -> tuple[int, int]:
        if self._real_screen_width is None or self._real_screen_height is None:
            screenshot = self._agent_os.screenshot()
            self._real_screen_width = screenshot.width
            self._real_screen_height = screenshot.height
        return self._real_screen_width, self._real_screen_height

    def _scale_coordinates_back(
        self,
        coordinate: tuple[Annotated[int, Field(ge=0)], Annotated[int, Field(ge=0)]],
    ) -> tuple[int, int]:
        real_screen_width, real_screen_height = self._get_real_screen_resolution()
        x, y = scale_coordinates_back(
            coordinate[0],
            coordinate[1],
            real_screen_width,
            real_screen_height,
            self._width,
            self._height,
        )
        x, y = int(x), int(y)
        return x, y

    @validate_call
    def _mouse_move(
        self,
        coordinate: tuple[Annotated[int, Field(ge=0)], Annotated[int, Field(ge=0)]],
    ) -> None:
        x, y = self._scale_coordinates_back(coordinate)
        self._agent_os.mouse_move(x, y)

    @validate_call
    def _left_click_drag(
        self,
        coordinate: tuple[Annotated[int, Field(ge=0)], Annotated[int, Field(ge=0)]],
    ) -> None:
        x, y = self._scale_coordinates_back(coordinate)
        # holding key pressed does not seem to work
        self._agent_os.mouse_down("left")
        self._agent_os.mouse_move(x, y)
        self._agent_os.mouse_up("left")

    def _screenshot(self) -> Image.Image:
        """
        Take a screenshot of the current screen, scale it and return it
        """
        screenshot = self._agent_os.screenshot()
        self._real_screen_width = screenshot.width
        self._real_screen_height = screenshot.height
        return scale_image_with_padding(screenshot, self._width, self._height)


class Computer20241022Tool(ComputerToolBase):
    type: Literal["computer_20241022"] = "computer_20241022"

    def __init__(
        self,
        agent_os: AgentOs,
    ) -> None:
        super().__init__(
            agent_os=agent_os,
            input_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": list(get_args(Action20241022)),
                    },
                    "text": {
                        "type": "string",
                    },
                    "coordinate": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "integer", "minimum": 0},
                            "y": {"type": "integer", "minimum": 0},
                        },
                    },
                },
                "required": ["action"],
            },
        )

    @override
    def to_params(
        self,
    ) -> BetaToolComputerUse20241022Param:
        return {
            **self.params_base,
            "type": self.type,
        }


class Computer20250124Tool(ComputerToolBase):
    type: Literal["computer_20250124"] = "computer_20250124"

    def __init__(
        self,
        agent_os: AgentOs,
    ) -> None:
        super().__init__(
            agent_os=agent_os,
            input_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": list(get_args(Action20250124)),
                    },
                    "text": {
                        "type": "string",
                    },
                    "coordinate": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "integer", "minimum": 0},
                            "y": {"type": "integer", "minimum": 0},
                        },
                    },
                    "scroll_direction": {
                        "type": "string",
                        "enum": list(get_args(ScrollDirection)),
                    },
                    "scroll_amount": {"type": "integer", "minimum": 0},
                    "duration": {"type": "number", "minimum": 0.0, "maximum": 100.0},
                    "key": {"type": "string"},
                },
                "required": ["action"],
            },
        )

    @override
    def to_params(
        self,
    ) -> BetaToolComputerUse20250124Param:
        return {
            **self.params_base,
            "type": self.type,
        }

    @override
    @validate_call
    def __call__(  # noqa: C901
        self,
        action: Action20250124,
        text: str | None = None,
        coordinate: tuple[Annotated[int, Field(ge=0)], Annotated[int, Field(ge=0)]]
        | None = None,
        scroll_direction: ScrollDirection | None = None,
        scroll_amount: Annotated[int, Field(ge=0)] | None = None,
        duration: Annotated[float, Field(ge=0.0, le=100.0)] | None = None,
        key: str | None = None,  # maybe not all keys supported
    ) -> Image.Image | None:
        match action:
            case "hold_key":
                self._hold_key(keystroke=text, duration=duration)  # type: ignore[arg-type]
            case "left_mouse_down":
                self._agent_os.mouse_down("left")
            case "left_mouse_up":
                self._agent_os.mouse_up("left")
            case "left_click":
                self._click("left", coordinate=coordinate, key=key)
            case "right_click":
                self._click("right", coordinate=coordinate, key=key)
            case "middle_click":
                self._click("middle", coordinate=coordinate, key=key)
            case "double_click":
                self._click("left", count=2, coordinate=coordinate, key=key)
            case "scroll":
                self._scroll(
                    scroll_direction=scroll_direction,  # type: ignore[arg-type]
                    scroll_amount=scroll_amount,  # type: ignore[arg-type]
                    text=text,
                    coordinate=coordinate,
                )
                return self._screenshot()
            case "triple_click":
                self._click("left", count=3, coordinate=coordinate, key=key)
            case "wait":
                self._wait(duration=duration)  # type: ignore[arg-type]
            case _:
                return super().__call__(action, text, coordinate)
        return None

    @validate_call
    def _hold_key(
        self, keystroke: str, duration: Annotated[float, Field(ge=0.0, le=100.0)]
    ) -> None:
        self._keyboard_pressed(keystroke=keystroke)
        time.sleep(duration)
        self._keyboard_released(keystroke=keystroke)

    @validate_call
    def _scroll(
        self,
        scroll_direction: ScrollDirection,
        scroll_amount: Annotated[int, Field(ge=0)],
        text: str | None = None,
        coordinate: tuple[Annotated[int, Field(ge=0)], Annotated[int, Field(ge=0)]]
        | None = None,
    ) -> None:
        real_screen_width, real_screen_height = self._get_real_screen_resolution()
        x = int(RELATIVE_SCROLL_FACTOR * scroll_amount * real_screen_width)
        y = int(RELATIVE_SCROLL_FACTOR * scroll_amount * real_screen_height)
        if coordinate is not None:
            self._mouse_move(coordinate)
        if text is not None:
            self._keyboard_pressed(text)
        match scroll_direction:
            case "up":
                self._agent_os.mouse_scroll(0, y)
            case "down":
                self._agent_os.mouse_scroll(0, -y)
            case "left":
                self._agent_os.mouse_scroll(x, 0)
            case "right":
                self._agent_os.mouse_scroll(-x, 0)
        if text is not None:
            self._keyboard_released(text)

    @validate_call
    def _wait(self, duration: Annotated[float, Field(ge=0.0, le=100.0)]) -> None:
        time.sleep(duration)

    def _click(
        self,
        button: Literal["left", "right", "middle"],
        count: int = 1,
        coordinate: tuple[Annotated[int, Field(ge=0)], Annotated[int, Field(ge=0)]]
        | None = None,
        key: str | None = None,
    ) -> None:
        if coordinate is not None:
            self._mouse_move(coordinate)
        if key is not None:
            self._keyboard_pressed(keystroke=key)
        self._agent_os.click(button, count)
        if key is not None:
            self._keyboard_released(keystroke=key)
