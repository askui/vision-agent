"""import_json_files

Revision ID: 9e0f1a2b3c4d
Revises: 8d9e0f1a2b3c
Create Date: 2025-01-27 11:01:00.000000

"""

import json
import logging
import mimetypes
from typing import Sequence, Union

from alembic import op
from sqlalchemy import MetaData, Table

from askui.chat.migrations.shared.files.models import FileV1
from askui.chat.migrations.shared.settings import SettingsV1

# revision identifiers, used by Alembic.
revision: str = "9e0f1a2b3c4d"
down_revision: Union[str, None] = "8d9e0f1a2b3c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger(__name__)


BATCH_SIZE = 100


def _insert_files_batch(files_table: Table, files_batch: list[FileV1]) -> None:
    """Insert a batch of files into the database."""
    op.bulk_insert(
        files_table,
        [file.to_db_dict() for file in files_batch],
    )


settings = SettingsV1()
workspaces_dir = settings.data_dir / "workspaces"


def upgrade() -> None:  # noqa: C901
    """Import existing files from JSON files in workspace static directories."""

    # Skip if workspaces directory doesn't exist (e.g., first-time setup)
    if not workspaces_dir.exists():
        return

    # Get the table from the current database schema
    connection = op.get_bind()
    files_table = Table("files", MetaData(), autoload_with=connection)

    # Process files in batches
    files_batch: list[FileV1] = []

    # Iterate through all workspace directories
    for workspace_dir in workspaces_dir.iterdir():
        if not workspace_dir.is_dir():
            continue

        workspace_id = workspace_dir.name
        files_dir = workspace_dir / "files"

        if not files_dir.exists():
            continue

        # Get all JSON files in the static directory
        json_files = list(files_dir.glob("*.json"))

        for json_file in json_files:
            try:
                content = json_file.read_text(encoding="utf-8").strip()
                data = json.loads(content)
                file = FileV1.model_validate({**data, "workspace_id": workspace_id})
                files_batch.append(file)
                if len(files_batch) >= BATCH_SIZE:
                    _insert_files_batch(files_table, files_batch)
                    files_batch.clear()
            except Exception:  # noqa: PERF203
                error_msg = "Failed to import file"
                logger.exception(error_msg, extra={"json_file": str(json_file)})
                continue

    # Insert remaining files in the final batch
    if files_batch:
        _insert_files_batch(files_table, files_batch)


def downgrade() -> None:
    """Recreate JSON files for files during downgrade."""

    connection = op.get_bind()
    files_table = Table("files", MetaData(), autoload_with=connection)

    # Fetch all files from the database
    result = connection.execute(files_table.select())
    rows = result.fetchall()
    if not rows:
        return

    for row in rows:
        try:
            file_model: FileV1 = FileV1.model_validate(row, from_attributes=True)
            if file_model.workspace_id:
                files_dir = workspaces_dir / str(file_model.workspace_id) / "files"
            else:
                files_dir = settings.data_dir / "files"
            files_dir.mkdir(parents=True, exist_ok=True)
            json_path = files_dir / f"{file_model.id}.json"
            if json_path.exists():
                continue
            with json_path.open("w", encoding="utf-8") as f:
                f.write(json.dumps(file_model.model_dump()))
        except Exception as e:  # noqa: PERF203
            error_msg = f"Failed to export row to json: {e}"
            logger.exception(error_msg, extra={"row": str(row)}, exc_info=e)
            continue
