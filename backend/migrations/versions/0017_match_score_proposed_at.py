"""a proposal carries its own deadline, so silence can answer it

ADR-0048 replaces *"`resultWindow` as a single constant"* with two — an **entry
deadline** on the match and a **proposal deadline** on each proposal — and only
the first was derivable from what this table stored. The record carried *a score
is on the table* as a boolean, so *"a lone proposal unanswered for 24 hours
stands"* had no moment behind it and the ladder could not resolve it: a score
entered at hour 23 read as `playedNoScore` at hour 24 with its own answer still
running, which is the rule ADR-0048 was written to reverse.

**The moment replaces the boolean rather than joining it.** `score_proposed` was
never a column — `Match.as_record()` composed it as *there is a score and it is
not agreed* — so nothing is dropped here; what arrives is the fact that
composition could not state. A reader gets the boolean back by asking whether
this is `NULL`, which is one fact with one spelling.

**Nullable, with no server default and no backfill**, and the absent backfill is
the decision rather than the omission. A default would date every future proposal
to whenever its row was inserted, which is the fabricated observation ADR-0027
exists to remove. A backfill would have to invent an instant — and it would
invent it for **no rows**: `score_sets` is written by exactly one method, whose
only caller before this migration is a use case no route has ever mounted, so
there is no database anywhere holding a proposal. A statement that can only match
zero rows is one nothing has ever seen work.

A row that somehow held a score and no moment degrades rather than breaking: the
ladder falls through to the entry deadline and answers `playedNoScore` twenty-four
hours after the match, which is exactly what it answered before this revision.

Revision ID: 0017_match_score_proposed_at
Revises: 0016_match_standby_places
Create Date: 2026-08-24
"""

import sqlalchemy as sa
from alembic import op

revision = "0017_match_score_proposed_at"
down_revision = "0016_match_standby_places"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "matches",
        sa.Column("score_proposed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("matches", "score_proposed_at")
