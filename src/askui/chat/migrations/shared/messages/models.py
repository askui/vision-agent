from typing import Annotated, Any, Literal

from pydantic import BaseModel, BeforeValidator, Field

from askui.chat.migrations.shared.assistants.models import AssistantIdV1
from askui.chat.migrations.shared.models import UnixDatetimeV1, WorkspaceIdV1
from askui.chat.migrations.shared.runs.models import RunIdV1
from askui.chat.migrations.shared.threads.models import ThreadIdV1
from askui.chat.migrations.shared.utils import build_prefixer

MessageIdV1 = Annotated[
    str, Field(pattern=r"^msg_[a-z0-9]+$"), BeforeValidator(build_prefixer("msg"))
]


class CacheControlEphemeralParamV1(BaseModel):
    type: Literal["ephemeral"] = "ephemeral"


class CitationCharLocationParamV1(BaseModel):
    cited_text: str
    document_index: int
    document_title: str | None = None
    end_char_index: int
    start_char_index: int
    type: Literal["char_location"] = "char_location"


class CitationPageLocationParamV1(BaseModel):
    cited_text: str
    document_index: int
    document_title: str | None = None
    end_page_number: int
    start_page_number: int
    type: Literal["page_location"] = "page_location"


class CitationContentBlockLocationParamV1(BaseModel):
    cited_text: str
    document_index: int
    document_title: str | None = None
    end_block_index: int
    start_block_index: int
    type: Literal["content_block_location"] = "content_block_location"


TextCitationParamV1 = (
    CitationCharLocationParamV1
    | CitationPageLocationParamV1
    | CitationContentBlockLocationParamV1
)


class UrlImageSourceParamV1(BaseModel):
    type: Literal["url"] = "url"
    url: str


class Base64ImageSourceParamV1(BaseModel):
    data: str
    media_type: Literal["image/jpeg", "image/png", "image/gif", "image/webp"]
    type: Literal["base64"] = "base64"


class FileImageSourceParamV1(BaseModel):
    """Image source that references a saved file."""

    id: str  # FileId equivalent
    type: Literal["file"] = "file"


class ImageBlockParamV1(BaseModel):
    source: Base64ImageSourceParamV1 | UrlImageSourceParamV1 | FileImageSourceParamV1
    type: Literal["image"] = "image"
    cache_control: CacheControlEphemeralParamV1 | None = None


class TextBlockParamV1(BaseModel):
    text: str
    type: Literal["text"] = "text"
    cache_control: CacheControlEphemeralParamV1 | None = None
    citations: list[TextCitationParamV1] | None = None


class ToolResultBlockParamV1(BaseModel):
    tool_use_id: str
    type: Literal["tool_result"] = "tool_result"
    cache_control: CacheControlEphemeralParamV1 | None = None
    content: str | list[TextBlockParamV1 | ImageBlockParamV1]
    is_error: bool = False


class ToolUseBlockParamV1(BaseModel):
    id: str
    input: object
    name: str
    type: Literal["tool_use"] = "tool_use"
    cache_control: CacheControlEphemeralParamV1 | None = None


class BetaThinkingBlockV1(BaseModel):
    signature: str
    thinking: str
    type: Literal["thinking"]


class BetaRedactedThinkingBlockV1(BaseModel):
    data: str
    type: Literal["redacted_thinking"]


class BetaFileDocumentSourceParamV1(BaseModel):
    file_id: str
    type: Literal["file"] = "file"


SourceV1 = BetaFileDocumentSourceParamV1


class RequestDocumentBlockParamV1(BaseModel):
    source: SourceV1
    type: Literal["document"] = "document"
    cache_control: CacheControlEphemeralParamV1 | None = None


ContentBlockParamV1 = (
    ImageBlockParamV1
    | TextBlockParamV1
    | ToolResultBlockParamV1
    | ToolUseBlockParamV1
    | BetaThinkingBlockV1
    | BetaRedactedThinkingBlockV1
    | RequestDocumentBlockParamV1
)


StopReasonV1 = Literal[
    "end_turn", "max_tokens", "stop_sequence", "tool_use", "pause_turn", "refusal"
]


class MessageV1(BaseModel):
    id: MessageIdV1
    object: Literal["thread.message"] = "thread.message"
    created_at: UnixDatetimeV1
    thread_id: ThreadIdV1
    role: Literal["user", "assistant"]
    content: str | list[ContentBlockParamV1]
    stop_reason: StopReasonV1 | None = None
    assistant_id: AssistantIdV1 | None = None
    run_id: RunIdV1 | None = None
    workspace_id: WorkspaceIdV1 = Field(exclude=True)

    def to_db_dict(self) -> dict[str, Any]:
        return {
            **self.model_dump(
                exclude={"id", "thread_id", "assistant_id", "run_id", "object"}
            ),
            "id": self.id.removeprefix("msg_"),
            "thread_id": self.thread_id.removeprefix("thread_"),
            "assistant_id": self.assistant_id.removeprefix("asst_")
            if self.assistant_id
            else None,
            "run_id": self.run_id.removeprefix("run_") if self.run_id else None,
            "workspace_id": self.workspace_id.hex,
        }
