from askui.models.shared.prompts import ActSystemPrompt
from askui.prompts.act_prompts import (
    ANDROID_AGENT_SYSTEM_PROMPT,
    ANDROID_CAPABILITIES,
    ANDROID_DEVICE_INFORMATION,
    ANDROID_RECOVERY_RULES,
    BROWSER_INSTALL_RULES,
    BROWSER_SPECIFIC_RULES,
    COMPUTER_AGENT_SYSTEM_PROMPT,
    COMPUTER_USE_CAPABILITIES,
    DESKTOP_DEVICE_INFORMATION,
    MD_REPORT_FORMAT,
    NO_REPORT_FORMAT,
    WEB_AGENT_DEVICE_INFORMATION,
    WEB_AGENT_SYSTEM_PROMPT,
    WEB_BROWSER_CAPABILITIES,
    create_android_agent_prompt,
    create_computer_agent_prompt,
    create_web_agent_prompt,
)


def test_act_system_prompt_renders_all_parts() -> None:
    """Test that ActSystemPrompt renders all parts with XML tags."""
    prompt = ActSystemPrompt(
        system_capabilities="Test capability",
        device_information="Test device",
        ui_information="Test UI",
        report_format="Test report format",
        additional_rules="Test rules",
    )

    rendered = str(prompt)

    # Verify all XML tags are present
    assert "<SYSTEM_CAPABILITIES>" in rendered
    assert "</SYSTEM_CAPABILITIES>" in rendered
    assert "<DEVICE_INFORMATION>" in rendered
    assert "</DEVICE_INFORMATION>" in rendered
    assert "<UI_INFORMATION>" in rendered
    assert "</UI_INFORMATION>" in rendered
    assert "<REPORT_FORMAT>" in rendered
    assert "</REPORT_FORMAT>" in rendered
    assert "<ADDITIONAL_RULES>" in rendered
    assert "</ADDITIONAL_RULES>" in rendered

    # Verify content is present
    assert "Test capability" in rendered
    assert "Test device" in rendered
    assert "Test UI" in rendered
    assert "Test report format" in rendered
    assert "Test rules" in rendered


def test_act_system_prompt_omits_empty_optional_parts() -> None:
    """Test that optional parts are omitted when empty."""
    prompt = ActSystemPrompt(
        system_capabilities="Test capability",
        device_information="Test device",
        report_format="Test report",
    )

    rendered = str(prompt)

    # Verify optional parts are not present when empty
    assert "<UI_INFORMATION>" not in rendered
    assert "<ADDITIONAL_RULES>" not in rendered

    # Verify required parts are present
    assert "<SYSTEM_CAPABILITIES>" in rendered
    assert "Test capability" in rendered
    assert "<DEVICE_INFORMATION>" in rendered
    assert "Test device" in rendered
    assert "<REPORT_FORMAT>" in rendered
    assert "Test report" in rendered


def test_act_system_prompt_with_only_empty_strings() -> None:
    """Test that ActSystemPrompt handles all empty strings gracefully."""
    prompt = ActSystemPrompt()

    rendered = str(prompt)

    # When all parts are empty, should return empty string
    assert rendered == ""


def test_act_system_prompt_proper_spacing() -> None:
    """Test that parts are separated with proper spacing."""
    prompt = ActSystemPrompt(
        system_capabilities="Cap1",
        device_information="Dev1",
        report_format="Rep1",
    )

    rendered = str(prompt)

    # Verify parts are separated by double newlines
    assert "\n\n" in rendered
    # Verify newlines are added inside tags
    assert "<SYSTEM_CAPABILITIES>\nCap1\n</SYSTEM_CAPABILITIES>" in rendered


def test_computer_agent_system_prompt_structure() -> None:
    """Test that COMPUTER_AGENT_SYSTEM_PROMPT has the correct structure."""
    assert "<SYSTEM_CAPABILITIES>" in COMPUTER_AGENT_SYSTEM_PROMPT
    assert "</SYSTEM_CAPABILITIES>" in COMPUTER_AGENT_SYSTEM_PROMPT
    assert "<DEVICE_INFORMATION>" in COMPUTER_AGENT_SYSTEM_PROMPT
    assert "</DEVICE_INFORMATION>" in COMPUTER_AGENT_SYSTEM_PROMPT
    assert "<REPORT_FORMAT>" in COMPUTER_AGENT_SYSTEM_PROMPT
    assert "</REPORT_FORMAT>" in COMPUTER_AGENT_SYSTEM_PROMPT
    assert "<ADDITIONAL_RULES>" in COMPUTER_AGENT_SYSTEM_PROMPT
    assert "</ADDITIONAL_RULES>" in COMPUTER_AGENT_SYSTEM_PROMPT

    # Verify content from constants is present
    assert COMPUTER_USE_CAPABILITIES in COMPUTER_AGENT_SYSTEM_PROMPT
    assert DESKTOP_DEVICE_INFORMATION in COMPUTER_AGENT_SYSTEM_PROMPT
    assert NO_REPORT_FORMAT in COMPUTER_AGENT_SYSTEM_PROMPT
    assert BROWSER_SPECIFIC_RULES in COMPUTER_AGENT_SYSTEM_PROMPT


