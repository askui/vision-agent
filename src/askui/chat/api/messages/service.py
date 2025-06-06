import io
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import httpx
from PIL import Image
from pydantic import AwareDatetime, BaseModel, Field, computed_field
from typing_extensions import Annotated

from askui.chat.api.models import Event
from askui.chat.api.utils import generate_time_ordered_id
from askui.models.shared.computer_agent_message_param import (
    Base64ImageSourceParam,
    ContentBlockParam,
    ImageBlockParam,
    MessageParam,
    TextBlockParam,
)
from askui.utils.image_utils import ImageSource

MessageId = Annotated[
    str,
    Field(default_factory=lambda: generate_time_ordered_id("msg")),
]


class MessageContentTextText(BaseModel):
    value: str
    annotations: list[Any] = Field(default_factory=list, max_length=0)


class MessageContentText(BaseModel):
    type: Literal["text"] = "text"
    text: MessageContentTextText

    @classmethod
    def from_str(cls, text: str) -> "MessageContentText":
        return cls(
            type="text",
            text=MessageContentTextText(value=text),
        )


class MessageDeltaContentText(MessageContentText):
    index: int = Field(ge=0)

    @classmethod
    def from_message_content(
        cls, message_content: MessageContentText, index: int
    ) -> "MessageDeltaContentText":
        return cls(
            index=index,
            text=message_content.text,
        )


class MessageContentImageUrlImageUrl(BaseModel):
    detail: Literal["auto", "low", "high"] = "auto"
    url: str


class MessageContentImageUrl(BaseModel):
    type: Literal["image_url"] = "image_url"
    image_url: MessageContentImageUrlImageUrl

    @classmethod
    def from_image_block_param(
        cls, image_block_param: ImageBlockParam
    ) -> "MessageContentImageUrl":
        match image_block_param.source.type:
            case "url":
                url = image_block_param.source.url
            case "base64":
                url = f"data:{image_block_param.source.media_type};base64,{image_block_param.source.data}"
        return cls(
            image_url=MessageContentImageUrlImageUrl(url=url),
        )


class MessageDeltaContentImageUrl(MessageContentImageUrl):
    index: int = Field(ge=0)

    @classmethod
    def from_message_content(
        cls, message_content: MessageContentImageUrl, index: int
    ) -> "MessageDeltaContentImageUrl":
        return cls(
            index=index,
            image_url=message_content.image_url,
        )


MessageContentBlock = MessageContentText | MessageContentImageUrl


MessageContent = list[MessageContentBlock]


MessageDeltaContentBlock = MessageDeltaContentText | MessageDeltaContentImageUrl

MessageDeltaContent = list[MessageDeltaContentBlock]


def map_message_content_block_to_message_delta_content_block(
    block: MessageContentBlock,
    index: int = 0,
) -> MessageDeltaContentBlock:
    match block.type:
        case "image_url":
            return MessageDeltaContentImageUrl(
                **block.model_dump(),
                index=index,
            )
        case "text":
            return MessageDeltaContentText(
                **block.model_dump(),
                index=index,
            )


def map_message_content_to_message_delta_content(
    message_content: MessageContent,
    start_index: int = 0,
) -> MessageDeltaContent:
    return [
        map_message_content_block_to_message_delta_content_block(
            block,
            index=start_index + i,
        )
        for i, block in enumerate(message_content)
    ]


class MessageDelta(BaseModel):
    content: MessageDeltaContent = Field(min_length=1)
    role: Literal["user", "assistant"]


class MessageDeltaEventData(BaseModel):
    id: MessageId
    delta: MessageDelta
    object: Literal["thread.message.delta"] = "thread.message.delta"


class MessageDeltaEvent(Event):
    data: MessageDeltaEventData
    event: Literal["thread.message.delta"] = "thread.message.delta"


class IncompleteDetails(BaseModel):
    reason: str


class MessageBase(BaseModel):
    id: MessageId
    thread_id: str
    created_at: AwareDatetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    object: Literal["thread.message"] = "thread.message"
    completed_at: AwareDatetime | None = None
    role: Literal["user", "assistant"]
    run_id: str | None = None
    incomplete_at: AwareDatetime | None = None
    incomplete_details: IncompleteDetails | None = None

    @computed_field
    @property
    def status(self) -> Literal["in_progress", "completed", "incomplete"]:
        if self.incomplete_at:
            return "incomplete"
        if self.completed_at:
            return "completed"
        return "in_progress"


