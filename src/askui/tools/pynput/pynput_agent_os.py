import ctypes
import platform
import queue
import shlex
import subprocess
import time
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Literal, TypeVar, cast

from mss import mss
from PIL import Image
from pynput.keyboard import Controller as KeyboardController
from pynput.keyboard import Key, KeyCode
from pynput.mouse import Button
from pynput.mouse import Controller as MouseController
from pynput.mouse import Listener as MouseListener
from typing_extensions import override

from askui.logger import logger
from askui.reporting import CompositeReporter, Reporter
from askui.tools.agent_os import AgentOs, InputEvent, ModifierKey, PcKey
from askui.utils.image_utils import draw_point_on_image

if platform.system() == "Windows":
    try:
        PROCESS_PER_MONITOR_DPI_AWARE = 2
        ctypes.windll.shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)  # type: ignore[attr-defined]
    except Exception as e:  # noqa: BLE001
        logger.error(f"Could not set DPI awareness: {e}")

if TYPE_CHECKING:
    from mss.screenshot import ScreenShot

_KEY_MAP: dict[PcKey | ModifierKey, Key | KeyCode] = {
    "backspace": Key.backspace,
    "delete": Key.delete,
    "enter": Key.enter,
    "tab": Key.tab,
    "escape": Key.esc,
    "up": Key.up,
    "down": Key.down,
    "right": Key.right,
    "left": Key.left,
    "home": Key.home,
    "end": Key.end,
    "pageup": Key.page_up,
    "pagedown": Key.page_down,
    "f1": Key.f1,
    "f2": Key.f2,
    "f3": Key.f3,
    "f4": Key.f4,
    "f5": Key.f5,
    "f6": Key.f6,
    "f7": Key.f7,
    "f8": Key.f8,
    "f9": Key.f9,
    "f10": Key.f10,
    "f11": Key.f11,
    "f12": Key.f12,
    "space": Key.space,
    "command": Key.cmd,
    "alt": Key.alt,
    "control": Key.ctrl,
    "shift": Key.shift,
    "right_shift": Key.shift_r,
}


_BUTTON_MAP: dict[Literal["left", "middle", "right", "unknown"], Button] = {
    "left": Button.left,
    "middle": Button.middle,
    "right": Button.right,
    "unknown": Button.unknown,
}

_BUTTON_MAP_REVERSE: dict[Button, Literal["left", "middle", "right", "unknown"]] = {
    Button.left: "left",
    Button.middle: "middle",
    Button.right: "right",
    Button.unknown: "unknown",
}


T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])
C = TypeVar("C", bound=type)


def await_action(pre_action_wait: float, post_action_wait: float) -> Callable[[F], F]:
    def wrapper(func: F) -> F:
        @wraps(func)
        def _wrapper(*args: Any, **kwargs: Any) -> Any:
            time.sleep(pre_action_wait)
            result = func(*args, **kwargs)
            time.sleep(post_action_wait)
            return result

        return cast("F", _wrapper)

    return wrapper


def decorate_all_methods(
    pre_action_wait: float, post_action_wait: float
) -> Callable[[C], C]:
    def decorate(cls: C) -> C:
        for attr_name, attr in cls.__dict__.items():
            if callable(attr) and not attr_name.startswith("__"):
                setattr(
                    cls,
                    attr_name,
                    await_action(pre_action_wait, post_action_wait)(
                        cast("Callable[..., Any]", attr)
                    ),
                )
        return cls

    return decorate


