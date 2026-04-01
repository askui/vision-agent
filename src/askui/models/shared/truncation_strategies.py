"""Truncation strategies for managing conversation message history."""

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path

from typing_extensions import override

from askui.model_providers.vlm_provider import VlmProvider
from askui.models.shared.agent_message_param import (
    Base64ImageSourceParam,
    CacheControlEphemeralParam,
    ContentBlockParam,
    ImageBlockParam,
    MessageParam,
    TextBlockParam,
    ToolResultBlockParam,
    ToolUseBlockParam,
)
from askui.models.shared.token_counter import SimpleTokenCounter

logger = logging.getLogger(__name__)

# needs to be below limits imposed by endpoint
MAX_INPUT_TOKENS = 100_000

# we will truncate as soon as we reach this threshold
TRUNCATION_THRESHOLD = 0.7

# see https://docs.anthropic.com/en/api/messages#body-messages
MAX_MESSAGES = 100_000

IMAGE_REMOVED_PLACEHOLDER = "[Screenshot removed to reduce message history length]"
"""Text used to replace stripped base64 images."""


def _has_orphaned_tool_results(msg: MessageParam) -> bool:
    """Check if a message contains tool_result blocks.

    Such a message cannot be the first in ``recent``
    because the preceding assistant message with the
    matching tool_use would be lost.
    """
    if msg.role != "user" or isinstance(msg.content, str):
        return False
    return any(isinstance(b, ToolResultBlockParam) for b in msg.content)


def _summarize_message_history(
    vlm_provider: VlmProvider,
    messages: list[MessageParam],
) -> str:
    """Ask the VLM to summarize the conversation history.

    Args:
        vlm_provider: VLM provider to use for summarization.
        messages: Messages to summarize.

    Returns:
        A summary string of the conversation so far.
    """
    messages_to_summarize = list(messages)

    # Ensure valid role alternation
    if messages_to_summarize and messages_to_summarize[-1].role == "user":
        messages_to_summarize.append(
            MessageParam(
                role="assistant",
                content="I understand. Please go ahead.",
            )
        )

    messages_to_summarize.append(
        MessageParam(
            role="user",
            content=(
                "Please provide a concise summary of the "
                "conversation history above. Focus on: key "
                "actions taken, results observed, current "
                "state, and any pending tasks or errors. "
                "This summary will replace the earlier "
                "conversation history to save context space."
            ),
        )
    )

    response = vlm_provider.create_message(
        messages=messages_to_summarize,
        max_tokens=2048,
    )

    if isinstance(response.content, str):
        return response.content

    texts = [
        block.text for block in response.content if isinstance(block, TextBlockParam)
    ]
    return "\n".join(texts)


def _clear_cache_control(msg: MessageParam) -> None:
    """Clear ``cache_control`` on all blocks of a message."""
    if isinstance(msg.content, str):
        return
    cacheable = (
        ImageBlockParam,
        TextBlockParam,
        ToolResultBlockParam,
        ToolUseBlockParam,
    )
    for block in msg.content:
        if isinstance(block, cacheable):
            block.cache_control = None
        if isinstance(block, ToolResultBlockParam) and isinstance(block.content, list):
            for nested in block.content:
                nested.cache_control = None


def _set_cache_breakpoint(msg: MessageParam) -> None:
    """Set cache breakpoint on last block of a message."""
    if isinstance(msg.content, str) or not msg.content:
        return
    last_block = msg.content[-1]
    cacheable = (
        ImageBlockParam,
        TextBlockParam,
        ToolResultBlockParam,
        ToolUseBlockParam,
    )
    if isinstance(last_block, cacheable):
        last_block.cache_control = CacheControlEphemeralParam()


