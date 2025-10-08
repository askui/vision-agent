"""Custom SQLAlchemy types for chat API."""

from typing import Any

from sqlalchemy import String, TypeDecorator


class PrefixedObjectId(TypeDecorator):
    """Custom type for storing BSON ObjectIds with prefixes in SQLite.

    Stores ObjectIds without prefix in the database. The service layer
    is responsible for adding/removing prefixes when converting to/from
    Pydantic models.
    """

    impl = String(24)
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> str | None:
        """Process value before storing in database."""
        if value is None:
            return value
        # Remove prefix before storing
        if isinstance(value, str) and "_" in value:
            return value.split("_", 1)[1]
        return str(value)

    def process_result_value(self, value: str | None, dialect: Any) -> str | None:
        """Process value when reading from database."""
        # Service layer will add prefix when converting to Pydantic
        return value


def create_prefixed_id_type(prefix: str) -> type[PrefixedObjectId]:
    """Create a specialized ObjectId type for a specific prefix.

    Args:
        prefix (str): The prefix to use (e.g., "asst", "thread").

    Returns:
        type[PrefixedObjectId]: A specialized type class.
    """

    class SpecializedPrefixedObjectId(PrefixedObjectId):
        """Specialized ObjectId type with prefix awareness."""

        cache_ok = True

        def process_result_value(self, value: str | None, dialect: Any) -> str | None:
            """Add prefix when reading from database."""
            if value is None:
                return value
            return f"{prefix}_{value}"

    return SpecializedPrefixedObjectId


# Specialized types for each resource
AssistantId = create_prefixed_id_type("asst")
ThreadId = create_prefixed_id_type("thread")
MessageId = create_prefixed_id_type("msg")
RunId = create_prefixed_id_type("run")
FileId = create_prefixed_id_type("file")
WorkflowId = create_prefixed_id_type("workflow")
McpConfigId = create_prefixed_id_type("mcp")
