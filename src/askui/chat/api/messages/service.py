import io
from datetime import datetime, timezone
from typing import Literal

import httpx
from PIL import Image
from pydantic import BaseModel, Field

from askui.chat.api.messages.message_persisted_service import (
    MessagePersisted,
    MessagePersistedService,
    Metadata,
)
from askui.chat.api.messages.models import (
    Message,
    MessageContentImageFile,
    MessageContentImageUrl,
)
from askui.chat.api.models import (
    ListQuery,
    ListResponse,
    MessageId,
    ThreadId,
    UnixDatetime,
)
from askui.models.shared.computer_agent_message_param import (
    Base64ImageSourceParam,
    ContentBlockParam,
    ImageBlockParam,
    TextBlockParam,
    UrlImageSourceParam,
)
from askui.utils.image_utils import ImageSource


class DoNotPatch(BaseModel):
    pass


DO_NOT_PATCH = DoNotPatch()


class MessagePatch(BaseModel):
    completed_at: UnixDatetime | None | DoNotPatch = Field(default=DO_NOT_PATCH)
    metadata: Metadata | None | DoNotPatch = Field(default=DO_NOT_PATCH)


class MessageCreateRequestContentText(BaseModel):
    type: Literal["text"] = "text"
    text: str


MessageCreateRequestContent = (
    str
    | list[
        MessageContentImageFile
        | MessageContentImageUrl
        | MessageCreateRequestContentText
    ]
)


class MessageCreateRequest(BaseModel):
    content: MessageCreateRequestContent
    role: Literal["user", "assistant"]

    def to_message_persisted(self, thread_id: ThreadId) -> MessagePersisted:
        match self.content:
            case str():
                content: str | list[ContentBlockParam] = self.content
            case list():
                content = []
                for block in self.content:
                    match block.type:
                        case "image_file":
                            # TODO
                            content.append(
                                ImageBlockParam(
                                    source=UrlImageSourceParam(
                                        # TODO
                                        url="https://test.com",
                                    ),
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
                        case "text":
                            content.append(
                                TextBlockParam(
                                    text=block.text,
                                )
                            )
        return MessagePersisted(  # type: ignore[call-arg]
            role=self.role,
            content=content,
            completed_at=datetime.now(tz=timezone.utc),
            thread_id=thread_id,
        )


class MessageService:
    def __init__(self, service: MessagePersistedService) -> None:
        self._service = service

    def list_(self, thread_id: ThreadId, query: ListQuery) -> ListResponse[Message]:
        """List all messages in a thread.

        Args:
            thread_id (str): ID of thread to list messages from
            query (ListQuery): Query parameters for listing messages

        Returns:
            ListResponse[Message]: ListResponse containing messages sorted by creation date

        Raises:
            FileNotFoundError: If thread doesn't exist
        """
        messages = self._service.list_(
            thread_id=thread_id,
            query=query,
        )
        return ListResponse(
            data=[Message.from_message_persisted(m) for m in messages],
            first_id=messages[0].id if messages else None,
            last_id=messages[-1].id if messages else None,
            has_more=len(messages) > query.limit,
        )

    def create(
        self,
        thread_id: ThreadId,
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
        self._service.create(thread_id=thread_id, message=message)
        return Message.from_message_persisted(message)

    def retrieve(self, thread_id: ThreadId, message_id: MessageId) -> Message:
        """Retrieve a specific message from a thread.

        Args:
            thread_id: ID of thread containing message
            message_id: ID of message to retrieve

        Returns:
            Message object

        Raises:
            FileNotFoundError: If thread or message doesn't exist
        """
        messages = self._service.list_(thread_id=thread_id, query=ListQuery(limit=1))
        for msg in messages:
            if msg.id == message_id:
                return Message.from_message_persisted(msg)
        error_msg = f"Message {message_id} not found in thread {thread_id}"
        raise FileNotFoundError(error_msg)

    def delete(self, thread_id: ThreadId, message_id: MessageId) -> None:
        """Delete a message from a thread.

        Args:
            thread_id (ThreadId): ID of thread containing message
            message_id (MessageId): ID of message to delete

        Raises:
            FileNotFoundError: If thread or message doesn't exist
        """
        self._service.delete(thread_id=thread_id, message_id=message_id)

    def patch(  # TODO move to service underneath
        self, thread_id: ThreadId, message_id: MessageId, patch: MessagePatch
    ) -> Message:
        """Complete a message in a thread.

        Args:
            thread_id (ThreadId): ID of thread containing message
            message_id (MessageId): ID of message to complete
            patch (MessagePatch): Patch to apply to message
        """
        messages = self._service.list_(thread_id=thread_id, query=ListQuery(limit=100))
        patched_message: MessagePersisted | None = None
        for msg in messages:
            if msg.id == message_id:
                if not isinstance(patch.completed_at, DoNotPatch):
                    msg.completed_at = patch.completed_at
                if not isinstance(patch.metadata, DoNotPatch):
                    msg.metadata = patch.metadata
                patched_message = msg
                break
        if patched_message is None:
            error_msg = f"Message {message_id} not found in thread {thread_id}"
            raise FileNotFoundError(error_msg)
        self._service.save(thread_id=thread_id, messages=messages)
        return Message.from_message_persisted(patched_message)
