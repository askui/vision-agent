from abc import ABC
from typing import Annotated, Literal, TypedDict

from anthropic.types.beta import (
    BetaToolComputerUse20241022Param,
    BetaToolComputerUse20250124Param,
)
from PIL import Image
from pydantic import Field, validate_call
from typing_extensions import override

from askui.tools.agent_os import AgentOs, PcKey
from askui.utils.dict_utils import IdentityDefaultDict
from askui.utils.image_utils import scale_coordinates_back, scale_image_with_padding

from ..models.shared.tools import InputSchema, Tool

Action20241022 = Literal[
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

Action20250124 = (
    Action20241022
    | Literal[
        "left_mouse_down",
        "left_mouse_up",
        "scroll",
        "hold_key",
        "wait",
        "triple_click",
    ]
)

ScrollDirection = Literal["up", "down", "left", "right"]

KeysToMap = Literal[
    "BackSpace",
    "Delete",
    "Return",
    "Enter",
    "Tab",
    "Escape",
    "Up",
    "Down",
    "Right",
    "Left",
    "Home",
    "End",
    "Page_Up",
    "Page_Down",
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
]

Key = PcKey | KeysToMap

KEYS_MAPPING: IdentityDefaultDict[Key, PcKey] = IdentityDefaultDict(
    {
        "BackSpace": "backspace",
        "Delete": "delete",
        "Return": "enter",
        "Enter": "enter",
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
            input_schema={},
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
    def __call__(
        self,
        action: Action20250124,
        text: str | None = None,
        coordinate: tuple[Annotated[int, Field(ge=0)], Annotated[int, Field(ge=0)]]
        | None = None,
    ) -> Image.Image | None:
        match action:
            case "mouse_move":
                self._mouse_move(coordinate)  # type: ignore[arg-type]
            case "left_click_drag":
                # does not seem to work
                self._left_click_drag(coordinate)  # type: ignore[arg-type]
            case "screenshot":
                return self._screenshot()
            case "left_click":
                self._agent_os.click("left")
            case "right_click":
                self._agent_os.click("right")
            case "middle_click":
                self._agent_os.click("middle")
            case "double_click":
                self._agent_os.click("left", 2)
            case "type":
                self._type(text)  # type: ignore[arg-type]
            case "key":
                # we do not seem to support all kinds of key nor modifier keys
                # + key combinations
                self._key(text)  # type: ignore[arg-type]
            case _:
                raise ActionNotImplementedError(action, self.name)
        return None

    @validate_call
    def _type(self, text: str) -> None:
        self._agent_os.type(text)

    @validate_call
    def _key(self, key: Key) -> None:
        _key = KEYS_MAPPING[key]
        self._agent_os.keyboard_pressed(_key)
        self._agent_os.keyboard_release(_key)

    @validate_call
    def _keyboard_pressed(self, key: Key) -> None:
        _key = KEYS_MAPPING[key]
        self._agent_os.keyboard_pressed(_key)

    @validate_call
    def _keyboard_released(self, key: Key) -> None:
        _key = KEYS_MAPPING[key]
        self._agent_os.keyboard_release(_key)

    def _scale_coordinates_back(
        self,
        coordinate: tuple[Annotated[int, Field(ge=0)], Annotated[int, Field(ge=0)]],
    ) -> tuple[int, int]:
        if self._real_screen_width is None or self._real_screen_height is None:
            screenshot = self._agent_os.screenshot()
            self._real_screen_width = screenshot.width
            self._real_screen_height = screenshot.height
        x, y = scale_coordinates_back(
            coordinate[0],
            coordinate[1],
            self._real_screen_width,  #
            self._real_screen_height,
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
                        "enum": list(Action20241022.__args__),
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
                        "enum": list(Action20250124.__args__),
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
                        "enum": list(ScrollDirection.__args__),
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
    def __call__(
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
            case "triple_click":
                self._click("left", count=3, coordinate=coordinate, key=key)
            case _:
                return super().__call__(action, text, coordinate)
        return None

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
            self._keyboard_pressed(key)  # type: ignore[arg-type]
        self._agent_os.click(button, count)
        if key is not None:
            self._keyboard_released(key)  # type: ignore[arg-type]
