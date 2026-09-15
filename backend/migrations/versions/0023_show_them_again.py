"""Show them again — the deck reset, as a durable row

`docs/adr/0169` §5 gives the deck a *Show them again*: one route that clears,
for one sport, every pass suppression, the day's dealt memory and the cool-off —
while the durable pass record stays, so that a re-shown card is still a re-show.
This table is the one thing that route writes: **the moment it was pressed**, per
player and per sport, and nothing about what it cleared. Each of the three is
derived at the next deal from the record it lives on — the pass row, the search
row, the game — read against this moment, so a column listing any of it would be
a copy of another table free to disagree with it.

**A durable row rather than a Redis key, and the direction of failure is why.**
Two of the three things it clears are read from rows that do not fail soft, so a
reset that could be lost on a cache outage would re-hide the people a player just
asked to see — the *empty the deck* failure every soft ledger in this module is
soft in order to avoid. And the ADR accepts a cost only a record can pay:
`PASS_SUPPRESS`'s falsifier now excludes re-shows a reset caused, and which those
are is computable only while every reset moment is on file.

**`deck_reset` is append-only and never deleted from**, on `player_pass`'s own
argument: the primary key is a surrogate rather than `(player, sport)`, because a
second press is a second fact — a deal between two presses was shaped by the
first — and the deal reads the latest. Erasure will be the only path that removes
one (`docs/adr/0104` §3).

No existing row moves and no column is added elsewhere: the reset is read by the
deal and written by nothing else.

Revision ID: 0023_deck_reset
Revises: 0022_deck_no_intent
Create Date: 2026-09-15

The revision id is short because `alembic_version.version_num` is `VARCHAR(32)`:
a longer one applies its DDL and then fails writing the stamp, which leaves the
schema ahead of the version table. The **filename** carries the sentence; the id
only has to be unique.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0023_deck_reset"
down_revision = "0022_deck_no_intent"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "deck_reset",
        # A surrogate: the fact is the *press*, not the deck. See the docstring.
        sa.Column("id", UUIDType(binary=False), nullable=False),
        sa.Column("player_id", UUIDType(binary=False), nullable=False),
        sa.Column("sport", sa.String(length=50), nullable=False),
        sa.Column("reset_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_deck_reset"),
    )
    # The deal's read: *when did this player last reset this sport's deck*. The
    # moment is in the index so the latest is the end of one keyed range.
    op.create_index(
        "ix_deck_reset_player",
        "deck_reset",
        ["player_id", "sport", "reset_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_deck_reset_player", table_name="deck_reset")
    op.drop_table("deck_reset")
