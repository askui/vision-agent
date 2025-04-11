import io
import base64
import pathlib

from PIL import Image, ImageDraw
from typing import Literal, Union


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

ANDROID_KEY = Literal[  # pylint: disable=C0103
    "home",
    "back",
    "call",
    "endcall",
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
    "star",
    "pound",
    "dpad_up",
    "dpad_down",
    "dpad_left",
    "dpad_right",
    "dpad_center",
    "volume_up",
    "volume_down",
    "power",
    "camera",
    "clear",
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
    "comma",
    "period",
    "alt_left",
    "alt_right",
    "shift_left",
    "shift_right",
    "tab",
    "space",
    "sym",
    "explorer",
    "envelope",
    "enter",
    "del",
    "grave",
    "minus",
    "equals",
    "left_bracket",
    "right_bracket",
    "backslash",
    "semicolon",
    "apostrophe",
    "slash",
    "at",
    "num",
    "headsethook",
    "focus",
    "plus",
    "menu",
    "notification",
    "search",
    "media_play_pause",
    "media_stop",
    "media_next",
    "media_previous",
    "media_rewind",
    "media_fast_forward",
    "mute",
    "page_up",
    "page_down",
    "switch_charset",
    "escape",
    "forward_del",
    "ctrl_left",
    "ctrl_right",
    "caps_lock",
    "scroll_lock",
    "function",
    "break",
    "move_home",
    "move_end",
    "insert",
    "forward",
    "media_play",
    "media_pause",
    "media_close",
    "media_eject",
    "media_record",
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
    "num_lock",
    "numpad_0",
    "numpad_1",
    "numpad_2",
    "numpad_3",
    "numpad_4",
    "numpad_5",
    "numpad_6",
    "numpad_7",
    "numpad_8",
    "numpad_9",
    "numpad_divide",
    "numpad_multiply",
    "numpad_subtract",
    "numpad_add",
    "numpad_dot",
    "numpad_comma",
    "numpad_enter",
    "numpad_equals",
    "numpad_left_paren",
    "numpad_right_paren",
    "volume_mute",
    "info",
    "channel_up",
    "channel_down",
    "zoom_in",
    "zoom_out",
    "window",
    "guide",
    "bookmark",
    "captions",
    "settings",
    "app_switch",
    "language_switch",
    "contacts",
    "calendar",
    "music",
    "calculator",
    "assist",
    "brightness_down",
    "brightness_up",
    "media_audio_track",
    "sleep",
    "wakeup",
    "pairing",
    "media_top_menu",
    "last_channel",
    "tv_data_service",
    "voice_assist",
    "help",
    "navigate_previous",
    "navigate_next",
    "navigate_in",
    "navigate_out",
    "dpad_up_left",
    "dpad_down_left",
    "dpad_up_right",
    "dpad_down_right",
    "media_skip_forward",
    "media_skip_backward",
    "media_step_forward",
    "media_step_backward",
    "soft_sleep",
    "cut",
    "copy",
    "paste",
    "all_apps",
    "refresh",
]