from pydantic import Field, constr
from typing_extensions import Annotated, Union

from askui.tools.agent_os import Coordinate
from askui.tools.askui.askui_ui_controller_grpc.generated.AgentOS_Send_Request_2501 import (  # noqa: E501
    AskuiAgentosSendRequestSchema,
    Command,
    Command1,
    Command2,
    Command3,
    Command4,
    Command5,
    Guid,
    Header,
    Length,
    Location2,
    Message,
    Name,
    Name1,
    Name2,
    Name3,
    Name4,
    Name5,
    RenderImage,
    RenderLinePoints,
    RenderObjectId,
    RenderObjectStyle,
    RenderText,
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
) -> AskuiAgentosSendRequestSchema:
    command = Command(name=Name.GetMousePosition)

    header = Header(authentication=Guid(root=session_guid))
    message = Message(header=header, command=command)
    return AskuiAgentosSendRequestSchema(message=message)


def create_set_mouse_position_command(
    x: int, y: int, session_guid: str
) -> AskuiAgentosSendRequestSchema:
    location = Location2(x=Length(root=x), y=Length(root=y))
    command = Command1(name=Name1.SetMousePosition, parameters=[location])

    header = Header(authentication=Guid(root=session_guid))
    message = Message(header=header, command=command)
    return AskuiAgentosSendRequestSchema(message=message)


def create_quad_command(
    style: RenderObjectStyle, session_guid: str
) -> AskuiAgentosSendRequestSchema:
    renderStyle = RenderObjectStyle(**style.model_dump(exclude_none=True))
    command = Command2(name=Name2.AddRenderObject, parameters=["Quad", renderStyle])

    header = Header(authentication=Guid(root=session_guid))
    message = Message(header=header, command=command)

    return AskuiAgentosSendRequestSchema(message=message)


def create_line_command(
    style: RenderObjectStyle, points: list[Coordinate], session_guid: str
) -> AskuiAgentosSendRequestSchema:
    command = Command2(
        name=Name2.AddRenderObject,
        parameters=["Line", style, create_render_line_points(points)],
    )

    header = Header(authentication=Guid(root=session_guid))
    message = Message(header=header, command=command)

    return AskuiAgentosSendRequestSchema(message=message)


def create_image_command(
    style: RenderObjectStyle, image_data: str, session_guid: str
) -> AskuiAgentosSendRequestSchema:
    image = RenderImage(root=image_data)
    command = Command2(name=Name2.AddRenderObject, parameters=["Image", style, image])

    header = Header(authentication=Guid(root=session_guid))
    message = Message(header=header, command=command)

    return AskuiAgentosSendRequestSchema(message=message)


def create_text_command(
    style: RenderObjectStyle, text_content: str, session_guid: str
) -> AskuiAgentosSendRequestSchema:
    text = RenderText(root=text_content)
    command = Command2(name=Name2.AddRenderObject, parameters=["Text", style, text])

    header = Header(authentication=Guid(root=session_guid))
    message = Message(header=header, command=command)

    return AskuiAgentosSendRequestSchema(message=message)


def create_render_line_points(points: list[Coordinate]) -> RenderLinePoints:
    location_points = [
        Location2(x=Length(root=point.x), y=Length(root=point.y)) for point in points
    ]

    return RenderLinePoints(location_points)


def create_render_object_id(object_id: int) -> RenderObjectId:
    return RenderObjectId(root=object_id)


def create_update_render_object_command(
    object_id: int, style: RenderObjectStyle, session_guid: str
) -> AskuiAgentosSendRequestSchema:
    command = Command3(name=Name3.UpdateRenderObject, parameters=[object_id, style])

    header = Header(authentication=Guid(root=session_guid))
    message = Message(header=header, command=command)

    return AskuiAgentosSendRequestSchema(message=message)


def create_delete_render_object_command(
    object_id: int, session_guid: str
) -> AskuiAgentosSendRequestSchema:
    render_object_id = create_render_object_id(object_id)
    command = Command4(name=Name4.DeleteRenderObject, parameters=[render_object_id])

    header = Header(authentication=Guid(root=session_guid))
    message = Message(header=header, command=command)

    return AskuiAgentosSendRequestSchema(message=message)


def create_clear_render_objects_command(
    session_guid: str,
) -> AskuiAgentosSendRequestSchema:
    command = Command5(name=Name5.ClearRenderObjects, parameters=[])

    header = Header(authentication=Guid(root=session_guid))
    message = Message(header=header, command=command)

    return AskuiAgentosSendRequestSchema(message=message)
