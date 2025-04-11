from typing import Callable
from askui.models.utils import scale_image_with_padding
from askui.tools.askui.askui_android_controller import AskUiAndroidControllerClient
from askui.utils import ANDROID_KEY, image_to_base64
from .base import Tool, ToolResult, ToolError


class AndroidScreenshotTool(Tool):
    def __init__(self, controller_client: AskUiAndroidControllerClient):
        super().__init__(
            name="android_screenshot_tool",
            description="Takes a screenshot from the currently connected Android device.",
            input_schema={"type": "object", "properties": {}, "required": []},
        )
        self.controller_client = controller_client

    def __call__(self) -> ToolResult:
        screenshot = self.controller_client.screenshot()
        self.real_screen_width = screenshot.width
        self.real_screen_height = screenshot.height
        scale_image = scale_image_with_padding(
            screenshot,
            self.controller_client.scaled_resolution[0],
            self.controller_client.scaled_resolution[1],
        )
        base64_image = image_to_base64(scale_image)
        return ToolResult(output=f"Screenshot was taken.", base64_image=base64_image)


class AndroidGetConnectedDisplaysTool(Tool):
    def __init__(self, controller_client: AskUiAndroidControllerClient):
        super().__init__(
            name="android_get_connected_displays_tool",
            description="Returns a list of connected displays on the Android device.",
            input_schema={"type": "object", "properties": {}, "required": []},
        )
        self.controller_client = controller_client

    def __call__(self) -> ToolResult:
        connected_displays = self.controller_client.get_connected_displays()
        return ToolResult(output=f"Connected displays: {connected_displays}")


class AndroidSelectDisplayTool(Tool):
    def __init__(self, controller_client: AskUiAndroidControllerClient):
        super().__init__(
            name="android_select_display_tool",
            description="Selects a specific display on the Android device for further actions.",
            input_schema={
                "type": "object",
                "properties": {
                    "display_index": {
                        "type": "integer",
                        "description": "The index of the display to select. Starts from 0.",
                    },
                },
                "required": ["display_index"],
            },
        )
        self.controller_client = controller_client

    def __call__(self, display_index: int) -> ToolResult:
        if not isinstance(display_index, int):
            raise ToolError(f"{display_index} must be an integer")
        if display_index < 0:
            raise ToolError(f"{display_index} must be a non-negative integer")
        self.controller_client.set_display_by_index(display_index)
        return ToolResult(output=f"Display {display_index} selected.")



class AndroidTapTool(Tool):
    def __init__(self, controller_client: AskUiAndroidControllerClient):
        super().__init__(
            name="android_tap_tool",
            description="Simulates a tap (touch) gesture at the given (x, y) coordinates on the Android device screen.",
            input_schema={
                "type": "object",
                "properties": {
                    "x": {
                        "type": "integer",
                        "description": "The X coordinate on the screen. It must be an integer, so only numbers are allowed.",
                    },
                    "y": {
                        "type": "integer",
                        "description": "The Y coordinate on the screen. It must be an integer, so only numbers are allowed.",
                    },
                },
                "required": ["x", "y"],
            },
        )
        self.controller_client = controller_client

    def __call__(self, x: int, y: int) -> ToolResult:
        if not isinstance(x, int) or not isinstance(y, int):
            raise ToolError(f"{x} and {y} must be integers")
        x, y = self.controller_client.rescale_back_coordinates(x, y)
        self.controller_client.tap(x, y)
        return ToolResult(output=f"Tapped at ({x}, {y})")


