import warnings

from pydantic import BaseModel, Field, model_validator


class SystemPrompt(BaseModel):
    """Base class for system prompts."""

    prompt: str = Field(default="", description="The system prompt")

    def __str__(self) -> str:
        return self.prompt


class GetSystemPrompt(SystemPrompt, BaseModel):
    prompt: str = Field(default="", description="The system prompt for the GetModel")


class LocateSystemPrompt(SystemPrompt, BaseModel):
    prompt: str = Field(default="", description="The system prompt for the LocateModel")


class ActSystemPrompt(SystemPrompt, BaseModel):
    """
    System prompt for the Vision Agent's act command following the 6-part structure:
    1. System Capabilities - What the agent can do
    2. Device Information - Information about the device/platform
    3. UI Information - Information about the UI being operated
    4. Report Format - How to format the final report
    5. Cache Use - How to use cache files
    6. Additional Rules - Extra rules and guidelines
    """

    system_capabilities: str = Field(
        default="",
        description="What the agent can do and how it should behave",
    )
    device_information: str = Field(
        default="",
        description="Information about the device or platform being operated",
    )
    ui_information: str = Field(
        default="",
        description="Information about the UI being operated",
    )
    report_format: str = Field(
        default="",
        description="How to format the final report",
    )
    cache_use: str = Field(
        default="",
        description="If and how to utilize cache files",
    )
    additional_rules: str = Field(
        default="",
        description="Additional rules and guidelines",
    )

    @model_validator(mode="after")
    def warn_on_prompt_override(self) -> "ActSystemPrompt":
        """Warn if the inherited prompt field is used as a power user override."""
        if self.prompt:
            warnings.warn(
                "Using the 'prompt' field is not recommended for the ActSystemPrompt"
                " and might lead to unexpected behavior. This field is intended for"
                " power users only and overrides all other prompt parts.",
                UserWarning,
                stacklevel=2,
            )
        return self

    def __str__(self) -> str:
        """Render the prompt as a string with XML tags wrapping each part."""
        # If the prompt field is used, return it directly and ignore all other fields
        if self.prompt:
            return self.prompt

        parts = []

        if self.system_capabilities:
            parts.append(
                f"<SYSTEM_CAPABILITIES>\n{self.system_capabilities}\n</SYSTEM_CAPABILITIES>"
            )

        if self.device_information:
            parts.append(
                f"<DEVICE_INFORMATION>\n{self.device_information}\n</DEVICE_INFORMATION>"
            )

        if self.ui_information:
            parts.append(f"<UI_INFORMATION>\n{self.ui_information}\n</UI_INFORMATION>")

        if self.report_format:
            parts.append(f"<REPORT_FORMAT>\n{self.report_format}\n</REPORT_FORMAT>")

        if self.cache_use:
            parts.append(f"<CACHE_USE>\n{self.cache_use}\n</CACHE_USE>")

        if self.additional_rules:
            parts.append(
                f"<ADDITIONAL_RULES>\n{self.additional_rules}\n</ADDITIONAL_RULES>"
            )

        return "\n\n".join(parts)
