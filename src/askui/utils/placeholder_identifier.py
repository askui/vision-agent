"""Module for identifying placeholders in trajectories using LLM analysis."""

import json
import logging
from typing import Any

from askui.models.shared.agent_message_param import MessageParam, ToolUseBlockParam
from askui.models.shared.messages_api import MessagesApi
from askui.prompts.caching import PLACEHOLDER_IDENTIFIER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class PlaceholderDefinition:
    """Represents a placeholder identified in a trajectory."""

    def __init__(self, name: str, value: Any, description: str) -> None:
        self.name = name
        self.value = value
        self.description = description

    def __repr__(self) -> str:
        return f"PlaceholderDefinition(name={self.name}, value={self.value})"


def identify_placeholders(
    trajectory: list[ToolUseBlockParam],
    messages_api: MessagesApi,
    model: str = "claude-sonnet-4-5-20250929",
) -> tuple[dict[str, str], list[PlaceholderDefinition]]:
    """Identify placeholders in a trajectory using LLM analysis.

    Args:
        trajectory: The trajectory to analyze (list of tool use blocks)
        messages_api: Messages API instance for LLM calls
        model: Model to use for analysis

    Returns:
        Tuple of:
        - Dict mapping placeholder names to descriptions
        - List of PlaceholderDefinition objects with name, value, and description
    """
    if not trajectory:
        logger.debug("Empty trajectory provided, skipping placeholder identification")
        return {}, []

    logger.info(
        "Starting placeholder identification for trajectory with %s steps",
        len(trajectory),
    )

    # Convert trajectory to serializable format for analysis
    trajectory_data = [tool.model_dump(mode="json") for tool in trajectory]
    logger.debug("Converted %s tool blocks to JSON format", len(trajectory_data))

    user_message = (
        "Analyze this UI automation trajectory and identify all values that "
        "should be placeholders:\n\n"
        f"```json\n{json.dumps(trajectory_data, indent=2)}\n```\n\n"
        "Return only the JSON object with identified placeholders. "
        "Be thorough but conservative - only mark values that are clearly "
        "dynamic or time-sensitive."
    )

    response_text = ""  # Initialize for error logging
    try:
        # Make single API call
        logger.debug("Calling LLM (%s) to analyze trajectory for placeholders", model)
        response = messages_api.create_message(
            messages=[MessageParam(role="user", content=user_message)],
            model=model,
            system=PLACEHOLDER_IDENTIFIER_SYSTEM_PROMPT,
            max_tokens=4096,
            temperature=0.0,  # Deterministic for analysis
        )
        logger.debug("Received response from LLM")

        # Extract text from response
        if isinstance(response.content, list):
            response_text = next(
                (block.text for block in response.content if hasattr(block, "text")),
                "",
            )
        else:
            response_text = str(response.content)

        # Parse the JSON response
        logger.debug("Parsing LLM response to extract placeholder definitions")
        # Handle markdown code blocks if present
        if "```json" in response_text:
            logger.debug("Removing JSON markdown code block wrapper from response")
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            logger.debug("Removing code block wrapper from response")
            response_text = response_text.split("```")[1].split("```")[0].strip()

        placeholder_data = json.loads(response_text)
        logger.debug(
            "Successfully parsed JSON response with %s placeholders",
            len(placeholder_data.get("placeholders", [])),
        )

        # Convert to our data structures
        placeholder_definitions = [
            PlaceholderDefinition(
                name=p["name"], value=p["value"], description=p["description"]
            )
            for p in placeholder_data.get("placeholders", [])
        ]

        placeholder_dict = {p.name: p.description for p in placeholder_definitions}

        if placeholder_definitions:
            logger.info(
                "Successfully identified %s placeholders in trajectory",
                len(placeholder_definitions),
            )
            for p in placeholder_definitions:
                logger.debug("  - %s: %s (%s)", p.name, p.value, p.description)
        else:
            logger.info(
                "No placeholders identified in trajectory "
                "(this is normal for trajectories with only static values)"
            )

    except json.JSONDecodeError as e:
        logger.warning(
            "Failed to parse LLM response as JSON: %s. "
            "Falling back to empty placeholder list.",
            e,
            extra={"response_text": response_text[:500]},  # Log first 500 chars
        )
        return {}, []
    except Exception as e:  # noqa: BLE001
        logger.warning(
            "Failed to identify placeholders with LLM: %s. "
            "Falling back to empty placeholder list.",
            e,
            exc_info=True,
        )
        return {}, []
    else:
        return placeholder_dict, placeholder_definitions