def test_web_agent_system_prompt_structure() -> None:
    """Test that WEB_AGENT_SYSTEM_PROMPT has the correct structure."""
    assert "<SYSTEM_CAPABILITIES>" in WEB_AGENT_SYSTEM_PROMPT
    assert "</SYSTEM_CAPABILITIES>" in WEB_AGENT_SYSTEM_PROMPT
    assert "<DEVICE_INFORMATION>" in WEB_AGENT_SYSTEM_PROMPT
    assert "</DEVICE_INFORMATION>" in WEB_AGENT_SYSTEM_PROMPT
    assert "<REPORT_FORMAT>" in WEB_AGENT_SYSTEM_PROMPT
    assert "</REPORT_FORMAT>" in WEB_AGENT_SYSTEM_PROMPT
    assert "<ADDITIONAL_RULES>" in WEB_AGENT_SYSTEM_PROMPT
    assert "</ADDITIONAL_RULES>" in WEB_AGENT_SYSTEM_PROMPT

    # Verify content from constants is present
    assert WEB_BROWSER_CAPABILITIES in WEB_AGENT_SYSTEM_PROMPT
    assert WEB_AGENT_DEVICE_INFORMATION in WEB_AGENT_SYSTEM_PROMPT
    assert NO_REPORT_FORMAT in WEB_AGENT_SYSTEM_PROMPT
    assert BROWSER_INSTALL_RULES in WEB_AGENT_SYSTEM_PROMPT


def test_android_agent_system_prompt_structure() -> None:
    """Test that ANDROID_AGENT_SYSTEM_PROMPT has the correct structure."""
    assert "<SYSTEM_CAPABILITIES>" in ANDROID_AGENT_SYSTEM_PROMPT
    assert "</SYSTEM_CAPABILITIES>" in ANDROID_AGENT_SYSTEM_PROMPT
    assert "<DEVICE_INFORMATION>" in ANDROID_AGENT_SYSTEM_PROMPT
    assert "</DEVICE_INFORMATION>" in ANDROID_AGENT_SYSTEM_PROMPT
    assert "<REPORT_FORMAT>" in ANDROID_AGENT_SYSTEM_PROMPT
    assert "</REPORT_FORMAT>" in ANDROID_AGENT_SYSTEM_PROMPT
    assert "<ADDITIONAL_RULES>" in ANDROID_AGENT_SYSTEM_PROMPT
    assert "</ADDITIONAL_RULES>" in ANDROID_AGENT_SYSTEM_PROMPT

    # Verify content from constants is present
    assert ANDROID_CAPABILITIES in ANDROID_AGENT_SYSTEM_PROMPT
    assert ANDROID_DEVICE_INFORMATION in ANDROID_AGENT_SYSTEM_PROMPT
    assert NO_REPORT_FORMAT in ANDROID_AGENT_SYSTEM_PROMPT
    assert ANDROID_RECOVERY_RULES in ANDROID_AGENT_SYSTEM_PROMPT


def test_create_computer_agent_prompt_default() -> None:
    """Test create_computer_agent_prompt with default parameters."""
    prompt = create_computer_agent_prompt()

    rendered = str(prompt)

    assert COMPUTER_USE_CAPABILITIES in rendered
    assert DESKTOP_DEVICE_INFORMATION in rendered
    assert NO_REPORT_FORMAT in rendered
    assert BROWSER_SPECIFIC_RULES in rendered


def test_create_computer_agent_prompt_with_custom_ui_info() -> None:
    """Test create_computer_agent_prompt with custom UI information."""
    custom_ui = "Login page with email and password fields"
    prompt = create_computer_agent_prompt(ui_information=custom_ui)

    rendered = str(prompt)

    assert custom_ui in rendered
    assert "<UI_INFORMATION>" in rendered
    assert "</UI_INFORMATION>" in rendered


def test_create_computer_agent_prompt_with_additional_rules() -> None:
    """Test create_computer_agent_prompt with additional rules."""
    additional = "Never submit without user confirmation"
    prompt = create_computer_agent_prompt(additional_rules=additional)

    rendered = str(prompt)

    # Both default and additional rules should be present
    assert BROWSER_SPECIFIC_RULES in rendered
    assert additional in rendered
    assert "<ADDITIONAL_RULES>" in rendered


