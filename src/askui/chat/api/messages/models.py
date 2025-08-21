from typing import Literal

from askui.chat.api.models import AssistantId, MessageId, RunId, ThreadId
from askui.models.shared.agent_message_param import MessageParam
from askui.utils.api_utils import Resource
from askui.utils.datetime_utils import UnixDatetime, now
from askui.utils.id_utils import generate_time_ordered_id


class MessageBase(MessageParam):
    assistant_id: AssistantId | None = None
    object: Literal["thread.message"] = "thread.message"
    role: Literal["user", "assistant"]
    run_id: RunId | None = None


class MessageCreateParams(MessageBase):
    pass


class Message(MessageBase, Resource):
    id: MessageId
    created_at: UnixDatetime
    thread_id: ThreadId

    @classmethod
    def create(cls, thread_id: ThreadId, params: MessageCreateParams) -> "Message":
        return cls(
            id=generate_time_ordered_id("msg"),
            created_at=now(),
            thread_id=thread_id,
            **params.model_dump(),
        )
