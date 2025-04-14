import re
import base64

from io import BytesIO
from PIL import Image


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
