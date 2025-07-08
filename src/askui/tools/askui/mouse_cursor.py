import time
from typing import TYPE_CHECKING, List

from .render_objects import Location, RenderObjectStyle, create_location, create_style

if TYPE_CHECKING:
    from .askui_controller import AskUiControllerClient


class MouseCursor:
    """
    A mouse cursor implementation using the AskUI rendering system.

    Creates and manages a visual mouse cursor that can be positioned and styled dynamically.
    """

    def __init__(
        self,
        controller: "AskUiControllerClient",
        x: int = 0,
        y: int = 0,
        color: str = "#000000",
        opacity: float = 1.0,
        line_width: int = 2,
    ) -> None:
        """
        Initialize the mouse cursor.

        Args:
            controller: The AskUI controller instance
            x: Initial horizontal position
            y: Initial vertical position
            color: Cursor color (hex format)
            opacity: Cursor opacity (0.0 to 1.0)
            line_width: Line width for cursor outline
        """
        self._controller = controller
        self._cursor_id: int | None = None
        self._current_x = x
        self._current_y = y
        self._color = color
        self._opacity = opacity
        self._line_width = line_width
        self._visible = True

        self._base_cursor_shape: List[Location] = [
            {"x": 0, "y": 0},  # Tip
            {"x": 5, "y": -15},  # Left bottom
            {"x": 15, "y": -5},  # Right bottom
            {"x": 0, "y": 0},  # Back to tip
        ]

        self._current_style = self._create_current_style()

    def _create_current_style(self) -> RenderObjectStyle:
        """Create the current style object for the cursor."""
        return create_style(
            top=self._current_y,
            left=self._current_x,
            color=self._color,
            opacity=self._opacity,
            line_width=self._line_width,
            visible=self._visible,
        )

    def create_cursor(self) -> int:
        """
        Create the cursor render object.

        Returns:
            The render object ID of the created cursor.
        """
        if self._cursor_id is not None:
            raise RuntimeError("Cursor already created")

        self._cursor_id = self._controller.add_line_render_object(
            self._current_style, self._base_cursor_shape
        )
        return self._cursor_id

    def update_cursor_position(self, x: int, y: int) -> None:
        """
        Update the cursor position.

        Args:
            x: New horizontal position
            y: New vertical position
        """
        if self._cursor_id is None:
            raise RuntimeError("Cursor not created yet")

        if x == self._current_x and y == self._current_y:
            return

        self._current_x = x
        self._current_y = y
        self._current_style = self._create_current_style()

        self._controller.update_render_object(
            self._cursor_id, self._current_style, self._base_cursor_shape
        )

    def animate_to(
        self, target_x: int, target_y: int, duration_ms: int = 500, frame_rate: int = 60
    ) -> None:
        """
        Smoothly animate cursor to target position.

        Args:
            target_x: Target horizontal position
            target_y: Target vertical position
            duration_ms: Animation duration in milliseconds
            frame_rate: Animation frame rate (fps)
        """
        if self._cursor_id is None:
            raise RuntimeError("Cursor not created yet")

        start_x, start_y = self._current_x, self._current_y

        if start_x == target_x and start_y == target_y:
            return

        total_frames = int((duration_ms / 1000) * frame_rate)
        frame_delay = 1 / frame_rate

        for frame in range(total_frames + 1):
            progress = frame / total_frames if total_frames > 0 else 1.0

            current_x = int(start_x + (target_x - start_x) * progress)
            current_y = int(start_y + (target_y - start_y) * progress)

            self.update_cursor_position(current_x, current_y)

            if frame < total_frames:
                time.sleep(frame_delay)

    def update_cursor_color(self, color: str) -> None:
        """
        Update the cursor color.

        Args:
            color: New color (hex format like "#FF0000")
        """
        if self._cursor_id is None:
            raise RuntimeError("Cursor not created yet")

        if color == self._color:
            return

        self._color = color
        self._current_style = self._create_current_style()

        self._controller.update_render_object(
            self._cursor_id, self._current_style, self._base_cursor_shape
        )

    def set_opacity(self, opacity: float) -> None:
        """
        Set the cursor opacity.

        Args:
            opacity: Opacity value (0.0 to 1.0)
        """
        if self._cursor_id is None:
            raise RuntimeError("Cursor not created yet")

        if opacity == self._opacity:
            return

        self._opacity = opacity
        self._current_style = self._create_current_style()

        self._controller.update_render_object(
            self._cursor_id, self._current_style, self._base_cursor_shape
        )

    def show_cursor(self) -> None:
        """Make the cursor visible."""
        if self._cursor_id is None:
            raise RuntimeError("Cursor not created yet")

        if self._visible:
            return

        self._visible = True
        self._current_style = self._create_current_style()

        self._controller.update_render_object(
            self._cursor_id, self._current_style, self._base_cursor_shape
        )

    def hide_cursor(self) -> None:
        """Hide the cursor."""
        if self._cursor_id is None:
            raise RuntimeError("Cursor not created yet")

        if not self._visible:
            return

        self._visible = False
        self._current_style = self._create_current_style()

        self._controller.update_render_object(
            self._cursor_id, self._current_style, self._base_cursor_shape
        )

    def destroy_cursor(self) -> None:
        """Destroy the cursor and clean up resources."""
        if self._cursor_id is not None:
            self._controller.delete_render_object(self._cursor_id)
            self._cursor_id = None

    @property
    def cursor_id(self) -> int | None:
        """Get the render object ID of the cursor."""
        return self._cursor_id

    @property
    def position(self) -> Location:
        """Get the current cursor position."""
        return create_location(self._current_x, self._current_y)

    @property
    def color(self) -> str:
        """Get the current cursor color."""
        return self._color

    @property
    def opacity(self) -> float:
        """Get the current cursor opacity."""
        return self._opacity

    @property
    def visible(self) -> bool:
        """Check if the cursor is visible."""
        return self._visible
