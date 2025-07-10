from __future__ import annotations

import io
import subprocess
from typing import Literal

from PIL import Image
from playwright.sync_api import (
    Browser,
    BrowserContext,
    BrowserType,
    Page,
    Playwright,
    ViewportSize,
    sync_playwright,
)
from typing_extensions import override

from ..agent_os import AgentOs, InputEvent, ModifierKey, PcKey


class PlaywrightAgentOs(AgentOs):
    """
    Playwright-based implementation of AgentOs.

    This implementation uses Playwright's Python SDK to control browser automation
    and simulate user interactions. It provides mouse control, keyboard input,
    and screen capture functionality through a browser context.

    Args:
        browser_type (Literal["chromium", "firefox", "webkit"], optional): The browser
            type to use. Defaults to `"chromium"`.
        headless (bool, optional): Whether to run the browser in headless mode.
            Defaults to `False`.
        viewport_size (ViewportSize | None, optional): The viewport size.
            Defaults to `None` (uses default).
        slow_mo (int, optional): Slows down Playwright operations by the specified
            amount of milliseconds. Defaults to `0`.
        install_browser (bool, optional): Whether to install browser on connection.
            Defaults to `True`.
        install_dependencies (bool, optional): Whether to install system dependencies
            (requires root permissions). Defaults to `False`.
    """

    def __init__(
        self,
        browser_type: Literal["chromium", "firefox", "webkit"] = "chromium",
        headless: bool = False,
        viewport_size: ViewportSize | None = None,
        slow_mo: int = 0,
        install_browser: bool = True,
        install_dependencies: bool = False,
    ) -> None:
        self._browser_type = browser_type
        self._headless = headless
        self._viewport_size = viewport_size
        self._slow_mo = slow_mo
        self._install_browser = install_browser
        self._install_dependencies = install_dependencies

        # Playwright objects
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

        # Event listening state
        self._listening = False
        self._event_queue: list[InputEvent] = []

    def _install_playwright_browser(self) -> None:
        """Install Playwright browser if requested."""
        if not self._install_browser:
            return

        try:
            # Install the specific browser type
            subprocess.run(
                ["playwright", "install", self._browser_type],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to install {self._browser_type} browser: {e}"
            raise RuntimeError(error_msg) from e
        except FileNotFoundError as e:
            error_msg = (
                "Playwright CLI not found. Install with `pip install playwright`"
            )
            raise RuntimeError(error_msg) from e

    def _install_system_dependencies(self) -> None:
        """Install system dependencies if requested (requires root permissions)."""
        if not self._install_dependencies:
            return

        try:
            # Install system dependencies
            subprocess.run(
                ["playwright", "install-deps"],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to install system dependencies: {e}"
            raise RuntimeError(error_msg) from e
        except FileNotFoundError as e:
            error_msg = (
                "Playwright CLI not found. Install with `pip install playwright`"
            )
            raise RuntimeError(error_msg) from e

    @override
    def connect(self) -> None:
        """Establishes a synchronous connection to the browser."""

        # Install browser and dependencies if requested
        if self._install_dependencies:
            self._install_system_dependencies()

        if self._install_browser:
            self._install_playwright_browser()

        self._playwright = sync_playwright().start()
        browser_launcher: BrowserType = getattr(self._playwright, self._browser_type)
        self._browser = browser_launcher.launch(
            headless=self._headless,
            slow_mo=self._slow_mo,
        )
        self._context = self._browser.new_context(
            viewport=self._viewport_size,
        )

        self._page = self._context.new_page()
        # Navigate to a blank page to ensure we have a working page
        self._page.goto("data:text/html,<html><body></body></html>")

    @override
    def disconnect(self) -> None:
        """Terminates the connection to the browser."""
        if self._listening:
            self.stop_listening()

        if self._page:
            self._page.close()
            self._page = None

        if self._context:
            self._context.close()
            self._context = None

        if self._browser:
            self._browser.close()
            self._browser = None

        if self._playwright:
            self._playwright.stop()
            self._playwright = None

    @override
    def screenshot(self, report: bool = True) -> Image.Image:
        """
        Captures a screenshot of the current page.

        Args:
            report (bool, optional): Whether to include the screenshot in
                reporting. Defaults to `True`.

        Returns:
            Image.Image: A PIL Image object containing the screenshot.
        """
        if not self._page:
            error_msg = "No active page. Call connect() first."
            raise RuntimeError(error_msg)

        screenshot_bytes = self._page.screenshot()
        return Image.open(io.BytesIO(screenshot_bytes))

    @override
    def mouse_move(self, x: int, y: int) -> None:
        """
        Moves the mouse cursor to specified coordinates on the page.

        Args:
            x (int): The horizontal coordinate (in pixels) to move to.
            y (int): The vertical coordinate (in pixels) to move to.
        """
        if not self._page:
            error_msg = "No active page. Call connect() first."
            raise RuntimeError(error_msg)

        self._page.mouse.move(x, y)

    @override
    def type(self, text: str, typing_speed: int = 50) -> None:
        """
        Simulates typing text as if entered on a keyboard.

        Args:
            text (str): The text to be typed.
            typing_speed (int, optional): The speed of typing in characters per
                minute. Defaults to `50`.
        """
        if not self._page:
            error_msg = "No active page. Call connect() first."
            raise RuntimeError(error_msg)

        # Convert typing speed from CPM to delay between characters
        delay = (60 / typing_speed) * 1000 if typing_speed > 0 else 0
        self._page.keyboard.type(text, delay=delay)

    @override
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
        for _ in range(count):
            self.mouse_down(button)
            self.mouse_up(button)

    @override
    def mouse_down(self, button: Literal["left", "middle", "right"] = "left") -> None:
        """
        Simulates pressing and holding a mouse button.

        Args:
            button (Literal["left", "middle", "right"], optional): The mouse
                button to press. Defaults to `"left"`.
        """
        if not self._page:
            error_msg = "No active page. Call connect() first."
            raise RuntimeError(error_msg)

        self._page.mouse.down(button=button)

    @override
    def mouse_up(self, button: Literal["left", "middle", "right"] = "left") -> None:
        """
        Simulates releasing a mouse button.

        Args:
            button (Literal["left", "middle", "right"], optional): The mouse
                button to release. Defaults to `"left"`.
        """
        if not self._page:
            error_msg = "No active page. Call connect() first."
            raise RuntimeError(error_msg)

        self._page.mouse.up(button=button)

    @override
    def mouse_scroll(self, x: int, y: int) -> None:
        """
        Simulates scrolling the mouse wheel.

        Args:
            x (int): The horizontal scroll amount. Positive values scroll right,
                negative values scroll left.
            y (int): The vertical scroll amount. Positive values scroll down,
                negative values scroll up.
        """
        if not self._page:
            error_msg = "No active page. Call connect() first."
            raise RuntimeError(error_msg)

        self._page.mouse.wheel(delta_x=x, delta_y=y)

    @override
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
        if not self._page:
            error_msg = "No active page. Call connect() first."
            raise RuntimeError(error_msg)

        # Press modifier keys first
        if modifier_keys:
            for modifier in modifier_keys:
                self._page.keyboard.down(self._convert_key(modifier))

        # Press the main key
        self._page.keyboard.down(self._convert_key(key))

    @override
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
        if not self._page:
            error_msg = "No active page. Call connect() first."
            raise RuntimeError(error_msg)

        # Release the main key first
        self._page.keyboard.up(self._convert_key(key))

        # Release modifier keys
        if modifier_keys:
            for modifier in modifier_keys:
                self._page.keyboard.up(self._convert_key(modifier))

    @override
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
        if not self._page:
            error_msg = "No active page. Call connect() first."
            raise RuntimeError(error_msg)

        for _ in range(count):
            # Press modifier keys first
            if modifier_keys:
                for modifier in modifier_keys:
                    self._page.keyboard.down(self._convert_key(modifier))

            # Press and release the main key
            self._page.keyboard.press(self._convert_key(key))

            # Release modifier keys
            if modifier_keys:
                for modifier in modifier_keys:
                    self._page.keyboard.up(self._convert_key(modifier))

    def _convert_key(self, key: PcKey | ModifierKey) -> str:
        """
        Convert our key format to Playwright's key format.

        Args:
            key (PcKey | ModifierKey): The key to convert.

        Returns:
            str: The Playwright-compatible key string.
        """
        # Map our modifier keys to Playwright format
        modifier_map: dict[PcKey | ModifierKey, str] = {
            "command": "Meta",
            "alt": "Alt",
            "control": "Control",
            "shift": "Shift",
            "right_shift": "Shift",
        }

        if key in modifier_map:
            return modifier_map[key]

        # For regular keys, Playwright uses similar format
        # but some keys might need conversion
        key_map: dict[PcKey | ModifierKey, str] = {
            "backspace": "Backspace",
            "delete": "Delete",
            "enter": "Enter",
            "tab": "Tab",
            "escape": "Escape",
            "up": "ArrowUp",
            "down": "ArrowDown",
            "right": "ArrowRight",
            "left": "ArrowLeft",
            "home": "Home",
            "end": "End",
            "pageup": "PageUp",
            "pagedown": "PageDown",
            "space": " ",
        }

        if key in key_map:
            return key_map[key]

        # Function keys
        if key.startswith("f") and key[1:].isdigit():
            return key.upper()

        # For most other keys, return as-is
        return key

    # --- Extra browser-oriented actions ---
    def goto(self, url: str) -> None:
        """
        Navigate to a specific URL.

        Args:
            url (str): The URL to navigate to.
        """
        if not self._page:
            error_msg = "No active page. Call connect() first."
            raise RuntimeError(error_msg)

        self._page.goto(url)

    def back(self) -> None:
        if not self._page:
            error_msg = "No active page. Call connect() first."
            raise RuntimeError(error_msg)

        self._page.go_back()

    def forward(self) -> None:
        if not self._page:
            error_msg = "No active page. Call connect() first."
            raise RuntimeError(error_msg)

        self._page.go_forward()

    def get_page_title(self) -> str:
        """
        Get the title of the current page.

        Returns:
            str: The page title.
        """
        if not self._page:
            error_msg = "No active page. Call connect() first."
            raise RuntimeError(error_msg)

        return self._page.title()

    def get_page_url(self) -> str:
        """
        Get the URL of the current page.

        Returns:
            str: The current page URL.
        """
        if not self._page:
            error_msg = "No active page. Call connect() first."
            raise RuntimeError(error_msg)

        return self._page.url
