"""import_json_threads

Revision ID: 4d5e6f7a8b9c
Revises: 3c4d5e6f7a8b
Create Date: 2025-01-27 12:03:00.000000

"""

import json
import logging
from typing import Sequence, Union

from alembic import op
from sqlalchemy import Connection, MetaData, Table

from askui.chat.migrations.shared.settings import SettingsV1
from askui.chat.migrations.shared.threads.models import ThreadV1

# revision identifiers, used by Alembic.
revision: str = "4d5e6f7a8b9c"
down_revision: Union[str, None] = "3c4d5e6f7a8b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger(__name__)


BATCH_SIZE = 1000


def _insert_threads_batch(
    connection: Connection, threads_table: Table, threads_batch: list[ThreadV1]
) -> None:
    """Insert a batch of threads into the database, ignoring conflicts."""
    if not threads_batch:
        return

    connection.execute(
        threads_table.insert().prefix_with("OR REPLACE"),
        [thread.to_db_dict() for thread in threads_batch],
    )


settings = SettingsV1()
workspaces_dir = settings.data_dir / "workspaces"


def upgrade() -> None:  # noqa: C901
    """Import existing threads from JSON files in workspace directories."""

    # Skip if workspaces directory doesn't exist (e.g., first-time setup)
    if not workspaces_dir.exists():
        return

    # Get the table from the current database schema
    connection = op.get_bind()
    threads_table = Table("threads", MetaData(), autoload_with=connection)

    # Process threads in batches
    threads_batch: list[ThreadV1] = []

    # Iterate through all workspace directories
    for workspace_dir in workspaces_dir.iterdir():
        if not workspace_dir.is_dir():
            continue

        workspace_id = workspace_dir.name
        threads_dir = workspace_dir / "threads"

        if not threads_dir.exists():
            continue

        # Get all JSON files in the threads directory
        json_files = list(threads_dir.glob("*.json"))

        for json_file in json_files:
            try:
                content = json_file.read_text(encoding="utf-8").strip()
                data = json.loads(content)
                thread = ThreadV1.model_validate({**data, "workspace_id": workspace_id})
                threads_batch.append(thread)
                if len(threads_batch) >= BATCH_SIZE:
                    _insert_threads_batch(connection, threads_table, threads_batch)
                    threads_batch.clear()
            except Exception:  # noqa: PERF203
                error_msg = "Failed to import thread"
                logger.exception(error_msg, extra={"json_file": str(json_file)})
                continue

    # Insert remaining threads in the final batch
    if threads_batch:
        _insert_threads_batch(connection, threads_table, threads_batch)


def downgrade() -> None:
    """Recreate JSON files for threads during downgrade."""

    connection = op.get_bind()
    threads_table = Table("threads", MetaData(), autoload_with=connection)

    # Fetch all threads from the database
    result = connection.execute(threads_table.select())
    rows = result.fetchall()
    if not rows:
        return

    for row in rows:
        try:
            thread_model: ThreadV1 = ThreadV1.model_validate(row, from_attributes=True)
            threads_dir = workspaces_dir / str(thread_model.workspace_id) / "threads"
            threads_dir.mkdir(parents=True, exist_ok=True)
            json_path = threads_dir / f"{thread_model.id}.json"
            if json_path.exists():
                continue
            with json_path.open("w", encoding="utf-8") as f:
                f.write(thread_model.model_dump_json())
        except Exception as e:  # noqa: PERF203
            error_msg = f"Failed to export row to json: {e}"
            logger.exception(error_msg, extra={"row": str(row)}, exc_info=e)
            continue
