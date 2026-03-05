"""Generic tool for switching conversation speakers."""

import logging
from typing import Any

from pydantic import validate_call
from typing_extensions import override

from askui.models.shared.tools import Tool

logger = logging.getLogger(__name__)


class SwitchSpeakerTool(Tool):
    """Tool that allows the VLM to request a speaker handoff.

    This tool is dynamically created with the set of valid speaker names
    as an enum constraint. When the VLM calls this tool, `AgentSpeaker`
    detects the tool call and returns a `SpeakerResult` with
    ``status="switch_speaker"``.

    The tool itself is a no-op — it serves as a signal. The actual
    speaker switch is handled by `AgentSpeaker` inspecting the VLM response.
    """

    is_cacheable: bool = False

    def __init__(self, speaker_names: list[str]) -> None:
        """Initialize with valid speaker names.

        Args:
            speaker_names: List of speaker names that can be switched to.
                Used to build the enum constraint in the input schema.
        """
        super().__init__(
            name="switch_speaker",
            description=(
                "Switch the conversation to a different specialized speaker. "
                "Use this tool when the current task is better handled by a "
                "different speaker. The speaker_context parameter passes "
                "activation data to the target speaker. See "
                "AVAILABLE_SPEAKERS in the system prompt for descriptions "
                "of each speaker."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "speaker_name": {
                        "type": "string",
                        "enum": speaker_names,
                        "description": ("Name of the speaker to switch to."),
                    },
                    "speaker_context": {
                        "type": "object",
                        "description": (
                            "Activation context to pass to the target "
                            "speaker. Each speaker expects specific context "
                            "keys — see the speaker descriptions in "
                            "AVAILABLE_SPEAKERS."
                        ),
                        "additionalProperties": True,
                        "default": {},
                    },
                },
                "required": ["speaker_name"],
            },
        )

    @override
    @validate_call
    def __call__(
        self,
        speaker_name: str,
        speaker_context: dict[str, Any] | None = None,
    ) -> str:
        """No-op execution — the tool is a signal, not an action.

        Args:
            speaker_name: Target speaker name.
            speaker_context: Activation context for the target speaker.

        Returns:
            Acknowledgment message.
        """
        logger.info(
            "Speaker switch requested to '%s' with context keys: %s",
            speaker_name,
            list((speaker_context or {}).keys()),
        )
        return f"Switching to speaker '{speaker_name}'"
