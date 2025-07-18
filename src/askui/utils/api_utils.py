from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Generic, Literal, Sequence

from fastapi import Query
from pydantic import BaseModel, ValidationError
from typing_extensions import TypeVar

ListOrder = Literal["asc", "desc"]
LIST_LIMIT_MAX = 100


Id = TypeVar("Id", bound=str, default=str)


@dataclass(kw_only=True)
class ListQuery(Generic[Id]):
    limit: Annotated[int, Query(ge=1, le=LIST_LIMIT_MAX)] = 20
    after: Annotated[Id | None, Query()] = None
    before: Annotated[Id | None, Query()] = None
    order: Annotated[ListOrder, Query()] = "desc"


ObjectType = TypeVar("ObjectType", bound=BaseModel)


class ListResponse(BaseModel, Generic[ObjectType]):
    object: Literal["list"] = "list"
    data: Sequence[ObjectType]
    first_id: str | None = None
    last_id: str | None = None
    has_more: bool = False


class ApiError(Exception):
    pass


class ConflictError(ApiError):
    pass


class NotFoundError(ApiError):
    pass


def list_resource_paths(base_dir: Path, list_query: ListQuery) -> list[Path]:
    paths: list[Path] = []
    for f in base_dir.glob("*.json"):
        try:
            if list_query.after:
                if f.name <= list_query.after:
                    continue
            if list_query.before:
                if f.name >= list_query.before:
                    continue
            paths.append(f)
        except ValidationError:  # noqa: PERF203
            continue
    return sorted(paths, key=lambda f: f.name, reverse=(list_query.order == "desc"))
