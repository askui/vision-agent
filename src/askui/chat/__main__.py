import json
import logging
import re
from pathlib import Path
from typing import Any, Union, cast

import streamlit as st
from PIL import Image, ImageDraw
from typing_extensions import override

from askui import VisionAgent
from askui.chat.api.messages.service import MessageRole, MessageService
from askui.chat.api.threads.service import ThreadService
from askui.chat.click_recorder import ClickRecorder
from askui.chat.exceptions import FunctionExecutionError, InvalidFunctionError
from askui.models import ModelName
from askui.reporting import Reporter
from askui.tools.pynput.pynput_agent_os import PynputAgentOs
from askui.tools.toolbox import AgentToolbox
from askui.utils.image_utils import base64_to_image, draw_point_on_image

st.set_page_config(
    page_title="Vision Agent Chat",
    page_icon="💬",
)


BASE_DIR = Path("./chat")
threads_api = ThreadService(BASE_DIR)
messages_api = MessageService(BASE_DIR)
click_recorder = ClickRecorder()


def get_image(img_b64_str_or_path: str) -> Image.Image:
    """Get image from base64 string or file path."""
    if Path(img_b64_str_or_path).is_file():
        return Image.open(img_b64_str_or_path)
    return base64_to_image(img_b64_str_or_path)


def write_message(
    role: str,
    content: str | dict[str, Any] | list[Any],
    timestamp: str,
    image: Image.Image
    | str
    | list[str | Image.Image]
    | list[str]
    | list[Image.Image]
    | None = None,
    message_id: str | None = None,
) -> None:
    _role = messages_api.ROLE_MAP.get(role.lower(), MessageRole.UNKNOWN)
    avatar = None if _role != MessageRole.UNKNOWN else "❔"

    # Create a container for the message and delete button
    col1, col2 = st.columns([0.95, 0.05])

    with col1:
        with st.chat_message(_role.value, avatar=avatar):
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

    # Add delete button in the second column if message_id is provided
    if message_id:
        with col2:
            if st.button("🗑️", key=f"delete_{message_id}"):
                messages_api.delete(st.session_state.thread_id, message_id)
                st.rerun()


class ChatHistoryAppender(Reporter):
    def __init__(self, thread_id: str) -> None:
        self._thread_id = thread_id

    @override
    def add_message(
        self,
        role: str,
        content: Union[str, dict[str, Any], list[Any]],
        image: Image.Image | list[Image.Image] | None = None,
    ) -> None:
        message = messages_api.create(
            thread_id=self._thread_id, role=role, content=content, image=image
        )
        write_message(
            role=message.role.value,
            content=message.content[0].text or "",
            timestamp=message.created_at.isoformat(),
            image=message.content[0].image_paths,
            message_id=message.id,
        )

    @override
    def generate(self) -> None:
        pass


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
        tools=tools,
    ) as agent:
        screenshot: Image.Image | None = None
        for message in messages_api.list_(st.session_state.thread_id).data:
            try:
                if (
                    message.role == MessageRole.ASSISTANT
                    or message.role == MessageRole.USER
                ):
                    content = message.content[0]
                    if content.text == "screenshot()":
                        screenshot = (
                            get_image(content.image_paths[0])
                            if content.image_paths
                            else None
                        )
                        continue
                    if content.text:
                        if match := re.match(
                            r"mouse\((\d+),\s*(\d+)\)", cast("str", content.text)
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
                            messages_api.create(
                                thread_id=st.session_state.thread_id,
                                role=message.role.value,
                                content=f"Move mouse to {element_description}",
                                image=screenshot_with_crosshair,
                            )
                            agent.mouse_move(
                                locator=element_description.replace('"', ""),
                                model=ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022,
                            )
                        else:
                            messages_api.create(
                                thread_id=st.session_state.thread_id,
                                role=message.role.value,
                                content=content.text,
                                image=None,
                            )
                            func_call = f"agent.tools.os.{content.text}"
                            eval(func_call)
            except json.JSONDecodeError:
                continue
            except AttributeError:
                st.write(str(InvalidFunctionError(cast("str", content.text))))
            except Exception as e:  # noqa: BLE001 - We want to catch all other exceptions here
                st.write(str(FunctionExecutionError(cast("str", content.text), e)))


if st.sidebar.button("New Chat"):
    thread = threads_api.create()
    st.session_state.thread_id = thread.id
    st.rerun()

available_threads = threads_api.list_().data
thread_id = st.session_state.get("thread_id", None)

if not thread_id and not available_threads:
    thread = threads_api.create()
    thread_id = thread.id
    st.session_state.thread_id = thread_id
    st.rerun()

index_of_thread = 0
if thread_id:
    for index, thread in enumerate(available_threads):
        if thread.id == thread_id:
            index_of_thread = index
            break

# Create columns for thread selection and delete buttons
thread_cols = st.sidebar.columns([0.8, 0.2])
with thread_cols[0]:
    thread_id = st.radio(
        "Threads",
        [t.id for t in available_threads],
        index=index_of_thread,
    )

# Add delete buttons for each thread
for t in available_threads:
    with thread_cols[1]:
        if st.button("🗑️", key=f"delete_thread_{t.id}"):
            if t.id == thread_id:
                # If deleting current thread, switch to first available thread
                remaining_threads = [th for th in available_threads if th.id != t.id]
                if remaining_threads:
                    st.session_state.thread_id = remaining_threads[0].id
                else:
                    # Create new thread if no threads left
                    new_thread = threads_api.create()
                    st.session_state.thread_id = new_thread.id
            threads_api.delete(t.id)
            st.rerun()

if thread_id != st.session_state.get("thread_id"):
    st.session_state.thread_id = thread_id
    st.rerun()

reporter = ChatHistoryAppender(thread_id)


@st.cache_resource
def get_tools() -> AgentToolbox:
    return AgentToolbox(agent_os=PynputAgentOs(reporter=reporter))


tools = get_tools()


st.title(f"Vision Agent Chat - {thread_id}")

# Display chat history
for message in messages_api.list_(thread_id).data:
    write_message(
        message.role.value,
        message.content[0].text or "",
        message.created_at.isoformat(),
        message.content[0].image_paths,
        message.id,  # Pass the message ID to enable deletion
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
        content=f"mouse_move({coordinates[0]}, {coordinates[1]})",
        image=draw_point_on_image(image, coordinates[0], coordinates[1]),
    )
    st.rerun()

if st.session_state.get("input_event_listening"):
    while input_event := tools.os.poll_event():
        image = tools.os.screenshot(report=False)
        if input_event.pressed:
            reporter.add_message(
                role="User (Demonstration)",
                content=f"mouse_move({input_event.x}, {input_event.y})",
                image=draw_point_on_image(image, input_event.x, input_event.y),
            )
            reporter.add_message(
                role="User (Demonstration)",
                content=f'click("{input_event.button}")',
            )
    if st.button("Refresh"):
        st.rerun()
    if st.button("Stop listening to input events"):
        tools.os.stop_listening()
        st.session_state["input_event_listening"] = False
        st.rerun()
else:
    if st.button("Listen to input events"):
        tools.os.start_listening()
        st.session_state["input_event_listening"] = True
        st.rerun()

if act_prompt := st.chat_input("Ask AI"):
    with VisionAgent(  # we need the vision agent
        log_level=logging.DEBUG,
        reporters=[reporter],
        tools=tools,
    ) as agent:
        agent.act(act_prompt, model=ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022)
        st.rerun()

if st.button("Rerun"):
    rerun()
