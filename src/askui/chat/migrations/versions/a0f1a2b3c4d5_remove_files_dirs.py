"""remove_files_dirs

Revision ID: a0f1a2b3c4d5
Revises: 9e0f1a2b3c4d
Create Date: 2025-01-27 11:02:00.000000

"""

import logging
import shutil
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
    """Remove JSON files from workspace static directories after successful migration."""

    # Skip if workspaces directory doesn't exist
    if not workspaces_dir.exists():
        logger.info(
            "Workspaces directory does not exist, skipping removal",
            extra={"workspaces_dir": str(workspaces_dir)},
        )
        return

    # Iterate through all workspace directories
    for workspace_dir in workspaces_dir.iterdir():
        if not workspace_dir.is_dir():
            continue

        files_dir = workspace_dir / "files"
        if not files_dir.exists():
            logger.info(
                "Files directory does not exist, skipping removal",
                extra={"files_dir": str(files_dir)},
            )
            continue

        try:
            shutil.rmtree(files_dir)
            logger.info(
                "Successfully removed files directory",
                extra={"files_dir": str(files_dir)},
            )
        except Exception as e:  # noqa: PERF203
            error_msg = "Failed to remove files directory"
            logger.exception(error_msg, extra={"files_dir": str(files_dir)})
            raise RuntimeError(error_msg) from e


def downgrade() -> None:
    """Recreate JSON files in workspace static directories during downgrade."""

    # This is handled by the import_json_files migration downgrade
    # No need to recreate files here as they will be recreated when downgrading
    # the import_json_files migration
