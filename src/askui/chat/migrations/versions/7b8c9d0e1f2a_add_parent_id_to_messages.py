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


def upgrade() -> None:
    # Get database connection
    connection = op.get_bind()

    # Check if parent_id column already exists
    inspector = sa.inspect(connection)
    columns = [col["name"] for col in inspector.get_columns("messages")]
    column_exists = "parent_id" in columns

    # Only run batch operation if column doesn't exist
    if not column_exists:
        # Add column, foreign key, and index all in one batch operation
        # This ensures the table is only recreated once in SQLite
        with op.batch_alter_table("messages") as batch_op:
            # Add parent_id column
            batch_op.add_column(sa.Column("parent_id", sa.String(24), nullable=True))

            # Add foreign key constraint (self-referential)
            # parent_id remains nullable - NULL indicates a root message
            batch_op.create_foreign_key(
                "fk_messages_parent_id",
                "messages",
                ["parent_id"],
                ["id"],
                ondelete="CASCADE",
            )

            # Add index for performance
            batch_op.create_index("ix_messages_parent_id", ["parent_id"])

    # NOW populate parent_id values AFTER the table structure is finalized
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
                # First message in thread has NULL as parent (root message)
                parent_id = None
            else:
                # Each subsequent message's parent is the previous message
                parent_id = message_ids[i - 1]

            connection.execute(
                sa.text(
                    "UPDATE messages SET parent_id = :parent_id WHERE id = :message_id"
                ),
                {"parent_id": parent_id, "message_id": message_id},
            )


def downgrade() -> None:
    # Use batch_alter_table for SQLite compatibility
    with op.batch_alter_table("messages") as batch_op:
        # Drop index
        batch_op.drop_index("ix_messages_parent_id")
        # Drop foreign key constraint
        batch_op.drop_constraint("fk_messages_parent_id", type_="foreignkey")
        # Drop column
        batch_op.drop_column("parent_id")
