import io
import base64
import pathlib

from PIL import Image, ImageDraw
from typing import Union


class AutomationError(Exception):
    """Exception raised when the automation step cannot complete."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


def truncate_long_strings(json_data, max_length=100, truncate_length=20, tag="[shortened]"):
    """
    Traverse and truncate long strings in JSON data.

    :param json_data: The JSON data (dict, list, or str).
    :param max_length: The maximum length before truncation.
    :param truncate_length: The length to truncate the string to.
    :param tag: The tag to append to truncated strings.
    :return: JSON data with truncated long strings.
    """
    if isinstance(json_data, dict):
        return {k: truncate_long_strings(v, max_length, truncate_length, tag) for k, v in json_data.items()}
    elif isinstance(json_data, list):
        return [truncate_long_strings(item, max_length, truncate_length, tag) for item in json_data]
    elif isinstance(json_data, str) and len(json_data) > max_length:
        return f"{json_data[:truncate_length]}... {tag}"
    return json_data


def image_to_base64(image: Union[pathlib.Path, Image.Image]) -> str:
    image_bytes: bytes | None = None
    if isinstance(image, Image.Image):
        with io.BytesIO() as _bytes:
            image.save(_bytes, format="PNG")
            image_bytes = _bytes.getvalue()
    elif isinstance(image, pathlib.Path):
        with open(image, "rb") as f:
            image_bytes = f.read()

    return base64.b64encode(image_bytes).decode("utf-8")


def base64_to_image(base64_string: str) -> Image.Image:
    """
    Convert a base64 string to a PIL Image.
    
    :param base64_string: The base64 encoded image string
    :return: PIL Image object
    """
    image_bytes = base64.b64decode(base64_string)
    image = Image.open(io.BytesIO(image_bytes))
    return image


def draw_point_on_image(image: Image.Image, x: int, y: int, size: int = 3) -> Image.Image:
    """
    Draw a red point at the specified x,y coordinates on a copy of the input image.
    
    :param image: PIL Image to draw on
    :param x: X coordinate for the point
    :param y: Y coordinate for the point
    :return: New PIL Image with the point drawn
    """    
    img_copy = image.copy()
    draw = ImageDraw.Draw(img_copy)
    draw.ellipse([x-size, y-size, x+size, y+size], fill='red')
    return img_copy
