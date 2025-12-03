"""Custom SQLAlchemy types for chat API."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Integer, String, TypeDecorator


def create_prefixed_id_type(prefix: str) -> type[TypeDecorator[str]]:
    class PrefixedObjectId(TypeDecorator[str]):
        impl = String(24)
        cache_ok = True

        def process_bind_param(self, value: str | None, dialect: Any) -> str | None:  # noqa: ARG002
            if value is None:
                return value
            return value.removeprefix(f"{prefix}_")

        def process_result_value(self, value: str | None, dialect: Any) -> str | None:  # noqa: ARG002
            if value is None:
                return value
            return f"{prefix}_{value}"

    return PrefixedObjectId


# Specialized types for each resource
ThreadId = create_prefixed_id_type("thread")
MessageId = create_prefixed_id_type("msg")
RunId = create_prefixed_id_type("run")
WorkflowId = create_prefixed_id_type("workflow")


class UnixDatetime(TypeDecorator[datetime]):
    impl = Integer
    LOCAL_TIMEZONE = datetime.now().astimezone().tzinfo

    def process_bind_param(
        self,
        value: datetime | int | None,
        dialect: Any,  # noqa: ARG002
    ) -> int | None:
        if value is None:
            return value
        if isinstance(value, int):
            return value
        if value.tzinfo is None:
            value = value.astimezone(self.LOCAL_TIMEZONE)
        return int(value.astimezone(timezone.utc).timestamp())

    def process_result_value(
        self,
        value: int | None,
        dialect: Any,  # noqa: ARG002
    ) -> datetime | None:
        if value is None:
            return value
        return datetime.fromtimestamp(value, timezone.utc)


def create_sentinel_id_type(
    prefix: str, sentinel_value: str
) -> type[TypeDecorator[str]]:
    """Create a type decorator that converts between a sentinel value and NULL.

    This is useful for self-referential nullable foreign keys where NULL in the database
    is represented by a sentinel value in the API (e.g., root nodes in a tree structure).

    Args:
        prefix (str): The prefix for the ID (e.g., "msg").
        sentinel_value (str): The sentinel value representing NULL (e.g., "msg_000000000000000000000000").

    Returns:
        type[TypeDecorator[str]]: A TypeDecorator class that handles the transformation.

    Example:
        ```python
        ParentMessageId = create_sentinel_id_type("msg", ROOT_MESSAGE_PARENT_ID)
        parent_id: Mapped[str] = mapped_column(ParentMessageId, nullable=True)
        ```
    """

    class SentinelId(TypeDecorator[str]):
        """Type decorator that converts between sentinel value (API) and NULL (database).

        - When writing to DB: sentinel_value → NULL
        - When reading from DB: NULL → sentinel_value
        """

        impl = String(24)
        cache_ok = (
            False  # Disable caching due to closure over prefix and sentinel_value
        )

        def process_bind_param(
            self,
            value: str | None,
            dialect: Any,  # noqa: ARG002
        ) -> str | None:
            """Convert from API model to database storage."""
            if value is None or value == sentinel_value:
                # Both None and sentinel value become NULL in database
                return None
            # Remove prefix for storage (like regular PrefixedObjectId)
            return value.removeprefix(f"{prefix}_")

        def process_result_value(
            self,
            value: str | None,
            dialect: Any,  # noqa: ARG002
        ) -> str:
            """Convert from database storage to API model."""
            if value is None:
                # NULL in database becomes sentinel value in API
                return sentinel_value
            # Add prefix (like regular PrefixedObjectId)
            return f"{prefix}_{value}"

    return SentinelId
