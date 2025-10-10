"""import_json_assistants

Revision ID: 057f82313448
Revises: 4d1e043b4254
Create Date: 2025-10-10 11:21:55.527341

"""

import json
import logging
from pathlib import Path
from typing import Annotated, Any, Literal, Sequence, Union
from uuid import UUID

from alembic import op
from pydantic import AwareDatetime, BaseModel, Field, PlainSerializer
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import MetaData, Table

# revision identifiers, used by Alembic.
revision: str = "057f82313448"
down_revision: Union[str, None] = "4d1e043b4254"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger(__name__)

# Local models to avoid dependencies on askui.chat.api
UnixDatetime = Annotated[
    AwareDatetime,
    PlainSerializer(
        lambda v: int(v.timestamp()),
        return_type=int,
    ),
]

AssistantId = Annotated[str, Field(pattern=r"^asst_[a-z0-9]+$")]
WorkspaceId = UUID


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ASKUI__CHAT_API__", env_nested_delimiter="__"
    )

    data_dir: Path = Field(
        default_factory=lambda: Path.cwd() / "chat",
        description="Base directory for chat data (used during migration)",
    )


class Assistant(BaseModel):
    id: AssistantId
    object: Literal["assistant"] = "assistant"
    created_at: UnixDatetime
    workspace_id: WorkspaceId | None = None
    name: str | None = None
    description: str | None = None
    avatar: str | None = None
    tools: list[str] = Field(default_factory=list)
    system: str | None = None

    def to_db_dict(self) -> dict[str, Any]:
        return {
            **self.model_dump(exclude={"id", "object", "workspace_id"}),
            "id": self.id.removeprefix("asst_"),
            "workspace_id": str(self.workspace_id) if self.workspace_id else None,
        }


BATCH_SIZE = 100


def _insert_assistants_batch(
    assistants_table: Table, assistants_batch: list[Assistant]
) -> None:
    """Insert a batch of assistants into the database."""
    op.bulk_insert(
        assistants_table,
        [assistant.to_db_dict() for assistant in assistants_batch],
    )


def upgrade() -> None:
    """Import existing assistants from JSON files."""
    settings = Settings()
    assistants_dir = settings.data_dir / "assistants"

    # Skip if directory doesn't exist (e.g., first-time setup)
    if not assistants_dir.exists():
        return

    # Get the table from the current database schema
    connection = op.get_bind()
    assistants_table = Table("assistants", MetaData(), autoload_with=connection)

    # Get all JSON files in the assistants directory
    json_files = list(assistants_dir.glob("*.json"))

    # Process assistants in batches
    assistants_batch: list[Assistant] = []

    for json_file in json_files:
        try:
            content = json_file.read_text(encoding="utf-8").strip()
            data = json.loads(content)
            assistant = Assistant.model_validate(data)
            assistants_batch.append(assistant)

            if len(assistants_batch) >= BATCH_SIZE:
                _insert_assistants_batch(assistants_table, assistants_batch)
                assistants_batch.clear()
        except Exception:  # noqa: PERF203
            error_msg = f"Failed to import {json_file}"
            logger.exception(error_msg)
            continue

    # Insert remaining assistants in the final batch
    if assistants_batch:
        _insert_assistants_batch(assistants_table, assistants_batch)


def downgrade() -> None:
    pass  # We don't remove the data
