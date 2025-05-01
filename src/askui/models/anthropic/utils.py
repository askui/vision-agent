import re


def extract_click_coordinates(text: str) -> tuple[int, int]:
    pattern = r"<click>(\d+),\s*(\d+)"
    matches = re.findall(pattern, text)
    x, y = matches[-1]
    return int(x), int(y)
