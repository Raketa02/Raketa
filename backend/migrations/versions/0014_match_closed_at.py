"""a match dates its own closing, because a card lives 24 hours from it

ADR-0073 narrows ADR-0048's `keepUntil`: *"A card lives 24 hours from the moment
it **closed**, not from when the match would have ended."* For a played match the
two coincide and `match_end` answers it, so nothing is stored; for the five
endings they do not, and the difference is the outcome nobody would defend —
*the further ahead a match was booked, the longer its corpse stays on screen*.

A cancellation's instant is the one closing a reader cannot date. `club_cancelled`
and its four siblings are booleans, and the outbox row that carries the moment is
the support trail rather than a read path (ADR-0034) — composing a home screen
out of announcements would be reading history to answer *what is true now*.

**Nullable, with no server default and no backfill.** A default would date every
row inserted without one to whenever it was inserted, which is the fabricated
observation ADR-0027 exists to remove; a backfill would have to invent an instant
for closings that were never recorded. A terminal row that predates this column
therefore has `NULL` here, and the composer reads that as ADR-0048's original
`matchEnd + 24 h` — the rule the card would have expired under before the
narrowing — rather than as *never expires*.

Revision ID: 0014_match_closed_at
Revises: 0013_category_cover
Create Date: 2026-08-23
"""

import sqlalchemy as sa
from alembic import op

revision = "0014_match_closed_at"
down_revision = "0013_category_cover"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "matches",
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("matches", "closed_at")
