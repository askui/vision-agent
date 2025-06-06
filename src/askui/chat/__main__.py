import io
import json
import time
from pathlib import Path

import httpx
import streamlit as st
from PIL import Image

from askui.chat.api.messages.service import Message, MessageService
from askui.chat.api.runs.service import RunService
from askui.chat.api.threads.service import ThreadService

# from askui.chat.click_recorder import ClickRecorder
from askui.models.shared.computer_agent_message_param import (
    Base64ImageSourceParam,
    MessageParam,
    UrlImageSourceParam,
)
from askui.utils.image_utils import base64_to_image

st.set_page_config(
    page_title="Vision Agent Chat",
    page_icon="💬",
)


BASE_DIR = Path("./chat")


@st.cache_resource
def get_thread_service() -> ThreadService:
    return ThreadService(BASE_DIR)


@st.cache_resource
def get_message_service() -> MessageService:
    return MessageService(BASE_DIR)


@st.cache_resource
def get_run_service() -> RunService:
    return RunService(BASE_DIR)


thread_service = get_thread_service()
message_service = get_message_service()
run_service = get_run_service()

# click_recorder = ClickRecorder()


def get_image(
    source: Base64ImageSourceParam | UrlImageSourceParam,
) -> Image.Image:
    match source.type:
        case "base64":
            data = source.data
            if isinstance(data, str):
                return base64_to_image(data)
            error_msg = f"Image source data type not supported: {type(data)}"
            raise NotImplementedError(error_msg)
        case "url":
            response = httpx.get(source.url)
            return Image.open(io.BytesIO(response.content))


def write_message(  # noqa: C901
    message: Message,
) -> None:
    # Create a container for the message and delete button
    col1, col2 = st.columns([0.95, 0.05])

    with col1:
        with st.chat_message(message.role):
            st.markdown(f"*{message.created_at.isoformat()}* - **{message.role}**\n\n")
            if isinstance(message.content, str):
                st.markdown(message.content)
            else:
                for block in message.content:
                    match block.type:
                        case "image":
                            st.image(get_image(block.source))
                        case "text":
                            st.markdown(block.text)
                        case "tool_result":
                            st.markdown(f"Tool use id: {block.tool_use_id}")
                            st.markdown(f"Erroneous: {block.is_error}")
                            content = block.content
                            if isinstance(content, str):
                                st.markdown(content)
                            else:
                                for nested_block in content:
                                    match nested_block.type:
                                        case "image":
                                            st.image(get_image(nested_block.source))
                                        case "text":
                                            st.markdown(nested_block.text)
                        case _:
                            st.markdown(
                                json.dumps(block.model_dump(mode="json"), indent=2)
                            )

    # Add delete button in the second column if message_id is provided
    with col2:
        if st.button("🗑️", key=f"delete_{message.id}"):
            message_service.delete(st.session_state.thread_id, message.id)
            st.rerun()


# def paint_crosshair(
#     image: Image.Image,
#     coordinates: tuple[int, int],
#     size: int | None = None,
#     color: str = "red",
#     width: int = 4,
# ) -> Image.Image:
#     """
#     Paints a crosshair at the given coordinates on the image.

#     :param image: A PIL Image object.
#     :param coordinates: A tuple (x, y) representing the coordinates of the point.
#     :param size: Optional length of each line in the crosshair. Defaults to min(width,height)/20
#     :param color: The color of the crosshair.
#     :param width: The width of the crosshair.
#     :return: A new image with the crosshair.
#     """
#     if size is None:
#         size = (
#             min(image.width, image.height) // 20
#         )  # Makes crosshair ~5% of smallest image dimension

#     image_copy = image.copy()
#     draw = ImageDraw.Draw(image_copy)
#     x, y = coordinates
#     # Draw horizontal and vertical lines
#     draw.line((x - size, y, x + size, y), fill=color, width=width)
#     draw.line((x, y - size, x, y + size), fill=color, width=width)
#     return image_copy


# prompt = """The following image is a screenshot with a red crosshair on top of an element that the user wants to interact with. Give me a description that uniquely describes the element as concise as possible across all elements on the screen that the user most likely wants to interact with. Examples:

# - "Submit button"
# - "Cell within the table about European countries in the third row and 6th column (area in km^2) in the right-hand browser window"
# - "Avatar in the top right hand corner of the browser in focus that looks like a woman"
# """