class AndroidSwipeTool(Tool):
    def __init__(self, controller_client: AskUiAndroidControllerClient):
        super().__init__(
            name="android_swipe_tool",
            description="Simulates a swipe gesture on the Android screen from point (x1, y1) to (x2, y2). "
            "Optional duration can control swipe speed.",
            input_schema={
                "type": "object",
                "properties": {
                    "x1": {
                        "type": "integer",
                        "description": "Start X position of the swipe. It must be an integer, so only numbers are allowed.",
                    },
                    "y1": {
                        "type": "integer",
                        "description": "Start Y position of the swipe. It must be an integer, so only numbers are allowed.",
                    },
                    "x2": {
                        "type": "integer",
                        "description": "End X position of the swipe. It must be an integer, so only numbers are allowed.",
                    },
                    "y2": {
                        "type": "integer",
                        "description": "End Y position of the swipe. It must be an integer, so only numbers are allowed.",
                    },
                    "duration_in_ms": {
                        "type": "integer",
                        "default": 1000,
                        "description": "Duration of swipe in milliseconds (default: 1000ms).",
                    },
                },
                "required": ["x1", "y1", "x2", "y2"],
            },
        )
        self.controller_client = controller_client

    def __call__(
        self, x1: int, y1: int, x2: int, y2: int, duration_in_ms: int = 1000
    ) -> ToolResult:
        if (
            not isinstance(x1, int)
            or not isinstance(y1, int)
            or not isinstance(x2, int)
            or not isinstance(y2, int)
            or not isinstance(duration_in_ms, int)
        ):
            raise ToolError(
                f"{x1}, {y1}, {x2}, {y2}, and {duration_in_ms} must be integers"
            )
        x1, y1 = self.controller_client.rescale_back_coordinates(x1, y1)
        x2, y2 = self.controller_client.rescale_back_coordinates(x2, y2)
        self.controller_client.swipe(
            x1,
            y1,
            x2,
            y2,
            duration_in_ms,
        )
        return ToolResult(output=f"Swiped from ({x1}, {y1}) to ({x2}, {y2})")


class AndroidDragAndDropTool(Tool):
    def __init__(self, controller_client: AskUiAndroidControllerClient):
        super().__init__(
            name="android_drag_and_drop_tool",
            description="Simulates a drag-and-drop gesture on the Android device from (x1, y1) to (x2, y2).",
            input_schema={
                "type": "object",
                "properties": {
                    "x1": {"type": "integer", "description": "Start X coordinate."},
                    "y1": {"type": "integer", "description": "Start Y coordinate."},
                    "x2": {"type": "integer", "description": "End X coordinate."},
                    "y2": {"type": "integer", "description": "End Y coordinate."},
                    "duration_in_ms": {
                        "type": "integer",
                        "default": 1000,
                        "description": "Duration of drag in milliseconds (default: 1000ms).",
                    },
                },
                "required": ["x1", "y1", "x2", "y2"],
            },
        )
        self.controller_client = controller_client

    def __call__(
        self, x1: int, y1: int, x2: int, y2: int, duration_in_ms: int = 1000
    ) -> ToolResult:
        if (
            not isinstance(x1, int)
            or not isinstance(y1, int)
            or not isinstance(x2, int)
            or not isinstance(y2, int)
            or not isinstance(duration_in_ms, int)
        ):
            raise ToolError(
                f"{x1}, {y1}, {x2}, {y2}, and {duration_in_ms} must be integers"
            )

        x1, y1 = self.controller_client.rescale_back_coordinates(x1, y1)
        x2, y2 = self.controller_client.rescale_back_coordinates(x2, y2)
        self.controller_client.drag_and_drop(
            x1,
            y1,
            x2,
            y2,
            duration_in_ms,
        )
        return ToolResult(output=f"Dragged from x {x1} y {y1} to x {x2} y {y2}")


class AndroidRollTool(Tool):
    def __init__(self, controller_client: AskUiAndroidControllerClient):
        super().__init__(
            name="android_roll_tool",
            description="Simulates a mouse scroll (roll) action by the given dx, dy deltas.",
            input_schema={
                "type": "object",
                "properties": {
                    "dx": {
                        "type": "integer",
                        "description": "Scroll delta along X-axis.",
                    },
                    "dy": {
                        "type": "integer",
                        "description": "Scroll delta along Y-axis.",
                    },
                },
                "required": ["dx", "dy"],
            },
        )
        self.controller_client = controller_client

    def __call__(self, dx: int, dy: int) -> ToolResult:
        if not isinstance(dx, int) or not isinstance(dy, int):
            raise ToolError(f"{dx} and {dy} must be integers")
        dx, dy = self.controller_client.rescale_back_coordinates(dx, dy)
        self.controller_client.roll(dx, dy)
        return ToolResult(output=f"Rolled by dx {dx} and dy {dy}")


