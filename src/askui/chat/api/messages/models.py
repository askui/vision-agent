from typing import Literal

from pydantic import BaseModel

from askui.chat.api.models import AssistantId, FileId, MessageId, RunId, ThreadId
from askui.models.shared.agent_message_param import (
    Base64ImageSourceParam,
    BetaRedactedThinkingBlock,
    BetaThinkingBlock,
    CacheControlEphemeralParam,
    StopReason,
    TextBlockParam,
    ToolUseBlockParam,
    UrlImageSourceParam,
)
from askui.utils.api_utils import Resource
from askui.utils.datetime_utils import UnixDatetime, now
from askui.utils.id_utils import generate_time_ordered_id


class BetaFileDocumentSourceParam(BaseModel):
    file_id: str
    type: Literal["file"] = "file"


Source = BetaFileDocumentSourceParam


class RequestDocumentBlockParam(BaseModel):
    source: Source
    type: Literal["document"] = "document"
    cache_control: CacheControlEphemeralParam | None = None


class FileImageSourceParam(BaseModel):
    """Image source that references a saved file."""

    id: FileId
    type: Literal["file"] = "file"


class ImageBlockParam(BaseModel):
    source: Base64ImageSourceParam | UrlImageSourceParam | FileImageSourceParam
    type: Literal["image"] = "image"
    cache_control: CacheControlEphemeralParam | None = None


class ToolResultBlockParam(BaseModel):
    tool_use_id: str
    type: Literal["tool_result"] = "tool_result"
    cache_control: CacheControlEphemeralParam | None = None
    content: str | list[TextBlockParam | ImageBlockParam]
    is_error: bool = False


ContentBlockParam = (
    ImageBlockParam
    | TextBlockParam
    | ToolResultBlockParam
    | ToolUseBlockParam
    | BetaThinkingBlock
    | BetaRedactedThinkingBlock
    | RequestDocumentBlockParam
)


class MessageParam(BaseModel):
    role: Literal["user", "assistant"]
    content: str | list[ContentBlockParam]
    stop_reason: StopReason | None = None


class MessageBase(MessageParam):
    assistant_id: AssistantId | None = None
    run_id: RunId | None = None


class MessageCreateParams(MessageBase):
    pass


class Message(MessageBase, Resource):
    id: MessageId
    object: Literal["thread.message"] = "thread.message"
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
