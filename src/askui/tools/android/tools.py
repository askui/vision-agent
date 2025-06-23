from typing import get_args

from PIL import Image
from typing_extensions import override

from askui.models.shared.tools import Tool
from askui.tools.android.agent_os import ANDROID_KEY
from askui.tools.android.agent_os_facade import AndroidAgentOsFacade


class AndroidScreenshotTool(Tool):
    """
    Takes a screenshot from the currently connected Android device.
    """

    def __init__(self, agent_os_facade: AndroidAgentOsFacade) -> None:
        super().__init__(
            name="android_screenshot_tool",
            description=(
                """
                Takes a screenshot of the currently active window.
                The image can be used to check the current state of the device.
                It's recommended to use this tool to check the current state of the
                    device before and after an action.
                """
            ),
        )
        self._agent_os_facade = agent_os_facade

    @override
    def __call__(self) -> tuple[str, Image.Image]:
        screenshot = self._agent_os_facade.screenshot()
        return "Screenshot was taken.", screenshot


class AndroidTapTool(Tool):
    """
    Performs a tap (touch) gesture at the given (x, y) coordinates on the
    Android device screen.
    The coordinates are absolute coordinates on the screen.
    The top left corner of the screen is (0, 0).
    """

    def __init__(self, agent_os_facade: AndroidAgentOsFacade) -> None:
        super().__init__(
            name="android_tap_tool",
            description=(
                """
                Performs a tap (touch) gesture at the given (x, y) coordinates on the
                Android device screen. The coordinates are absolute coordinates on the
                screen. The top left corner of the screen is (0, 0).
                """
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "x": {
                        "type": "integer",
                        "description": "The x coordinate of the tap gesture in pixels.",
                    },
                    "y": {
                        "type": "integer",
                        "description": "The y coordinate of the tap gesture in pixels.",
                    },
                },
                "required": ["x", "y"],
            },
        )
        self._agent_os_facade = agent_os_facade

    @override
    def __call__(self, x: int, y: int) -> str:
        self._agent_os_facade.tap(x, y)
        return f"Tapped at ({x}, {y})"


