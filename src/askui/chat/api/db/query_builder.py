"""Shared query building utilities for database operations."""

from typing import Any, Callable, TypeVar

from askui.utils.api_utils import ListQuery, ListResponse
from sqlalchemy import Column, desc
from sqlalchemy.orm import Query

ModelT = TypeVar("ModelT")


class QueryBuilder:
    """Builder for common database queries."""

    @staticmethod
    def apply_list_query(
        query: Query[ModelT],
        model_class: type[ModelT],
        list_query: ListQuery,
        created_at_column: Column[Any],
        id_column: Column[str] | None = None,
    ) -> Query[ModelT]:
        """Apply list query parameters to a SQLAlchemy query.

        Args:
            query (Query[ModelT]): The base query to modify.
            model_class (type[ModelT]): The model class for type hints.
            list_query (ListQuery): The list query parameters.
            created_at_column (Column[Any]): The created_at column for ordering.
            id_column (Column[str] | None): The ID column for pagination.

        Returns:
            Query[ModelT]: The modified query.
        """
        # Apply ordering using created_at
        if list_query.order == "desc":
            query = query.order_by(desc(created_at_column))
        else:
            query = query.order_by(created_at_column)

        # Apply pagination using created_at by looking up the created_at values
        # for the given IDs
        if list_query.after and id_column is not None:
            # Look up the created_at value for the after ID
            after_subquery = (
                query.session.query(created_at_column)
                .filter(id_column == list_query.after)
                .scalar_subquery()
            )

            if list_query.order == "desc":
                query = query.filter(created_at_column < after_subquery)
            else:
                query = query.filter(created_at_column > after_subquery)

        if list_query.before and id_column is not None:
            # Look up the created_at value for the before ID
            before_subquery = (
                query.session.query(created_at_column)
                .filter(id_column == list_query.before)
                .scalar_subquery()
            )

            if list_query.order == "desc":
                query = query.filter(created_at_column > before_subquery)
            else:
                query = query.filter(created_at_column < before_subquery)

        return query

    @staticmethod
    def build_list_response(
        results: list[ModelT],
        limit: int | None,
        to_pydantic_func: Callable[[ModelT], Any],
    ) -> ListResponse[Any]:
        """Build a ListResponse from query results.

        Args:
            results (list[ModelT]): The query results.
            limit (int | None): The limit that was applied.
            to_pydantic_func (Callable[[ModelT], Any]): Function to convert model to Pydantic.

        Returns:
            ListResponse[Any]: The list response.
        """
        has_more = len(results) > (limit or 20)
        if has_more:
            results = results[: limit or 20]

        data = [to_pydantic_func(result) for result in results]

        return ListResponse(
            data=data,
            has_more=has_more,
            first_id=data[0].id if data else None,
            last_id=data[-1].id if data else None,
        )