@decorate_all_methods(pre_action_wait=0.1, post_action_wait=0.1)
class PynputAgentOs(AgentOs):
    """
    Implementation of AgentOs using `pynput` for mouse and keyboard control, and `mss`
    for screenshots.

    Args:
        reporter (Reporter): Reporter used for reporting with the `AgentOs`.
        display (int, optional): Display number to use. Defaults to `1`.
    """

    def __init__(
        self,
        reporter: Reporter | None = None,
        display: int = 1,
    ) -> None:
        self._mouse = MouseController()
        self._keyboard = KeyboardController()
        self._sct = mss()
        self._display = display
        self._reporter = reporter or CompositeReporter()
        self._mouse_listener: MouseListener | None = None
        self._input_event_queue: queue.Queue[InputEvent] = queue.Queue()

    @override
    def connect(self) -> None:
        """No connection needed for pynput."""

    @override
    def disconnect(self) -> None:
        """No disconnection needed for pynput."""

    @override
    def screenshot(self, report: bool = True) -> Image.Image:
        """
        Take a screenshot of the current screen.

        Args:
            report (bool, optional): Whether to include the screenshot in reporting.
                Defaults to `True`.

        Returns:
            Image.Image: A PIL Image object containing the screenshot.
        """
        monitor = self._sct.monitors[self._display]
        screenshot: ScreenShot = self._sct.grab(monitor)
        image = Image.frombytes(
            "RGB",
            screenshot.size,
            screenshot.rgb,
        )

        scaled_size = (monitor["width"], monitor["height"])
        image = image.resize(scaled_size, Image.Resampling.LANCZOS)

        if report:
            self._reporter.add_message("AgentOS", "screenshot()", image)
        return image

    @override
    def mouse_move(self, x: int, y: int) -> None:
        """
        Move the mouse cursor to specified screen coordinates.

        Args:
            x (int): The horizontal coordinate (in pixels) to move to.
            y (int): The vertical coordinate (in pixels) to move to.
        """
        self._reporter.add_message(
            "AgentOS",
            f"mouse_move({x}, {y})",
            draw_point_on_image(self.screenshot(report=False), x, y, size=5),
        )
        self._mouse.position = (x, y)

    @override
    def type(self, text: str, typing_speed: int = 50) -> None:
        """
        Type text at current cursor position as if entered on a keyboard.

        Args:
            text (str): The text to type.
            typing_speed (int, optional): The speed of typing in characters per second.
                Defaults to `50`.
        """
        self._reporter.add_message("AgentOS", f'type("{text}", {typing_speed})')
        delay = 1.0 / typing_speed
        for char in text:
            self._keyboard.press(char)
            self._keyboard.release(char)
            time.sleep(delay)

    @override
    def click(
        self, button: Literal["left", "middle", "right"] = "left", count: int = 1
    ) -> None:
        """
        Click a mouse button.

        Args:
            button (Literal["left", "middle", "right"], optional): The mouse button to
                click. Defaults to `"left"`.
            count (int, optional): Number of times to click. Defaults to `1`.
        """
        self._reporter.add_message("AgentOS", f'click("{button}", {count})')
        pynput_button = _BUTTON_MAP[button]
        for _ in range(count):
            self._mouse.click(pynput_button)

    @override
    def mouse_down(self, button: Literal["left", "middle", "right"] = "left") -> None:
        """
        Press and hold a mouse button.

        Args:
            button (Literal["left", "middle", "right"], optional): The mouse button to
                press. Defaults to `"left"`.
        """
        self._reporter.add_message("AgentOS", f'mouse_down("{button}")')
        self._mouse.press(_BUTTON_MAP[button])

    @override
    def mouse_up(self, button: Literal["left", "middle", "right"] = "left") -> None:
        """
        Release a mouse button.

        Args:
            button (Literal["left", "middle", "right"], optional): The mouse button to
                release. Defaults to "left".
        """
        self._reporter.add_message("AgentOS", f'mouse_up("{button}")')
        self._mouse.release(_BUTTON_MAP[button])

    @override
    def mouse_scroll(self, x: int, y: int) -> None:
        """
        Scroll the mouse wheel.

        Args:
            x (int): The horizontal scroll amount. Positive values scroll right,
                negative values scroll left.
            y (int): The vertical scroll amount. Positive values scroll down,
                negative values scroll up.
        """
        self._reporter.add_message("AgentOS", f"mouse_scroll({x}, {y})")
        self._mouse.scroll(x, y)

    def _get_pynput_key(self, key: PcKey | ModifierKey) -> Key | KeyCode | str:
        """Convert our key type to pynput key."""
        if key in _KEY_MAP:
            return _KEY_MAP[key]
        return key  # For regular characters

    @override
    def keyboard_pressed(
        self, key: PcKey | ModifierKey, modifier_keys: list[ModifierKey] | None = None
    ) -> None:
        """
        Press and hold a keyboard key.

        Args:
            key (PcKey | ModifierKey): The key to press.
            modifier_keys (list[ModifierKey] | None, optional): List of modifier keys to
                press along with the main key. Defaults to `None`.
        """
        self._reporter.add_message(
            "AgentOS", f'keyboard_pressed("{key}", {modifier_keys})'
        )
        if modifier_keys:
            for mod in modifier_keys:
                self._keyboard.press(_KEY_MAP[mod])
        self._keyboard.press(self._get_pynput_key(key))

    @override
    def keyboard_release(
        self, key: PcKey | ModifierKey, modifier_keys: list[ModifierKey] | None = None
    ) -> None:
        """
        Release a keyboard key.

        Args:
            key (PcKey | ModifierKey): The key to release.
            modifier_keys (list[ModifierKey] | None, optional): List of modifier keys to
                release along with the main key. Defaults to `None`.
        """
        self._reporter.add_message(
            "AgentOS", f'keyboard_release("{key}", {modifier_keys})'
        )
        self._keyboard.release(self._get_pynput_key(key))
        if modifier_keys:
            for mod in reversed(modifier_keys):  # Release in reverse order
                self._keyboard.release(_KEY_MAP[mod])

    @override
    def keyboard_tap(
        self,
        key: PcKey | ModifierKey,
        modifier_keys: list[ModifierKey] | None = None,
        count: int = 1,
    ) -> None:
        """
        Press and immediately release a keyboard key.

        Args:
            key (PcKey | ModifierKey): The key to tap.
            modifier_keys (list[ModifierKey] | None, optional): List of modifier keys to
                press along with the main key. Defaults to `None`.
            count (int, optional): The number of times to tap the key. Defaults to `1`.
        """
        self._reporter.add_message(
            "AgentOS",
            f'keyboard_tap("{key}", {modifier_keys}, {count})',
        )
        for _ in range(count):
            self.keyboard_pressed(key, modifier_keys)
            self.keyboard_release(key, modifier_keys)

    @override
    def set_display(self, display: int = 1) -> None:
        """
        Set the active display.

        Args:
            display (int, optional): The display ID to set as active.
                Defaults to `1`.
        """
        self._reporter.add_message("AgentOS", f"set_display({display})")
        if display < 1 or len(self._sct.monitors) <= display:
            error_msg = f"Display {display} not found"
            raise ValueError(error_msg)
        self._display = display

    @override
    def run_command(self, command: str, timeout_ms: int = 30000) -> None:
        """
        Run a shell command.

        Args:
            command (str): The command to run.
            timeout_ms (int, optional): Timeout in milliseconds. Defaults to 30000.

        Raises:
            subprocess.TimeoutExpired: If the command takes longer than the timeout.
            subprocess.CalledProcessError: If the command returns a non-zero exit code.
        """

        subprocess.run(shlex.split(command), timeout=timeout_ms / 1000)

    def _on_mouse_click(
        self, x: float, y: float, button: Button, pressed: bool, injected: bool
    ) -> None:
        """Handle mouse click events."""
        self._input_event_queue.put(
            InputEvent(
                x=int(x),
                y=int(y),
                button=_BUTTON_MAP_REVERSE[button],
                pressed=pressed,
                injected=injected,
                timestamp=time.time(),
            )
        )

    @override
    def start_listening(self) -> None:
        """
        Start listening for mouse and keyboard events.

        Args:
            callback (InputEventCallback): Callback function that will be called for
                each event.
        """
        if self._mouse_listener:
            self.stop_listening()
        self._mouse_listener = MouseListener(
            on_click=self._on_mouse_click,  # type: ignore[arg-type]
            name="PynputAgentOsMouseListener",
            args=(self._input_event_queue,),
        )
        self._mouse_listener.start()

    @override
    def poll_event(self) -> InputEvent | None:
        """Poll for a single input event."""
        try:
            return self._input_event_queue.get(False)
        except queue.Empty:
            return None

    @override
    def stop_listening(self) -> None:
        """Stop listening for mouse and keyboard events."""
        if self._mouse_listener:
            self._mouse_listener.stop()
            self._mouse_listener = None
        while not self._input_event_queue.empty():
            self._input_event_queue.get()
