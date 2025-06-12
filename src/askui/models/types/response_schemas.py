from typing import Type, TypeVar, overload

from pydantic import BaseModel, ConfigDict, RootModel


class ResponseSchemaBase(BaseModel):
    """Response schemas for defining the response of data extraction, e.g., using
    `askui.VisionAgent.get()`.

    This class extends Pydantic's `BaseModel` and adds constraints and configuration
    on top so that it can be used with models to define the schema (type) of
    the data to be extracted.

    **Important**: Default values are not supported, e.g., `url: str = "github.com"` or
    `url: str | None = None`. This includes `default_factory` and `default` args
    of `pydantic.Field` as well, e.g., `url: str = Field(default="github.com")` or
    `url: str = Field(default_factory=lambda: "github.com")`.

    Example:
        ```python
        class UrlResponse(ResponseSchemaBase):
            url: str

        # nested models should also extend ResponseSchemaBase
        class NestedResponse(ResponseSchemaBase):
            nested: UrlResponse

        # metadata, e.g., `examples` or `description` of `Field`, is generally also
        # passed to and considered by the models
        class UrlResponse(ResponseSchemaBase):
            url: str = Field(
                description="The URL of the response. Should used `\"https\"` scheme.",
                examples=["https://www.example.com"]
            )

        # To define recursive response schemas, you can use quotation marks around the
        # type of the field, e.g., `next: "LinkedListNode | None"`.
        class LinkedListNode(ResponseSchemaBase):
            value: str
            next: "LinkedListNode | None"
        ```
    """

    model_config = ConfigDict(extra="forbid")


ResponseSchema = TypeVar(
    "ResponseSchema",
    bound=ResponseSchemaBase | str | bool | int | float,
)
"""Type of the responses of data extracted, e.g., using `askui.VisionAgent.get()`.

The following types are allowed:
- `ResponseSchemaBase`: Custom Pydantic models that extend `ResponseSchemaBase`
- `str`: String responses
- `bool`: Boolean responses
- `int`: Integer responses
- `float`: Floating point responses

Usually, serialized as a JSON schema, e.g., `str` as `{"type": "string"}`, to be
passed to model(s). Also used for validating the responses of the model(s) used for
data extraction.
"""


@overload
def to_response_schema(response_schema: None) -> Type[RootModel[str]]: ...
@overload
def to_response_schema(
    response_schema: Type[ResponseSchema],
) -> Type[RootModel[ResponseSchema]]: ...
def to_response_schema(
    response_schema: Type[ResponseSchema] | None,
) -> Type[RootModel[str]] | Type[RootModel[ResponseSchema]]:
    if response_schema is None:
        return RootModel[str]
    return RootModel[response_schema]  # type: ignore[valid-type]
