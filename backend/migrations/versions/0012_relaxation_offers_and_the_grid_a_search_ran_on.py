"""The rungs a search offered, the rung it took, and the week it ran on.

[ADR-0099](../../docs/adr/0099-relaxation-offers-the-searchers-own-asks.md) makes
relaxation an **offer over the searcher's own asks**, and
[ADR-0100](../../docs/adr/0100-challenge-window-derived-never-chosen.md) makes
the window **derived from the grid the search actually ran on**. Four columns
follow, and each holds a search-time fact that cannot be reconstructed later —
`search-telemetry.md`'s standing rule, and the reason these tables are wide:

- **`rung_offers`** — which of A/B/C were offered and each one's **real** count,
  from a genuine re-run. `NULL` means the offers were **not computed at all**,
  because the shortlist cleared `MIN_SHORTLIST`; an empty list means computed and
  none available. That difference is `MIN_SHORTLIST`'s own falsifier and it is
  read straight off these rows, so the two states may never be collapsed.
- **`offered_by_search_id`** and **`rung_taken`** — the pair that makes take-up a
  **join**. An accepted widen is a new search citing the one that offered it, so
  *what was offered* and *what the same person did next* are two rows and the
  table stays append-only. A check constraint keeps them from being written half:
  a rung named without a citation is a numerator with no denominator.
  `ON DELETE RESTRICT` rather than a cascade, because nothing deletes a search —
  erasure will be the only path that ever does, and it will have to decide what a
  citation of an erased search means rather than discovering it as a null.
- **`searcher_grid`** — the week this search ran on: the profile's own, or the
  one a rung-A widening improvised for this search alone. It is stored so the
  window can be **re-derived** from it rather than read back as a stored label —
  a label read back is how a stale window ships the day `window_of` changes,
  where this grid and the row's own `at` reproduce the answer that was given.

**Not a backfill, and there is nothing to backfill.** `0010` created the table on
this same branch against a platform with no deployed environment, and the columns
arrive with the code that reads them.

Revision ID: 0012_relaxation_offers_and_the_grid_a_search_ran_on
Revises: 0011_search_candidate_records_the_answer
Create Date: 2026-08-28
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0012_relaxation_offers_and_the_grid_a_search_ran_on"
down_revision = "0011_search_candidate_records_the_answer"
branch_labels = None
depends_on = None

# The same two variants `0010`, `0011` and the model declare, so the four cannot
# disagree about what a column is.
CODE_ARRAY = postgresql.ARRAY(sa.String()).with_variant(sa.JSON(), "sqlite")
BLOB = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    # `NOT NULL` because every search runs on some grid — a blank week is a real
    # answer and an empty array says so, where a null would mean *we did not
    # record it* and would make the window underivable for that row for ever.
    # The server default seeds whatever `0010` left behind and is dropped
    # immediately: a default that stayed would let a writer omit the column and
    # still look correct.
    op.add_column(
        "search",
        sa.Column("searcher_grid", CODE_ARRAY, nullable=False, server_default="{}"),
    )
    op.alter_column("search", "searcher_grid", server_default=None)
    op.add_column("search", sa.Column("rung_offers", BLOB, nullable=True))
    op.add_column(
        "search",
        sa.Column(
            "offered_by_search_id",
            UUIDType(binary=False),
            sa.ForeignKey("search.id", ondelete="RESTRICT"),
            nullable=True,
        ),
    )
    op.add_column("search", sa.Column("rung_taken", sa.String(1), nullable=True))
    op.create_check_constraint(
        "ck_search_rung_taken_cites_its_offer",
        "search",
        "(rung_taken IS NULL) = (offered_by_search_id IS NULL)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_search_rung_taken_cites_its_offer", "search")
    op.drop_column("search", "rung_taken")
    op.drop_column("search", "offered_by_search_id")
    op.drop_column("search", "rung_offers")
    op.drop_column("search", "searcher_grid")
