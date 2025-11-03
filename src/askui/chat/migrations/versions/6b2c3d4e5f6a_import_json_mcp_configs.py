"""import_json_mcp_configs

Revision ID: 6b2c3d4e5f6a
Revises: 5a1b2c3d4e5f
Create Date: 2025-01-27 10:01:00.000000

"""

import json
import logging
from typing import Sequence, Union

from alembic import op
from sqlalchemy import Connection, MetaData, Table

from askui.chat.migrations.shared.mcp_configs.models import McpConfigV1
from askui.chat.migrations.shared.settings import SettingsV1

# revision identifiers, used by Alembic.
revision: str = "6b2c3d4e5f6a"
down_revision: Union[str, None] = "5a1b2c3d4e5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger(__name__)


BATCH_SIZE = 1000


def _insert_mcp_configs_batch(
    connection: Connection,
    mcp_configs_table: Table,
    mcp_configs_batch: list[McpConfigV1],
) -> None:
    """Insert a batch of MCP configs into the database, ignoring conflicts."""
    if not mcp_configs_batch:
        logger.info("No MCP configs to insert, skipping batch")
        return

    connection.execute(
        mcp_configs_table.insert().prefix_with("OR REPLACE"),
        [mcp_config.to_db_dict() for mcp_config in mcp_configs_batch],
    )


settings = SettingsV1()
mcp_configs_dir = settings.data_dir / "mcp_configs"


def upgrade() -> None:
    """Import existing MCP configs from JSON files."""

    # Skip if directory doesn't exist (e.g., first-time setup)
    if not mcp_configs_dir.exists():
        logger.info(
            "MCP configs directory does not exist, skipping import of MCP configs",
            extra={"mcp_configs_dir": str(mcp_configs_dir)},
        )
        return

    # Get the table from the current database schema
    connection = op.get_bind()
    mcp_configs_table = Table("mcp_configs", MetaData(), autoload_with=connection)

    # Get all JSON files in the mcp_configs directory
    json_files = list(mcp_configs_dir.glob("*.json"))

    # Process MCP configs in batches
    mcp_configs_batch: list[McpConfigV1] = []

    for json_file in json_files:
        try:
            content = json_file.read_text(encoding="utf-8").strip()
            data = json.loads(content)
            mcp_config = McpConfigV1.model_validate(data)
            mcp_configs_batch.append(mcp_config)
            if len(mcp_configs_batch) >= BATCH_SIZE:
                _insert_mcp_configs_batch(
                    connection, mcp_configs_table, mcp_configs_batch
                )
                mcp_configs_batch.clear()
        except Exception:  # noqa: PERF203
            error_msg = "Failed to import"
            logger.exception(error_msg, extra={"json_file": str(json_file)})
            continue

    # Insert remaining MCP configs in the final batch
    if mcp_configs_batch:
        _insert_mcp_configs_batch(connection, mcp_configs_table, mcp_configs_batch)


def downgrade() -> None:
    """Recreate JSON files for MCP configs during downgrade."""

    mcp_configs_dir.mkdir(parents=True, exist_ok=True)

    connection = op.get_bind()
    mcp_configs_table = Table("mcp_configs", MetaData(), autoload_with=connection)

    # Fetch all MCP configs from the database
    result = connection.execute(mcp_configs_table.select())
    rows = result.fetchall()
    if not rows:
        logger.info(
            "No MCP configs found in the database, skipping export of rows to json",
        )
        return

    for row in rows:
        try:
            mcp_config: McpConfigV1 = McpConfigV1.model_validate(
                row, from_attributes=True
            )
            json_path = mcp_configs_dir / f"{mcp_config.id}.json"
            if json_path.exists():
                logger.info(
                    "Json file for mcp config already exists, skipping export of row to json",
                    extra={"mcp_config_id": mcp_config.id, "json_path": str(json_path)},
                )
                continue
            with json_path.open("w", encoding="utf-8") as f:
                f.write(mcp_config.model_dump_json())
        except Exception as e:  # noqa: PERF203
            error_msg = f"Failed to export row to json: {e}"
            logger.exception(error_msg, extra={"row": str(row)}, exc_info=e)
            continue
