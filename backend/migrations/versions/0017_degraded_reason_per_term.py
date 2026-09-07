"""a degraded term records whose gap it is

`Fit.degraded_terms` is the renormalisation basis, and until now it was a flat
list of `Term` holding two different sentences as one fact: *reliability is not a
thing on this platform yet* and *they have not said what kind of evening they
want*. `floor.py` refuses that conflation by name, at the exact point it changes
a number — *the gate counts person-specific gaps and never platform-wide
absence* — and the wire committed it twenty times a search.

**Index-aligned, and never folded into `degraded_terms`.** `0011`'s own argument
for lifting that column out of the opaque `terms` blob was that a per-term
`NoEvidence` rate has to be an array query rather than a blob scan; widening it
to JSONB pairs would spend exactly that. So the reason travels beside it, one
code per entry, in the same order.

**`missing_terms` stays and is not replaced.** It answers a floor investigation —
*nobody was good enough* against *nobody was known enough* — and is stamped by
the evidence gate's own `live`/`fired`, where this column is stamped by the term
that stood down. Two columns computing overlapping facts is how they drift, so
the relationship is asserted rather than trusted:
`missing_terms == [t for t, r in zip(degraded_terms, degraded_reasons) if r is
not NOT_YET_ON_THIS_PLATFORM]`, over real recorded rows in
`tests/unit/test_run_shortlist_search.py`. The two columns' own alignment is a
`SearchCandidateRecord` invariant, refused at the write rather than at the wire.

**This is not a backfill and there is nothing to backfill.** `0010` created the
table on this same branch, against a platform with no deployed environment, and
the column arrives with the contract change that reads it — `0011`'s pattern on
the same table. It is `nullable=False` with a server-side empty default for the
duration of the DDL only, because a row with a `degraded_terms` and no reasons
beside it would be a basis nobody can read, which is the shape this column exists
to refuse.

Revision ID: 0017_degraded_reasons
Revises: 0016_candidate_row_range
Create Date: 2026-08-30

The revision id is short because `alembic_version.version_num` is `VARCHAR(32)`:
a longer one applies its DDL and then fails writing the stamp, which leaves the
schema ahead of the version table. The **filename** carries the sentence; the id
only has to be unique.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0017_degraded_reasons"
down_revision = "0016_candidate_row_range"
branch_labels = None
depends_on = None

# The same variant `0010`, `0011` and the model declare, so the four cannot
# disagree about what a column is.
CODE_ARRAY = postgresql.ARRAY(sa.String()).with_variant(sa.JSON(), "sqlite")


def upgrade() -> None:
    # `NOT NULL` because an empty list is a real answer — *every term fired* —
    # and a null would be a third state meaning *we did not record it*, which is
    # the state this column exists to remove. The server default is `0011`'s
    # pattern on this same table and is dropped immediately: a default that
    # stayed would let a writer omit the column and look correct, and a basis
    # with terms in it and no reasons beside them is unreadable rather than
    # empty.
    op.add_column(
        "search_candidate",
        sa.Column("degraded_reasons", CODE_ARRAY, nullable=False, server_default="{}"),
    )
    op.alter_column("search_candidate", "degraded_reasons", server_default=None)


def downgrade() -> None:
    op.drop_column("search_candidate", "degraded_reasons")
