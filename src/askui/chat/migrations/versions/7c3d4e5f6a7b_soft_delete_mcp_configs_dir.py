"""soft_delete_mcp_configs_dir

Revision ID: 7c3d4e5f6a7b
Revises: 6b2c3d4e5f6a
Create Date: 2025-01-27 10:02:00.000000

"""

import logging
from typing import Sequence, Union

from askui.chat.migrations.shared.settings import SettingsV1

# revision identifiers, used by Alembic.
revision: str = "7c3d4e5f6a7b"
down_revision: Union[str, None] = "6b2c3d4e5f6a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger(__name__)

settings = SettingsV1()
mcp_configs_dir = settings.data_dir / "mcp_configs"


def upgrade() -> None:
    """Soft delete the mcp_configs directory by moving it to .deleted subdirectory."""

    # Skip if directory doesn't exist
    if not mcp_configs_dir.exists():
        logger.info("MCP configs directory does not exist, skipping soft delete")
        return

    try:
        # Create .deleted directory if it doesn't exist
        deleted_dir = settings.data_dir / ".deleted"
        deleted_dir.mkdir(parents=True, exist_ok=True)

        # Move mcp_configs directory to .deleted subdirectory
        deleted_mcp_configs_dir = deleted_dir / "mcp_configs"
        if deleted_mcp_configs_dir.exists():
            logger.info(
                "Deleted mcp_configs directory already exists, skipping soft delete",
                extra={"deleted_mcp_configs_dir": str(deleted_mcp_configs_dir)},
            )
            return

        mcp_configs_dir.rename(deleted_mcp_configs_dir)
        logger.info(
            "Successfully soft deleted mcp_configs directory",
            extra={
                "mcp_configs_dir": str(mcp_configs_dir),
                "deleted_mcp_configs_dir": str(deleted_mcp_configs_dir),
            },
        )
    except Exception as e:
        error_msg = "Failed to soft delete mcp_configs directory"
        logger.exception(
            error_msg,
            extra={"mcp_configs_dir": str(mcp_configs_dir)},
        )
        raise RuntimeError(error_msg) from e


def downgrade() -> None:
    """Restore the mcp_configs directory from .deleted subdirectory."""
    deleted_dir = settings.data_dir / ".deleted"
    deleted_mcp_configs_dir = deleted_dir / "mcp_configs"

    if not deleted_mcp_configs_dir.exists():
        logger.info("No deleted mcp_configs directory found to restore")
        return

    try:
        deleted_mcp_configs_dir.rename(mcp_configs_dir)
        logger.info(
            "Successfully restored mcp_configs directory",
            extra={"mcp_configs_dir": str(mcp_configs_dir)},
        )
    except Exception as e:
        error_msg = "Failed to restore mcp_configs directory"
        logger.exception(
            error_msg,
            extra={"mcp_configs_dir": str(mcp_configs_dir)},
        )
        raise RuntimeError(error_msg) from e
