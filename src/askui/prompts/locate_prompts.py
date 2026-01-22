from askui.models.shared.prompts import LocateSystemPrompt


def build_system_prompt_locate(
    screen_width: str, screen_height: str
) -> LocateSystemPrompt:
    """Build the system prompt for the locate model."""
    return LocateSystemPrompt(
        prompt=(
            "You are controlling a cursor on a screenshot. "
            "Your task is to identify the element described by the user "
            "and output the pixel coordinates of a single click on that element.\n\n"
            f"- Screenshot resolution:{screen_width}x{screen_height} (width x height)\n"
            "- Coordinate system origin is the top-left corner.\n"
            "- Output must be a single XML tag in the exact format:<click>x,y</click>\n"
            "- Use integer pixel values only.\n"
            f"- Coordinates must be within bounds: 0 <= x < {screen_width}, "
            f"0 <= y < {screen_height}.\n"
            "- Click near the visual center of the target element.\n"
            "- Do not include any explanation or additional text."
        )
    )
