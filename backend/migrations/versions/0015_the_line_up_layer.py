"""Layer 4 — the winning combination and the runner-up, on the search row.

`the-group-objective.md` §6: the first three layers are all **per candidate**,
and a line-up's unit is the **combination**. Neither
[ADR-0116](../../docs/adr/0116-in-a-four-every-gate-binds-all-six-pairs.md)'s
six-pair gate nor §5's deciding reason code is falsifiable without a layer whose
unit is one, because *how many combinations the pairwise gate refused* and *what
the winner gained over the runner-up on each term* exist nowhere else.

**Two rows, not 1 771**, and that bound is the whole design. A layer holding
every combination that lost would be a group-shaped answer to *who was withheld*,
which is the question nobody may ask — and the two kept here are exactly what the
deciding margin is computed from and no more.

**One JSON column rather than a second table**, on this schema's own precedent:
`terms`, `excluded_by_gate`, `pool_description` and `rung_offers` are all opaque
blobs for the same reason. The `G` breakdown is stamped with `ruleset_version`
and the group vector may gain or lose a term between rulesets, which is precisely
what a relational schema would fight — and nothing joins to a combination, because
no route returns one.

**Line-up surfaces only, by check constraint**, the fourth on this table beside
`mode`, `intent_read` and the suppression count. It is applicable to every row
already here without a backfill, and not by luck: those rows are shortlists and
deals, and a null in a column that did not exist satisfies the biconditional on
both sides. The only row it could refuse is a line-up that forgot to record what
it compared, and there are none — this migration is what makes line-ups possible.

Revision ID: 0015_lineup_layer
Revises: 0014_deck_and_pass
Create Date: 2026-08-28

The revision id is short because `alembic_version.version_num` is `VARCHAR(32)`:
a longer one applies its DDL and then fails writing the stamp, which leaves the
schema ahead of the version table. The **filename** carries the sentence; the id
only has to be unique.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

#: The same variant the search row's other opaque columns use — `JSONB` where
#: the analyst's queries will run, plain `JSON` where the suite does — with one
#: difference the check constraint forces: `none_as_null`. By default a JSON
#: column writes a Python `None` as the JSON literal `null`, which is a value
#: rather than an absence, and every row would then read as *present* and be
#: refused. It is the first column on this table whose emptiness is checked.
BLOB = sa.JSON(none_as_null=True).with_variant(
    JSONB(none_as_null=True), "postgresql"
)

revision = "0015_lineup_layer"
down_revision = "0014_deck_and_pass"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("search", sa.Column("lineup", BLOB, nullable=True))
    op.create_check_constraint(
        "ck_search_lineup_only_where_seats_were_filled",
        "search",
        "(lineup IS NOT NULL) = (surface IN ('LINEUP', 'FILL_SEATS'))",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_search_lineup_only_where_seats_were_filled", "search", type_="check"
    )
    op.drop_column("search", "lineup")
