"""remove_mcp_configs_dir

Revision ID: 7c3d4e5f6a7b
Revises: 6b2c3d4e5f6a
Create Date: 2025-01-27 10:02:00.000000

"""

import logging
import shutil
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
    """Remove the mcp_configs directory and all its contents."""

    # Skip if directory doesn't exist
    if not mcp_configs_dir.exists():
        logger.info("MCP configs directory does not exist, skipping removal")
        return

    try:
        shutil.rmtree(mcp_configs_dir)
        logger.info(
            "Successfully removed mcp_configs directory",
            extra={"mcp_configs_dir": str(mcp_configs_dir)},
        )
    except Exception as e:
        error_msg = "Failed to remove mcp_configs directory"
        logger.exception(
            error_msg,
            extra={"mcp_configs_dir": str(mcp_configs_dir)},
        )
        raise RuntimeError(error_msg) from e


def downgrade() -> None:
    mcp_configs_dir.mkdir(parents=True, exist_ok=True)