class TruncationStrategy(ABC):
    """Abstract base class for truncation strategies.

    Manages two separate message histories:

    - ``full_messages``: append-only, preserves all original
      messages for cache recording
    - ``truncated_messages``: may have images stripped and
      history summarized for LLM calls

    Args:
        max_messages: Maximum number of messages before
            forcing truncation.
        max_input_tokens: Maximum input tokens for the endpoint.
        truncation_threshold: Fraction of `max_input_tokens`
            at which to truncate.
    """

    def __init__(
        self,
        max_messages: int = MAX_MESSAGES,
        max_input_tokens: int = MAX_INPUT_TOKENS,
        truncation_threshold: float = TRUNCATION_THRESHOLD,
    ) -> None:
        self._full_message_history: list[MessageParam] = []
        self._truncated_message_history: list[MessageParam] = []
        self._max_messages = max_messages
        self._absolute_truncation_threshold = int(
            max_input_tokens * truncation_threshold
        )

    @abstractmethod
    def append_message(self, message: MessageParam) -> None:
        """Append a message and apply any truncation logic."""
        ...

    @abstractmethod
    def truncate(self) -> None:
        """Force-truncate the message history."""
        ...

    def reset(self, messages: list[MessageParam] | None = None) -> None:
        """Reset message histories with optional initial messages.

        Creates independent copies so modifications to truncated
        history do not affect full history.

        Args:
            messages: Initial messages to populate both histories.
                If ``None``, both histories are cleared.
        """
        if messages is not None:
            self._full_message_history = list(messages)
            self._truncated_message_history = list(messages)
        else:
            self._full_message_history = []
            self._truncated_message_history = []

    @property
    def truncated_messages(self) -> list[MessageParam]:
        """Get the truncated messages sent to the LLM."""
        return self._truncated_message_history

    @property
    def full_messages(self) -> list[MessageParam]:
        """Get the full, untruncated messages for cache recording."""
        return self._full_message_history