class AndroidTypeTool(Tool):
    """
    Types the given text on the Android device screen.
    """

    def __init__(self, agent_os_facade: AndroidAgentOsFacade) -> None:
        super().__init__(
            name="android_type_tool",
            description=(
                """
                Types the given text on the Android device screen.
                The to typed text can not contains non ASCII printable characters.
                """
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": """
                    The text to type. It must be a valid ASCII printable string.
                    text such as "Hello, world!" is valid,
                    but "Hello, 世界!" is not valid and will raise an error.
                    """,
                    },
                },
                "required": ["text"],
            },
        )
        self._agent_os_facade = agent_os_facade

    @override
    def __call__(self, text: str) -> str:
        self._agent_os_facade.type(text)
        return f"Typed: {text}"


class AndroidDragAndDropTool(Tool):
    """
    Performs a drag and drop gesture on the Android device screen.
    """

    def __init__(self, agent_os_facade: AndroidAgentOsFacade) -> None:
        self._agent_os_facade = agent_os_facade
        super().__init__(
            name="android_drag_and_drop_tool",
            description=(
                """
                Performs a drag and drop gesture on the Android device screen.
                Will hold the element at the requested start position and drag and drop
                it in the requested end position in pixels in the given duration.
                TopLeftCorner of the screen is (0, 0).
                To get the coordinates of an element, take and analyze a screenshot of
                the screen.
                """
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "x1": {
                        "type": "integer",
                        "description": "The x1 pixel coordinate of the start position",
                    },
                    "y1": {
                        "type": "integer",
                        "description": "The y1 pixel coordinate of the start position",
                    },
                    "x2": {
                        "type": "integer",
                        "description": "The x2 pixel coordinate of the end position",
                    },
                    "y2": {
                        "type": "integer",
                        "description": "The y2 pixel coordinate of the end position",
                    },
                    "duration": {
                        "type": "integer",
                        "description": (
                            "The duration of the drag and drop gesture in milliseconds"
                        ),
                        "default": 1000,
                    },
                },
                "required": ["x1", "y1", "x2", "y2"],
            },
        )

    @override
    def __call__(self, x1: int, y1: int, x2: int, y2: int, duration: int = 1000) -> str:
        self._agent_os_facade.drag_and_drop(x1, y1, x2, y2, duration)
        return f"Dragged and dropped from ({x1}, {y1}) to ({x2}, {y2}) in {duration}ms"


class AndroidKeyTapEventTool(Tool):
    def __init__(self, agent_os_facade: AndroidAgentOsFacade) -> None:
        super().__init__(
            name="android_key_event_tool",
            description=(
                """
                Performs a key press on the android device.
                e.g 'HOME' to simulate the home button press.
                """
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "key_name": {
                        "type": "string",
                        "description": (
                            "The key event to perform. e.g 'HOME' "
                            "to simulate the home button press."
                        ),
                        "enum": get_args(ANDROID_KEY),
                    },
                },
                "required": ["key_name"],
            },
        )
        self._agent_os_facade = agent_os_facade

    @override
    def __call__(self, key_name: ANDROID_KEY) -> str:
        self._agent_os_facade.key_tap(key_name)
        return f"Tapped on Key: {key_name}"


class AndroidSwipeTool(Tool):
    """
    Performs a swipe gesture on the Android device screen.
    """

    def __init__(self, agent_os_facade: AndroidAgentOsFacade) -> None:
        super().__init__(
            name="android_swipe_tool",
            description=(
                """
                Performs a swipe gesture on the Android device screen, similar to
                how a user would swipe their finger across the screen.
                This is useful for scrolling through content, navigating between
                screens, or revealing hidden elements.
                The gesture will start at the specified coordinates and move to the end
                coordinates over the given duration.
                The screen coordinates are absolute, with (0,0) at the top-left
                corner of the screen. For best results, ensure the coordinates
                are within the visible screen bounds.
                """
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "x1": {
                        "type": "integer",
                        "description": (
                            "The starting x-coordinate in pixels from the left edge "
                            "of the screen. Must be a positive integer."
                        ),
                    },
                    "y1": {
                        "type": "integer",
                        "description": (
                            "The starting y-coordinate in pixels from the top edge "
                            "of the screen. Must be a positive integer."
                        ),
                    },
                    "x2": {
                        "type": "integer",
                        "description": (
                            "The ending x-coordinate in pixels from the left edge "
                            "of the screen. Must be a positive integer."
                        ),
                    },
                    "y2": {
                        "type": "integer",
                        "description": (
                            "The ending y-coordinate in pixels from the top edge "
                            "of the screen. Must be a positive integer."
                        ),
                    },
                    "duration": {
                        "type": "integer",
                        "description": (
                            "The duration of the swipe gesture in milliseconds. "
                            "A longer duration creates a slower swipe. "
                            "Default is 1000ms (1 second)."
                        ),
                        "default": 1000,
                    },
                },
                "required": ["x1", "y1", "x2", "y2"],
            },
        )
        self._agent_os_facade = agent_os_facade

    @override
    def __call__(self, x1: int, y1: int, x2: int, y2: int, duration: int = 1000) -> str:
        self._agent_os_facade.swipe(x1, y1, x2, y2, duration)
        return f"Swiped from ({x1}, {y1}) to ({x2}, {y2}) in {duration}ms"


class AndroidKeyCombinationTool(Tool):
    """
    Performs a key combination on the Android device.
    """

    def __init__(self, agent_os_facade: AndroidAgentOsFacade) -> None:
        super().__init__(
            name="android_key_combination_tool",
            description=(
                """
                Performs a combination of key presses on the Android device, similar to
                keyboard shortcuts on a computer.
                This is useful for performing complex actions that require multiple keys
                to be pressed simultaneously.
                For example, you can use this to copy text (ctrl+c), switch apps
                (alt+tab), or perform other system-wide shortcuts.
                The keys will be pressed in the order specified, with a small delay
                between each press.
                """
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "keys": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": get_args(ANDROID_KEY),
                        },
                        "description": (
                            "An array of keys to press in combination. "
                            "Each key must be a valid Android key "
                            "code. For example: ['ctrl_left', 'c'] for copy."
                        ),
                    },
                    "duration": {
                        "type": "integer",
                        "description": (
                            "The duration in milliseconds to hold the key combination. "
                            "A longer duration may be needed for some system actions. "
                            "Default is 100ms."
                        ),
                        "default": 100,
                    },
                },
                "required": ["keys"],
            },
        )
        self._agent_os_facade = agent_os_facade

    @override
    def __call__(self, keys: list[ANDROID_KEY], duration: int = 100) -> str:
        self._agent_os_facade.key_combination(keys, duration)
        return f"Performed key combination: {keys}"


class AndroidShellTool(Tool):
    """
    Executes a shell command on the Android device.
    """

    def __init__(self, agent_os_facade: AndroidAgentOsFacade) -> None:
        super().__init__(
            name="android_shell_tool",
            description=(
                """
                Executes a shell command directly on the Android device through ADB.
                This provides low-level access to the Android system, allowing you to
                run system commands, check device status, or perform administrative
                tasks. The command will be executed in the Android shell environment
                with the current user's permissions.
                """
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": (
                            "The shell command to execute on the Android device. "
                            "This can be any valid "
                            "Android shell command, such as 'pm list packages' "
                            "to list installed apps or "
                            "'dumpsys battery' to check battery status."
                        ),
                    },
                },
                "required": ["command"],
            },
        )
        self._agent_os_facade = agent_os_facade

    @override
    def __call__(self, command: str) -> str:
        output = self._agent_os_facade.shell(command)
        return f"Shell command executed. Output: {output}"
