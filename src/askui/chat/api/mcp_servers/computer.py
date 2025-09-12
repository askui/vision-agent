from typing import Annotated

from fastmcp import FastMCP
from fastmcp.utilities.types import Image
from PIL import Image as PILImage
from pydantic import BaseModel, Field

from askui.models.shared.settings import COMPUTER_USE_20250124_BETA_FLAG
from askui.tools.askui.askui_controller import AskUiControllerClient
from askui.tools.computer import (
    RESOLUTIONS_RECOMMENDED_BY_ANTHROPIC,
    Action20250124,
    Computer20250124Tool,
    ScrollDirection,
)
from askui.utils.image_utils import ImageSource

mcp = FastMCP(name="AskUI Computer MCP")

RESOLUTION = RESOLUTIONS_RECOMMENDED_BY_ANTHROPIC["WXGA"]

active_display = 1


@mcp.tool(
    description="Interact with your computer",
    tags={"computer"},
    meta={
        "betas": [COMPUTER_USE_20250124_BETA_FLAG],
        "params": {
            "name": "computer",
            "display_width_px": RESOLUTION.width,
            "display_height_px": RESOLUTION.height,
            "type": "computer_20250124",
        },
    },
)
def computer(
    action: Action20250124,
    text: str | None = None,
    coordinate: tuple[Annotated[int, Field(ge=0)], Annotated[int, Field(ge=0)]]
    | None = None,
    scroll_direction: ScrollDirection | None = None,
    scroll_amount: Annotated[int, Field(ge=0)] | None = None,
    duration: Annotated[float, Field(ge=0.0, le=100.0)] | None = None,
    key: str | None = None,
) -> Image | None | str:
    with AskUiControllerClient(display=active_display) as agent_os:
        result = Computer20250124Tool(agent_os=agent_os, resolution=RESOLUTION)(
            action=action,
            text=text,
            coordinate=coordinate,
            scroll_direction=scroll_direction,
            scroll_amount=scroll_amount,
            duration=duration,
            key=key,
        )
        if isinstance(result, PILImage.Image):
            src = ImageSource(result)
            return Image(data=src.to_bytes(), format="png")
        return result


class Display(BaseModel):
    id: int


class DisplayListResponse(BaseModel):
    data: list[Display]


@mcp.tool(description="List all available displays", tags={"computer"})
def list_displays() -> DisplayListResponse:
    with AskUiControllerClient(display=active_display) as agent_os:
        return DisplayListResponse(
            data=[Display(id=display.id) for display in agent_os.list_displays().data],
        )


@mcp.tool(
    description="Set the active display from which screenshots are taken / on which actions are performed (coordinates are relative to the active display)",
    tags={"computer"},
)
def set_active_display(
    display_id: Annotated[int, Field(ge=1)],
) -> None:
    global active_display
    active_display = display_id


@mcp.tool(
    description="Retrieve the active display from which screenshots are taken / on which actions are performed (coordinates are relative to the active display)",
    tags={"computer"},
)
def retrieve_active_display() -> Display:
    return Display(id=active_display)
