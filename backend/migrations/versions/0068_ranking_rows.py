"""rankings: the ranking projection — ``ranking_rows``

**A ranking per sport, sorted by the level** ([#768](https://github.com/Rakieta02/Rakieta/issues/768);
[ADR-0203](../../docs/adr/0203-a-ranking-per-sport-sorted-by-the-level.md) §10).
One row per player per sport, made on their first confirmed competitive result
with a winner there: the Level in hundredths and its uncertainty, the count of
results, when the last settled, when the Level took its current value, when the
player first entered General (the fifth result) and Friends (the first), and
the last five outcomes, oldest first. A fold of the player's rating stream in
``event_store``, written when ``rating.moved_on_result`` is delivered.

**General's order is the index**: sport, Level descending, results descending,
Level reached ascending, player id.

**Nothing is backfilled here**: the rows of the results already played are
folded from the event store by the rebuild (``make rankings-rebuild``), the
same fold the delivery runs.

Revision ID: 0068_ranking_rows
Revises: 0067_a_level_ask_may_be_set_aside
Create Date: 2026-11-07
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0068_ranking_rows"
down_revision = "0067_a_level_ask_may_be_set_aside"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ranking_rows",
        sa.Column("player_id", UUIDType(binary=False), nullable=False),
        sa.Column("sport", sa.String(16), nullable=False),
        sa.Column("hundredths", sa.Integer(), nullable=False),
        sa.Column("sigma", sa.Float(), nullable=False),
        sa.Column("results", sa.Integer(), nullable=False),
        sa.Column("last_result_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("level_reached_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("general_entered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("friends_entered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("form", sa.String(5), nullable=False),
        sa.PrimaryKeyConstraint("player_id", "sport"),
    )
    op.create_index(
        "ix_ranking_rows_order",
        "ranking_rows",
        [
            "sport",
            sa.text("hundredths DESC"),
            sa.text("results DESC"),
            "level_reached_at",
            "player_id",
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_ranking_rows_order", table_name="ranking_rows")
    op.drop_table("ranking_rows")
