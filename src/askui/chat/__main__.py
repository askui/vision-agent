import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from random import randint
from typing import Union

import streamlit as st
from PIL import Image, ImageDraw
from typing_extensions import TypedDict, override

from askui import VisionAgent
from askui.chat.click_recorder import ClickRecorder
from askui.chat.exceptions import FunctionExecutionError, InvalidFunctionError
from askui.models import ModelName
from askui.reporting import Reporter
from askui.utils.image_utils import base64_to_image, draw_point_on_image

st.set_page_config(
    page_title="Vision Agent Chat",
    page_icon="💬",
)


CHAT_SESSIONS_DIR_PATH = Path("./chat/sessions")
CHAT_IMAGES_DIR_PATH = Path("./chat/images")

click_recorder = ClickRecorder()


def setup_chat_dirs() -> None:
    Path.mkdir(CHAT_SESSIONS_DIR_PATH, parents=True, exist_ok=True)
    Path.mkdir(CHAT_IMAGES_DIR_PATH, parents=True, exist_ok=True)


def get_session_id_from_path(path: str) -> str:
    """Get session ID from file path."""
    return Path(path).stem


def load_chat_history(session_id: str) -> list[dict]:
    """Load chat history for a given session ID."""
    messages: list[dict] = []
    session_path = CHAT_SESSIONS_DIR_PATH / f"{session_id}.jsonl"
    if session_path.exists():
        with session_path.open("r") as f:
            messages.extend(json.loads(line) for line in f)
    return messages


ROLE_MAP = {
    "user": "user",
    "anthropic computer use": "ai",
    "agentos": "assistant",
    "user (demonstration)": "user",
}


UNKNOWN_ROLE = "unknown"


def get_image(img_b64_str_or_path: str) -> Image.Image:
    """Get image from base64 string or file path."""
    if Path(img_b64_str_or_path).is_file():
        return Image.open(img_b64_str_or_path)
    return base64_to_image(img_b64_str_or_path)


def write_message(
    role: str,
    content: str | dict | list,
    timestamp: str,
    image: Image.Image
    | str
    | list[str | Image.Image]
    | list[str]
    | list[Image.Image]
    | None = None,
) -> None:
    _role = ROLE_MAP.get(role.lower(), UNKNOWN_ROLE)
    avatar = None if _role != UNKNOWN_ROLE else "❔"
    with st.chat_message(_role, avatar=avatar):
        st.markdown(f"*{timestamp}* - **{role}**\n\n")
        st.markdown(
            json.dumps(content, indent=2)
            if isinstance(content, (dict, list))
            else content
        )
        if image:
            if isinstance(image, list):
                for img in image:
                    img = get_image(img) if isinstance(img, str) else img
                    st.image(img)
            else:
                img = get_image(image) if isinstance(image, str) else image
                st.image(img)


def save_image(image: Image.Image) -> str:
    """Save image to disk and return path."""
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    image_path = CHAT_IMAGES_DIR_PATH / f"image_{timestamp}.png"
    image.save(image_path)
    return str(image_path)


class Message(TypedDict):
    role: str
    content: str | dict | list
    timestamp: str
    image: str | list[str] | None


class ChatHistoryAppender(Reporter):
    def __init__(self, session_id: str) -> None:
        self._session_id = session_id

    @override
    def add_message(
        self,
        role: str,
        content: Union[str, dict, list],
        image: Image.Image | list[Image.Image] | None = None,
    ) -> None:
        image_paths: list[str] = []
        if image is None:
            _images = []
        elif isinstance(image, list):
            _images = image
        else:
            _images = [image]
        image_paths.extend(save_image(img) for img in _images)
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now(tz=timezone.utc).isoformat(),
            image=image_paths,
        )
        write_message(**message)
        with (CHAT_SESSIONS_DIR_PATH / f"{self._session_id}.jsonl").open("a") as f:
            json.dump(message, f)
            f.write("\n")

    @override
    def generate(self) -> None:
        pass


def get_available_sessions() -> list[str]:
    """Get list of available session IDs."""
    session_files = list(CHAT_SESSIONS_DIR_PATH.glob("*.jsonl"))
    return sorted([get_session_id_from_path(f) for f in session_files], reverse=True)


def create_new_session() -> str:
    """Create a new chat session."""
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d%H%M%S%f")
    random_suffix = f"{randint(100, 999)}"
    session_id = f"{timestamp}{random_suffix}"
    (CHAT_SESSIONS_DIR_PATH / f"{session_id}.jsonl").touch()
    return session_id


