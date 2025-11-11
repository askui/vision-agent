"""add_parent_id_to_messages

Revision ID: 7b8c9d0e1f2a
Revises: 5e6f7a8b9c0d
Create Date: 2025-11-05 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7b8c9d0e1f2a"
down_revision: Union[str, None] = "5e6f7a8b9c0d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ROOT_MESSAGE_PARENT_ID = "msg_000000000000000000000000"


def upgrade() -> None:
    # Get database connection
    connection = op.get_bind()

    # Check if parent_id column already exists
    inspector = sa.inspect(connection)
    columns = [col["name"] for col in inspector.get_columns("messages")]
    column_exists = "parent_id" in columns

    # Add parent_id column as nullable first (only if it doesn't exist)
    if not column_exists:
        op.add_column(
            "messages",
            sa.Column("parent_id", sa.String(27), nullable=True),
        )

    # Check if there are any messages with NULL parent_id that need updating
    null_parent_count_result = connection.execute(
        sa.text("SELECT COUNT(*) FROM messages WHERE parent_id IS NULL")
    )
    null_parent_count = null_parent_count_result.scalar()

    # Only update parent_ids if there are messages without them
    if null_parent_count > 0:
        # Fetch all threads
        threads_result = connection.execute(sa.text("SELECT id FROM threads"))
        thread_ids = [row[0] for row in threads_result]

        # For each thread, set up parent-child relationships
        for thread_id in thread_ids:
            # Get all messages in this thread, sorted by ID (which is time-ordered)
            messages_result = connection.execute(
                sa.text(
                    "SELECT id FROM messages WHERE thread_id = :thread_id ORDER BY id ASC"
                ),
                {"thread_id": thread_id},
            )
            message_ids = [row[0] for row in messages_result]

            # Set parent_id for each message
            for i, message_id in enumerate(message_ids):
                if i == 0:
                    # First message in thread has root as parent
                    parent_id = _ROOT_MESSAGE_PARENT_ID
                else:
                    # Each subsequent message's parent is the previous message
                    parent_id = message_ids[i - 1]

                connection.execute(
                    sa.text(
                        "UPDATE messages SET parent_id = :parent_id WHERE id = :message_id"
                    ),
                    {"parent_id": parent_id, "message_id": message_id},
                )

    # Make column non-nullable after setting all parent_ids (only if it was just created)
    if not column_exists:
        # Use batch_alter_table for SQLite compatibility
        with op.batch_alter_table("messages") as batch_op:
            batch_op.alter_column("parent_id", nullable=False)


def downgrade() -> None:
    # Drop column (FK constraint will be dropped automatically by the ORM)
    op.drop_column("messages", "parent_id")
