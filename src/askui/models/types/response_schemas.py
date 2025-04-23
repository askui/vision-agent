from typing import Type, TypeVar, overload
from pydantic import BaseModel, ConfigDict, RootModel


class ResponseSchemaBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


String = RootModel[str]
Boolean = RootModel[bool]
Integer = RootModel[int]
Float = RootModel[float]


ResponseSchema = TypeVar('ResponseSchema', ResponseSchemaBase, str, bool, int, float)


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
def to_response_schema(response_schema: Type[ResponseSchemaBase]) -> Type[ResponseSchemaBase]: ...
def to_response_schema(response_schema: Type[ResponseSchemaBase] | Type[str] | Type[bool] | Type[int] | Type[float] | None = None) -> Type[ResponseSchemaBase] | Type[String] | Type[Boolean] | Type[Integer] | Type[Float]:
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
    raise ValueError(f"Invalid response schema type: {response_schema}")
