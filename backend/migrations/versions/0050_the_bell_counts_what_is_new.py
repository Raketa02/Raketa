"""notifications: the bell counts what is new

**The bell's number** ([#621](https://github.com/Rakieta02/Rakieta/issues/621);
the mechanics Q101, Q102; ADR-0189's 2026-10-09 amendment). A third stream —
a player's **bell**, when they last opened their recent notices — and beside it:

- **``notices_opened``** — one row per player who ever opened the list: when,
  and the newest place in the store among the notices the list held then. A
  notice whose own place is past it reached the list since, and the bell
  counts it.
- **``notices.own``** — a notice of the player's own act (the yes that filled
  the game, the seat they took): born seen, and never counted. Every notice
  given before it was asked reads as nobody's own.
- **``ix_notices_player_id_sequence_no``** — the count's read: a player's
  notices past their last visit.

Revision ID: 0050_the_bell_counts_what_is_new
Revises: 0049_the_tester_mark_is_gone
Create Date: 2026-10-09
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0050_the_bell_counts_what_is_new"
down_revision = "0049_the_tester_mark_is_gone"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "notices",
        sa.Column("own", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index(
        "ix_notices_player_id_sequence_no", "notices", ["player_id", "sequence_no"]
    )
    op.create_table(
        "notices_opened",
        sa.Column("player_id", UUIDType(binary=False), primary_key=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("seen_through", sa.BigInteger(), nullable=False),
    )


def downgrade() -> None:
    # The bells' streams still say when each player opened the list; the
    # projection is gone, and so is which notice was whose own.
    op.drop_table("notices_opened")
    op.drop_index("ix_notices_player_id_sequence_no", table_name="notices")
    op.drop_column("notices", "own")
