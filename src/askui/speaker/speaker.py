"""Base speaker class and result types for conversation architecture."""

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field
from typing_extensions import Literal

from askui.models.shared.agent_message_param import MessageParam, UsageParam
from askui.utils.caching.cache_manager import CacheManager

if TYPE_CHECKING:
    from .conversation import Conversation

logger = logging.getLogger(__name__)

SPEAKER_RESULT_STATUS = Literal["continue", "switch_speaker", "done", "failed"]


class SpeakerResult(BaseModel):
    """Result of a speaker handling a conversation step.

    Attributes:
        status: Execution status
            - "continue": Continue with same speaker (recurse)
            - "switch_speaker": Switch to a different speaker
            - "done": Conversation finished successfully
            - "failed": Conversation failed with error
        next_speaker: Name of next speaker to switch to
            (required if status="switch_speaker")
        messages_to_add: Messages to add to conversation history
        usage: Token usage from this step (if applicable)
    """

    status: SPEAKER_RESULT_STATUS
    next_speaker: str | None = None
    messages_to_add: list[MessageParam] = Field(default_factory=list)
    usage: UsageParam | None = None


class Speaker(ABC):
    """Abstract base class for conversation speakers.

    A speaker handles specific types of conversation steps (e.g., normal agent
    API calls, cache execution, human-in-the-loop).

    Each speaker determines whether it can handle the current conversation state
    and executes one step when activated.
    """

    @abstractmethod
    def can_handle(self, conversation: "Conversation") -> bool:
        """Check if this speaker can handle the current conversation state.

        Args:
            conversation: The conversation instance with current state

        Returns:
            True if this speaker can handle the current state
        """
        ...

    @abstractmethod
    def handle_step(
        self, conversation: "Conversation", cache_manager: CacheManager | None
    ) -> SpeakerResult:
        """Execute one conversation step.

        Args:
            conversation: The conversation instance with current state

        Returns:
            SpeakerResult indicating what to do next
        """
        ...

    @abstractmethod
    def get_name(self) -> str:
        """Return the speaker's name for logging and identification.

        Returns:
            Speaker name (e.g., "AskUIAgent", "CacheExecutor")
        """
        ...


class Speakers:
    def __init__(self, speakers: dict[str, Speaker] | None = None) -> None:
        # Lazy import to avoid circular dependency
        from .askui_agent import AskUIAgent

        self.speakers: dict[str, Speaker] = speakers or {"AskUIAgent": AskUIAgent()}
        self.default_speaker: str = (
            "AskUIAgent"
            if "AskUIAgent" in self.speakers.keys()
            else list(self.speakers.keys())[0]
        )

    def add_speaker(self, speaker: Speaker) -> None:
        self.speakers[speaker.get_name()] = speaker

    def get_names(self) -> list[str]:
        return list(self.speakers.keys())

    def __add__(self, other: "Speakers") -> "Speakers":
        result = Speakers()
        result.speakers = self.speakers | other.speakers
        result.default_speaker = self.default_speaker
        return result

    def __getitem__(self, name: str) -> Speaker:
        if name in self.speakers.keys():
            return self.speakers[name]
        msg = (
            f"Speaker {name} is not part of Speakers."
            f"Will use default Speaker {self.default_speaker} instead"
        )
        logger.warning(msg)
        return self.speakers[self.default_speaker]