class MessagePatch(BaseModel):
    completed_at: AwareDatetime | None = None


class MessagePersisted(MessageBase, MessageParam):
    pass


def map_message_param_content_to_message_content(
    content: str | list[ContentBlockParam],
) -> MessageContent:
    match content:
        case str():
            return [MessageContentText.from_str(content)]
        case list():
            result: MessageContent = []
            for block in content:
                match block.type:
                    case "image":
                        result.append(
                            MessageContentImageUrl.from_image_block_param(block)
                        )
                    case "text":
                        result.append(MessageContentText.from_str(block.text))
                    case "tool_use":
                        result.append(
                            MessageContentText.from_str(block.model_dump_json())
                        )
                    case "tool_result":
                        result.append(
                            MessageContentText.from_str(
                                f"Tool use id: {block.tool_use_id}\n"
                                f"Erroneous: {block.is_error}\n"
                                "Content:\n"
                            )
                        )
                        result.extend(
                            map_message_param_content_to_message_content(block.content)
                        )
            return result


class Message(MessageBase):
    content: MessageContent = Field(min_length=1)

    @classmethod
    def from_message_persisted(
        cls,
        message: MessagePersisted,
    ) -> "Message":
        return cls(
            **message.model_dump(exclude={"content"}),
            content=map_message_param_content_to_message_content(message.content),
        )


class MessageCreateRequestContentText(BaseModel):
    type: Literal["text"] = "text"
    text: str


MessageCreateRequestContent = (
    str | list[MessageContentImageUrl | MessageCreateRequestContentText]
)


def map_message_content_to_message_create_request_content(
    content: MessageContent,
) -> MessageCreateRequestContent:
    result: list[MessageCreateRequestContentText | MessageContentImageUrl] = []
    for block in content:
        match block.type:
            case "text":
                result.append(MessageCreateRequestContentText(text=block.text.value))
            case "image_url":
                result.append(block)
    return result


class MessageCreateRequest(BaseModel):
    content: MessageCreateRequestContent
    role: Literal["user", "assistant"]

    def to_message_persisted(self, thread_id: str) -> MessagePersisted:
        match self.content:
            case str():
                content: str | list[ContentBlockParam] = self.content
            case list():
                content = []
                for block in self.content:
                    match block.type:
                        case "text":
                            content.append(
                                TextBlockParam(
                                    text=block.text,
                                )
                            )
                        case "image_url":
                            if block.image_url.url.startswith(
                                "data:"
                            ):  # TODO Make more stable
                                image_source = ImageSource(block.image_url.url)
                            else:
                                image_content = httpx.get(block.image_url.url).content
                                image = Image.open(io.BytesIO(image_content))
                                image_source = ImageSource(image)
                            content.append(
                                ImageBlockParam(
                                    source=Base64ImageSourceParam(
                                        data=image_source.to_base64(),
                                        media_type="image/png",
                                    ),
                                )
                            )
        return MessagePersisted(  # type: ignore[call-arg]
            role=self.role,
            content=content,
            thread_id=thread_id,
        )


class MessageEvent(Event):
    data: Message
    event: Literal[
        "thread.message.created",
        "thread.message.in_progress",
        "thread.message.completed",
        "thread.message.incomplete",
    ]


class MessageListResponse(BaseModel):
    """Response model for listing messages."""

    object: str = "list"
    data: list[Message]
    first_id: str | None = None
    last_id: str | None = None
    has_more: bool = False