def test_create_web_agent_prompt_default() -> None:
    """Test create_web_agent_prompt with default parameters."""
    prompt = create_web_agent_prompt()

    rendered = str(prompt)

    assert WEB_BROWSER_CAPABILITIES in rendered
    assert WEB_AGENT_DEVICE_INFORMATION in rendered
    assert NO_REPORT_FORMAT in rendered
    assert BROWSER_INSTALL_RULES in rendered


def test_create_web_agent_prompt_with_custom_ui_info() -> None:
    """Test create_web_agent_prompt with custom UI information."""
    custom_ui = "E-commerce website with product catalog"
    prompt = create_web_agent_prompt(ui_information=custom_ui)

    rendered = str(prompt)

    assert custom_ui in rendered
    assert "<UI_INFORMATION>" in rendered
    assert "</UI_INFORMATION>" in rendered


def test_create_android_agent_prompt_default() -> None:
    """Test create_android_agent_prompt with default parameters."""
    prompt = create_android_agent_prompt()

    rendered = str(prompt)

    assert ANDROID_CAPABILITIES in rendered
    assert ANDROID_DEVICE_INFORMATION in rendered
    assert NO_REPORT_FORMAT in rendered
    assert ANDROID_RECOVERY_RULES in rendered


def test_create_android_agent_prompt_with_custom_ui_info() -> None:
    """Test create_android_agent_prompt with custom UI information."""
    custom_ui = "Mobile banking application"
    prompt = create_android_agent_prompt(ui_information=custom_ui)

    rendered = str(prompt)

    assert custom_ui in rendered
    assert "<UI_INFORMATION>" in rendered
    assert "</UI_INFORMATION>" in rendered


def test_create_android_agent_prompt_with_additional_rules() -> None:
    """Test create_android_agent_prompt with additional rules."""
    additional = "Always verify balance before transfers"
    prompt = create_android_agent_prompt(additional_rules=additional)

    rendered = str(prompt)

    # Both default and additional rules should be present
    assert ANDROID_RECOVERY_RULES in rendered
    assert additional in rendered
    assert "<ADDITIONAL_RULES>" in rendered


def test_prompt_constants_are_non_empty() -> None:
    """Test that all prompt constants are non-empty strings."""
    assert len(COMPUTER_USE_CAPABILITIES) > 0
    assert len(ANDROID_CAPABILITIES) > 0
    assert len(WEB_BROWSER_CAPABILITIES) > 0
    assert len(DESKTOP_DEVICE_INFORMATION) > 0
    assert len(ANDROID_DEVICE_INFORMATION) > 0
    assert len(WEB_AGENT_DEVICE_INFORMATION) > 0
    assert len(MD_REPORT_FORMAT) > 0
    assert len(NO_REPORT_FORMAT) > 0
    assert len(BROWSER_SPECIFIC_RULES) > 0
    assert len(BROWSER_INSTALL_RULES) > 0
    assert len(ANDROID_RECOVERY_RULES) > 0


def test_legacy_prompts_backward_compatibility() -> None:
    """Test that legacy string prompts still exist for backward compatibility."""
    # These should be strings, not ActSystemPrompt instances
    assert isinstance(COMPUTER_AGENT_SYSTEM_PROMPT, str)
    assert isinstance(WEB_AGENT_SYSTEM_PROMPT, str)
    assert isinstance(ANDROID_AGENT_SYSTEM_PROMPT, str)

    # And they should be non-empty
    assert len(COMPUTER_AGENT_SYSTEM_PROMPT) > 0
    assert len(WEB_AGENT_SYSTEM_PROMPT) > 0
    assert len(ANDROID_AGENT_SYSTEM_PROMPT) > 0


def test_act_system_prompt_is_pydantic_model() -> None:
    """Test that ActSystemPrompt is a proper Pydantic model."""
    prompt = ActSystemPrompt(
        system_capabilities="Test",
        device_information="Device",
    )

    # Should have Pydantic model methods
    assert hasattr(prompt, "model_dump")
    assert hasattr(prompt, "model_validate")

    # Test serialization
    data = prompt.model_dump()
    assert data["system_capabilities"] == "Test"
    assert data["device_information"] == "Device"

    # Test deserialization
    new_prompt = ActSystemPrompt.model_validate(data)
    assert new_prompt.system_capabilities == "Test"
    assert new_prompt.device_information == "Device"


def test_act_system_prompt_field_defaults() -> None:
    """Test that ActSystemPrompt has correct default values."""
    prompt = ActSystemPrompt()

    assert prompt.system_capabilities == ""
    assert prompt.device_information == ""
    assert prompt.ui_information == ""
    assert prompt.report_format == ""
    assert prompt.additional_rules == ""