def paint_crosshair(
    image: Image.Image,
    coordinates: tuple[int, int],
    size: int | None = None,
    color: str = "red",
    width: int = 4,
) -> Image.Image:
    """
    Paints a crosshair at the given coordinates on the image.

    :param image: A PIL Image object.
    :param coordinates: A tuple (x, y) representing the coordinates of the point.
    :param size: Optional length of each line in the crosshair. Defaults to min(width,height)/20
    :param color: The color of the crosshair.
    :param width: The width of the crosshair.
    :return: A new image with the crosshair.
    """
    if size is None:
        size = (
            min(image.width, image.height) // 20
        )  # Makes crosshair ~5% of smallest image dimension

    image_copy = image.copy()
    draw = ImageDraw.Draw(image_copy)
    x, y = coordinates
    # Draw horizontal and vertical lines
    draw.line((x - size, y, x + size, y), fill=color, width=width)
    draw.line((x, y - size, x, y + size), fill=color, width=width)
    return image_copy


prompt = """The following image is a screenshot with a red crosshair on top of an element that the user wants to interact with. Give me a description that uniquely describes the element as concise as possible across all elements on the screen that the user most likely wants to interact with. Examples:

- "Submit button"
- "Cell within the table about European countries in the third row and 6th column (area in km^2) in the right-hand browser window"
- "Avatar in the top right hand corner of the browser in focus that looks like a woman"
"""


def rerun() -> None:
    st.markdown("### Re-running...")
    with VisionAgent(
        log_level=logging.DEBUG,
    ) as agent:
        screenshot: Image.Image | None = None
        for message in st.session_state.messages:
            try:
                if (
                    message.get("role") == "AgentOS"
                    or message.get("role") == "User (Demonstration)"
                ):
                    if message.get("content") == "screenshot()":
                        screenshot = get_image(message["image"])
                        continue
                    if message.get("content"):
                        if match := re.match(
                            r"mouse\((\d+),\s*(\d+)\)", message["content"]
                        ):
                            if not screenshot:
                                error_msg = "Screenshot is required to paint crosshair"
                                raise ValueError(error_msg)  # noqa: TRY301
                            x, y = map(int, match.groups())
                            screenshot_with_crosshair = paint_crosshair(
                                screenshot, (x, y)
                            )
                            element_description = agent.get(
                                query=prompt,
                                image=screenshot_with_crosshair,
                                model=ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022,
                            )
                            write_message(
                                message["role"],
                                f"Move mouse to {element_description}",
                                datetime.now(tz=timezone.utc).isoformat(),
                                image=screenshot_with_crosshair,
                            )
                            agent.mouse_move(
                                locator=element_description.replace('"', ""),
                                model=ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022,
                            )
                        else:
                            write_message(
                                message["role"],
                                message["content"],
                                datetime.now(tz=timezone.utc).isoformat(),
                                message.get("image"),
                            )
                            func_call = f"agent.tools.os.{message['content']}"
                            eval(func_call)
            except json.JSONDecodeError:
                continue
            except AttributeError:
                st.write(str(InvalidFunctionError(message["content"])))
            except Exception as e:  # noqa: BLE001 - We want to catch all other exceptions here
                st.write(str(FunctionExecutionError(message["content"], e)))


setup_chat_dirs()

if st.sidebar.button("New Chat"):
    st.session_state.session_id = create_new_session()
    st.rerun()

available_sessions = get_available_sessions()
session_id = st.session_state.get("session_id", None)

if not session_id and not available_sessions:
    session_id = create_new_session()
    st.session_state.session_id = session_id
    st.rerun()

index_of_session = available_sessions.index(session_id) if session_id else 0
session_id = st.sidebar.radio(
    "Sessions",
    available_sessions,
    index=index_of_session,
)
if session_id != st.session_state.get("session_id"):
    st.session_state.session_id = session_id
    st.rerun()

reporter = ChatHistoryAppender(session_id)

st.title(f"Vision Agent Chat - {session_id}")
st.session_state.messages = load_chat_history(session_id)

# Display chat history
for message in st.session_state.messages:
    write_message(
        message["role"],
        message["content"],
        message["timestamp"],
        message.get("image"),
    )

if value_to_type := st.chat_input("Simulate Typing for User (Demonstration)"):
    reporter.add_message(
        role="User (Demonstration)",
        content=f'type("{value_to_type}", 50)',
    )
    st.rerun()

if st.button("Simulate left click"):
    reporter.add_message(
        role="User (Demonstration)",
        content='click("left", 1)',
    )
    st.rerun()

# Chat input
if st.button(
    "Demonstrate where to move mouse"
):  # only single step, only click supported for now, independent of click always registered as click
    image, coordinates = click_recorder.record()
    reporter.add_message(
        role="User (Demonstration)",
        content="screenshot()",
        image=image,
    )
    reporter.add_message(
        role="User (Demonstration)",
        content=f"mouse({coordinates[0]}, {coordinates[1]})",
        image=draw_point_on_image(image, coordinates[0], coordinates[1]),
    )
    st.rerun()

if act_prompt := st.chat_input("Ask AI"):
    with VisionAgent(
        log_level=logging.DEBUG,
        reporters=[reporter],
    ) as agent:
        agent.act(act_prompt, model="claude")
        st.rerun()

if st.button("Rerun"):
    rerun()
