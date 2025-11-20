from typing import Literal

from pydantic import BaseModel

from askui.chat.api.models import (
    AssistantId,
    FileId,
    MessageId,
    RunId,
    ThreadId,
    WorkspaceId,
    WorkspaceResource,
)
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
from askui.utils.datetime_utils import UnixDatetime, now
from askui.utils.id_utils import generate_time_ordered_id

ROOT_MESSAGE_PARENT_ID = "msg_000000000000000000000000"


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
    parent_id: MessageId | None = None


class MessageCreate(MessageBase):
    pass


class Message(MessageBase, WorkspaceResource):
    id: MessageId
    object: Literal["thread.message"] = "thread.message"
    created_at: UnixDatetime
    thread_id: ThreadId

    @classmethod
    def create(
        cls, workspace_id: WorkspaceId, thread_id: ThreadId, params: MessageCreate
    ) -> "Message":
        return cls(
            id=generate_time_ordered_id("msg"),
            created_at=now(),
            workspace_id=workspace_id,
            thread_id=thread_id,
            **params.model_dump(),
        )
