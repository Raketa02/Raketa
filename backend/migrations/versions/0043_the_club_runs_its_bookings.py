"""the club runs its bookings: move, cancel, check-in

**The club moves, cancels and checks in its Rakieta bookings**
([#547](https://github.com/Rakieta02/Rakieta/issues/547); the mechanics §15,
§16.7–§16.10; ADR-0189 §5). The Booking stream records each act; its
projections need one thing more:

- **``proposals.club_cancelled``** — the club cancelled the booked game the
  proposal filled, so its people are owed a new card first, as a turned-down
  game's are. The proposer reads its candidates by it beside
  ``ended = 'TURNED_DOWN'``; the stream says whether one is still owed.

Nothing else moves: a move rewrites ``bookings.court_id`` under the court
hour's own unique index, a cancel is ``state = 'CALLED_OFF'`` — which the index
already ignores, so the hour is the club's again — and a check-in is the
stream's alone.

Revision ID: 0043_the_club_runs_its_bookings
Revises: 0042_leaving_and_the_cut_off
Create Date: 2026-10-02
"""

import sqlalchemy as sa
from alembic import op

revision = "0043_the_club_runs_its_bookings"
down_revision = "0042_leaving_and_the_cut_off"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "proposals",
        sa.Column(
            "club_cancelled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    # A cancelled game's people go unowed: the stream still says they are.
    op.drop_column("proposals", "club_cancelled")
