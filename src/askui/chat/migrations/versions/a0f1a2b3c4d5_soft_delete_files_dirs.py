"""soft_delete_files_dirs

Revision ID: a0f1a2b3c4d5
Revises: 9e0f1a2b3c4d
Create Date: 2025-01-27 11:02:00.000000

"""

import logging
from typing import Sequence, Union

from askui.chat.migrations.shared.settings import SettingsV1

# revision identifiers, used by Alembic.
revision: str = "a0f1a2b3c4d5"
down_revision: Union[str, None] = "9e0f1a2b3c4d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger(__name__)

settings = SettingsV1()
workspaces_dir = settings.data_dir / "workspaces"


def upgrade() -> None:
    """Soft delete JSON files from workspace static directories by moving them to .deleted subdirectory."""

    # Skip if workspaces directory doesn't exist
    if not workspaces_dir.exists():
        logger.info(
            "Workspaces directory does not exist, skipping soft delete",
            extra={"workspaces_dir": str(workspaces_dir)},
        )
        return

    # Create .deleted directory if it doesn't exist
    deleted_dir = settings.data_dir / ".deleted"
    deleted_dir.mkdir(parents=True, exist_ok=True)

    # Iterate through all workspace directories
    for workspace_dir in workspaces_dir.iterdir():
        if not workspace_dir.is_dir():
            continue

        files_dir = workspace_dir / "files"
        if not files_dir.exists():
            logger.info(
                "Files directory does not exist, skipping soft delete",
                extra={"files_dir": str(files_dir)},
            )
            continue

        try:
            # Create workspace-specific deleted directory
            deleted_workspace_dir = deleted_dir / workspace_dir.name
            deleted_workspace_dir.mkdir(parents=True, exist_ok=True)

            # Move files directory to .deleted subdirectory
            deleted_files_dir = deleted_workspace_dir / "files"
            if deleted_files_dir.exists():
                logger.info(
                    "Deleted files directory already exists, skipping soft delete",
                    extra={"deleted_files_dir": str(deleted_files_dir)},
                )
                continue

            files_dir.rename(deleted_files_dir)
            logger.info(
                "Successfully soft deleted files directory",
                extra={
                    "files_dir": str(files_dir),
                    "deleted_files_dir": str(deleted_files_dir),
                },
            )
        except Exception as e:  # noqa: PERF203
            error_msg = "Failed to soft delete files directory"
            logger.exception(error_msg, extra={"files_dir": str(files_dir)})
            raise RuntimeError(error_msg) from e


def downgrade() -> None:
    """Restore JSON files in workspace static directories from .deleted subdirectory."""
    deleted_dir = settings.data_dir / ".deleted"

    if not deleted_dir.exists():
        logger.info("No .deleted directory found to restore from")
        return

    # Restore files directories for all workspaces
    for workspace_dir in workspaces_dir.iterdir():
        if not workspace_dir.is_dir():
            continue

        deleted_workspace_dir = deleted_dir / workspace_dir.name
        deleted_files_dir = deleted_workspace_dir / "files"

        if deleted_files_dir.exists():
            try:
                files_dir = workspace_dir / "files"
                deleted_files_dir.rename(files_dir)
                logger.info(
                    "Successfully restored files directory",
                    extra={"files_dir": str(files_dir)},
                )
            except Exception as e:
                error_msg = f"Failed to restore files directory: {files_dir}"
                logger.exception(error_msg, exc_info=e)
