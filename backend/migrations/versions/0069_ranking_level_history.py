"""rankings: the level history — ``ranking_level_history``

**Where each Level stood, point by point** ([#769](https://github.com/Rakieta02/Rakieta/issues/769);
[ADR-0203](../../docs/adr/0203-a-ranking-per-sport-sorted-by-the-level.md) §4, §10).
One point per stored event that put a player's Level where it stood: the
rating's opening, and every ``rating.moved_on_result`` — the Level in
hundredths, how many results had moved it by then, and when it took that
value. **Keyed by the event** (``event_store.id``), so a redelivery changes
nothing. The chip reads it 7 days back; no night-time job is needed.

**Served by one index**: sport, player id, when — *each player's point in a
sport at an instant*.

**Nothing is backfilled here**: the points of the results already played are
folded from the event store by the rebuild (``make rankings-rebuild``), the
same fold the delivery runs.

Revision ID: 0069_ranking_level_history
Revises: 0068_ranking_rows
Create Date: 2026-11-08
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0069_ranking_level_history"
down_revision = "0068_ranking_rows"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ranking_level_history",
        sa.Column("event_id", UUIDType(binary=False), nullable=False),
        sa.Column("player_id", UUIDType(binary=False), nullable=False),
        sa.Column("sport", sa.String(16), nullable=False),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("hundredths", sa.Integer(), nullable=False),
        sa.Column("results", sa.Integer(), nullable=False),
        sa.Column("level_reached_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index(
        "ix_ranking_level_history_points",
        "ranking_level_history",
        ["sport", "player_id", "at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_ranking_level_history_points", table_name="ranking_level_history"
    )
    op.drop_table("ranking_level_history")