class SlidingImageWindowSummarizingTruncationStrategy(TruncationStrategy):
    """Truncation strategy that strips old images, manages
    cache breakpoints, and summarizes.

    On each appended message:

    1. Strips base64 images beyond `n_images_to_keep`
       (oldest first)
    2. Places dual cache breakpoints (at image-removal
       boundary + last user message)
    3. If token count exceeds threshold, summarizes
       the history via the VLM

    Args:
        vlm_provider: VLM provider used for summarization.
        n_images_to_keep: Number of most-recent base64 images
            to retain.
        n_messages_to_keep: Number of most-recent messages to
            preserve during summarization.
        max_messages: Maximum number of messages before
            forcing truncation.
        max_input_tokens: Maximum input tokens for the
            endpoint.
        truncation_threshold: Fraction of `max_input_tokens`
            at which to truncate.
        debug_dir: When set, write diagnostic snapshots to
            this directory after each append/truncate.
    """

    def __init__(
        self,
        vlm_provider: VlmProvider,
        n_images_to_keep: int = 3,
        n_messages_to_keep: int = 10,
        max_messages: int = MAX_MESSAGES,
        max_input_tokens: int = MAX_INPUT_TOKENS,
        truncation_threshold: float = TRUNCATION_THRESHOLD,
        debug_dir: Path | None = None,
    ) -> None:
        super().__init__(max_messages, max_input_tokens, truncation_threshold)
        self._vlm_provider = vlm_provider
        self._n_images_to_keep = n_images_to_keep
        self._n_messages_to_keep = n_messages_to_keep
        self._token_counter = SimpleTokenCounter()
        self._image_removal_boundary_index: int | None = None
        self._debug_dir = debug_dir
        self._debug_step = 0

        msg = """CAUTION: The Truncation Strategy you are using is experimental!
        While it will lead to faster executions in longer runs it might crash or
        lead to overall unexpected behavior! If in doubt, we recommend using the
        default truncation strategy instead."""
        logger.warning(msg)

        if self._debug_dir is not None:
            self._debug_dir.mkdir(parents=True, exist_ok=True)
            # Write config
            config = {
                "n_images_to_keep": n_images_to_keep,
                "n_messages_to_keep": n_messages_to_keep,
                "max_messages": max_messages,
                "max_input_tokens": max_input_tokens,
                "truncation_threshold": truncation_threshold,
                "absolute_threshold": self._absolute_truncation_threshold,
            }
            (self._debug_dir / "config.json").write_text(
                json.dumps(config, indent=2), encoding="utf-8"
            )

    @override
    def append_message(self, message: MessageParam) -> None:
        """Append a message and apply image stripping,
        cache breakpoints, and truncation.

        Args:
            message: The message to append.
        """
        self._full_message_history.append(message)
        self._truncated_message_history.append(message)

        # Strip old base64 images (sets _image_removal_boundary_index)
        self._remove_images()

        # Place cache breakpoints using the boundary index
        self._move_cache_breakpoints()

        # Check if truncation is needed
        token_counts = self._token_counter.count_tokens(
            messages=self._truncated_message_history,
        )
        truncated = False
        if (
            len(self._truncated_message_history) > self._max_messages
            or token_counts.total > self._absolute_truncation_threshold
        ):
            self.truncate()
            truncated = True

        self._write_debug_snapshot(
            event="truncate" if truncated else "append",
            token_total=token_counts.total,
        )

    @override
    def truncate(self) -> None:
        """Summarize old messages and keep only recent ones."""
        if len(self._truncated_message_history) <= self._n_messages_to_keep:
            msg = "Cannot truncate: too few messages in history"
            logger.warning(msg)
            return

        logger.info("Summarizing message history")
        summary = _summarize_message_history(
            self._vlm_provider, self._truncated_message_history
        )

        # Find a safe cut point that doesn't orphan tool_results.
        # A user message with tool_result blocks requires the
        # preceding assistant message to contain the matching
        # tool_use blocks, so we must not start `recent` on one.
        cut = len(self._truncated_message_history) - self._n_messages_to_keep
        while cut > 0 and _has_orphaned_tool_results(
            self._truncated_message_history[cut]
        ):
            cut -= 1

        if cut <= 0:
            msg = "Cannot truncate: no safe cut point found"
            logger.warning(msg)
            return

        recent = self._truncated_message_history[cut:]

        # Build new history with the summary as a user message
        new_messages: list[MessageParam] = [
            MessageParam(role="user", content=summary),
        ]

        # Ensure valid role alternation: if first recent message
        # is also "user", insert a synthetic assistant ack.
        if recent and recent[0].role == "user":
            new_messages.append(
                MessageParam(
                    role="assistant",
                    content=(
                        "Understood. I'll continue based on "
                        "the conversation summary above."
                    ),
                )
            )

        new_messages.extend(recent)
        self._truncated_message_history = new_messages
        self._image_removal_boundary_index = None

    # ------------------------------------------------------------------
    # Image removal
    # ------------------------------------------------------------------

    def _remove_images(self) -> None:
        """Strip old base64 images from truncated history.

        Walks from the beginning and replaces excess base64
        `ImageBlockParam` blocks with text placeholders.  Also
        recurses into `ToolResultBlockParam.content` lists.
        URL-based images are never stripped.
        """
        total = self._count_base64_images(self._truncated_message_history)
        to_remove = total - self._n_images_to_keep
        if to_remove <= 0:
            return

        removed = 0
        for i, msg in enumerate(self._truncated_message_history):
            if removed >= to_remove:
                break
            if isinstance(msg.content, str):
                continue

            new_content, removed_in_msg = self._strip_base64_images(
                msg.content, to_remove - removed
            )
            if removed_in_msg > 0:
                self._truncated_message_history[i] = MessageParam(
                    role=msg.role,
                    content=new_content,
                    stop_reason=msg.stop_reason,
                    usage=msg.usage,
                )
                self._image_removal_boundary_index = i
                removed += removed_in_msg

    @staticmethod
    def _count_base64_images(
        messages: list[MessageParam],
    ) -> int:
        """Count total base64 image blocks across messages."""
        count = 0
        for msg in messages:
            if isinstance(msg.content, str):
                continue
            for block in msg.content:
                if isinstance(block, ImageBlockParam) and isinstance(
                    block.source, Base64ImageSourceParam
                ):
                    count += 1
                elif isinstance(block, ToolResultBlockParam) and isinstance(
                    block.content, list
                ):
                    for nested in block.content:
                        if isinstance(nested, ImageBlockParam) and isinstance(
                            nested.source,
                            Base64ImageSourceParam,
                        ):
                            count += 1
        return count

    @staticmethod
    def _strip_base64_images(
        content: list[ContentBlockParam],
        max_to_strip: int,
    ) -> tuple[list[ContentBlockParam], int]:
        """Strip up to `max_to_strip` base64 images.

        Args:
            content: The content blocks to process.
            max_to_strip: Maximum number of images to strip.

        Returns:
            Tuple of (new content list, count stripped).
        """
        stripped = 0
        new_content: list[ContentBlockParam] = []

        for block in content:
            if stripped >= max_to_strip:
                new_content.append(block)
                continue

            if isinstance(block, ImageBlockParam) and isinstance(
                block.source, Base64ImageSourceParam
            ):
                new_content.append(TextBlockParam(text=IMAGE_REMOVED_PLACEHOLDER))
                stripped += 1
            elif isinstance(block, ToolResultBlockParam) and isinstance(
                block.content, list
            ):
                new_nested: list[TextBlockParam | ImageBlockParam] = []
                for nested in block.content:
                    if (
                        stripped < max_to_strip
                        and isinstance(nested, ImageBlockParam)
                        and isinstance(
                            nested.source,
                            Base64ImageSourceParam,
                        )
                    ):
                        new_nested.append(
                            TextBlockParam(text=IMAGE_REMOVED_PLACEHOLDER)
                        )
                        stripped += 1
                    else:
                        new_nested.append(nested)
                new_content.append(
                    ToolResultBlockParam(
                        tool_use_id=block.tool_use_id,
                        content=new_nested,
                        is_error=block.is_error,
                        cache_control=block.cache_control,
                    )
                )
            else:
                new_content.append(block)

        return new_content, stripped

    # ------------------------------------------------------------------
    # Cache breakpoints
    # ------------------------------------------------------------------

    def _move_cache_breakpoints(self) -> None:
        """Place dual cache breakpoints on truncated history.

        - **Breakpoint 1** – image-removal boundary.
        - **Breakpoint 2** – last user message.
        """
        # Clear all existing cache_control
        for msg in self._truncated_message_history:
            self._clear_cache_control(msg)

        # Breakpoint 1: at image removal boundary
        if (
            self._image_removal_boundary_index is not None
            and self._image_removal_boundary_index
            < len(self._truncated_message_history)
        ):
            self._set_cache_breakpoint(
                self._truncated_message_history[self._image_removal_boundary_index]
            )

        # Breakpoint 2: last user message
        for msg in reversed(self._truncated_message_history):
            if msg.role == "user":
                self._set_cache_breakpoint(msg)
                break

    @staticmethod
    def _clear_cache_control(msg: MessageParam) -> None:
        """Clear ``cache_control`` on all blocks."""
        _clear_cache_control(msg)

    @staticmethod
    def _set_cache_breakpoint(msg: MessageParam) -> None:
        """Set cache breakpoint on last block of a message."""
        _set_cache_breakpoint(msg)

    # ------------------------------------------------------------------
    # Debug diagnostics
    # ------------------------------------------------------------------

    def _write_debug_snapshot(
        self,
        event: str,
        token_total: int = 0,
    ) -> None:
        """Write a diagnostic snapshot to the debug dir.

        Each snapshot summarises both message histories
        compactly (no base64 data) so you can verify at a
        glance that image stripping, cache breakpoints, and
        truncation work correctly.

        Args:
            event: ``"append"`` or ``"truncate"``.
            token_total: Estimated token count for the
                truncated history.
        """
        if self._debug_dir is None:
            return

        self._debug_step += 1

        full_imgs = self._count_base64_images(self._full_message_history)
        trunc_imgs = self._count_base64_images(self._truncated_message_history)

        snapshot: dict[str, object] = {
            "step": self._debug_step,
            "event": event,
            "full_msg_count": len(self._full_message_history),
            "full_base64_images": full_imgs,
            "truncated_msg_count": len(self._truncated_message_history),
            "truncated_base64_images": trunc_imgs,
            "images_stripped": full_imgs - trunc_imgs,
            "image_boundary_idx": (self._image_removal_boundary_index),
            "token_estimate": token_total,
            "threshold": self._absolute_truncation_threshold,
            "truncated_messages": [
                self._summarise_message(i, m)
                for i, m in enumerate(self._truncated_message_history)
            ],
        }

        filename = f"step_{self._debug_step:03d}_{event}.json"
        (self._debug_dir / filename).write_text(
            json.dumps(snapshot, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _summarise_message(self, index: int, msg: MessageParam) -> dict[str, object]:
        """Build a compact summary of a message for debug.

        Returns a dict with role, block descriptions, and
        cache breakpoint info — no base64 data.
        """
        result: dict[str, object] = {
            "index": index,
            "role": msg.role,
        }

        if isinstance(msg.content, str):
            preview = msg.content
            if len(preview) > 120:
                preview = preview[:120] + "..."
            result["content"] = preview
            return result

        blocks: list[str] = []
        has_cache_bp = False

        for block in msg.content:
            desc = self._describe_block(block)
            blocks.append(desc)
            cc = getattr(block, "cache_control", None)
            if cc is not None:
                has_cache_bp = True

        result["blocks"] = blocks
        result["has_cache_breakpoint"] = has_cache_bp
        return result

    @staticmethod
    def _describe_block(
        block: ContentBlockParam,
    ) -> str:
        """One-line description of a content block."""
        if isinstance(block, TextBlockParam):
            preview = block.text[:60]
            if len(block.text) > 60:
                preview += "..."
            return f"text({preview})"

        if isinstance(block, ImageBlockParam):
            kind = (
                "base64" if isinstance(block.source, Base64ImageSourceParam) else "url"
            )
            return f"image:{kind}"

        if isinstance(block, ToolUseBlockParam):
            return f"tool_use({block.name})"

        if isinstance(block, ToolResultBlockParam):
            return _describe_tool_result(block)

        return block.type


class SummarizingTruncationStrategy(TruncationStrategy):
    """Truncation strategy that summarizes when limits are hit.

    Unlike `SlidingImageWindowSummarizingTruncationStrategy`,
    this strategy does **not** strip images. It places a
    single cache breakpoint on the last user message (moving
    it forward on each append) and summarizes the conversation
    history via the VLM when the token or message count
    exceeds the configured threshold.

    Args:
        vlm_provider: VLM provider used for summarization.
        n_messages_to_keep: Number of most-recent messages to
            preserve during summarization.
        max_messages: Maximum number of messages before
            forcing truncation.
        max_input_tokens: Maximum input tokens for the
            endpoint.
        truncation_threshold: Fraction of `max_input_tokens`
            at which to truncate.
    """

    def __init__(
        self,
        vlm_provider: VlmProvider,
        n_messages_to_keep: int = 10,
        max_messages: int = MAX_MESSAGES,
        max_input_tokens: int = MAX_INPUT_TOKENS,
        truncation_threshold: float = TRUNCATION_THRESHOLD,
    ) -> None:
        super().__init__(max_messages, max_input_tokens, truncation_threshold)
        self._vlm_provider = vlm_provider
        self._n_messages_to_keep = n_messages_to_keep
        self._token_counter = SimpleTokenCounter()

    @override
    def append_message(self, message: MessageParam) -> None:
        """Append a message, move cache breakpoint, summarize
        if limits are hit.

        Places a cache breakpoint on the last user message
        and clears it from any previous position so the LLM
        caches the full prefix optimally.

        Args:
            message: The message to append.
        """
        self._full_message_history.append(message)
        self._truncated_message_history.append(message)

        # Move cache breakpoint to last user message
        self._move_cache_breakpoint()

        token_counts = self._token_counter.count_tokens(
            messages=self._truncated_message_history,
        )
        if (
            len(self._truncated_message_history) > self._max_messages
            or token_counts.total > self._absolute_truncation_threshold
        ):
            self.truncate()

    def _move_cache_breakpoint(self) -> None:
        """Place a cache breakpoint on the last user message.

        Clears ``cache_control`` from the previous last user
        message first so only one breakpoint exists at a time.
        """
        found_last = False
        for msg in reversed(self._truncated_message_history):
            if msg.role != "user":
                continue
            if not found_last:
                found_last = True
                _set_cache_breakpoint(msg)
            else:
                _clear_cache_control(msg)
                break

    @override
    def truncate(self) -> None:
        """Summarize old messages and keep only recent ones."""
        if len(self._truncated_message_history) <= self._n_messages_to_keep:
            msg = "Cannot truncate: too few messages in history"
            logger.warning(msg)
            return

        logger.info("Summarizing message history")
        summary = _summarize_message_history(
            self._vlm_provider, self._truncated_message_history
        )

        # Find a safe cut point that doesn't orphan
        # tool_results from their tool_use.
        cut = len(self._truncated_message_history) - self._n_messages_to_keep
        while cut > 0 and _has_orphaned_tool_results(
            self._truncated_message_history[cut]
        ):
            cut -= 1

        if cut <= 0:
            msg = "Cannot truncate: no safe cut point found"
            logger.warning(msg)
            return

        recent = self._truncated_message_history[cut:]

        new_messages: list[MessageParam] = [
            MessageParam(role="user", content=summary),
        ]

        # Ensure valid role alternation
        if recent and recent[0].role == "user":
            new_messages.append(
                MessageParam(
                    role="assistant",
                    content=(
                        "Understood. I'll continue based on "
                        "the conversation summary above."
                    ),
                )
            )

        new_messages.extend(recent)
        self._truncated_message_history = new_messages


def _describe_tool_result(
    block: ToolResultBlockParam,
) -> str:
    """One-line description of a tool result block."""
    if isinstance(block.content, str):
        return f"tool_result({block.content[:40]})"
    nested = []
    for n in block.content:
        if isinstance(n, TextBlockParam):
            nested.append(f"text({n.text[:30]})")
        elif isinstance(n, ImageBlockParam):
            kind = "b64" if isinstance(n.source, Base64ImageSourceParam) else "url"
            nested.append(f"img:{kind}")
    return f"tool_result[{', '.join(nested)}]"