# def rerun() -> None:
#     st.markdown("### Re-running...")
#     with VisionAgent(
#         log_level=logging.DEBUG,
#         tools=tools,
#     ) as agent:
#         screenshot: Image.Image | None = None
#         for message in messages_service.list_(st.session_state.thread_id).data:
#             try:
#                 if (
#                     message.role == MessageRole.ASSISTANT
#                     or message.role == MessageRole.USER
#                 ):
#                     content = message.content[0]
#                     if content.text == "screenshot()":
#                         screenshot = (
#                             get_image(content.image_paths[0])
#                             if content.image_paths
#                             else None
#                         )
#                         continue
#                     if content.text:
#                         if match := re.match(
#                             r"mouse\((\d+),\s*(\d+)\)", cast("str", content.text)
#                         ):
#                             if not screenshot:
#                                 error_msg = "Screenshot is required to paint crosshair"
#                                 raise ValueError(error_msg)  # noqa: TRY301
#                             x, y = map(int, match.groups())
#                             screenshot_with_crosshair = paint_crosshair(
#                                 screenshot, (x, y)
#                             )
#                             element_description = agent.get(
#                                 query=prompt,
#                                 image=screenshot_with_crosshair,
#                                 model=ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022,
#                             )
#                             messages_service.create(
#                                 thread_id=st.session_state.thread_id,
#                                 role=message.role.value,
#                                 content=f"Move mouse to {element_description}",
#                                 image=screenshot_with_crosshair,
#                             )
#                             agent.mouse_move(
#                                 locator=element_description.replace('"', ""),
#                                 model=ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022,
#                             )
#                         else:
#                             messages_service.create(
#                                 thread_id=st.session_state.thread_id,
#                                 role=message.role.value,
#                                 content=content.text,
#                                 image=None,
#                             )
#                             func_call = f"agent.tools.os.{content.text}"
#                             eval(func_call)
#             except json.JSONDecodeError:
#                 continue
#             except AttributeError:
#                 st.write(str(InvalidFunctionError(cast("str", content.text))))
#             except Exception as e:  # noqa: BLE001 - We want to catch all other exceptions here
#                 st.write(str(FunctionExecutionError(cast("str", content.text), e)))


if st.sidebar.button("New Chat"):
    thread = thread_service.create()
    st.session_state.thread_id = thread.id
    st.rerun()

available_threads = thread_service.list_().data
thread_id = st.session_state.get("thread_id", None)

if not thread_id and not available_threads:
    thread = thread_service.create()
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
                    new_thread = thread_service.create()
                    st.session_state.thread_id = new_thread.id
            thread_service.delete(t.id)
            st.rerun()

if thread_id != st.session_state.get("thread_id"):
    st.session_state.thread_id = thread_id
    st.rerun()


st.title(f"Vision Agent Chat - {thread_id}")

# Display chat history
messages = message_service.list_(thread_id).data
for message in messages:
    write_message(message)

last_message = messages[-1] if messages else None

# if value_to_type := st.chat_input("Simulate Typing for User (Demonstration)"):
#     reporter.add_message(
#         role="user",
#         content=f'type("{value_to_type}", 50)',
#     )
#     st.rerun()

# if st.button("Simulate left click"):
#     reporter.add_message(
#         role="User (Demonstration)",
#         content='click("left", 1)',
#     )
#     st.rerun()

# # Chat input
# if st.button(
#     "Demonstrate where to move mouse"
# ):  # only single step, only click supported for now, independent of click always registered as click
#     image, coordinates = click_recorder.record()
#     reporter.add_message(
#         role="User (Demonstration)",
#         content="screenshot()",
#         image=image,
#     )
#     reporter.add_message(
#         role="User (Demonstration)",
#         content=f"mouse_move({coordinates[0]}, {coordinates[1]})",
#         image=draw_point_on_image(image, coordinates[0], coordinates[1]),
#     )
#     st.rerun()

# if st.session_state.get("input_event_listening"):
#     while input_event := tools.os.poll_event():
#         image = tools.os.screenshot(report=False)
#         if input_event.pressed:
#             reporter.add_message(
#                 role="User (Demonstration)",
#                 content=f"mouse_move({input_event.x}, {input_event.y})",
#                 image=draw_point_on_image(image, input_event.x, input_event.y),
#             )
#             reporter.add_message(
#                 role="User (Demonstration)",
#                 content=f'click("{input_event.button}")',
#             )
#     if st.button("Refresh"):
#         st.rerun()
#     if st.button("Stop listening to input events"):
#         tools.os.stop_listening()
#         st.session_state["input_event_listening"] = False
#         st.rerun()
# else:
#     if st.button("Listen to input events"):
#         tools.os.start_listening()
#         st.session_state["input_event_listening"] = True
#         st.rerun()

if act_prompt := st.chat_input("Ask AI"):
    if act_prompt != "Continue":
        last_message = message_service.create(
            thread_id=thread_id,
            message=MessageParam(
                role="user",
                content=act_prompt,
            ),
        )
        write_message(last_message)
    run = run_service.create(thread_id, stream=False)
    time.sleep(1)
    while run := run_service.retrieve(run.id):
        new_messages = message_service.list_(
            thread_id, after=last_message.id if last_message else None
        ).data
        for message in new_messages:
            write_message(message)
        last_message = new_messages[-1] if new_messages else last_message
        if run.status not in {"queued", "running", "in_progress"}:
            break
        time.sleep(1)


if act_prompt := st.chat_input("Ask AI (streaming)"):
    if act_prompt != "Continue":
        last_message = message_service.create(
            thread_id=thread_id,
            message=MessageParam(
                role="user",
                content=act_prompt,
            ),
        )
        write_message(last_message)

    # Use the streaming API
    event_stream = run_service.create(thread_id, stream=True)
    import asyncio

    async def handle_stream() -> None:
        last_msg_id = last_message.id if last_message else None
        async for event in event_stream:
            if event.event == "message.created":
                msg = event.data
                if msg and (not last_msg_id or msg.id > last_msg_id):
                    write_message(msg)
                    last_msg_id = msg.id

    # Run the async handler in Streamlit (sync context)
    asyncio.run(handle_stream())

# if st.button("Rerun"):
#     rerun()
