"""rankings: *Show me in General* beside the rows — ``ranking_visibility``

**The ranking follows the switch** ([#772](https://github.com/Rakieta02/Rakieta/issues/772);
[ADR-0203](../../docs/adr/0203-a-ranking-per-sport-sorted-by-the-level.md) §7, §10).
One row per player: whether they turned *Show me in General* off, and the
profile stream's version that was read at. **Per player, never per sport**:
the switch is a fact about the player, and it must hold when a first result
in a sport makes that sport's row — so it is kept beside the rows rather than
on them, and the pass reads it by joining on the player.

Written from ``player_profile.ranking_visibility_set`` through the outbox, a
write at an older version never replacing a newer one, and by the rebuild.
**No row is shown**, so nothing is backfilled: every player starts shown.

Revision ID: 0070_ranking_visibility
Revises: 0069_ranking_level_history
Create Date: 2026-11-08
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0070_ranking_visibility"
down_revision = "0069_ranking_level_history"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ranking_visibility",
        sa.Column("player_id", UUIDType(binary=False), nullable=False),
        sa.Column("hidden", sa.Boolean(), nullable=False),
        sa.Column("profile_version", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("player_id"),
    )


def downgrade() -> None:
    op.drop_table("ranking_visibility")
