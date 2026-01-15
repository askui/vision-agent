from typing import Callable

from PIL import Image

from askui.models.types.geometry import PointList
from askui.utils.image_utils import draw_point_on_image


class AnnotatedImage:
    """A class that represents an annotated image and
        provides methods to get the image with the points drawn on it.

    Args:
        screenshot_function: The function to take the screenshot.
        point_list: The list of points to draw on the image.
    """

    def __init__(
        self,
        screenshot_function: Callable[[], Image.Image],
        point_list: PointList | None = None,
    ) -> None:
        self.screenshot_function = screenshot_function
        self.point_list = point_list

    def get_images(self) -> list[Image.Image]:
        """Get the image with the points drawn on it."""
        screenshot = self.screenshot_function()
        if self.point_list is None:
            return [screenshot]
        return [
            draw_point_on_image(screenshot, point[0], point[1], size=5)
            for point in self.point_list
        ]
