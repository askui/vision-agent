"""Placeholder handling for cache trajectories.

This module provides utilities for detecting, validating, and substituting
placeholders in cached trajectories. Placeholders use the {{variable_name}}
syntax and allow dynamic values to be injected during cache execution.
"""

import re
from typing import Any

from askui.models.shared.agent_message_param import ToolUseBlockParam

# Regex pattern for matching placeholders: {{variable_name}}
# Allows alphanumeric characters and underscores, must start with letter/underscore
PLACEHOLDER_PATTERN = r"\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}"


class PlaceholderHandler:
    """Handler for placeholder detection, validation, and substitution."""

    @staticmethod
    def extract_placeholders(trajectory: list[ToolUseBlockParam]) -> set[str]:
        """Extract all placeholder names from a trajectory.

        Scans all tool inputs for {{placeholder_name}} patterns and returns
        a set of unique placeholder names.

        Args:
            trajectory: List of tool use blocks to scan

        Returns:
            Set of unique placeholder names found in the trajectory

        Example:
            >>> trajectory = [
            ...     ToolUseBlockParam(
            ...         id="1",
            ...         name="computer",
            ...         input={"action": "type", "text": "Today is {{current_date}}"},
            ...         type="tool_use"
            ...     )
            ... ]
            >>> PlaceholderHandler.extract_placeholders(trajectory)
            {'current_date'}
        """
        placeholders: set[str] = set()

        for step in trajectory:
            # Recursively find placeholders in the input object
            placeholders.update(
                PlaceholderHandler._extract_from_value(step.input)
            )

        return placeholders

    @staticmethod
    def _extract_from_value(value: Any) -> set[str]:
        """Recursively extract placeholders from a value.

        Args:
            value: Any value (str, dict, list, etc.) to search for placeholders

        Returns:
            Set of placeholder names found
        """
        placeholders: set[str] = set()

        if isinstance(value, str):
            # Find all matches in the string
            matches = re.finditer(PLACEHOLDER_PATTERN, value)
            placeholders.update(match.group(1) for match in matches)
        elif isinstance(value, dict):
            # Recursively search dict values
            for v in value.values():
                placeholders.update(PlaceholderHandler._extract_from_value(v))
        elif isinstance(value, list):
            # Recursively search list items
            for item in value:
                placeholders.update(PlaceholderHandler._extract_from_value(item))

        return placeholders

    @staticmethod
    def validate_placeholders(
        trajectory: list[ToolUseBlockParam], provided_values: dict[str, str]
    ) -> tuple[bool, list[str]]:
        """Validate that all required placeholders have values.

        Args:
            trajectory: List of tool use blocks containing placeholders
            provided_values: Dict of placeholder names to their values

        Returns:
            Tuple of (is_valid, missing_placeholders)
            - is_valid: True if all placeholders have values, False otherwise
            - missing_placeholders: List of placeholder names that are missing values

        Example:
            >>> trajectory = [...]  # Contains {{current_date}} and {{user_name}}
            >>> is_valid, missing = PlaceholderHandler.validate_placeholders(
            ...     trajectory,
            ...     {"current_date": "2025-12-11"}
            ... )
            >>> is_valid
            False
            >>> missing
            ['user_name']
        """
        required_placeholders = PlaceholderHandler.extract_placeholders(trajectory)
        missing = [
            name for name in required_placeholders if name not in provided_values
        ]

        return len(missing) == 0, missing

    @staticmethod
    def replace_values_with_placeholders(
        trajectory: list[ToolUseBlockParam],
        placeholder_definitions: list[Any],  # list[PlaceholderDefinition]
    ) -> list[ToolUseBlockParam]:
        """Replace actual values in trajectory with {{placeholder_name}} syntax.

        This is the reverse of substitute_placeholders - it takes identified values
        and replaces them with placeholder syntax for saving to cache.

        Args:
            trajectory: The trajectory to templatize
            placeholder_definitions: List of PlaceholderDefinition objects with
                name and value attributes

        Returns:
            New trajectory with values replaced by placeholders

        Example:
            >>> trajectory = [
            ...     ToolUseBlockParam(
            ...         id="1",
            ...         name="computer",
            ...         input={"action": "type", "text": "Date: 2025-12-11"},
            ...         type="tool_use"
            ...     )
            ... ]
            >>> placeholders = [
            ...     PlaceholderDefinition(
            ...         name="current_date",
            ...         value="2025-12-11",
            ...         description="Current date"
            ...     )
            ... ]
            >>> result = PlaceholderHandler.replace_values_with_placeholders(
            ...     trajectory, placeholders
            ... )
            >>> result[0].input["text"]
            'Date: {{current_date}}'
        """
        # Build replacement map: value -> placeholder name
        replacements = {
            str(p.value): f"{{{{{p.name}}}}}" for p in placeholder_definitions
        }

        # Apply replacements to each tool block
        templated_trajectory = []
        for tool_block in trajectory:
            templated_input = PlaceholderHandler._replace_values_in_value(
                tool_block.input, replacements
            )

            templated_trajectory.append(
                ToolUseBlockParam(
                    id=tool_block.id,
                    name=tool_block.name,
                    input=templated_input,
                    type=tool_block.type,
                    cache_control=tool_block.cache_control,
                )
            )

        return templated_trajectory

    @staticmethod
    def _replace_values_in_value(
        value: Any, replacements: dict[str, str]
    ) -> Any:
        """Recursively replace actual values with placeholder syntax.

        Args:
            value: Any value (str, dict, list, etc.) to process
            replacements: Dict mapping actual values to placeholder syntax

        Returns:
            New value with replacements applied
        """
        if isinstance(value, str):
            # Replace exact matches and substring matches
            result = value
            # Sort by length descending to replace longer matches first
            # This prevents partial replacements
            for actual_value in sorted(replacements.keys(), key=len, reverse=True):
                if actual_value in result:
                    result = result.replace(actual_value, replacements[actual_value])
            return result
        elif isinstance(value, dict):
            # Recursively replace in dict values
            return {
                k: PlaceholderHandler._replace_values_in_value(v, replacements)
                for k, v in value.items()
            }
        elif isinstance(value, list):
            # Recursively replace in list items
            return [
                PlaceholderHandler._replace_values_in_value(item, replacements)
                for item in value
            ]
        else:
            # For non-string types, check if the value matches exactly
            str_value = str(value)
            if str_value in replacements:
                # Return the placeholder as a string
                return replacements[str_value]
            return value

    @staticmethod
    def substitute_placeholders(
        tool_block: ToolUseBlockParam, placeholder_values: dict[str, str]
    ) -> ToolUseBlockParam:
        """Replace placeholders in a tool block with actual values.

        Creates a new ToolUseBlockParam with all {{placeholder}} occurrences
        replaced with their corresponding values from placeholder_values.

        Args:
            tool_block: The tool use block containing placeholders
            placeholder_values: Dict mapping placeholder names to replacement values

        Returns:
            New ToolUseBlockParam with placeholders substituted

        Example:
            >>> tool_block = ToolUseBlockParam(
            ...     id="1",
            ...     name="computer",
            ...     input={"action": "type", "text": "Date: {{current_date}}"},
            ...     type="tool_use"
            ... )
            >>> result = PlaceholderHandler.substitute_placeholders(
            ...     tool_block,
            ...     {"current_date": "2025-12-11"}
            ... )
            >>> result.input["text"]
            'Date: 2025-12-11'
        """
        # Deep copy the input and substitute placeholders
        substituted_input = PlaceholderHandler._substitute_in_value(
            tool_block.input, placeholder_values
        )

        # Create new ToolUseBlockParam with substituted values
        return ToolUseBlockParam(
            id=tool_block.id,
            name=tool_block.name,
            input=substituted_input,
            type=tool_block.type,
            cache_control=tool_block.cache_control,
        )

    @staticmethod
    def _substitute_in_value(value: Any, placeholder_values: dict[str, str]) -> Any:
        """Recursively substitute placeholders in a value.

        Args:
            value: Any value (str, dict, list, etc.) containing placeholders
            placeholder_values: Dict of placeholder names to replacement values

        Returns:
            New value with placeholders substituted
        """
        if isinstance(value, str):
            # Replace all placeholders in the string
            result = value
            for name, replacement in placeholder_values.items():
                pattern = r"\{\{" + re.escape(name) + r"\}\}"
                result = re.sub(pattern, replacement, result)
            return result
        elif isinstance(value, dict):
            # Recursively substitute in dict values
            return {
                k: PlaceholderHandler._substitute_in_value(v, placeholder_values)
                for k, v in value.items()
            }
        elif isinstance(value, list):
            # Recursively substitute in list items
            return [
                PlaceholderHandler._substitute_in_value(item, placeholder_values)
                for item in value
            ]
        else:
            # Return other types as-is
            return value
