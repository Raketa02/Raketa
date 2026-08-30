"""The decline row — the half of ADR-0094's pattern that was owed.

That record paired an inline offer with a **30-day suppression on decline** and
put the suppression *"in the sweeper's Redis with a TTL"*. Its amendment bends
that one clause and keeps every other word: *for that sport*, *30 days*, and
*declining a prompt is not a domain fact and earns no event* — a pass earns no
event either, and is still a durable row.

This migration is that amendment. `prompts.py`'s two constants declare falsifiers
a TTL destroys — *take-up rate on the prompt* and *acceptance rate on the offer* —
and of a prompt's three outcomes only the decline is nowhere: a raise is
recomputable from the search store forever and an accept writes a value through
the route that owns it. So the decline earns a row, and **nothing else does**:
there is deliberately no `prompts_raised` column on `search`, because
`ShortlistAnswer.prompts` is beside the record rather than on it and the raise
runs after the commit (`search-telemetry.md` §6).

**Append-only, and never deleted from.** Erasure will be the only path that
removes one, which is `docs/adr/0104` §3's rule for the search and pass records.
The primary key is a **surrogate**: a natural key on the player and the prompt
would collapse a second *not now* into the first, and a decline never escalates.

**`sport` is nullable and the null is the meaning** — *this player, every sport*,
which is what a search radius and an availability grid are facts about, where a
declaration is per sport. There is no check constraint restating that mapping in
SQL: a biconditional naming prompt codes here would be a second copy of a table
the domain owns, drifting the first time a fifth prompt is added.

Revision ID: 0018_prompt_decline
Revises: 0017_degraded_reasons
Create Date: 2026-08-30

The revision id is short because `alembic_version.version_num` is `VARCHAR(32)`:
a longer one applies its DDL and then fails writing the stamp, which leaves the
schema ahead of the version table. The **filename** carries the sentence; the id
only has to be unique.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0018_prompt_decline"
down_revision = "0017_degraded_reasons"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "prompt_decline",
        # A surrogate: the fact is the *answer*, not the question. See the
        # docstring.
        sa.Column("id", UUIDType(binary=False), nullable=False),
        sa.Column("player_id", UUIDType(binary=False), nullable=False),
        # The prompt's own code and never the value it quoted: the player
        # answered about a habit, and the ladder hands them a different number
        # next month.
        sa.Column("prompt", sa.String(length=50), nullable=False),
        # What the silence is keyed by, not the sport the search was in.
        sa.Column("sport", sa.String(length=50), nullable=True),
        sa.Column("declined_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_prompt_decline"),
    )
    # The filter's read: *what has this player declined lately*, both families at
    # once. The date is in the index because the window is always applied.
    op.create_index(
        "ix_prompt_decline_player",
        "prompt_decline",
        ["player_id", "declined_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_prompt_decline_player", table_name="prompt_decline")
    op.drop_table("prompt_decline")
