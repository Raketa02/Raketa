"""the likely range, on the index row that a card is assembled from

`rating.rating_initialised` has carried `range_low` / `range_high` since the
contract existed; the index simply never kept them, so a player card could print
μ and had no way to say how sure of it anybody is. Two columns, projected from
the event exactly as `band_lower` / `band_upper` already are.

**Projected, never derived.** `likely_range()` returns *unrounded* values and the
rounding lives in the engine, so a card that computed μ ± σ at assembly would own
a rounding rule for a number `rating` publishes — the second-source-of-truth
defect the band's edges being projected rather than derived settled once already.

**Nullable, like every other Level column on this table.** A Play intent may be
declared for a sport before it is rated, and such a row is kept rather than
deferred because the fold may not look anything up. The inner join that builds a
snapshot refuses a row with no `mu`, and `_decode` then requires every remaining
column — so a null that reached a search would be a broken projection rather than
a defaulted zero.

**This is not a backfill and there is nothing to backfill.** `0008` created the
table on this same branch, against a platform with no deployed environment, and
the columns arrive with the route that reads them — `0011`'s pattern, one table
over. A rebuild replays the log and fills them; `make rebuild-candidate-index`.

Revision ID: 0016_candidate_row_range
Revises: 0015_lineup_layer
Create Date: 2026-08-30

The revision id is short because `alembic_version.version_num` is `VARCHAR(32)`:
a longer one applies its DDL and then fails writing the stamp, which leaves the
schema ahead of the version table. The **filename** carries the sentence; the id
only has to be unique.
"""

import sqlalchemy as sa
from alembic import op

revision = "0016_candidate_row_range"
down_revision = "0015_lineup_layer"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("candidate_row", sa.Column("range_low", sa.Float(), nullable=True))
    op.add_column("candidate_row", sa.Column("range_high", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("candidate_row", "range_high")
    op.drop_column("candidate_row", "range_low")
