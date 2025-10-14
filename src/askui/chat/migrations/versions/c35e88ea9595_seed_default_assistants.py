"""seed_default_assistants

Revision ID: c35e88ea9595
Revises: 057f82313448
Create Date: 2025-10-10 11:22:12.576195

"""

import logging
from typing import Sequence, Union

from alembic import op
from sqlalchemy import MetaData, Table
from sqlalchemy.exc import IntegrityError

from askui.chat.migrations.shared.assistants.seeds import SEEDS_V1

# revision identifiers, used by Alembic.
revision: str = "c35e88ea9595"
down_revision: Union[str, None] = "057f82313448"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger(__name__)


def upgrade() -> None:
    """Seed default assistants one by one, skipping duplicates.

    For each assistant in `SEEDS_V1`, insert a row into `assistants`. If a
    row with the same `id` already exists, skip it and log on info level.
    """
    connection = op.get_bind()
    assistants_table: Table = Table("assistants", MetaData(), autoload_with=connection)

    for seed in SEEDS_V1:
        payload: dict[str, object] = seed.to_db_dict()
        try:
            connection.execute(assistants_table.insert().values(**payload))
        except IntegrityError:
            logger.info(
                "Assistant already exists, skipping", extra={"assistant_id": seed.id}
            )
            continue
        except Exception as e:  # noqa: PERF203
            logger.exception(
                "Failed to insert assistant",
                extra={"assistant": seed.model_dump_json()},
                exc_info=e,
            )
            continue


def downgrade() -> None:
    """Remove exactly those assistants that were seeded in upgrade()."""
    connection = op.get_bind()
    assistant_table: Table = Table("assistants", MetaData(), autoload_with=connection)

    seed_db_ids: list[str] = [seed.id for seed in SEEDS_V1]
    for id_ in seed_db_ids:
        connection.execute(assistant_table.delete().where(assistant_table.c.id == id_))
