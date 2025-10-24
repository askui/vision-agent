"""import_json_messages

Revision ID: 5e6f7a8b9c0d
Revises: 4d5e6f7a8b9c
Create Date: 2025-01-27 12:04:00.000000

"""

import json
import logging
from typing import Sequence, Union

from alembic import op
from sqlalchemy import Connection, MetaData, Table, text

from askui.chat.migrations.shared.messages.models import MessageV1
from askui.chat.migrations.shared.settings import SettingsV1

# revision identifiers, used by Alembic.
revision: str = "5e6f7a8b9c0d"
down_revision: Union[str, None] = "4d5e6f7a8b9c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger(__name__)


BATCH_SIZE = 1000


def _insert_messages_batch(
    connection: Connection, messages_table: Table, messages_batch: list[MessageV1]
) -> None:
    """Insert a batch of messages into the database, handling foreign key violations."""
    if not messages_batch:
        return

    # Validate and fix foreign key references
    valid_messages = _validate_and_fix_foreign_keys(connection, messages_batch)

    if valid_messages:
        connection.execute(
            messages_table.insert().prefix_with("OR REPLACE"),
            [message.to_db_dict() for message in valid_messages],
        )


def _validate_and_fix_foreign_keys(  # noqa: C901
    connection: Connection, messages_batch: list[MessageV1]
) -> list[MessageV1]:
    """
    Validate foreign key references and fix invalid ones.

    - If thread_id is invalid: ignore the message completely
    - If assistant_id is invalid: set to None
    - If run_id is invalid: set to None
    """
    if not messages_batch:
        return []

    # Extract all foreign key values
    thread_ids = {msg.thread_id.removeprefix("thread_") for msg in messages_batch}
    assistant_ids = {
        msg.assistant_id.removeprefix("asst_")
        for msg in messages_batch
        if msg.assistant_id
    }
    run_ids = {msg.run_id.removeprefix("run_") for msg in messages_batch if msg.run_id}

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

    valid_run_ids: set[str] = set()
    if run_ids:
        # Create placeholders for SQLite IN clause
        placeholders = ",".join([":id" + str(i) for i in range(len(run_ids))])
        params = {f"id{i}": run_id for i, run_id in enumerate(run_ids)}
        result = connection.execute(
            text(f"SELECT id FROM runs WHERE id IN ({placeholders})"), params
        )
        valid_run_ids = {row[0] for row in result}

    # Process each message
    valid_messages: list[MessageV1] = []
    for message in messages_batch:
        thread_id = message.thread_id.removeprefix("thread_")
        assistant_id = (
            message.assistant_id.removeprefix("asst_") if message.assistant_id else None
        )
        run_id = message.run_id.removeprefix("run_") if message.run_id else None

        # If thread_id is invalid, ignore the message completely
        if thread_id not in valid_thread_ids:
            logger.warning(
                "Ignoring message with invalid thread_id (thread does not exist)",
                extra={
                    "message_id": message.id,
                    "thread_id": thread_id,
                    "workspace_id": str(message.workspace_id),
                },
            )
            continue

        # Check and fix assistant_id and run_id
        fixed_assistant_id = None
        fixed_run_id = None
        changes_made: list[str] = []

        if assistant_id is not None and assistant_id not in valid_assistant_ids:
            fixed_assistant_id = None
            changes_made.append(f"assistant_id set to None (was: {assistant_id})")
        elif assistant_id is not None:
            fixed_assistant_id = assistant_id

        if run_id is not None and run_id not in valid_run_ids:
            fixed_run_id = None
            changes_made.append(f"run_id set to None (was: {run_id})")
        elif run_id is not None:
            fixed_run_id = run_id

        # Create a copy of the message with fixed foreign keys
        if changes_made:
            logger.info(
                "Fixed foreign key references for message",
                extra={
                    "message_id": message.id,
                    "thread_id": thread_id,
                    "changes": changes_made,
                },
            )

            # Create new message with fixed foreign keys
            fixed_message = MessageV1(
                id=message.id,
                object=message.object,
                created_at=message.created_at,
                thread_id=message.thread_id,
                role=message.role,
                content=message.content,
                stop_reason=message.stop_reason,
                assistant_id=f"asst_{fixed_assistant_id}"
                if fixed_assistant_id
                else None,
                run_id=f"run_{fixed_run_id}" if fixed_run_id else None,
                workspace_id=message.workspace_id,
            )
            valid_messages.append(fixed_message)
        else:
            # No changes needed, use original message
            valid_messages.append(message)

    return valid_messages


settings = SettingsV1()
workspaces_dir = settings.data_dir / "workspaces"


def upgrade() -> None:  # noqa: C901
    """Import existing messages from JSON files in workspace directories."""
    # Skip if workspaces directory doesn't exist (e.g., first-time setup)
    if not workspaces_dir.exists():
        return

    # Get the table from the current database schema
    connection = op.get_bind()
    messages_table = Table("messages", MetaData(), autoload_with=connection)

    # Process messages in batches
    messages_batch: list[MessageV1] = []

    # Iterate through all workspace directories
    for workspace_dir in workspaces_dir.iterdir():
        if not workspace_dir.is_dir():
            continue

        workspace_id = workspace_dir.name
        messages_dir = workspace_dir / "messages"

        if not messages_dir.exists():
            continue

        # Iterate through thread directories
        for thread_dir in messages_dir.iterdir():
            if not thread_dir.is_dir():
                continue

            # Get all JSON files in the thread directory
            json_files = list(thread_dir.glob("*.json"))

            for json_file in json_files:
                try:
                    content = json_file.read_text(encoding="utf-8").strip()
                    data = json.loads(content)
                    message = MessageV1.model_validate(
                        {**data, "workspace_id": workspace_id}
                    )
                    messages_batch.append(message)
                    if len(messages_batch) >= BATCH_SIZE:
                        _insert_messages_batch(
                            connection, messages_table, messages_batch
                        )
                        messages_batch.clear()
                except Exception:  # noqa: PERF203
                    error_msg = "Failed to import message"
                    logger.exception(error_msg, extra={"json_file": str(json_file)})
                    continue

    # Insert remaining messages in the final batch
    if messages_batch:
        _insert_messages_batch(connection, messages_table, messages_batch)


def downgrade() -> None:
    """Recreate JSON files for messages during downgrade."""

    connection = op.get_bind()
    messages_table = Table("messages", MetaData(), autoload_with=connection)

    # Fetch all messages from the database
    result = connection.execute(messages_table.select())
    rows = result.fetchall()
    if not rows:
        return

    for row in rows:
        try:
            message_model: MessageV1 = MessageV1.model_validate(
                row, from_attributes=True
            )
            messages_dir = (
                workspaces_dir
                / str(message_model.workspace_id)
                / "messages"
                / message_model.thread_id
            )
            messages_dir.mkdir(parents=True, exist_ok=True)
            json_path = messages_dir / f"{message_model.id}.json"
            if json_path.exists():
                continue
            with json_path.open("w", encoding="utf-8") as f:
                f.write(message_model.model_dump_json())
        except Exception as e:  # noqa: PERF203
            error_msg = f"Failed to export row to json: {e}"
            logger.exception(error_msg, extra={"row": str(row)}, exc_info=e)
            continue
