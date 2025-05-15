from typing import Type, TypeVar, overload

from pydantic import BaseModel, ConfigDict, RootModel


class ResponseSchemaBase(BaseModel):
    """Response schemas for defining the response of data extraction, e.g., using
    `askui.VisionAgent.get()`.

    This class extends Pydantic's `BaseModel` and adds constraints and configuration
    on top so that it can be used with models to define the schema (type) of
    the data to be extracted.

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
        ```
    """

    model_config = ConfigDict(extra="forbid")


String = RootModel[str]
Boolean = RootModel[bool]
Integer = RootModel[int]
Float = RootModel[float]


ResponseSchema = TypeVar("ResponseSchema", ResponseSchemaBase, str, bool, int, float)
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
def to_response_schema(response_schema: None) -> Type[String]: ...
@overload
def to_response_schema(response_schema: Type[str]) -> Type[String]: ...
@overload
def to_response_schema(response_schema: Type[bool]) -> Type[Boolean]: ...
@overload
def to_response_schema(response_schema: Type[int]) -> Type[Integer]: ...
@overload
def to_response_schema(response_schema: Type[float]) -> Type[Float]: ...
@overload
def to_response_schema(
    response_schema: Type[ResponseSchemaBase],
) -> Type[ResponseSchemaBase]: ...
def to_response_schema(
    response_schema: Type[ResponseSchemaBase]
    | Type[str]
    | Type[bool]
    | Type[int]
    | Type[float]
    | None = None,
) -> (
    Type[ResponseSchemaBase]
    | Type[String]
    | Type[Boolean]
    | Type[Integer]
    | Type[Float]
):
    if response_schema is None:
        return String
    if response_schema is str:
        return String
    if response_schema is bool:
        return Boolean
    if response_schema is int:
        return Integer
    if response_schema is float:
        return Float
    if issubclass(response_schema, ResponseSchemaBase):
        return response_schema
    error_msg = f"Invalid response schema type: {response_schema}"
    raise ValueError(error_msg)
