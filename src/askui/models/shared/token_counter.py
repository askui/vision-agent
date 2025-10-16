import base64
import json
from abc import ABC, abstractmethod

import httpx
from anthropic.types.beta import BetaTextBlockParam, BetaToolUnionParam
from typing_extensions import override

from askui.models.shared.agent_message_param import (
    Base64ImageSourceParam,
    ContentBlockParam,
    ImageBlockParam,
    MessageParam,
    ToolResultBlockParam,
)
from askui.utils.image_utils import base64_to_image


class TokenCounts:
    """Token counts for a message."""

    def __init__(
        self,
        system: int,
        tools: int,
        messages: list[int],
    ) -> None:
        self._system = system
        self._tools = tools
        self._messages = messages
        self._static = system + tools
        self._total = self._static + sum(messages)

    def append_message_tokens(self, tokens: int) -> None:
        self._messages.append(tokens)
        self._total += tokens

    def retrieve_message_tokens(self, index: int) -> int:
        return self._messages[index]

    def reset_message_tokens(self, tokens: list[int]) -> None:
        self._messages = tokens
        self._total = self._static + sum(tokens)

    @property
    def total(self) -> int:
        return self._total

    @property
    def static(self) -> int:
        return self._static


class TokenCounter(ABC):
    @abstractmethod
    def count_tokens(
        self,
        tools: list[BetaToolUnionParam] | None = None,
        system: str | list[BetaTextBlockParam] | None = None,
        messages: list[MessageParam] | None = None,
    ) -> TokenCounts:
        """Count total tokens (estimated) using simple string length estimation.

        Args:
            tools (list[BetaToolUnionParam] | None, optional): The tools to count
                tokens for. Defaults to `None`.
            system (str | list[BetaTextBlockParam] | None, optional): The system
                prompt or system blocks to count tokens for. Defaults to `None`.
            messages (list[MessageParam] | None, optional):
                The messages to count tokens for. Defaults to `None`.
            model (str | None, optional): The model to count tokens for.
                Defaults to `None`.

        Returns:
            int: The total estimated number of tokens across all components.
        """
        raise NotImplementedError


