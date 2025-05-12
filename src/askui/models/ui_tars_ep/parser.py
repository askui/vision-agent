import re
from typing import Literal, Union

from pydantic import BaseModel, Field


class BoxCoordinate(BaseModel):
    """Represents a box coordinate in the format (x,y)."""

    x: int
    y: int

    @classmethod
    def parse(cls, coord_str: str) -> "BoxCoordinate":
        """Parse a coordinate string in the format (x,y)."""
        match = re.match(r"\((\d+),(\d+)\)", coord_str)
        if not match:
            error_msg = f"Invalid coordinate format: {coord_str}"
            raise ValueError(error_msg)
        return cls(x=int(match.group(1)), y=int(match.group(2)))


class ClickAction(BaseModel):
    """Click action with start box coordinates."""

    action_type: Literal["click"] = "click"
    start_box: BoxCoordinate


class DoubleClickAction(BaseModel):
    """Double left click action with start box coordinates."""

    action_type: Literal["left_double"] = "left_double"
    start_box: BoxCoordinate


class RightClickAction(BaseModel):
    """Right click action with start box coordinates."""

    action_type: Literal["right_single"] = "right_single"
    start_box: BoxCoordinate


class DragAction(BaseModel):
    """Drag action with start and end box coordinates."""

    action_type: Literal["drag"] = "drag"
    start_box: BoxCoordinate
    end_box: BoxCoordinate


class HotkeyAction(BaseModel):
    """Hotkey action with key combination."""

    action_type: Literal["hotkey"] = "hotkey"
    key: str


class TypeAction(BaseModel):
    """Type action with content."""

    action_type: Literal["type"] = "type"
    content: str


class ScrollAction(BaseModel):
    """Scroll action with direction and start box."""

    action_type: Literal["scroll"] = "scroll"
    start_box: BoxCoordinate
    direction: Literal["up", "down", "left", "right"]


class WaitAction(BaseModel):
    """Wait action."""

    action_type: Literal["wait"] = "wait"


class FinishedAction(BaseModel):
    """Finished action."""

    action_type: Literal["finished"] = "finished"


class CallUserAction(BaseModel):
    """Call user action."""

    action_type: Literal["call_user"] = "call_user"


ActionType = Union[
    ClickAction,
    DoubleClickAction,
    RightClickAction,
    DragAction,
    HotkeyAction,
    TypeAction,
    ScrollAction,
    WaitAction,
    FinishedAction,
    CallUserAction,
]


class UITarsEPMessage(BaseModel):
    """Pydantic model for parsing messages from UI-TARS-EP model."""

    thought: str = Field(description="The reasoning/thought process behind the action")
    raw_action: str = Field(
        description="The raw action string as received from the model"
    )
    parsed_action: ActionType = Field(
        description="The parsed action with its specific parameters"
    )

    @classmethod
    def parse_message(cls, message: str) -> "UITarsEPMessage":
        """Parse a message string into a UITarsEPMessage object."""
        # Split on actual newlines or escaped newlines
        parts = re.split(r"\n|\\n", message)

        thought = ""
        action = ""

        for part in parts:
            if part.startswith("Thought:"):
                thought = part.replace("Thought:", "").strip()
            elif part.startswith("Action:"):
                action = part.replace("Action:", "").strip()

        parsed_action = cls.parse_action(action)

        return cls(thought=thought, raw_action=action, parsed_action=parsed_action)

    @staticmethod
    def parse_action(action_str: str) -> ActionType:  # noqa: C901
        """Parse the action string into the appropriate action type."""
        # Extract action type and parameters
        match = re.match(r"(\w+)\((.*)\)", action_str)
        if not match:
            error_msg = f"Invalid action format: {action_str}"
            raise ValueError(error_msg)

        action_type, params_str = match.groups()

        # Handle parameters more robustly
        params = {}
        if params_str:
            # Split by = but preserve the rest of the string
            key_value = params_str.split("=", 1)
            if len(key_value) == 2:
                key = key_value[0].strip()
                value = key_value[1].strip("'\"")
                params[key] = value

        if action_type == "click":
            return ClickAction(start_box=BoxCoordinate.parse(params["start_box"]))
        if action_type == "left_double":
            return DoubleClickAction(start_box=BoxCoordinate.parse(params["start_box"]))
        if action_type == "right_single":
            return RightClickAction(start_box=BoxCoordinate.parse(params["start_box"]))
        if action_type == "drag":
            return DragAction(
                start_box=BoxCoordinate.parse(params["start_box"]),
                end_box=BoxCoordinate.parse(params["end_box"]),
            )
        if action_type == "hotkey":
            return HotkeyAction(key=params["key"])
        if action_type == "type":
            return TypeAction(content=params["content"])
        if action_type == "scroll":
            return ScrollAction(
                start_box=BoxCoordinate.parse(params["start_box"]),
                direction=params["direction"],
            )
        if action_type == "wait":
            return WaitAction()
        if action_type == "finished":
            return FinishedAction()
        if action_type == "call_user":
            return CallUserAction()
        error_msg = f"Unknown action type: {action_type}"
        raise ValueError(error_msg)
