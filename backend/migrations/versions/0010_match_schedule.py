"""the schedule is a column: next_wake_at, wake_reason, and one partial index

ADR-0076: *"A match carries `next_wake_at` and `wake_reason`, recomputed on
**every** write, under a partial index over non-terminal rows."* This is the
whole of the timekeeper's storage — no queue table, no timer store, no Redis.

**Two derived columns on a table whose every other column earns its place by
being underivable.** ADR-0034's five kinds refuse a stored `filled`, a stored
situation, a stored court; these two are computed by `kernel.next_wake` from the
row they sit on, and they are stored anyway. The reason is the direction of the
question: *when does this match next change* is a function call, and *which
matches change in the next second* is a scan. A function cannot be indexed.

**The index is partial on `next_wake_at IS NOT NULL`, not on the four
cancellation flags.** Both spell *non-terminal rows* today, and the second is a
restatement of rungs 1-4 in SQL — a second ladder (ADR-0040), in the schema,
where nothing type-checks it. It also fails in the silent direction: the wider
predicate over-covers by a page, and the narrower one, once it drifts, leaves a
due row unindexed and a club's court held for ever. The column being present is
already exactly *there is something to look at*, because `next_wake` answers
`None` for a terminal match — and for a settled one past its result window,
which is not terminal and has nothing left to wake for either.

Nothing here is PostgreSQL-only: the partial index has a SQLite spelling and
gets one, so `scripts/test-postgres-gates.sh` is untouched and the rule is
enforced by the fast suite.

Revision ID: 0010_match_schedule
Revises: 0009_matches
Create Date: 2026-08-22
"""

import sqlalchemy as sa
from alembic import op

revision = "0010_match_schedule"
down_revision = "0009_matches"
branch_labels = None
depends_on = None

#: A row is due to be looked at exactly when it names a moment. The same string
#: `app/modules/matches/infrastructure/sqlalchemy_match_models.py` declares, and
#: `tests/unit/test_matches_migration.py` fails if the two drift.
SCHEDULED = "next_wake_at IS NOT NULL"


def upgrade() -> None:
    op.add_column(
        "matches",
        sa.Column("next_wake_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "matches",
        sa.Column("wake_reason", sa.String(24), nullable=True),
    )
    op.create_index(
        "ix_matches_due_wake",
        "matches",
        ["next_wake_at"],
        postgresql_where=sa.text(SCHEDULED),
        sqlite_where=sa.text(SCHEDULED),
    )
    # Existing rows are left with a null schedule deliberately, and it repairs
    # itself: the columns are recomputed on every write, so the first thing that
    # touches a match arms it. Backfilling here would mean running the ladder in
    # a migration — a second implementation of `kernel.next_wake`, in SQL, at the
    # one moment nothing is watching. There are no deployed environments
    # (ADR-0010), so the set of rows this could have stranded is the seed's.


def downgrade() -> None:
    op.drop_index("ix_matches_due_wake", table_name="matches")
    op.drop_column("matches", "wake_reason")
    op.drop_column("matches", "next_wake_at")
