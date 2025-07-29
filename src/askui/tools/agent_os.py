from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Literal

from PIL import Image
from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from askui.tools.askui.askui_ui_controller_grpc.generated.AgentOS_Send_Request_2501 import (  # noqa: E501
        RenderObjectStyle,
    )


ModifierKey = Literal[
    "command",
    "alt",
    "control",
    "shift",
    "right_shift",
]
"""Modifier keys for keyboard actions."""

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
"""PC keys for keyboard actions."""


class ClickEvent(BaseModel):
    type: Literal["click"] = "click"
    x: int
    y: int
    button: Literal["left", "middle", "right", "unknown"]
    pressed: bool
    injected: bool = False
    timestamp: float


class Coordinate(BaseModel):
    x: int
    y: int


class DisplaySize(BaseModel):
    """Represents the size of a display in pixels."""

    width: int
    height: int


class Display(BaseModel):
    model_config = ConfigDict(
        validate_by_name=True,
    )

    id: int = Field(validation_alias="displayID")
    size: DisplaySize = Field(validation_alias="sizeInPixels")


class DisplaysListResponse(BaseModel):
    data: list[Display] = Field(validation_alias="displays")


InputEvent = ClickEvent


class AgentOs(ABC):
    """
    Abstract base class for Agent OS. Cannot be instantiated directly.

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

    @abstractmethod
    def disconnect(self) -> None:
        """
        Terminates the connection to the Agent OS.

        This method is called after all OS-level operations are complete.
        It handles any necessary cleanup or resource release.
        """

    @abstractmethod
    def screenshot(self, report: bool = True) -> Image.Image:
        """
        Captures a screenshot of the current display.

        Args:
            report (bool, optional): Whether to include the screenshot in
                reporting. Defaults to `True`.

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
    def type(self, text: str, typing_speed: int = 50) -> None:
        """
        Simulates typing text as if entered on a keyboard.

        Args:
            text (str): The text to be typed.
            typing_speed (int, optional): The speed of typing in characters per
                minute. Defaults to `50`.
        """
        raise NotImplementedError

    @abstractmethod
    def click(
        self, button: Literal["left", "middle", "right"] = "left", count: int = 1
    ) -> None:
        """
        Simulates clicking a mouse button.

        Args:
            button (Literal["left", "middle", "right"], optional): The mouse
                button to click. Defaults to `"left"`.
            count (int, optional): Number of times to click. Defaults to `1`.
        """
        raise NotImplementedError

    @abstractmethod
    def mouse_down(self, button: Literal["left", "middle", "right"] = "left") -> None:
        """
        Simulates pressing and holding a mouse button.

        Args:
            button (Literal["left", "middle", "right"], optional): The mouse
                button to press. Defaults to `"left"`.
        """
        raise NotImplementedError

    @abstractmethod
    def mouse_up(self, button: Literal["left", "middle", "right"] = "left") -> None:
        """
        Simulates releasing a mouse button.

        Args:
            button (Literal["left", "middle", "right"], optional): The mouse
                button to release. Defaults to `"left"`.
        """
        raise NotImplementedError

    @abstractmethod
    def mouse_scroll(self, x: int, y: int) -> None:
        """
        Simulates scrolling the mouse wheel.

        Args:
            x (int): The horizontal scroll amount. Positive values scroll right,
                negative values scroll left.
            y (int): The vertical scroll amount. Positive values scroll down,
                negative values scroll up.
        """
        raise NotImplementedError

    @abstractmethod
    def keyboard_pressed(
        self, key: PcKey | ModifierKey, modifier_keys: list[ModifierKey] | None = None
    ) -> None:
        """
        Simulates pressing and holding a keyboard key.

        Args:
            key (PcKey | ModifierKey): The key to press.
            modifier_keys (list[ModifierKey] | None, optional): List of modifier keys to
                press along with the main key. Defaults to `None`.
        """
        raise NotImplementedError

    @abstractmethod
    def keyboard_release(
        self, key: PcKey | ModifierKey, modifier_keys: list[ModifierKey] | None = None
    ) -> None:
        """
        Simulates releasing a keyboard key.

        Args:
            key (PcKey | ModifierKey): The key to release.
            modifier_keys (list[ModifierKey] | None, optional): List of modifier keys to
                release along with the main key. Defaults to `None`.
        """
        raise NotImplementedError

    @abstractmethod
    def keyboard_tap(
        self,
        key: PcKey | ModifierKey,
        modifier_keys: list[ModifierKey] | None = None,
        count: int = 1,
    ) -> None:
        """
        Simulates pressing and immediately releasing a keyboard key.

        Args:
            key (PcKey | ModifierKey): The key to tap.
            modifier_keys (list[ModifierKey] | None, optional): List of modifier keys to
                press along with the main key. Defaults to `None`.
            count (int, optional): The number of times to tap the key. Defaults to `1`.
        """
        raise NotImplementedError

    def list_displays(self) -> DisplaysListResponse:
        """
        List all the available displays.
        """
        raise NotImplementedError

    @abstractmethod
    def retrieve_active_display(self) -> Display:
        """
        Retrieve the currently active display/screen.

        Returns:
            Display: The currently active display/screen.
        """
        raise NotImplementedError

    def set_display(self, display: int = 1) -> None:
        """
        Sets the active display for screen interactions.

        Args:
            display (int, optional): The display ID to set as active.
                Defaults to `1`.
        """
        raise NotImplementedError

    def run_command(self, command: str, timeout_ms: int = 30000) -> None:
        """
        Executes a shell command.

        Args:
            command (str): The command to execute.
            timeout_ms (int, optional): The timeout for command
                execution in milliseconds. Defaults to `30000` (30 seconds).

        """
        raise NotImplementedError

    def start_listening(self) -> None:
        """
        Start listening for mouse and keyboard events.

        IMPORTANT: This method is still experimental and may not work at all and may
        change in the future.
        """
        raise NotImplementedError

    def poll_event(self) -> InputEvent | None:
        """
        Poll for a single input event.

        IMPORTANT: This method is still experimental and may not work at all and may
        change in the future.
        """
        raise NotImplementedError

    def stop_listening(self) -> None:
        """Stop listening for mouse and keyboard events.

        IMPORTANT: This method is still experimental and may not work at all and may
        change in the future.
        """
        raise NotImplementedError

    def get_mouse_position(self) -> Coordinate:
        """
        Get the current mouse cursor position.

        Returns:
            The current mouse position data.
        """
        raise NotImplementedError

    def set_mouse_position(self, x: int, y: int) -> None:
        """
        Set the mouse cursor position to specific coordinates.

        Args:
            x (int): The horizontal coordinate (in pixels) to set the cursor to.
            y (int): The vertical coordinate (in pixels) to set the cursor to.

        """
        raise NotImplementedError

    def render_quad(self, style: "RenderObjectStyle") -> int:
        """
        Render a quad object to the display.

        Args:
            style (RenderObjectStyle): The style properties for the quad.

        Returns:
            Response containing the render object ID.
        """
        raise NotImplementedError

    def render_line(self, style: "RenderObjectStyle", points: list[Coordinate]) -> int:
        """
        Render a line object to the display.

        Args:
            style (RenderObjectStyle): The style properties for the line.
            points (list[Coordinate]): The points defining the line.

        Returns:
            Response containing the render object ID.
        """
        raise NotImplementedError

    def render_image(self, style: "RenderObjectStyle", image_data: str) -> int:
        """
        Render an image object to the display.

        Args:
            style (RenderObjectStyle): The style properties for the image.
            image_data (str): The image data to display.

        Returns:
            Response containing the render object ID.
        """
        raise NotImplementedError

    def render_text(self, style: "RenderObjectStyle", content: str) -> int:
        """
        Render a text object to the display.

        Args:
            style (RenderObjectStyle): The style properties for the text.
            text_content (str): The text content to display.

        Returns:
            Response containing the render object ID.
        """
        raise NotImplementedError

    def update_render_object(self, object_id: int, style: "RenderObjectStyle") -> None:
        """
        Update styling properties of an existing render object.

        Args:
            object_id (int): The ID of the render object to update.
            style (RenderObjectStyle): The new style properties.
        """
        raise NotImplementedError

    def delete_render_object(self, object_id: int) -> None:
        """
        Delete an existing render object from the display.

        Args:
            object_id (int): The ID of the render object to delete.

        Returns:
            Response confirming the deletion.
        """
        raise NotImplementedError

    def clear_render_objects(self) -> None:
        """
        Clear all render objects from the display.

        Returns:
            Response confirming the clearing.
        """
        raise NotImplementedError
