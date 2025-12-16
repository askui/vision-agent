"""Unit tests for CacheParameterHandler."""

import pytest

from askui.models.shared.agent_message_param import ToolUseBlockParam
from askui.utils.caching.cache_parameter_handler import (
    CACHE_PARAMETER_PATTERN,
    CacheParameterHandler,
)


def test_parameter_pattern_matches_valid_parameters() -> None:
    """Test that the regex pattern matches valid parameter syntax."""
    import re

    valid_parameters = [
        "{{variable}}",
        "{{current_date}}",
        "{{user_name}}",
        "{{_private}}",
        "{{VAR123}}",
    ]

    for parameter in valid_parameters:
        match = re.search(CACHE_PARAMETER_PATTERN, parameter)
        assert match is not None, f"Should match valid parameter: {parameter}"


def test_parameter_pattern_does_not_match_invalid() -> None:
    """Test that the regex pattern rejects invalid parameter syntax."""
    import re

    invalid_parameters = [
        "{{123invalid}}",  # Starts with number
        "{{var-name}}",  # Contains hyphen
        "{{var name}}",  # Contains space
        "{single}",  # Single braces
        "{{}}",  # Empty
    ]

    for parameter in invalid_parameters:
        match = re.search(CACHE_PARAMETER_PATTERN, parameter)
        if match and match.group(0) == parameter:
            pytest.fail(f"Should not match invalid parameter: {parameter}")


def test_extract_parameters_from_simple_string() -> None:
    """Test extracting parameters from a simple string input."""
    trajectory = [
        ToolUseBlockParam(
            id="1",
            name="computer",
            input={"action": "type", "text": "Today is {{current_date}}"},
            type="tool_use",
        )
    ]

    parameters = CacheParameterHandler.extract_parameters(trajectory)
    assert parameters == {"current_date"}


def test_extract_parameters_multiple_in_one_string() -> None:
    """Test extracting multiple parameters from one string."""
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

    parameters = CacheParameterHandler.extract_parameters(trajectory)
    assert parameters == {"user_name", "current_date"}


def test_extract_parameters_from_nested_dict() -> None:
    """Test extracting parameters from nested dictionary structures."""
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

    parameters = CacheParameterHandler.extract_parameters(trajectory)
    assert parameters == {"nested_var", "another_var"}


def test_extract_parameters_from_list() -> None:
    """Test extracting parameters from lists in input."""
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

    parameters = CacheParameterHandler.extract_parameters(trajectory)
    assert parameters == {"item1", "item2", "item3"}


def test_extract_parameters_no_parameters() -> None:
    """Test that extracting from trajectory without parameters returns empty set."""
    trajectory = [
        ToolUseBlockParam(
            id="1",
            name="computer",
            input={"action": "click", "coordinate": [100, 200]},
            type="tool_use",
        )
    ]

    parameters = CacheParameterHandler.extract_parameters(trajectory)
    assert parameters == set()


def test_extract_parameters_from_multiple_steps() -> None:
    """Test extracting parameters from multiple trajectory steps."""
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

    parameters = CacheParameterHandler.extract_parameters(trajectory)
    assert parameters == {"var1", "var2"}  # No duplicates


def test_validate_parameters_all_provided() -> None:
    """Test validation passes when all parameters have values."""
    trajectory = [
        ToolUseBlockParam(
            id="1",
            name="tool",
            input={"text": "{{var1}} and {{var2}}"},
            type="tool_use",
        )
    ]

    is_valid, missing = CacheParameterHandler.validate_parameters(
        trajectory, {"var1": "value1", "var2": "value2"}
    )

    assert is_valid is True
    assert missing == []


def test_validate_parameters_missing_some() -> None:
    """Test validation fails when some parameters are missing."""
    trajectory = [
        ToolUseBlockParam(
            id="1",
            name="tool",
            input={"text": "{{var1}} and {{var2}} and {{var3}}"},
            type="tool_use",
        )
    ]

    is_valid, missing = CacheParameterHandler.validate_parameters(
        trajectory, {"var1": "value1"}
    )

    assert is_valid is False
    assert set(missing) == {"var2", "var3"}


def test_validate_parameters_extra_values_ok() -> None:
    """Test validation passes when extra values are provided (they're ignored)."""
    trajectory = [
        ToolUseBlockParam(
            id="1",
            name="tool",
            input={"text": "{{var1}}"},
            type="tool_use",
        )
    ]

    is_valid, missing = CacheParameterHandler.validate_parameters(
        trajectory, {"var1": "value1", "extra_var": "extra_value"}
    )

    assert is_valid is True
    assert missing == []


def test_validate_parameters_no_parameters() -> None:
    """Test validation passes when trajectory has no parameters."""
    trajectory = [
        ToolUseBlockParam(
            id="1",
            name="tool",
            input={"text": "No parameters here"},
            type="tool_use",
        )
    ]

    is_valid, missing = CacheParameterHandler.validate_parameters(trajectory, {})

    assert is_valid is True
    assert missing == []


