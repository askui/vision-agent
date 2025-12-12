"""Unit tests for PlaceholderHandler."""

import pytest
from askui.models.shared.agent_message_param import ToolUseBlockParam
from askui.utils.placeholder_handler import PLACEHOLDER_PATTERN, PlaceholderHandler


def test_placeholder_pattern_matches_valid_placeholders() -> None:
    """Test that the regex pattern matches valid placeholder syntax."""
    import re

    valid_placeholders = [
        "{{variable}}",
        "{{current_date}}",
        "{{user_name}}",
        "{{_private}}",
        "{{VAR123}}",
    ]

    for placeholder in valid_placeholders:
        match = re.search(PLACEHOLDER_PATTERN, placeholder)
        assert match is not None, f"Should match valid placeholder: {placeholder}"


def test_placeholder_pattern_does_not_match_invalid() -> None:
    """Test that the regex pattern rejects invalid placeholder syntax."""
    import re

    invalid_placeholders = [
        "{{123invalid}}",  # Starts with number
        "{{var-name}}",  # Contains hyphen
        "{{var name}}",  # Contains space
        "{single}",  # Single braces
        "{{}}",  # Empty
    ]

    for placeholder in invalid_placeholders:
        match = re.search(PLACEHOLDER_PATTERN, placeholder)
        if match and match.group(0) == placeholder:
            pytest.fail(f"Should not match invalid placeholder: {placeholder}")


def test_extract_placeholders_from_simple_string() -> None:
    """Test extracting placeholders from a simple string input."""
    trajectory = [
        ToolUseBlockParam(
            id="1",
            name="computer",
            input={"action": "type", "text": "Today is {{current_date}}"},
            type="tool_use",
        )
    ]

    placeholders = PlaceholderHandler.extract_placeholders(trajectory)
    assert placeholders == {"current_date"}


def test_extract_placeholders_multiple_in_one_string() -> None:
    """Test extracting multiple placeholders from one string."""
    trajectory = [
        ToolUseBlockParam(
            id="1",
            name="computer",
            input={
                "action": "type",
                "text": "Hello {{user_name}}, today is {{current_date}}",
            },
            type="tool_use",
        )
    ]

    placeholders = PlaceholderHandler.extract_placeholders(trajectory)
    assert placeholders == {"user_name", "current_date"}


def test_extract_placeholders_from_nested_dict() -> None:
    """Test extracting placeholders from nested dictionary structures."""
    trajectory = [
        ToolUseBlockParam(
            id="1",
            name="complex_tool",
            input={
                "outer": {"inner": {"text": "Value is {{nested_var}}"}},
                "another": "{{another_var}}",
            },
            type="tool_use",
        )
    ]

    placeholders = PlaceholderHandler.extract_placeholders(trajectory)
    assert placeholders == {"nested_var", "another_var"}


def test_extract_placeholders_from_list() -> None:
    """Test extracting placeholders from lists in input."""
    trajectory = [
        ToolUseBlockParam(
            id="1",
            name="tool",
            input={
                "items": [
                    "{{item1}}",
                    "{{item2}}",
                    {"nested": "{{item3}}"},
                ]
            },
            type="tool_use",
        )
    ]

    placeholders = PlaceholderHandler.extract_placeholders(trajectory)
    assert placeholders == {"item1", "item2", "item3"}


def test_extract_placeholders_no_placeholders() -> None:
    """Test that extracting from trajectory without placeholders returns empty set."""
    trajectory = [
        ToolUseBlockParam(
            id="1",
            name="computer",
            input={"action": "click", "coordinate": [100, 200]},
            type="tool_use",
        )
    ]

    placeholders = PlaceholderHandler.extract_placeholders(trajectory)
    assert placeholders == set()


def test_extract_placeholders_from_multiple_steps() -> None:
    """Test extracting placeholders from multiple trajectory steps."""
    trajectory = [
        ToolUseBlockParam(
            id="1",
            name="tool1",
            input={"text": "{{var1}}"},
            type="tool_use",
        ),
        ToolUseBlockParam(
            id="2",
            name="tool2",
            input={"text": "{{var2}}"},
            type="tool_use",
        ),
        ToolUseBlockParam(
            id="3",
            name="tool3",
            input={"text": "{{var1}}"},  # Duplicate
            type="tool_use",
        ),
    ]

    placeholders = PlaceholderHandler.extract_placeholders(trajectory)
    assert placeholders == {"var1", "var2"}  # No duplicates


def test_validate_placeholders_all_provided() -> None:
    """Test validation passes when all placeholders have values."""
    trajectory = [
        ToolUseBlockParam(
            id="1",
            name="tool",
            input={"text": "{{var1}} and {{var2}}"},
            type="tool_use",
        )
    ]

    is_valid, missing = PlaceholderHandler.validate_placeholders(
        trajectory, {"var1": "value1", "var2": "value2"}
    )

    assert is_valid is True
    assert missing == []


def test_validate_placeholders_missing_some() -> None:
    """Test validation fails when some placeholders are missing."""
    trajectory = [
        ToolUseBlockParam(
            id="1",
            name="tool",
            input={"text": "{{var1}} and {{var2}} and {{var3}}"},
            type="tool_use",
        )
    ]

    is_valid, missing = PlaceholderHandler.validate_placeholders(
        trajectory, {"var1": "value1"}
    )

    assert is_valid is False
    assert set(missing) == {"var2", "var3"}


