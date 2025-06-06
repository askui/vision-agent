from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from anthropic import Anthropic
from pydantic import AwareDatetime, BaseModel, Field

from askui.chat.api.messages.service import MessageService
from askui.chat.api.utils import generate_time_ordered_id


class ChatCompletionRequest(BaseModel):
    """Request model for creating a chat completion."""

    model: str
    messages: list[dict[str, Any]]
    temperature: float | None = 1.0
    top_p: float | None = 1.0
    max_tokens: int | None = None
    stream: bool = False
    thread_id: str | None = None
    assistant_id: str | None = None


class ChatCompletionChoice(BaseModel):
    """A choice in a chat completion response."""

    index: int
    message: dict[str, str]
    finish_reason: str | None = None


class ChatCompletionUsage(BaseModel):
    """Usage statistics for a chat completion."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletion(BaseModel):
    """A chat completion response."""

    id: str = Field(default_factory=lambda: generate_time_ordered_id("chatcmpl"))
    object: Literal["chat.completion"] = "chat.completion"
    created: AwareDatetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    model: str
    choices: list[ChatCompletionChoice]
    usage: ChatCompletionUsage


class ChatCompletionService:
    """Service for managing chat completions."""

    def __init__(
        self,
        base_dir: Path,
        anthropic_api_key: str,
        message_service: MessageService,
    ) -> None:
        """Initialize chat completion service.

        Args:
            base_dir: Base directory to store chat completion data
            anthropic_api_key: API key for Anthropic
            message_service: Service for managing messages
        """
        self._base_dir = base_dir
        self._completions_dir = base_dir / "completions"
        self._anthropic = Anthropic(api_key=anthropic_api_key)
        self._message_service = message_service

    async def create(
        self,
        request: ChatCompletionRequest,
    ) -> ChatCompletion:
        """Create a new chat completion.

        Args:
            request: Chat completion request

        Returns:
            ChatCompletion object

        Raises:
            FileNotFoundError: If thread or assistant doesn't exist
        """
        # Convert messages to Anthropic format
        anthropic_messages = [
            {"role": msg["role"], "content": msg["content"]} for msg in request.messages
        ]

        # Call Anthropic API
        response = await self._anthropic.messages.create(
            model=request.model,
            messages=anthropic_messages,
            temperature=request.temperature,
            top_p=request.top_p,
            max_tokens=request.max_tokens,
            stream=request.stream,
        )

        # Create completion object
        completion = ChatCompletion(
            model=request.model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message={"role": "assistant", "content": response.content[0].text},
                    finish_reason=response.stop_reason,
                )
            ],
            usage=ChatCompletionUsage(
                prompt_tokens=response.usage.input_tokens,
                completion_tokens=response.usage.output_tokens,
                total_tokens=response.usage.input_tokens + response.usage.output_tokens,
            ),
        )

        # Store completion if thread_id is provided
        if request.thread_id:
            self._completions_dir.mkdir(parents=True, exist_ok=True)
            completion_file = self._completions_dir / f"{completion.id}.json"
            with completion_file.open("w") as f:
                f.write(completion.model_dump_json())

            # Store assistant's response as a message in the thread
            if not request.stream:
                await self._message_service.create(
                    thread_id=request.thread_id,
                    request={
                        "role": "assistant",
                        "content": [{"type": "text", "text": response.content[0].text}],
                    },
                )

        return completion
