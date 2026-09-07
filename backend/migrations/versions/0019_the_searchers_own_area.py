"""the searcher's own area, on the search that ran on it

A card may say **`In your area · 4 km`**, and that sentence is a *comparison
between two codes* — the shape
[ADR-0021](../../docs/adr/0021-kernel-in-backend-clients-derive-by-comparison.md)
licenses a client to compute. Both codes have to reach it, and until now only the
candidate's did: `area_code` crossed on `player_card` and on the distance
evidence, and both of those are the person being looked at
([#279](https://github.com/Raketa02/Raketa/issues/279)).

**One column, and it is stored rather than looked up.** The searcher's area is on
their profile and could be read there per response — but the profile's area is
what it is *now*, and a search read back a month later would draw *in your area*
over an area the player has left. `GET /searches/{id}` never recomputes
([ADR-0104](../../docs/adr/0104-the-search-record-is-the-answer-and-never-expires.md)),
so the area the search *ran on* is a search-time fact that cannot be
reconstructed later — `search-telemetry.md`'s standing rule, and exactly why
`0012` stored `searcher_grid` beside it.

**Nullable, where `searcher_grid` is `NOT NULL`, and the difference is that an
empty week is a real answer and an empty area is not.** A blank code is a string
nothing can produce and every real code compares unequal to, which is *never in
your area* written into a column; a null says *this search did not record it*,
which is true of every row written before this migration and of no row written
after. The wire spells that absence by omitting the field
([ADR-0106](../../docs/adr/0106-evidence-vocabulary-is-contract-weights-are-configuration.md)
§4), so the one
sentence it licenses is dropped rather than answered wrongly.

**Not a backfill, and there is nothing to backfill.** `0010` created the table on
this same branch against a platform with no deployed environment, and the column
arrives with the code that reads it.

Revision ID: 0019_searcher_area
Revises: 0018_prompt_decline
Create Date: 2026-09-01

The revision id is short because `alembic_version.version_num` is `VARCHAR(32)`:
a longer one applies its DDL and then fails writing the stamp, which leaves the
schema ahead of the version table. The **filename** carries the sentence; the id
only has to be unique.
"""

import sqlalchemy as sa
from alembic import op

revision = "0019_searcher_area"
down_revision = "0018_prompt_decline"
branch_labels = None
depends_on = None


#: `areas.AREA_CODE_WIDTH`, spelled out here for `0012`'s reason — the model and
#: the migration declare a column's type twice on purpose, so that neither can
#: drift into the other's assumption. An area code is the prefix plus a signed
#: six-character latitude and a signed seven-character longitude, and is that
#: wide at every point on Earth.
AREA_CODE_WIDTH = 14


def upgrade() -> None:
    op.add_column(
        "search",
        sa.Column("searcher_area_code", sa.String(AREA_CODE_WIDTH), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("search", "searcher_area_code")
