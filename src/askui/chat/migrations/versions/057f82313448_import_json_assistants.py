"""import_json_assistants

Revision ID: 057f82313448
Revises: 4d1e043b4254
Create Date: 2025-10-10 11:21:55.527341

"""

import json
import logging
from typing import Sequence, Union

from alembic import op
from sqlalchemy import Connection, MetaData, Table

from askui.chat.migrations.shared.assistants.models import AssistantV1
from askui.chat.migrations.shared.settings import SettingsV1

# revision identifiers, used by Alembic.
revision: str = "057f82313448"
down_revision: Union[str, None] = "4d1e043b4254"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger(__name__)


BATCH_SIZE = 1000


def _insert_assistants_batch(
    connection: Connection, assistants_table: Table, assistants_batch: list[AssistantV1]
) -> None:
    """Insert a batch of assistants into the database, ignoring conflicts."""
    if not assistants_batch:
        return

    connection.execute(
        assistants_table.insert().prefix_with("OR REPLACE"),
        [assistant.to_db_dict() for assistant in assistants_batch],
    )


settings = SettingsV1()
assistants_dir = settings.data_dir / "assistants"


def upgrade() -> None:
    """Import existing assistants from JSON files."""

    # Skip if directory doesn't exist (e.g., first-time setup)
    if not assistants_dir.exists():
        return

    # Get the table from the current database schema
    connection = op.get_bind()
    assistants_table = Table("assistants", MetaData(), autoload_with=connection)

    # Get all JSON files in the assistants directory
    json_files = list(assistants_dir.glob("*.json"))

    # Process assistants in batches
    assistants_batch: list[AssistantV1] = []

    for json_file in json_files:
        try:
            content = json_file.read_text(encoding="utf-8").strip()
            data = json.loads(content)
            assistant = AssistantV1.model_validate(data)
            assistants_batch.append(assistant)

            if len(assistants_batch) >= BATCH_SIZE:
                _insert_assistants_batch(connection, assistants_table, assistants_batch)
                assistants_batch.clear()
        except Exception:  # noqa: PERF203
            error_msg = "Failed to import"
            logger.exception(error_msg, extra={"json_file": str(json_file)})
            continue

    # Insert remaining assistants in the final batch
    if assistants_batch:
        _insert_assistants_batch(connection, assistants_table, assistants_batch)


def downgrade() -> None:
    """Recreate JSON files for assistants during downgrade."""

    assistants_dir.mkdir(parents=True, exist_ok=True)

    connection = op.get_bind()
    assistants_table = Table("assistants", MetaData(), autoload_with=connection)

    # Fetch all assistants from the database
    result = connection.execute(assistants_table.select())
    rows = result.fetchall()
    if not rows:
        return

    for row in rows:
        try:
            assistant: AssistantV1 = AssistantV1.model_validate(
                row, from_attributes=True
            )
            json_path = assistants_dir / f"{assistant.id}.json"
            if json_path.exists():
                continue
            with json_path.open("w", encoding="utf-8") as f:
                f.write(assistant.model_dump_json())
        except Exception as e:  # noqa: PERF203
            error_msg = f"Failed to export row to json: {e}"
            logger.exception(error_msg, extra={"row": str(row)}, exc_info=e)
            continue
