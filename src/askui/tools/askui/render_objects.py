from typing import Literal, TypedDict, Union

from typing_extensions import NotRequired

Length = Union[int, float, str]
Color = str


class Location(TypedDict):
    x: Length
    y: Length


class RenderObjectStyle(TypedDict, total=False):
    """Style properties for render objects."""

    top: NotRequired[Length]
    left: NotRequired[Length]
    bottom: NotRequired[Length]
    right: NotRequired[Length]
    width: NotRequired[Length]
    height: NotRequired[Length]
    color: NotRequired[Color]
    opacity: NotRequired[float]
    visible: NotRequired[bool]
    font_size: NotRequired[Length]
    line_width: NotRequired[Length]


class QuadRenderObject(TypedDict):
    """Quad render object with no additional parameters."""

    type: Literal["Quad"]


class LineRenderObject(TypedDict):
    """Line render object with points array."""

    type: Literal["Line"]
    points: list[Location]


class ImageRenderObject(TypedDict):
    """Image render object with base64 bitmap data."""

    type: Literal["Image"]
    bitmap_data: str


class TextRenderObject(TypedDict):
    """Text render object with text content."""

    type: Literal["Text"]
    text: str


RenderObject = Union[
    QuadRenderObject, LineRenderObject, ImageRenderObject, TextRenderObject
]


class GetMousePositionCommand(TypedDict):
    """Get mouse position command."""

    name: Literal["GetMousePosition"]
    parameters: list[None]


class SetMousePositionCommand(TypedDict):
    """Set mouse position command."""

    name: Literal["SetMousePosition"]
    parameters: list[Location]


class AddRenderObjectCommand(TypedDict):
    """Add render object command."""

    name: Literal["AddRenderObject"]
    parameters: list[Union[str, dict[str, object], list[Location]]]


class UpdateRenderObjectCommand(TypedDict):
    """Update render object command."""

    name: Literal["UpdateRenderObject"]
    parameters: list[Union[int, dict[str, object], list[Location], str]]


class DeleteRenderObjectCommand(TypedDict):
    """Delete render object command."""

    name: Literal["DeleteRenderObject"]
    parameters: list[int]


class ClearRenderObjectsCommand(TypedDict):
    """Clear all render objects command."""

    name: Literal["ClearRenderObjects"]
    parameters: list[None]


RenderCommand = Union[
    GetMousePositionCommand,
    SetMousePositionCommand,
    AddRenderObjectCommand,
    UpdateRenderObjectCommand,
    DeleteRenderObjectCommand,
    ClearRenderObjectsCommand,
]


class MousePositionData(TypedDict):
    """Mouse position response data."""

    position: Location


class RenderObjectIdData(TypedDict):
    """Render object ID response data."""

    id: int


class CommandResponse(TypedDict):
    """Base response for commands."""

    name: str
    actionId: int


class AddRenderObjectResponse(TypedDict):
    """Response for AddRenderObject command."""

    name: Literal["AddRenderObject"]
    actionId: int
    response: RenderObjectIdData


class UpdateRenderObjectResponse(TypedDict):
    """Response for UpdateRenderObject command."""

    name: Literal["UpdateRenderObject"]
    actionId: int


class DeleteRenderObjectResponse(TypedDict):
    """Response for DeleteRenderObject command."""

    name: Literal["DeleteRenderObject"]
    actionId: int


class ClearRenderObjectsResponse(TypedDict):
    """Response for ClearRenderObjects command."""

    name: Literal["ClearRenderObjects"]
    actionId: int


class GetMousePositionResponse(TypedDict):
    """Response for GetMousePosition command."""

    name: Literal["GetMousePosition"]
    actionId: int
    response: MousePositionData


class SetMousePositionResponse(TypedDict):
    """Response for SetMousePosition command."""

    name: Literal["SetMousePosition"]
    actionId: int


RenderCommandResponse = Union[
    GetMousePositionResponse,
    AddRenderObjectResponse,
    UpdateRenderObjectResponse,
    DeleteRenderObjectResponse,
    ClearRenderObjectsResponse,
    SetMousePositionResponse,
]


class RenderMessage(TypedDict):
    """Message structure for render object API."""

    header: dict[str, str]
    command: RenderCommand