class MessageService:
    """Service for managing messages within threads."""

    def __init__(self, base_dir: Path) -> None:
        """Initialize message service.

        Args:
            base_dir: Base directory to store message data
        """
        self._base_dir = base_dir
        self._threads_dir = base_dir / "threads"

    def list_messages_persisted(
        self, thread_id: str, limit: int | None = None, after: str | None = None
    ) -> list[MessagePersisted]:
        thread_file = self._threads_dir / f"{thread_id}.jsonl"
        if not thread_file.exists():
            error_msg = f"Thread {thread_id} not found"
            raise FileNotFoundError(error_msg)

        messages: list[MessagePersisted] = []
        with thread_file.open("r") as f:
            for line in f:
                msg = MessagePersisted.model_validate_json(line)
                messages.append(msg)

        # Sort by creation date
        messages = sorted(messages, key=lambda m: m.created_at)
        if after:
            messages = [m for m in messages if m.id > after]

        # Apply limit if specified
        if limit is not None:
            messages = messages[:limit]

        return messages

    def list_(
        self, thread_id: str, limit: int | None = None, after: str | None = None
    ) -> MessageListResponse:
        """List all messages in a thread.

        Args:
            thread_id: ID of thread to list messages from
            limit: Optional maximum number of messages to return
            after: Optional message ID after which messages are returned

        Returns:
            MessageListResponse containing messages sorted by creation date

        Raises:
            FileNotFoundError: If thread doesn't exist
        """
        messages = self.list_messages_persisted(
            thread_id=thread_id,
            limit=limit,
            after=after,
        )
        return MessageListResponse(
            data=[Message.from_message_persisted(m) for m in messages],
            first_id=messages[0].id if messages else None,
            last_id=messages[-1].id if messages else None,
            has_more=len(messages) > (limit or len(messages)),
        )

    def create(
        self,
        thread_id: str,
        request: MessageCreateRequest,
    ) -> Message:
        """Create a new message in a thread.

        Args:
            thread_id: ID of thread to create message in
            request: Message create request

        Returns:
            Created message object

        Raises:
            FileNotFoundError: If thread doesn't exist
        """
        message = request.to_message_persisted(thread_id=thread_id)
        self._save(thread_id=thread_id, messages=[message])
        return Message.from_message_persisted(message)

    def retrieve(self, thread_id: str, message_id: str) -> Message:
        """Retrieve a specific message from a thread.

        Args:
            thread_id: ID of thread containing message
            message_id: ID of message to retrieve

        Returns:
            Message object

        Raises:
            FileNotFoundError: If thread or message doesn't exist
        """
        messages = self.list_messages_persisted(thread_id=thread_id, limit=1)
        for msg in messages:
            if msg.id == message_id:
                return Message.from_message_persisted(msg)
        error_msg = f"Message {message_id} not found in thread {thread_id}"
        raise FileNotFoundError(error_msg)

    def delete(self, thread_id: str, message_id: str) -> None:
        """Delete a message from a thread.

        Args:
            thread_id: ID of thread containing message
            message_id: ID of message to delete

        Raises:
            FileNotFoundError: If thread or message doesn't exist
        """
        messages = self.list_messages_persisted(thread_id=thread_id)
        filtered_messages = [m for m in messages if m.id != message_id]
        if len(filtered_messages) == len(messages):
            error_msg = f"Message {message_id} not found in thread {thread_id}"
            raise FileNotFoundError(error_msg)
        self._save(thread_id=thread_id, messages=filtered_messages)

    def _save(self, thread_id: str, messages: list[MessagePersisted]) -> None:
        thread_file = self._threads_dir / f"{thread_id}.jsonl"
        if not thread_file.exists():
            error_msg = f"Thread {thread_id} not found"
            raise FileNotFoundError(error_msg)
        with thread_file.open("w") as f:
            for msg in messages:
                f.write(msg.model_dump_json())
                f.write("\n")

    def patch(self, thread_id: str, message_id: str, patch: MessagePatch) -> Message:
        """Complete a message in a thread.

        Args:
            thread_id: ID of thread containing message
            message_id: ID of message to complete
            patch: Patch to apply to message
        """
        messages = self.list_messages_persisted(thread_id=thread_id)
        patched_message: MessagePersisted | None = None
        for msg in messages:
            if msg.id == message_id:
                if patch.completed_at is not None:
                    msg.completed_at = patch.completed_at
                patched_message = msg
                break
        if patched_message is None:
            error_msg = f"Message {message_id} not found in thread {thread_id}"
            raise FileNotFoundError(error_msg)
        self._save(thread_id=thread_id, messages=messages)
        return Message.from_message_persisted(patched_message)
