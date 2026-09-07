"""A recorded candidate carries the whole row that was shown.

The read-back (`GET /api/v1/searches/{id}`) reproduces the recorded answer, and
`the-two-contracts.md` §1 allows it exactly two departures: a row the live gates
now withhold, and a photo link minted per response
([ADR-0109](../../docs/adr/0109-a-read-back-names-what-it-withholds.md),
[ADR-0107](../../docs/adr/0107-the-player-card-is-assembled-outside-the-engine.md)).
Everything else must come back **as it went out** — which means it has to be on
the row, because none of the sources it was assembled from remembers what it said
an hour ago. A nickname changes, a Level moves, a player leaves an area, and a
ruleset is replaced; a read-back that re-read them would answer a different
search and call it the same one.

So four columns, and each is a fact the row could not otherwise reproduce:

- **`player_card`** — the card as it was shown, assembled outside the engine from
  the index row and `users`. It holds a **`photo_id` and never a URL**: a
  presigned link is dead within the hour and this row is kept for ever.
- **`concerns`** — the terms the engine judged genuinely weak, over *points
  forgone*. Stored rather than re-derived, because the judgement belongs to the
  ruleset this row is stamped with and re-deriving it under a later one would
  answer a question about a search that never ran. An array, for the same shape
  of query `degraded_terms` is one for.
- **`distance_km`** — whole kilometres, already promoted out of the distance
  evidence so that *Closest* reads a field rather than reaching into a variant.
  Null when the term stood down, which is **omitted** on the wire and is not a
  zero — and it is what lets the read-back say honestly which sorts it can draw.
- **`at_stake`** — what a counted game would have been worth then. Null in for
  fun, where a counted result is meaningless rather than unavailable.

**This is not a backfill and there is nothing to backfill.** `0010` created both
tables on this same branch, against a platform with no deployed environment; the
columns arrive with the route that reads them, which is the pattern `0010`'s own
docstring set for the columns three later tickets add.

Revision ID: 0011_recorded_candidate_row
Revises: 0010_search_telemetry
Create Date: 2026-08-28

The revision id is short because `alembic_version.version_num` is
`VARCHAR(32)`: a longer one applies its DDL and then fails writing the stamp,
which leaves the schema ahead of the version table. The **filename** carries the
sentence; the id only has to be unique.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0011_recorded_candidate_row"
down_revision = "0010_search_telemetry"
branch_labels = None
depends_on = None

# The same two variants `0010` declared, and the model declares, so the three
# cannot disagree about what a column is.
CODE_ARRAY = postgresql.ARRAY(sa.String()).with_variant(sa.JSON(), "sqlite")
BLOB = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    # `concerns` is `NOT NULL` because an empty list is a real answer — *the
    # engine found nothing worth warning about* — and a null would be a third
    # state meaning *we did not record it*, which is the state this migration
    # exists to remove. The server default seeds the rows `0010` could have left
    # behind and is dropped immediately: a default that stayed would let a writer
    # omit the column and look correct.
    op.add_column(
        "search_candidate",
        sa.Column("concerns", CODE_ARRAY, nullable=False, server_default="{}"),
    )
    op.alter_column("search_candidate", "concerns", server_default=None)
    op.add_column(
        "search_candidate", sa.Column("distance_km", sa.Integer(), nullable=True)
    )
    op.add_column("search_candidate", sa.Column("player_card", BLOB, nullable=True))
    op.add_column("search_candidate", sa.Column("at_stake", BLOB, nullable=True))


def downgrade() -> None:
    op.drop_column("search_candidate", "at_stake")
    op.drop_column("search_candidate", "player_card")
    op.drop_column("search_candidate", "distance_km")
    op.drop_column("search_candidate", "concerns")