class ResponseCommandWrapper(TypedDict):
    """Command wrapper for response messages."""

    command: RenderCommandResponse


class RenderResponseMessage(TypedDict):
    """Response message structure."""

    message: ResponseCommandWrapper


def create_quad_command(style: RenderObjectStyle) -> AddRenderObjectCommand:
    """Create a Quad render object command."""
    transformed_style = transform_style_for_serialization(style)
    return {
        "name": "AddRenderObject",
        "parameters": ["Quad", transformed_style],
    }


def create_line_command(
    style: RenderObjectStyle, points: list[Location]
) -> AddRenderObjectCommand:
    """Create a Line render object command."""
    transformed_style = transform_style_for_serialization(style)
    return {
        "name": "AddRenderObject",
        "parameters": ["Line", transformed_style, points],
    }


def create_image_command(
    style: RenderObjectStyle, bitmap_data: str
) -> AddRenderObjectCommand:
    """Create an Image render object command."""
    transformed_style = transform_style_for_serialization(style)
    return {
        "name": "AddRenderObject",
        "parameters": ["Image", transformed_style, bitmap_data],
    }


def create_text_command(style: RenderObjectStyle, text: str) -> AddRenderObjectCommand:
    """Create a Text render object command."""
    transformed_style = transform_style_for_serialization(style)
    return {
        "name": "AddRenderObject",
        "parameters": ["Text", transformed_style, text],
    }


def create_get_mouse_position_command() -> GetMousePositionCommand:
    """Create a GetMousePosition command."""
    return {"name": "GetMousePosition", "parameters": []}


def create_set_mouse_position_command(x: Length, y: Length) -> SetMousePositionCommand:
    """Create a SetMousePosition command."""
    return {"name": "SetMousePosition", "parameters": [{"x": x, "y": y}]}


def create_update_render_object_command(
    object_id: int,
    style: RenderObjectStyle,
    additional_params: Union[list[Location], str, None] = None,
) -> UpdateRenderObjectCommand:
    """Create an UpdateRenderObject command."""
    transformed_style = transform_style_for_serialization(style)
    parameters: list[Union[int, dict[str, object], list[Location], str]] = [
        object_id,
        transformed_style,
    ]
    if additional_params is not None:
        parameters.append(additional_params)
    return {"name": "UpdateRenderObject", "parameters": parameters}


def create_delete_render_object_command(object_id: int) -> DeleteRenderObjectCommand:
    """Create a DeleteRenderObject command."""
    return {"name": "DeleteRenderObject", "parameters": [object_id]}


def create_clear_render_objects_command() -> ClearRenderObjectsCommand:
    """Create a ClearRenderObjects command."""
    return {"name": "ClearRenderObjects", "parameters": []}


def create_style(
    top: Length | None = None,
    left: Length | None = None,
    bottom: Length | None = None,
    right: Length | None = None,
    width: Length | None = None,
    height: Length | None = None,
    color: Color | None = None,
    opacity: float | None = None,
    visible: bool | None = None,
    font_size: Length | None = None,
    line_width: Length | None = None,
) -> RenderObjectStyle:
    """Create a style object with the specified properties."""
    style = RenderObjectStyle()
    args_to_process = {
        "top": top,
        "left": left,
        "bottom": bottom,
        "right": right,
        "width": width,
        "height": height,
        "color": color,
        "opacity": opacity,
        "visible": visible,
        "font_size": font_size,
        "line_width": line_width,
    }

    for key, value in args_to_process.items():
        if value is not None:
            style[key] = value  # type: ignore[literal-required]
    return style


def transform_style_for_serialization(
    style: RenderObjectStyle,
) -> dict[str, object]:
    """
    Transform style keys from snake_case to kebab-case for serialization.

    Args:
        style (RenderObjectStyle): The style object to transform.

    Returns:
        dict[str, object]: A new dictionary with transformed keys.
    """
    key_mapping = {
        "font_size": "font-size",
        "line_width": "line-width",
    }

    transformed_style: dict[str, object] = {}
    for k, v in style.items():
        transformed_key = key_mapping.get(k, k)
        transformed_style[transformed_key] = v

    return transformed_style


def create_location(x: Length, y: Length) -> Location:
    return {"x": x, "y": y}
