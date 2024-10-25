import re
import base64

from io import BytesIO
from PIL import Image, ImageOps


def scale_image_with_padding(image, max_width, max_height):
    original_width, original_height = image.size
    aspect_ratio = original_width / original_height
    if (max_width / max_height) > aspect_ratio:
        scale_factor = max_height / original_height
    else:
        scale_factor = max_width / original_width
    scaled_width = int(original_width * scale_factor)
    scaled_height = int(original_height * scale_factor)
    scaled_image = image.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
    pad_left = (max_width - scaled_width) // 2
    pad_top = (max_height - scaled_height) // 2
    padded_image = ImageOps.expand(
        scaled_image,
        border=(pad_left, pad_top, max_width - scaled_width - pad_left, max_height - scaled_height - pad_top),
        fill=(0, 0, 0)  # Black padding
    )
    return padded_image


def scale_coordinates_back(x, y, original_width, original_height, max_width, max_height):
    aspect_ratio = original_width / original_height
    if (max_width / max_height) > aspect_ratio:
        scale_factor = max_height / original_height
        scaled_width = int(original_width * scale_factor)
        scaled_height = max_height
    else:
        scale_factor = max_width / original_width
        scaled_width = max_width
        scaled_height = int(original_height * scale_factor)
    pad_left = (max_width - scaled_width) // 2
    pad_top = (max_height - scaled_height) // 2
    adjusted_x = x - pad_left
    adjusted_y = y - pad_top
    if adjusted_x < 0 or adjusted_x > scaled_width or adjusted_y < 0 or adjusted_y > scaled_height:
        raise ValueError("Coordinates are outside the padded image area")
    original_x = adjusted_x / scale_factor
    original_y = adjusted_y / scale_factor
    return original_x, original_y


def extract_click_coordinates(text: str):
    pattern = r'<click>(\d+),\s*(\d+)'
    matches = re.findall(pattern, text)
    x, y = matches[-1]
    return int(x), int(y)


def base64_to_image(base64_string):
    base64_string = base64_string.split(",")[1]
    while len(base64_string) % 4 != 0:
        base64_string += '='
    image_data = base64.b64decode(base64_string)
    image = Image.open(BytesIO(image_data))
    return image


def image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_str
