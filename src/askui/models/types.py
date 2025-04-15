from typing import TypeVar
from pydantic import BaseModel, ConfigDict


class JsonSchemaBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


JsonSchema = TypeVar('JsonSchema', bound=JsonSchemaBase)