def test_validate_placeholders_extra_values_ok() -> None:
    """Test validation passes when extra values are provided (they're ignored)."""
    trajectory = [
        ToolUseBlockParam(
            id="1",
            name="tool",
            input={"text": "{{var1}}"},
            type="tool_use",
        )
    ]

    is_valid, missing = PlaceholderHandler.validate_placeholders(
        trajectory, {"var1": "value1", "extra_var": "extra_value"}
    )

    assert is_valid is True
    assert missing == []


def test_validate_placeholders_no_placeholders() -> None:
    """Test validation passes when trajectory has no placeholders."""
    trajectory = [
        ToolUseBlockParam(
            id="1",
            name="tool",
            input={"text": "No placeholders here"},
            type="tool_use",
        )
    ]

    is_valid, missing = PlaceholderHandler.validate_placeholders(trajectory, {})

    assert is_valid is True
    assert missing == []


def test_substitute_placeholders_simple_string() -> None:
    """Test substituting placeholders in a simple string."""
    tool_block = ToolUseBlockParam(
        id="1",
        name="computer",
        input={"action": "type", "text": "Today is {{current_date}}"},
        type="tool_use",
    )

    result = PlaceholderHandler.substitute_placeholders(
        tool_block, {"current_date": "2025-12-11"}
    )

    assert result.input["text"] == "Today is 2025-12-11"
    assert result.id == tool_block.id
    assert result.name == tool_block.name


def test_substitute_placeholders_multiple() -> None:
    """Test substituting multiple placeholders in one string."""
    tool_block = ToolUseBlockParam(
        id="1",
        name="computer",
        input={
            "action": "type",
            "text": "Hello {{user_name}}, date is {{current_date}}",
        },
        type="tool_use",
    )

    result = PlaceholderHandler.substitute_placeholders(
        tool_block, {"user_name": "Alice", "current_date": "2025-12-11"}
    )

    assert result.input["text"] == "Hello Alice, date is 2025-12-11"


def test_substitute_placeholders_nested_dict() -> None:
    """Test substituting placeholders in nested dictionaries."""
    tool_block = ToolUseBlockParam(
        id="1",
        name="tool",
        input={
            "outer": {"inner": {"text": "Value: {{var1}}"}},
            "another": "{{var2}}",
        },
        type="tool_use",
    )

    result = PlaceholderHandler.substitute_placeholders(
        tool_block, {"var1": "value1", "var2": "value2"}
    )

    assert result.input["outer"]["inner"]["text"] == "Value: value1"
    assert result.input["another"] == "value2"


def test_substitute_placeholders_in_list() -> None:
    """Test substituting placeholders in lists."""
    tool_block = ToolUseBlockParam(
        id="1",
        name="tool",
        input={"items": ["{{item1}}", "static", {"nested": "{{item2}}"}]},
        type="tool_use",
    )

    result = PlaceholderHandler.substitute_placeholders(
        tool_block, {"item1": "value1", "item2": "value2"}
    )

    assert result.input["items"][0] == "value1"
    assert result.input["items"][1] == "static"
    assert result.input["items"][2]["nested"] == "value2"


def test_substitute_placeholders_no_change_if_no_placeholders() -> None:
    """Test that substitution doesn't change input without placeholders."""
    tool_block = ToolUseBlockParam(
        id="1",
        name="computer",
        input={"action": "click", "coordinate": [100, 200]},
        type="tool_use",
    )

    result = PlaceholderHandler.substitute_placeholders(tool_block, {})

    assert result.input == tool_block.input


def test_substitute_placeholders_partial_substitution() -> None:
    """Test that only provided placeholders are substituted."""
    tool_block = ToolUseBlockParam(
        id="1",
        name="tool",
        input={"text": "{{var1}} and {{var2}}"},
        type="tool_use",
    )

    result = PlaceholderHandler.substitute_placeholders(tool_block, {"var1": "value1"})

    assert result.input["text"] == "value1 and {{var2}}"


def test_substitute_placeholders_preserves_original() -> None:
    """Test that substitution creates a new object, doesn't modify original."""
    tool_block = ToolUseBlockParam(
        id="1",
        name="tool",
        input={"text": "{{var1}}"},
        type="tool_use",
    )

    original_input = tool_block.input.copy()
    PlaceholderHandler.substitute_placeholders(tool_block, {"var1": "value1"})

    # Original should be unchanged
    assert tool_block.input == original_input


def test_substitute_placeholders_with_special_characters() -> None:
    """Test substitution with values containing special regex characters."""
    tool_block = ToolUseBlockParam(
        id="1",
        name="tool",
        input={"text": "Pattern: {{pattern}}"},
        type="tool_use",
    )

    # Value contains regex special characters
    result = PlaceholderHandler.substitute_placeholders(
        tool_block, {"pattern": r".*[test]$"}
    )

    assert result.input["text"] == r"Pattern: .*[test]$"


def test_substitute_placeholders_same_placeholder_multiple_times() -> None:
    """Test substituting the same placeholder appearing multiple times."""
    tool_block = ToolUseBlockParam(
        id="1",
        name="tool",
        input={"text": "{{var}} is {{var}} is {{var}}"},
        type="tool_use",
    )

    result = PlaceholderHandler.substitute_placeholders(tool_block, {"var": "value"})

    assert result.input["text"] == "value is value is value"
