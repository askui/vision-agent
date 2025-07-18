from typing import Any, ClassVar
from uuid import uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    SerializerFunctionWrapHandler,
    model_serializer,
)


class NotGiven(BaseModel):
    """
    A sentinel value that represents a value that is not given.
    """

    model_config = ConfigDict(frozen=True)

    _uuid: ClassVar[str] = str(uuid4())
    _instance: ClassVar["NotGiven | None"] = None

    def __new__(cls) -> "NotGiven":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "NOT_GIVEN"

    def __str__(self) -> str:
        return "NOT_GIVEN"

    def __bool__(self) -> bool:
        return False

    @model_serializer
    def serialize(self) -> str:
        return f"NOT_GIVEN<{self._uuid}>"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return other == self.serialize()
        return isinstance(other, NotGiven)


NOT_GIVEN = NotGiven()


class BaseModelWithNotGiven(BaseModel):
    @model_serializer(mode="wrap", when_used="always")
    def serialize_with_not_given(self, nxt: SerializerFunctionWrapHandler) -> Any:
        serialized: dict[Any, Any] | Any = nxt(self)
        if isinstance(serialized, dict):
            return {k: v for k, v in serialized.items() if v != NOT_GIVEN}
        return serialized
