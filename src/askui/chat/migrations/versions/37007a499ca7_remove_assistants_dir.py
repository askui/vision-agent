"""remove_assistants_dir

Revision ID: 37007a499ca7
Revises: c35e88ea9595
Create Date: 2025-10-10 14:01:53.410908

"""

import logging
import shutil
from pathlib import Path
from typing import Sequence, Union

from alembic import op
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# revision identifiers, used by Alembic.
revision: str = "37007a499ca7"
down_revision: Union[str, None] = "c35e88ea9595"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ASKUI__CHAT_API__", env_nested_delimiter="__"
    )

    data_dir: Path = Field(
        default_factory=lambda: Path.cwd() / "chat",
        description="Base directory for chat data (used during migration)",
    )


def upgrade() -> None:
    """Remove the assistants directory and all its contents."""
    settings = Settings()
    assistants_dir = settings.data_dir / "assistants"

    # Skip if directory doesn't exist
    if not assistants_dir.exists():
        logger.info("Assistants directory does not exist, skipping removal")
        return

    try:
        shutil.rmtree(assistants_dir)
        logger.info(f"Successfully removed assistants directory: {assistants_dir}")
    except Exception as e:
        error_msg = f"Failed to remove assistants directory: {assistants_dir}"
        logger.exception(error_msg)
        raise RuntimeError(error_msg) from e


def downgrade() -> None:
    pass  # We don't restore the directory
