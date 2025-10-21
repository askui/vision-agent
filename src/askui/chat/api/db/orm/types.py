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
FileId = create_prefixed_id_type("file")
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
