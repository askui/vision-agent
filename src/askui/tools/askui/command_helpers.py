from pydantic import Field, constr
from typing_extensions import Annotated, Union

from askui.tools.agent_os import Coordinate
from askui.tools.askui.askui_ui_controller_grpc.generated.AgentOS_Send_Request_2501 import (  # noqa: E501
    AddRenderObjectCommand,
    AskUIAgentOSSendRequestSchema,
    ClearRenderObjectsCommand,
    DeleteRenderObjectCommand,
    GetMousePositionCommand,
    Guid,
    Header,
    Length,
    Location2,
    Message,
    RenderImage,
    RenderLinePoints,
    RenderObjectId,
    RenderObjectStyle,
    RenderText,
    SetMousePositionCommand,
    UpdateRenderObjectCommand,
)

LengthType = Union[
    Annotated[str, constr(pattern=r"^(\d+(\.\d+)?(px|%)|auto)$")], int, float
]

ColorType = Union[
    Annotated[str, constr(pattern=r"^#([0-9a-fA-F]{6})$")],  # Hex color like #RRGGBB
    Annotated[
        str, constr(pattern=r"^rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)$")
    ],  # RGB color like rgb(255, 0, 128)
]


def create_style(
    top: LengthType | None = None,
    left: LengthType | None = None,
    bottom: LengthType | None = None,
    right: LengthType | None = None,
    width: LengthType | None = None,
    height: LengthType | None = None,
    color: ColorType | None = None,
    opacity: Annotated[float, Field(ge=0.0, le=1.0)] | None = None,
    visible: bool | None = None,
    font_size: LengthType | None = None,
    line_width: LengthType | None = None,
) -> RenderObjectStyle:
    """Create a style object with the specified properties."""

    return RenderObjectStyle.model_validate(
        {
            "top": top,
            "left": left,
            "bottom": bottom,
            "right": right,
            "width": width,
            "height": height,
            "color": color,
            "opacity": opacity,
            "visible": visible,
            "font-size": font_size,
            "line-width": line_width,
        }
    )


def create_get_mouse_position_command(
    session_guid: str,
) -> AskUIAgentOSSendRequestSchema:
    command = GetMousePositionCommand()

    header = Header(authentication=Guid(root=session_guid))
    message = Message(header=header, command=command)
    return AskUIAgentOSSendRequestSchema(message=message)


def create_set_mouse_position_command(
    x: int, y: int, session_guid: str
) -> AskUIAgentOSSendRequestSchema:
    location = Location2(x=Length(root=x), y=Length(root=y))
    command = SetMousePositionCommand(parameters=[location])

    header = Header(authentication=Guid(root=session_guid))
    message = Message(header=header, command=command)
    return AskUIAgentOSSendRequestSchema(message=message)


def create_quad_command(
    style: RenderObjectStyle, session_guid: str
) -> AskUIAgentOSSendRequestSchema:
    renderStyle = RenderObjectStyle(**style.model_dump(exclude_none=True))
    command = AddRenderObjectCommand(parameters=["Quad", renderStyle])

    header = Header(authentication=Guid(root=session_guid))
    message = Message(header=header, command=command)

    return AskUIAgentOSSendRequestSchema(message=message)


def create_line_command(
    style: RenderObjectStyle, points: list[Coordinate], session_guid: str
) -> AskUIAgentOSSendRequestSchema:
    command = AddRenderObjectCommand(
        parameters=["Line", style, create_render_line_points(points)],
    )

    header = Header(authentication=Guid(root=session_guid))
    message = Message(header=header, command=command)

    return AskUIAgentOSSendRequestSchema(message=message)


def create_image_command(
    style: RenderObjectStyle, image_data: str, session_guid: str
) -> AskUIAgentOSSendRequestSchema:
    image = RenderImage(root=image_data)
    command = AddRenderObjectCommand(parameters=["Image", style, image])

    header = Header(authentication=Guid(root=session_guid))
    message = Message(header=header, command=command)

    return AskUIAgentOSSendRequestSchema(message=message)


def create_text_command(
    style: RenderObjectStyle, text_content: str, session_guid: str
) -> AskUIAgentOSSendRequestSchema:
    text = RenderText(root=text_content)
    command = AddRenderObjectCommand(parameters=["Text", style, text])

    header = Header(authentication=Guid(root=session_guid))
    message = Message(header=header, command=command)

    return AskUIAgentOSSendRequestSchema(message=message)


def create_render_line_points(points: list[Coordinate]) -> RenderLinePoints:
    location_points = [
        Location2(x=Length(root=point.x), y=Length(root=point.y)) for point in points
    ]

    return RenderLinePoints(location_points)


def create_render_object_id(object_id: int) -> RenderObjectId:
    return RenderObjectId(root=object_id)


def create_update_render_object_command(
    object_id: int, style: RenderObjectStyle, session_guid: str
) -> AskUIAgentOSSendRequestSchema:
    command = UpdateRenderObjectCommand(parameters=[object_id, style])

    header = Header(authentication=Guid(root=session_guid))
    message = Message(header=header, command=command)

    return AskUIAgentOSSendRequestSchema(message=message)


def create_delete_render_object_command(
    object_id: int, session_guid: str
) -> AskUIAgentOSSendRequestSchema:
    render_object_id = RenderObjectId(root=object_id)
    command = DeleteRenderObjectCommand(parameters=[render_object_id])

    header = Header(authentication=Guid(root=session_guid))
    message = Message(header=header, command=command)

    return AskUIAgentOSSendRequestSchema(message=message)


def create_clear_render_objects_command(
    session_guid: str,
) -> AskUIAgentOSSendRequestSchema:
    command = ClearRenderObjectsCommand(parameters=[])

    header = Header(authentication=Guid(root=session_guid))
    message = Message(header=header, command=command)

    return AskUIAgentOSSendRequestSchema(message=message)
