from pydantic import BaseModel, Field


class ActSystemPrompt(BaseModel):
    """
    System prompt for the Vision Agent's act command following the 5-part structure:
    1. System Capabilities - What the agent can do
    2. Device Information - Information about the device/platform
    3. UI Information - Information about the UI being operated
    4. Report Format - How to format the final report
    5. Additional Rules - Extra rules and guidelines
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
        description="If and how tu utilize cache files",
    )
    additional_rules: str = Field(
        default="",
        description="Additional rules and guidelines",
    )

    def __str__(self) -> str:
        """Render the prompt as a string with XML tags wrapping each part."""
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
