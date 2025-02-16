from random import randint
from PIL import Image
from typing import Callable, Literal
import streamlit as st
from askui import VisionAgent
import logging
from askui.utils import base64_to_image
import json
from datetime import date, datetime
import os
import glob


CHAT_SESSIONS_DIR_PATH = "./chat/sessions"
CHAT_IMAGES_DIR_PATH = "./chat/images"


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


def setup_chat_dirs():
    os.makedirs(CHAT_SESSIONS_DIR_PATH, exist_ok=True)
    os.makedirs(CHAT_IMAGES_DIR_PATH, exist_ok=True)


def get_session_id_from_path(path):
    return os.path.splitext(os.path.basename(path))[0]


def load_chat_history(session_id):
    messages = []
    session_path = os.path.join(CHAT_SESSIONS_DIR_PATH, f"{session_id}.jsonl")
    if os.path.exists(session_path):
        with open(session_path, "r") as f:
            for line in f:
                messages.append(json.loads(line))
    return messages


ROLE_MAP = {"user": "user", "anthropic computer use": "ai", "agentos": "assistant"}


UNKNOWN_ROLE = "unknown"


def write_message(
    role: Literal["User", "Anthropic Computer Use", "AgentOS"],
    content: str,
    timestamp: str,
    image: str | None = None,
):
    _role = ROLE_MAP.get(role.lower(), UNKNOWN_ROLE)
    avatar = None if _role != UNKNOWN_ROLE else "❔"
    with st.chat_message(_role, avatar=avatar):
        st.markdown(f"*{timestamp}* - **{role}**\n\n")
        st.markdown(content)
        if image:
            if os.path.isfile(image):
                img: Image.Image = Image.open(image)
                st.image(img)
            else:
                img = base64_to_image(image)
                st.image(img)


def chat_history_appender(session_id: str) -> Callable[[str | dict], None]:
    def append_to_chat_history(report: str | dict) -> None:
        if isinstance(report, dict):
            if report.get("image"):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                image_path = os.path.join(
                    CHAT_IMAGES_DIR_PATH, f"image_{timestamp}.png"
                )
                img = base64_to_image(report["image"])
                img.save(image_path)
                report["image"] = image_path
        else:
            report = {
                "role": "unknown",
                "content": f"🔄 {report}",
                "timestamp": datetime.now().isoformat(),
            }
        write_message(
            report["role"],
            report["content"],
            report["timestamp"],
            report.get("image"),
        )
        with open(
            os.path.join(CHAT_SESSIONS_DIR_PATH, f"{session_id}.jsonl"), "a"
        ) as f:
            json.dump(report, f, default=json_serial)
            f.write("\n")

    return append_to_chat_history


def get_available_sessions():
    session_files = glob.glob(os.path.join(CHAT_SESSIONS_DIR_PATH, "*.jsonl"))
    return sorted([get_session_id_from_path(f) for f in session_files])


def create_new_session() -> str:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    random_suffix = f"{randint(100, 999)}"
    session_id = f"{timestamp}{random_suffix}"
    with open(os.path.join(CHAT_SESSIONS_DIR_PATH, f"{session_id}.jsonl"), "w") as f:
        pass
    return session_id


def rerun():
    with VisionAgent(
        log_level=logging.DEBUG,
    ) as agent:
        for message in st.session_state.messages:
            try:
                if (
                    message.get("role") == "AgentOS"
                    and message.get("content") != "screenshot()"
                ):
                    func_call = f"agent.tools.os.{message['content']}"
                    print(func_call)
                    eval(func_call)
            except json.JSONDecodeError:
                continue
            except AttributeError:
                st.write(f"Invalid function: {message['content']}")
            except Exception as e:
                st.write(f"Error executing {message['content']}: {str(e)}")


def main():
    setup_chat_dirs()

    if st.sidebar.button("New Chat"):
        st.session_state.session_id = create_new_session()
        st.rerun()

    available_sessions = get_available_sessions()
    session_id = st.session_state.get("session_id", None)
    index_of_new_session = available_sessions.index(session_id) if session_id else 0
    session_id = st.sidebar.radio(
        "Sessions",
        available_sessions,
        index=index_of_new_session,
    )
    if session_id != st.session_state.get("session_id"):
        st.session_state.session_id = session_id
        st.rerun()

    report_callback = chat_history_appender(session_id)

    st.title(f"Agent Chat - {session_id}")
    st.session_state.messages = load_chat_history(session_id)

    # Display chat history
    for message in st.session_state.messages:
        write_message(
            message["role"],
            message["content"],
            message["timestamp"],
            message.get("image"),
        )

    # Chat input
    if len(st.session_state.messages) == 0:
        if prompt := st.chat_input("Say something"):
            with VisionAgent(
                log_level=logging.DEBUG,
                enable_report=True,
                report_callback=report_callback,
            ) as agent:
                agent.act(prompt, model_name="claude")
                st.rerun()
    else:
        if st.button("Rerun"):
            rerun()


if __name__ == "__main__":
    main()
