"""soft_delete_threads_dirs

Revision ID: 7a8b9c0d1e2f
Revises: 6f7a8b9c0d1e
Create Date: 2025-01-27 12:06:00.000000

"""

import logging
from typing import Sequence, Union

from askui.chat.migrations.shared.settings import SettingsV1

# revision identifiers, used by Alembic.
revision: str = "7a8b9c0d1e2f"
down_revision: Union[str, None] = "6f7a8b9c0d1e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger(__name__)

settings = SettingsV1()
workspaces_dir = settings.data_dir / "workspaces"


def upgrade() -> None:
    """Soft delete threads directories by moving them to .deleted subdirectory."""

    # Skip if workspaces directory doesn't exist (e.g., first-time setup)
    if not workspaces_dir.exists():
        return

    # Create .deleted directory if it doesn't exist
    deleted_dir = settings.data_dir / ".deleted"
    deleted_dir.mkdir(parents=True, exist_ok=True)

    # Soft delete threads directories from all workspaces
    for workspace_dir in workspaces_dir.iterdir():
        if not workspace_dir.is_dir():
            continue

        threads_dir = workspace_dir / "threads"
        if threads_dir.exists():
            try:
                # Create workspace-specific deleted directory
                deleted_workspace_dir = deleted_dir / workspace_dir.name
                deleted_workspace_dir.mkdir(parents=True, exist_ok=True)

                # Move threads directory to .deleted subdirectory
                deleted_threads_dir = deleted_workspace_dir / "threads"
                if deleted_threads_dir.exists():
                    logger.info(
                        "Deleted threads directory already exists, skipping soft delete",
                        extra={"deleted_threads_dir": str(deleted_threads_dir)},
                    )
                    continue

                threads_dir.rename(deleted_threads_dir)
                logger.info(
                    "Soft deleted threads directory",
                    extra={
                        "threads_dir": str(threads_dir),
                        "deleted_threads_dir": str(deleted_threads_dir),
                    },
                )
            except Exception as e:
                error_msg = f"Failed to soft delete threads directory: {threads_dir}"
                logger.exception(error_msg, exc_info=e)


def downgrade() -> None:
    """Restore threads directories from .deleted subdirectory."""
    deleted_dir = settings.data_dir / ".deleted"

    if not deleted_dir.exists():
        logger.info("No .deleted directory found to restore from")
        return

    # Restore threads directories for all workspaces
    for workspace_dir in workspaces_dir.iterdir():
        if not workspace_dir.is_dir():
            continue

        deleted_workspace_dir = deleted_dir / workspace_dir.name
        deleted_threads_dir = deleted_workspace_dir / "threads"

        if deleted_threads_dir.exists():
            threads_dir = workspace_dir / "threads"
            try:
                deleted_threads_dir.rename(threads_dir)
                logger.info(
                    "Restored threads directory",
                    extra={"threads_dir": str(threads_dir)},
                )
            except Exception as e:
                error_msg = f"Failed to restore threads directory: {threads_dir}"
                logger.exception(error_msg, exc_info=e)
