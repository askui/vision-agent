"""soft_delete_runs_dirs

Revision ID: 9c0d1e2f3a4b
Revises: 8b9c0d1e2f3a
Create Date: 2025-01-27 12:08:00.000000

"""

import logging
from typing import Sequence, Union

from askui.chat.migrations.shared.settings import SettingsV1

# revision identifiers, used by Alembic.
revision: str = "9c0d1e2f3a4b"
down_revision: Union[str, None] = "8b9c0d1e2f3a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger(__name__)

settings = SettingsV1()
workspaces_dir = settings.data_dir / "workspaces"


def upgrade() -> None:
    """Soft delete runs directories by moving them to .deleted subdirectory."""

    # Skip if workspaces directory doesn't exist (e.g., first-time setup)
    if not workspaces_dir.exists():
        return

    # Create .deleted directory if it doesn't exist
    deleted_dir = settings.data_dir / ".deleted"
    deleted_dir.mkdir(parents=True, exist_ok=True)

    # Soft delete runs directories from all workspaces
    for workspace_dir in workspaces_dir.iterdir():
        if not workspace_dir.is_dir():
            continue

        runs_dir = workspace_dir / "runs"
        if runs_dir.exists():
            try:
                # Create workspace-specific deleted directory
                deleted_workspace_dir = deleted_dir / workspace_dir.name
                deleted_workspace_dir.mkdir(parents=True, exist_ok=True)

                # Move runs directory to .deleted subdirectory
                deleted_runs_dir = deleted_workspace_dir / "runs"
                if deleted_runs_dir.exists():
                    logger.info(
                        "Deleted runs directory already exists, skipping soft delete",
                        extra={"deleted_runs_dir": str(deleted_runs_dir)},
                    )
                    continue

                runs_dir.rename(deleted_runs_dir)
                logger.info(
                    "Soft deleted runs directory",
                    extra={
                        "runs_dir": str(runs_dir),
                        "deleted_runs_dir": str(deleted_runs_dir),
                    },
                )
            except Exception as e:
                error_msg = f"Failed to soft delete runs directory: {runs_dir}"
                logger.exception(error_msg, exc_info=e)


def downgrade() -> None:
    """Restore runs directories from .deleted subdirectory."""
    deleted_dir = settings.data_dir / ".deleted"

    if not deleted_dir.exists():
        logger.info("No .deleted directory found to restore from")
        return

    # Restore runs directories for all workspaces
    for workspace_dir in workspaces_dir.iterdir():
        if not workspace_dir.is_dir():
            continue

        deleted_workspace_dir = deleted_dir / workspace_dir.name
        deleted_runs_dir = deleted_workspace_dir / "runs"

        if deleted_runs_dir.exists():
            try:
                runs_dir = workspace_dir / "runs"
                deleted_runs_dir.rename(runs_dir)
                logger.info(
                    "Restored runs directory",
                    extra={"runs_dir": str(runs_dir)},
                )
            except Exception as e:
                error_msg = f"Failed to restore runs directory: {runs_dir}"
                logger.exception(error_msg, exc_info=e)