class AndroidMoveMouseTool(Tool):
    def __init__(self, controller_client: AskUiAndroidControllerClient):
        super().__init__(
            name="android_move_mouse_tool",
            description="Moves the virtual mouse (internal tracking) to the given coordinates on the Android screen. "
            "This does not trigger touch input but is useful for debugging and tracking position.",
            input_schema={
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "Target X coordinate."},
                    "y": {"type": "integer", "description": "Target Y coordinate."},
                },
                "required": ["x", "y"],
            },
        )
        self.controller_client = controller_client

    def __call__(self, x: int, y: int) -> ToolResult:
        if not isinstance(x, int) or not isinstance(y, int):
            raise ToolError(f"{x} and {y} must be integers")
        x, y = self.controller_client.rescale_back_coordinates(x, y)
        self.controller_client.move_mouse(x, y)
        return ToolResult(output=f"Moved mouse to x {x} y {y}")


class AndroidKeyEventTool(Tool):
    def __init__(self, controller_client: AskUiAndroidControllerClient):
        super().__init__(
            name="android_key_event_tool",
            description="Simulates a physical key press on the Android device using a predefined key string (e.g., 'home', 'volume_up', 'a', 'f5').",
            input_schema={
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "The key to send as an input event. Must be a valid Android key.",
                        "enum": list(ANDROID_KEY.__args__),
                    }
                },
                "required": ["key"],
            },
        )
        self.controller_client = controller_client

    def __call__(self, key: str) -> ToolResult:
        if key not in ANDROID_KEY.__args__:
            raise ToolError(
                f"{key} is not a valid key event. Valid keys are: {', '.join(ANDROID_KEY.__args__)}"
            )
        self.controller_client.key_event(key)
        return ToolResult(output=f"Sent key event: {key}")


class AndroidShellTool(Tool):
    def __init__(self, controller_client: AskUiAndroidControllerClient):
        super().__init__(
            name="android_shell_tool",
            description="Executes a raw shell command on the Android device using ADB and returns the output.",
            input_schema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "A valid shell command string to run on the Android device.",
                    }
                },
                "required": ["command"],
            },
        )
        self.controller_client = controller_client

    def __call__(self, command: str) -> ToolResult:
        command_output = self.controller_client.shell(command)
        return ToolResult(
            output=f"shell command was executed and this command output was received: {command_output}"
        )


class AndroidGetCursorPositionTool(Tool):
    def __init__(self, controller_client: AskUiAndroidControllerClient):
        super().__init__(
            name="android_get_cursor_position_tool",
            description="Returns the current internal mouse position (as tracked by the controller) on the Android device.",
            input_schema={"type": "object", "properties": {}, "required": []},
        )
        self.controller_client = controller_client

    def __call__(self) -> ToolResult:
        x, y = self.controller_client.get_cursor_position()
        return ToolResult(output=f" The current mouse position is x {x} y {y}")


class DebugDrawTool(Tool):
    def __init__(self, controller_client: AskUiAndroidControllerClient):
        super().__init__(
            name="debug_draw_tool",
            description="Draws a box on the screen at the given coordinates. To visualize the box, and to see the result",
            input_schema={
                "type": "object",
                "properties": {
                    "x1": {"type": "integer", "description": "Top-left X coordinate."},
                    "y1": {"type": "integer", "description": "Top-left Y coordinate."},
                    "x2": {
                        "type": "integer",
                        "description": "Bottom-right X coordinate.",
                    },
                    "y2": {
                        "type": "integer",
                        "description": "Bottom-right Y coordinate.",
                    },
                },
                "required": ["x1", "y1", "x2", "y2"],
            },
        )
        self.controller_client = controller_client

    def __call__(self, x1: int, y1: int, x2: int, y2: int) -> ToolResult:
        if (
            not isinstance(x1, int)
            or not isinstance(y1, int)
            or not isinstance(x2, int)
            or not isinstance(y2, int)
        ):
            raise ToolError(f"{x1}, {y1}, {x2}, {y2} must be integers")
        x1, y1 = self.controller_client.rescale_back_coordinates(x1, y1)
        x2, y2 = self.controller_client.rescale_back_coordinates(x2, y2)
        image = self.controller_client.debug_draw(x1, y1, x2, y2)
        base64_image = image_to_base64(image)
        return ToolResult(output="Box drawn on the image.", base64_image=base64_image)