class SimpleTokenCounter(TokenCounter):
    """Simple token counter implementation that estimates tokens by dividing string
    length by 3.

    This is a basic approximation that assumes roughly 3 characters per token
    on average.For more accurate token counting, consider using model-specific
    tokenizers.
    """

    def __init__(self, chars_per_token: float = 3.0) -> None:
        """Initialize the simple token counter.

        Args:
            chars_per_token (float, optional): The estimated characters per token.
                Defaults to `3.0`.
        """
        self._chars_per_token = chars_per_token
        self._url_cache: dict[str, tuple[int, int] | None] = {}

    def _get_image_dimensions_from_url(self, url: str) -> tuple[int, int] | None:
        """Fetch image dimensions from a URL with caching.

        Args:
            url (str): The URL of the image to fetch.

        Returns:
            tuple[int, int] | None: The (width, height) of the image, or None if
                fetching fails.
        """
        # Check cache first
        if url in self._url_cache:
            return self._url_cache[url]

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url)
                response.raise_for_status()

                # Check if the response is actually an image
                content_type = response.headers.get("content-type", "").lower()
                if not content_type.startswith("image/"):
                    self._url_cache[url] = None
                    return None

                # Convert response content to PIL Image to get dimensions
                image_data_base64 = base64.b64encode(response.content).decode("utf-8")
                image = base64_to_image(image_data_base64)
                dimensions = image.size
                self._url_cache[url] = dimensions
                return dimensions
        except (httpx.HTTPError, httpx.TimeoutException, ValueError, TypeError):
            # If fetching fails, cache None and return None to fall back to estimation
            self._url_cache[url] = None
            return None

    @override
    def count_tokens(
        self,
        tools: list[BetaToolUnionParam] | None = None,
        system: str | list[BetaTextBlockParam] | None = None,
        messages: list[MessageParam] | None = None,
        model: str | None = None,  # noqa: ARG002
    ) -> TokenCounts:
        system_tokens = 0
        tools_tokens = 0
        message_tokens = []
        if tools:
            tools_str = self._stringify_object(tools)
            tools_tokens = int(len(tools_str) / self._chars_per_token)
        if system:
            system_str = self._stringify_object(system)
            system_tokens = int(len(system_str) / self._chars_per_token)
        if messages:
            message_tokens = [
                self._count_tokens_for_message(message) for message in messages
            ]
        return TokenCounts(
            system=system_tokens,
            tools=tools_tokens,
            messages=message_tokens,
        )

    def _count_tokens_for_message(self, message: MessageParam) -> int:
        """Count tokens for a message by processing content blocks individually.

        For image blocks, uses the formula: tokens = (width * height) / 750 (see https://docs.anthropic.com/en/docs/build-with-claude/vision)
        For other content types, uses the standard character-based estimation.

        Args:
            message (MessageParam): The message to count tokens for.

        Returns:
            int: The estimated number of tokens for the message.
        """
        if isinstance(message.content, str):
            # Simple string content - use standard estimation
            return int(len(message.content) / self._chars_per_token)

        # base tokens for rest of message
        total_tokens = 10
        # Content is a list of blocks - process each individually
        for block in message.content:
            total_tokens += self._count_tokens_for_content_block(block)

        return total_tokens

    def _count_tokens_for_content_block(self, block: ContentBlockParam) -> int:
        """Count tokens for a single content block.

        Args:
            block (ContentBlockParam): The content block to count tokens for.

        Returns:
            int: The estimated number of tokens for the block.
        """
        if isinstance(block, ImageBlockParam):
            return self._count_tokens_for_image_block(block)

        if isinstance(block, ToolResultBlockParam):
            # Tool result blocks can contain text or nested content blocks
            if isinstance(block.content, str):
                return int(len(block.content) / self._chars_per_token)

            # base tokens for tool result block
            total_tokens = 20
            # Recursively count nested content blocks
            for nested_block in block.content:
                total_tokens += self._count_tokens_for_content_block(nested_block)
            return total_tokens

        # For other block types, use string representation
        return int(len(self._stringify_object(block)) / self._chars_per_token)

    def _count_tokens_for_image_block(self, block: ImageBlockParam) -> int:
        """Count tokens for an image block using Anthropic's formula.

        Uses the formula: tokens = (width * height) / 750

        Args:
            block (ImageBlockParam): The image block to count tokens for.

        Returns:
            int: The estimated number of tokens for the image.
        """
        # If fetching fails, fall back to estimation
        # Assume average image size of ~4 megapixel (2000x2000) for URL images
        estimated_tokens = int((2000 * 2000) / 750)
        try:
            if isinstance(block.source, Base64ImageSourceParam):
                # Decode base64 image to get dimensions
                image = base64_to_image(block.source.data)
                width, height = image.size
                return int((width * height) / 750)

            # For URL-based images, try to fetch the image to get actual dimensions
            dimensions = self._get_image_dimensions_from_url(block.source.url)
            if dimensions is not None:
                width, height = dimensions
                return int((width * height) / 750)

        except (ValueError, TypeError, AttributeError):
            # If image processing fails, fall back to string-based estimation
            return int(len(self._stringify_object(block)) / self._chars_per_token)
        return estimated_tokens

    def _stringify_object(self, obj: object) -> str:
        """Convert any object to a string representation for token counting.

        Not whitespace in dumped jsons between object keys and values and among array
        elements.

        Args:
            obj (object): The object to stringify.

        Returns:
            str: String representation of the object.
        """
        if isinstance(obj, str):
            return obj
        try:
            return json.dumps(obj, separators=(",", ":"))
        except (TypeError, ValueError):
            return str(obj)
