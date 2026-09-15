"""the intro, on the facts row a card is assembled from

`docs/adr/0170` lets a player write one line about themselves — at most a
hundred characters, no line breaks, fenced at the write against contact — and
puts it on the player card and the record. The card is assembled from the
candidate index (`docs/adr/0107`), so the line is projected onto the per-player
facts row exactly as the tags are, from its own event
`player_profile.intro_written`.

**The one text column in the index, and deliberately unbounded.** The cap
(`INTRO_MAX_CHARACTERS`) binds the write: the domain refused anything longer
before it reached a stream, and the tail copies what the stream holds. A
`VARCHAR(100)` here would be a second fence with a different owner — raising the
cap without a migration would have Postgres refuse the projection's insert for a
line the domain had already admitted, and the tail would stall on that row.

**Nullable for the ordinary reason.** Most players write no line — the step is
optional with a visible *Skip* — and a `NULL` here is what the wire omits, never
a fact the fold failed to supply. The snapshot's join is unchanged.

**This is not a backfill and there is nothing to backfill.** No stream holds an
`intro_written` yet; the column arrives with the event that fills it, `0016`'s
pattern one table over. A rebuild replays the log and fills it;
`make rebuild-candidate-index`.

Revision ID: 0024_the_intro
Revises: 0023_deck_reset
Create Date: 2026-09-15

The revision id is short because `alembic_version.version_num` is `VARCHAR(32)`:
a longer one applies its DDL and then fails writing the stamp, which leaves the
schema ahead of the version table. The **filename** carries the sentence; the id
only has to be unique.
"""

import sqlalchemy as sa
from alembic import op

revision = "0024_the_intro"
down_revision = "0023_deck_reset"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "candidate_player_facts", sa.Column("intro", sa.Text(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("candidate_player_facts", "intro")
