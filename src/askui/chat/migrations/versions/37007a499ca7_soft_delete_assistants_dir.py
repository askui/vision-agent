"""soft_delete_assistants_dir

Revision ID: 37007a499ca7
Revises: c35e88ea9595
Create Date: 2025-10-10 14:01:53.410908

"""

import logging
from pathlib import Path
from typing import Sequence, Union

from askui.chat.migrations.shared.settings import SettingsV1

# revision identifiers, used by Alembic.
revision: str = "37007a499ca7"
down_revision: Union[str, None] = "c35e88ea9595"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger(__name__)

settings = SettingsV1()
assistants_dir = settings.data_dir / "assistants"


def upgrade() -> None:
    """Soft delete the assistants directory by moving it to .deleted subdirectory."""

    # Skip if directory doesn't exist
    if not assistants_dir.exists():
        logger.info("Assistants directory does not exist, skipping soft delete")
        return

    try:
        # Create .deleted directory if it doesn't exist
        deleted_dir = settings.data_dir / ".deleted"
        deleted_dir.mkdir(parents=True, exist_ok=True)

        # Move assistants directory to .deleted subdirectory
        deleted_assistants_dir = deleted_dir / "assistants"
        if deleted_assistants_dir.exists():
            logger.info(
                "Deleted assistants directory already exists, skipping soft delete",
                extra={"deleted_assistants_dir": str(deleted_assistants_dir)},
            )
            return

        assistants_dir.rename(deleted_assistants_dir)
        logger.info(
            "Successfully soft deleted assistants directory",
            extra={
                "assistants_dir": str(assistants_dir),
                "deleted_assistants_dir": str(deleted_assistants_dir),
            },
        )
    except Exception as e:
        error_msg = "Failed to soft delete assistants directory"
        logger.exception(
            error_msg,
            extra={"assistants_dir": str(assistants_dir)},
        )
        raise RuntimeError(error_msg) from e


def downgrade() -> None:
    """Restore the assistants directory from .deleted subdirectory."""
    deleted_dir = settings.data_dir / ".deleted"
    deleted_assistants_dir = deleted_dir / "assistants"

    if not deleted_assistants_dir.exists():
        logger.info("No deleted assistants directory found to restore")
        return

    try:
        deleted_assistants_dir.rename(assistants_dir)
        logger.info(
            "Successfully restored assistants directory",
            extra={"assistants_dir": str(assistants_dir)},
        )
    except Exception as e:
        error_msg = "Failed to restore assistants directory"
        logger.exception(
            error_msg,
            extra={"assistants_dir": str(assistants_dir)},
        )
        raise RuntimeError(error_msg) from e
