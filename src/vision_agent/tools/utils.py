import base64
import socket
import subprocess
import time

from PIL import Image, ImageOps
from io import BytesIO


def wait_for_port(port: int, host: str = 'localhost', timeout: float = 5.0):
    """Wait until a port starts accepting TCP connections.
    Args:
        port: Port number.
        host: Host address on which the port should exist.
        timeout: In seconds. How long to wait before raising errors.
    Raises:
        TimeoutError: The port isn't accepting connection after time specified in `timeout`.
    """
    start_time = time.perf_counter()
    while True:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                break
        except OSError as ex:
            time.sleep(0.01)
            if time.perf_counter() - start_time >= timeout:
                raise TimeoutError('Waited too long for the port {} on host {} to start accepting '
                                   'connections.'.format(port, host)) from ex


def process_exists(process_name):
    call = 'TASKLIST', '/FI', 'imagename eq %s' % process_name
    # use buildin check_output right away
    output = subprocess.check_output(call).decode("utf-16-le", errors='ignore')
    # check in last line for process name
    last_line = output.strip().split('\r\n')[-1]
    # because Fail message could be translated
    return last_line.lower().startswith(process_name.lower())


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
