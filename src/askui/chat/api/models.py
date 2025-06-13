from typing import Annotated, Generic, Literal, Sequence

from attr import dataclass
from fastapi import Depends, Query
from pydantic import AwareDatetime, BaseModel, PlainSerializer
from typing_extensions import TypeVar

UnixDatetime = Annotated[
    AwareDatetime,
    PlainSerializer(
        lambda v: int(v.timestamp()),
        return_type=int,
    ),
]


AssistantId = str
ListOrder = Literal["asc", "desc"]


MAX_MESSAGES_PER_THREAD = 100


@dataclass(kw_only=True)
class ListQuery:
    limit: Annotated[int, Query(ge=1, le=MAX_MESSAGES_PER_THREAD)] = 20
    after: Annotated[str | None, Query()] = None
    before: Annotated[str | None, Query()] = None
    order: Annotated[ListOrder, Query()] = "desc"


ListQueryDep = Depends(ListQuery)


ObjectType = TypeVar("ObjectType", bound=BaseModel)


class ListResponse(BaseModel, Generic[ObjectType]):
    object: Literal["list"] = "list"
    data: Sequence[ObjectType]
    first_id: str | None = None
    last_id: str | None = None
    has_more: bool = False


RunId = str
ThreadId = str
MODEL_DEFAULT = "gpt-4o"
ASSISTANT_ID_DEFAULT = "asst_ge3tiojsga3dgnruge3di2u5ov36shedkcslxnmca"
MessageId = str
FileId = str
