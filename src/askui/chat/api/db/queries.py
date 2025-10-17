"""Shared query building utilities for database operations."""

from typing import Any, TypeVar

from sqlalchemy import desc
from sqlalchemy.orm import InstrumentedAttribute, Query

from askui.chat.api.db.orm.base import Base
from askui.utils.api_utils import ListQuery

OrmT = TypeVar("OrmT", bound=Base)


def list_all(
    db_query: Query[OrmT],
    list_query: ListQuery,
    id_column: InstrumentedAttribute[Any],
) -> tuple[list[OrmT], bool]:
    if list_query.order == "asc":
        if list_query.after:
            db_query = db_query.filter(id_column > list_query.after)
        if list_query.before:
            db_query = db_query.filter(id_column < list_query.before)
        db_query = db_query.order_by(id_column)
    else:
        if list_query.after:
            db_query = db_query.filter(id_column < list_query.after)
        if list_query.before:
            db_query = db_query.filter(id_column > list_query.before)
        db_query = db_query.order_by(desc(id_column))
    db_query = db_query.limit(list_query.limit + 1)
    orms = db_query.all()
    has_more = len(orms) > list_query.limit
    return orms[: list_query.limit], has_more
