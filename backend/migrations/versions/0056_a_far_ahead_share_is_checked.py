"""payments, bookings: a game that fills far ahead is checked, and held at its holding time

**A share whose hold would not last until the cut-off is checked at the fill
and held four days before it**
([#639](https://github.com/Raketa02/Raketa/issues/639); the mechanics Q113;
ADR-0189's 2026-10-10 amendment). A refused holding gives its player time to
fix the card on the booked game. Three changes to the projections, written from
the aggregates on every save:

- **``seat_charges.status`` may be ``CHECKED``** — held at the fill and let go
  at once, a Card check: nothing held, not paid.
- **``seat_charges.hold_at``** — a checked share's Holding time. The holding job
  reads the checked shares whose moment has come, by it.
- **``booking_seats.card_to_fix_until``** — a player whose holding was refused,
  and until when their time to fix the card runs. The time-to-pay job reads the
  times run out, and a player's *To confirm* rows theirs, by it.

Every charge recorded before was held or taken at the fill, and checked
nothing; nobody's card is to fix.

Revision ID: 0056_a_far_ahead_share_is_checked
Revises: 0055_a_notice_keeps_what_was_kept
Create Date: 2026-10-10
"""

import sqlalchemy as sa
from alembic import op

revision = "0056_a_far_ahead_share_is_checked"
down_revision = "0055_a_notice_keeps_what_was_kept"
branch_labels = None
depends_on = None

_BEFORE = (
    "status IN ('AUTHORISED', 'FAILED', 'HELD', 'TAKING', 'CAPTURED', "
    "'RELEASING', 'CANCELLED')"
)
_NOW = (
    "status IN ('AUTHORISED', 'FAILED', 'CHECKED', 'HELD', 'TAKING', "
    "'CAPTURED', 'RELEASING', 'CANCELLED')"
)


def upgrade() -> None:
    op.drop_constraint("ck_seat_charges_status", "seat_charges", type_="check")
    op.create_check_constraint("ck_seat_charges_status", "seat_charges", _NOW)
    op.add_column(
        "seat_charges",
        sa.Column("hold_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_seat_charges_status_hold_at", "seat_charges", ["status", "hold_at"]
    )
    op.add_column(
        "booking_seats",
        sa.Column("card_to_fix_until", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_booking_seats_card_to_fix_until", "booking_seats", ["card_to_fix_until"]
    )


def downgrade() -> None:
    # The code before this knows no checked share: the old check refuses to be
    # put back while any row is ``CHECKED``, so hold or close every checked
    # share before going back.
    op.drop_index("ix_booking_seats_card_to_fix_until", table_name="booking_seats")
    op.drop_column("booking_seats", "card_to_fix_until")
    op.drop_index("ix_seat_charges_status_hold_at", table_name="seat_charges")
    op.drop_column("seat_charges", "hold_at")
    op.drop_constraint("ck_seat_charges_status", "seat_charges", type_="check")
    op.create_check_constraint("ck_seat_charges_status", "seat_charges", _BEFORE)