def test_substitute_parameters_simple_string() -> None:
    """Test substituting parameters in a simple string."""
    tool_block = ToolUseBlockParam(
        id="1",
        name="computer",
        input={"action": "type", "text": "Today is {{current_date}}"},
        type="tool_use",
    )

    result = CacheParameterHandler.substitute_parameters(
        tool_block, {"current_date": "2025-12-11"}
    )

    assert result.input["text"] == "Today is 2025-12-11"  # type: ignore[index]
    assert result.id == tool_block.id
    assert result.name == tool_block.name


def test_substitute_parameters_multiple() -> None:
    """Test substituting multiple parameters in one string."""
    tool_block = ToolUseBlockParam(
        id="1",
        name="computer",
        input={
            "action": "type",
            "text": "Hello {{user_name}}, date is {{current_date}}",
        },
        type="tool_use",
    )

    result = CacheParameterHandler.substitute_parameters(
        tool_block, {"user_name": "Alice", "current_date": "2025-12-11"}
    )

    assert result.input["text"] == "Hello Alice, date is 2025-12-11"  # type: ignore[index]


def test_substitute_parameters_nested_dict() -> None:
    """Test substituting parameters in nested dictionaries."""
    tool_block = ToolUseBlockParam(
        id="1",
        name="tool",
        input={
            "outer": {"inner": {"text": "Value: {{var1}}"}},
            "another": "{{var2}}",
        },
        type="tool_use",
    )

    result = CacheParameterHandler.substitute_parameters(
        tool_block, {"var1": "value1", "var2": "value2"}
    )

    assert result.input["outer"]["inner"]["text"] == "Value: value1"  # type: ignore[index]
    assert result.input["another"] == "value2"  # type: ignore[index]


def test_substitute_parameters_in_list() -> None:
    """Test substituting parameters in lists."""
    tool_block = ToolUseBlockParam(
        id="1",
        name="tool",
        input={"items": ["{{item1}}", "static", {"nested": "{{item2}}"}]},
        type="tool_use",
    )

    result = CacheParameterHandler.substitute_parameters(
        tool_block, {"item1": "value1", "item2": "value2"}
    )

    assert result.input["items"][0] == "value1"  # type: ignore[index]
    assert result.input["items"][1] == "static"  # type: ignore[index]
    assert result.input["items"][2]["nested"] == "value2"  # type: ignore[index]


def test_substitute_parameters_no_change_if_no_parameters() -> None:
    """Test that substitution doesn't change input without parameters."""
    tool_block = ToolUseBlockParam(
        id="1",
        name="computer",
        input={"action": "click", "coordinate": [100, 200]},
        type="tool_use",
    )

    result = CacheParameterHandler.substitute_parameters(tool_block, {})

    assert result.input == tool_block.input


def test_substitute_parameters_partial_substitution() -> None:
    """Test that only provided parameters are substituted."""
    tool_block = ToolUseBlockParam(
        id="1",
        name="tool",
        input={"text": "{{var1}} and {{var2}}"},
        type="tool_use",
    )

    result = CacheParameterHandler.substitute_parameters(tool_block, {"var1": "value1"})

    assert result.input["text"] == "value1 and {{var2}}"  # type: ignore[index]


def test_substitute_parameters_preserves_original() -> None:
    """Test that substitution creates a new object, doesn't modify original."""
    tool_block = ToolUseBlockParam(
        id="1",
        name="tool",
        input={"text": "{{var1}}"},
        type="tool_use",
    )

    original_input = tool_block.input.copy()  # type: ignore[attr-defined]
    CacheParameterHandler.substitute_parameters(tool_block, {"var1": "value1"})

    # Original should be unchanged
    assert tool_block.input == original_input


def test_substitute_parameters_with_special_characters() -> None:
    """Test substitution with values containing special regex characters."""
    tool_block = ToolUseBlockParam(
        id="1",
        name="tool",
        input={"text": "Pattern: {{pattern}}"},
        type="tool_use",
    )

    # Value contains regex special characters
    result = CacheParameterHandler.substitute_parameters(
        tool_block, {"pattern": r".*[test]$"}
    )

    assert result.input["text"] == r"Pattern: .*[test]$"  # type: ignore[index]


def test_substitute_parameters_same_parameter_multiple_times() -> None:
    """Test substituting the same parameter appearing multiple times."""
    tool_block = ToolUseBlockParam(
        id="1",
        name="tool",
        input={"text": "{{var}} is {{var}} is {{var}}"},
        type="tool_use",
    )

    result = CacheParameterHandler.substitute_parameters(tool_block, {"var": "value"})

    assert result.input["text"] == "value is value is value"  # type: ignore[index]
