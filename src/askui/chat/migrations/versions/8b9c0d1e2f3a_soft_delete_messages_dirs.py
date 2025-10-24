"""soft_delete_messages_dirs

Revision ID: 8b9c0d1e2f3a
Revises: 7a8b9c0d1e2f
Create Date: 2025-01-27 12:07:00.000000

"""

import logging
from typing import Sequence, Union

from askui.chat.migrations.shared.settings import SettingsV1

# revision identifiers, used by Alembic.
revision: str = "8b9c0d1e2f3a"
down_revision: Union[str, None] = "7a8b9c0d1e2f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger(__name__)

settings = SettingsV1()
workspaces_dir = settings.data_dir / "workspaces"


def upgrade() -> None:
    """Soft delete messages directories by moving them to .deleted subdirectory."""

    # Skip if workspaces directory doesn't exist (e.g., first-time setup)
    if not workspaces_dir.exists():
        return

    # Create .deleted directory if it doesn't exist
    deleted_dir = settings.data_dir / ".deleted"
    deleted_dir.mkdir(parents=True, exist_ok=True)

    # Soft delete messages directories from all workspaces
    for workspace_dir in workspaces_dir.iterdir():
        if not workspace_dir.is_dir():
            continue

        messages_dir = workspace_dir / "messages"
        if messages_dir.exists():
            try:
                # Create workspace-specific deleted directory
                deleted_workspace_dir = deleted_dir / workspace_dir.name
                deleted_workspace_dir.mkdir(parents=True, exist_ok=True)

                # Move messages directory to .deleted subdirectory
                deleted_messages_dir = deleted_workspace_dir / "messages"
                if deleted_messages_dir.exists():
                    logger.info(
                        "Deleted messages directory already exists, skipping soft delete",
                        extra={"deleted_messages_dir": str(deleted_messages_dir)},
                    )
                    continue

                messages_dir.rename(deleted_messages_dir)
                logger.info(
                    "Soft deleted messages directory",
                    extra={
                        "messages_dir": str(messages_dir),
                        "deleted_messages_dir": str(deleted_messages_dir),
                    },
                )
            except Exception as e:
                error_msg = f"Failed to soft delete messages directory: {messages_dir}"
                logger.exception(error_msg, exc_info=e)


def downgrade() -> None:
    """Restore messages directories from .deleted subdirectory."""
    deleted_dir = settings.data_dir / ".deleted"

    if not deleted_dir.exists():
        logger.info("No .deleted directory found to restore from")
        return

    # Restore messages directories for all workspaces
    for workspace_dir in workspaces_dir.iterdir():
        if not workspace_dir.is_dir():
            continue

        deleted_workspace_dir = deleted_dir / workspace_dir.name
        deleted_messages_dir = deleted_workspace_dir / "messages"

        if deleted_messages_dir.exists():
            try:
                messages_dir = workspace_dir / "messages"
                deleted_messages_dir.rename(messages_dir)
                logger.info(
                    "Restored messages directory",
                    extra={"messages_dir": str(messages_dir)},
                )
            except Exception as e:
                error_msg = f"Failed to restore messages directory: {messages_dir}"
                logger.exception(error_msg, exc_info=e)
