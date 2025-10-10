"""seed_default_assistants

Revision ID: c35e88ea9595
Revises: 057f82313448
Create Date: 2025-10-10 11:22:12.576195

"""

import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

from askui.chat.api.assistants.orms import AssistantOrm
from askui.chat.api.assistants.seeds import SEEDS

# revision identifiers, used by Alembic.
revision: str = "c35e88ea9595"
down_revision: Union[str, None] = "057f82313448"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed default assistants from seeds.py."""
    connection = op.get_bind()

    # Seed each default assistant
    for seed_assistant in SEEDS:
        # Check if assistant already exists
        result = connection.execute(
            text("SELECT id FROM assistants WHERE id = :id"), {"id": seed_assistant.id}
        ).fetchone()

        if result is None:
            # Convert to ORM and insert
            assistant_orm = AssistantOrm.from_model(seed_assistant)

            connection.execute(
                text("""
                    INSERT INTO assistants (
                        id, workspace_id, created_at, name, description,
                        avatar, tools, system
                    ) VALUES (
                        :id, :workspace_id, :created_at, :name, :description,
                        :avatar, :tools, :system
                    )
                """),
                {
                    "id": assistant_orm.id,
                    "workspace_id": str(assistant_orm.workspace_id)
                    if assistant_orm.workspace_id
                    else None,
                    "created_at": int(assistant_orm.created_at.timestamp()),
                    "name": assistant_orm.name,
                    "description": assistant_orm.description,
                    "avatar": assistant_orm.avatar,
                    "tools": json.dumps(assistant_orm.tools),
                    "system": assistant_orm.system,
                },
            )


def downgrade() -> None:
    """Delete the three specific seed assistant IDs."""
    connection = op.get_bind()

    # Delete the three default assistants
    seed_ids = [
        "asst_68ac2c4edc4b2f27faa5a253",  # COMPUTER_AGENT
        "asst_68ac2c4edc4b2f27faa5a255",  # ANDROID_AGENT
        "asst_68ac2c4edc4b2f27faa5a256",  # WEB_AGENT
    ]

    for seed_id in seed_ids:
        connection.execute(
            text("DELETE FROM assistants WHERE id = :id"), {"id": seed_id}
        )
