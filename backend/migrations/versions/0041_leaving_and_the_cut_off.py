"""leaving a booked game, and the cut-off

**A player may leave a booked game, and a game plays full or not at all**
([#544](https://github.com/Raketa02/Raketa/issues/544); the mechanics §12.3,
§13, §15.4; ADR-0189 §5). The Booking stream records the leaving and the
call-off; its projections learn them:

- **``bookings.state``** gains ``SEAT_OPEN`` — booked and paid, a seat open —
  which still holds its court and is still a game in a player's week.
- **``bookings.open_since``** — when the first seat still open opened — read
  with the state and the cut-off by the cut-off job: a seat open since before
  the cut-off is what calls a game off at it.
- **``booking_seats.left_at``** — a leaver keeps their seat row, marked: the
  record reads who ever held a seat, every other read the seats still held.

Revision ID: 0041_leaving_and_the_cut_off
Revises: 0040_on_request_the_club_confirms
Create Date: 2026-10-01
"""

import sqlalchemy as sa
from alembic import op

revision = "0041_leaving_and_the_cut_off"
down_revision = "0040_on_request_the_club_confirms"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "bookings",
        sa.Column("open_since", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_bookings_state_cut_off", "bookings", ["state", "cut_off"])
    op.add_column(
        "booking_seats",
        sa.Column("left_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    # A leaver had no seat on the projection before this one knew leaving, and
    # a game with a seat open was a booked game to everybody who read it.
    op.execute("DELETE FROM booking_seats WHERE left_at IS NOT NULL")
    op.drop_column("booking_seats", "left_at")
    op.execute("UPDATE bookings SET state = 'BOOKED' WHERE state = 'SEAT_OPEN'")
    op.drop_index("ix_bookings_state_cut_off", table_name="bookings")
    op.drop_column("bookings", "open_since")
