from pydantic import BaseModel
from typing_extensions import Literal


class CitationCharLocationParam(BaseModel):
    cited_text: str
    document_index: int
    document_title: str | None = None
    end_char_index: int
    start_char_index: int
    type: Literal["char_location"] = "char_location"


class CitationPageLocationParam(BaseModel):
    cited_text: str
    document_index: int
    document_title: str | None = None
    end_page_number: int
    start_page_number: int
    type: Literal["page_location"] = "page_location"


class CitationContentBlockLocationParam(BaseModel):
    cited_text: str
    document_index: int
    document_title: str | None = None
    end_block_index: int
    start_block_index: int
    type: Literal["content_block_location"] = "content_block_location"


TextCitationParam = (
    CitationCharLocationParam
    | CitationPageLocationParam
    | CitationContentBlockLocationParam
)


class UrlImageSourceParam(BaseModel):
    type: Literal["url"] = "url"
    url: str


class Base64ImageSourceParam(BaseModel):
    data: str
    media_type: Literal["image/jpeg", "image/png", "image/gif", "image/webp"]
    type: Literal["base64"] = "base64"


class CacheControlEphemeralParam(BaseModel):
    type: Literal["ephemeral"] = "ephemeral"


class ImageBlockParam(BaseModel):
    source: Base64ImageSourceParam | UrlImageSourceParam
    type: Literal["image"] = "image"
    cache_control: CacheControlEphemeralParam | None = None


class TextBlockParam(BaseModel):
    text: str
    type: Literal["text"] = "text"
    cache_control: CacheControlEphemeralParam | None = None
    citations: list[TextCitationParam] | None = None


class ToolResultBlockParam(BaseModel):
    tool_use_id: str
    type: Literal["tool_result"] = "tool_result"
    cache_control: CacheControlEphemeralParam | None = None
    content: str | list[TextBlockParam | ImageBlockParam]
    is_error: bool = False


class ToolUseBlockParam(BaseModel):
    id: str
    input: object
    name: str
    type: Literal["tool_use"] = "tool_use"
    cache_control: CacheControlEphemeralParam | None = None


ContentBlockParam = (
    ImageBlockParam | TextBlockParam | ToolResultBlockParam | ToolUseBlockParam
)


class MessageParam(BaseModel):
    role: Literal["user", "assistant"]
    content: str | list[ContentBlockParam]


__all__ = [
    "Base64ImageSourceParam",
    "CacheControlEphemeralParam",
    "CitationCharLocationParam",
    "CitationContentBlockLocationParam",
    "CitationPageLocationParam",
    "ContentBlockParam",
    "ImageBlockParam",
    "MessageParam",
    "TextBlockParam",
    "TextCitationParam",
    "ToolResultBlockParam",
    "ToolUseBlockParam",
    "UrlImageSourceParam",
]
