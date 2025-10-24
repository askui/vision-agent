"""import_json_runs

Revision ID: 6f7a8b9c0d1e
Revises: 5e6f7a8b9c0d
Create Date: 2025-01-27 12:05:00.000000

"""

import json
import logging
from typing import Sequence, Union

from alembic import op
from sqlalchemy import Connection, MetaData, Table, text

from askui.chat.migrations.shared.runs.models import RunV1
from askui.chat.migrations.shared.settings import SettingsV1

# revision identifiers, used by Alembic.
revision: str = "6f7a8b9c0d1e"
down_revision: Union[str, None] = "5e6f7a8b9c0d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger(__name__)


BATCH_SIZE = 1000


def _insert_runs_batch(
    connection: Connection, runs_table: Table, runs_batch: list[RunV1]
) -> None:
    """Insert a batch of runs into the database, handling foreign key violations."""
    if not runs_batch:
        return

    # Validate and fix foreign key references
    valid_runs = _validate_and_fix_foreign_keys(connection, runs_batch)

    if valid_runs:
        connection.execute(
            runs_table.insert().prefix_with("OR REPLACE"),
            [run.to_db_dict() for run in valid_runs],
        )


def _validate_and_fix_foreign_keys(  # noqa: C901
    connection: Connection, runs_batch: list[RunV1]
) -> list[RunV1]:
    """
    Validate foreign key references and fix invalid ones.

    - If thread_id is invalid: ignore the run completely
    - If assistant_id is invalid: set to None
    """
    if not runs_batch:
        return []

    # Extract all foreign key values
    thread_ids = {run.thread_id.removeprefix("thread_") for run in runs_batch}
    assistant_ids = {
        run.assistant_id.removeprefix("asst_") for run in runs_batch if run.assistant_id
    }

    # Check which foreign keys exist in the database
    valid_thread_ids: set[str] = set()
    if thread_ids:
        # Create placeholders for SQLite IN clause
        placeholders = ",".join([":id" + str(i) for i in range(len(thread_ids))])
        params = {f"id{i}": thread_id for i, thread_id in enumerate(thread_ids)}
        result = connection.execute(
            text(f"SELECT id FROM threads WHERE id IN ({placeholders})"), params
        )
        valid_thread_ids = {row[0] for row in result}

    valid_assistant_ids: set[str] = set()
    if assistant_ids:
        # Create placeholders for SQLite IN clause
        placeholders = ",".join([":id" + str(i) for i in range(len(assistant_ids))])
        params = {
            f"id{i}": assistant_id for i, assistant_id in enumerate(assistant_ids)
        }
        result = connection.execute(
            text(f"SELECT id FROM assistants WHERE id IN ({placeholders})"), params
        )
        valid_assistant_ids = {row[0] for row in result}

    # Process each run
    valid_runs: list[RunV1] = []
    for run in runs_batch:
        thread_id = run.thread_id.removeprefix("thread_")
        assistant_id = (
            run.assistant_id.removeprefix("asst_") if run.assistant_id else None
        )

        # If thread_id is invalid, ignore the run completely
        if thread_id not in valid_thread_ids:
            logger.warning(
                "Ignoring run with invalid thread_id (thread does not exist)",
                extra={
                    "run_id": run.id,
                    "thread_id": thread_id,
                    "workspace_id": str(run.workspace_id),
                },
            )
            continue

        # Check and fix assistant_id
        fixed_assistant_id = None
        changes_made: list[str] = []

        if assistant_id is not None and assistant_id not in valid_assistant_ids:
            fixed_assistant_id = None
            changes_made.append(f"assistant_id set to None (was: {assistant_id})")
        elif assistant_id is not None:
            fixed_assistant_id = assistant_id

        # Create a copy of the run with fixed foreign keys
        if changes_made:
            logger.info(
                "Fixed foreign key references for run",
                extra={
                    "run_id": run.id,
                    "thread_id": thread_id,
                    "changes": changes_made,
                },
            )

            # Create new run with fixed foreign keys
            fixed_run = RunV1(
                id=run.id,
                object=run.object,
                thread_id=run.thread_id,
                created_at=run.created_at,
                expires_at=run.expires_at,
                started_at=run.started_at,
                completed_at=run.completed_at,
                failed_at=run.failed_at,
                cancelled_at=run.cancelled_at,
                tried_cancelling_at=run.tried_cancelling_at,
                last_error=run.last_error,
                assistant_id=f"asst_{fixed_assistant_id}"
                if fixed_assistant_id
                else None,
                workspace_id=run.workspace_id,
            )
            valid_runs.append(fixed_run)
        else:
            # No changes needed, use original run
            valid_runs.append(run)

    return valid_runs


settings = SettingsV1()
workspaces_dir = settings.data_dir / "workspaces"


def upgrade() -> None:  # noqa: C901
    """Import existing runs from JSON files in workspace directories."""

    # Skip if workspaces directory doesn't exist (e.g., first-time setup)
    if not workspaces_dir.exists():
        return

    # Get the table from the current database schema
    connection = op.get_bind()
    runs_table = Table("runs", MetaData(), autoload_with=connection)

    # Process runs in batches
    runs_batch: list[RunV1] = []

    # Iterate through all workspace directories
    for workspace_dir in workspaces_dir.iterdir():
        if not workspace_dir.is_dir():
            continue

        workspace_id = workspace_dir.name
        runs_dir = workspace_dir / "runs"

        if not runs_dir.exists():
            continue

        # Iterate through thread directories
        for thread_dir in runs_dir.iterdir():
            if not thread_dir.is_dir():
                continue

            # Get all JSON files in the thread directory
            json_files = list(thread_dir.glob("*.json"))

            for json_file in json_files:
                try:
                    content = json_file.read_text(encoding="utf-8").strip()
                    data = json.loads(content)
                    run = RunV1.model_validate({**data, "workspace_id": workspace_id})
                    runs_batch.append(run)
                    if len(runs_batch) >= BATCH_SIZE:
                        _insert_runs_batch(connection, runs_table, runs_batch)
                        runs_batch.clear()
                except Exception:  # noqa: PERF203
                    error_msg = "Failed to import run"
                    logger.exception(error_msg, extra={"json_file": str(json_file)})
                    continue

    # Insert remaining runs in the final batch
    if runs_batch:
        _insert_runs_batch(connection, runs_table, runs_batch)


def downgrade() -> None:
    """Recreate JSON files for runs during downgrade."""

    connection = op.get_bind()
    runs_table = Table("runs", MetaData(), autoload_with=connection)

    # Fetch all runs from the database
    result = connection.execute(runs_table.select())
    rows = result.fetchall()
    if not rows:
        return

    for row in rows:
        try:
            run_model: RunV1 = RunV1.model_validate(row, from_attributes=True)
            runs_dir = (
                workspaces_dir
                / str(run_model.workspace_id)
                / "runs"
                / run_model.thread_id
            )
            runs_dir.mkdir(parents=True, exist_ok=True)
            json_path = runs_dir / f"{run_model.id}.json"
            if json_path.exists():
                continue
            with json_path.open("w", encoding="utf-8") as f:
                f.write(run_model.model_dump_json())
        except Exception as e:  # noqa: PERF203
            error_msg = f"Failed to export row to json: {e}"
            logger.exception(error_msg, extra={"row": str(row)}, exc_info=e)
            continue
