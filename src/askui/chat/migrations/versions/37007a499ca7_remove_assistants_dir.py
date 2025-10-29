"""remove_assistants_dir

Revision ID: 37007a499ca7
Revises: c35e88ea9595
Create Date: 2025-10-10 14:01:53.410908

"""

import logging
import shutil
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
    """Remove the assistants directory and all its contents."""

    # Skip if directory doesn't exist
    if not assistants_dir.exists():
        logger.info("Assistants directory does not exist, skipping removal")
        return

    try:
        shutil.rmtree(assistants_dir)
        logger.info(
            "Successfully removed assistants directory",
            extra={"assistants_dir": str(assistants_dir)},
        )
    except Exception as e:
        error_msg = "Failed to remove assistants directory"
        logger.exception(
            error_msg,
            extra={"assistants_dir": str(assistants_dir)},
        )
        raise RuntimeError(error_msg) from e


def downgrade() -> None:
    assistants_dir.mkdir(parents=True, exist_ok=True)
