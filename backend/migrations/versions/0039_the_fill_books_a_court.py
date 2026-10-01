"""the fill: a booking holds a court, and every seat is charged

**The last yes books the game** ([#541](https://github.com/Raketa02/Raketa/issues/541);
the mechanics §11–§12.2; ADR-0189 §2, §4–§5). The Booking and the Seat charge
are streams in ``event_store`` and need no table; their projections do:

- **``bookings``** — one row per booking: the club, the court and the hour it
  holds, so what a club can still sell is one read by club and start. A court
  hour is held by one booking (``ux_bookings_court_id_start``).
- **``booking_seats``** — one row per player on a booking and their side, so a
  player's booked games — *games per week*, *one game per hour* — are one read.
- **``seat_charges``** — one row per charge: whose share, for which game, its
  payment at the provider and where it stands, so receipts, the next fill and a
  provider's notice each find their charges in one read.

And the proposal projections learn the fill: ``proposals.ended`` gains
``FILLED``, and ``proposal_people.answer`` gains ``PAUSED`` — a yes another
booking holds the player's week against.

Revision ID: 0039_the_fill_books_a_court
Revises: 0038_club_payments_accounts
Create Date: 2026-10-01
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0039_the_fill_books_a_court"
down_revision = "0038_club_payments_accounts"
branch_labels = None
depends_on = None

_ENDED = "ck_proposals_ended"
_ANSWER = "ck_proposal_people_answer"


def upgrade() -> None:
    op.create_table(
        "bookings",
        sa.Column("id", UUIDType(binary=False), primary_key=True),
        sa.Column("pool_id", UUIDType(binary=False), nullable=False),
        sa.Column("club_id", UUIDType(binary=False), nullable=False),
        sa.Column("court_id", UUIDType(binary=False), nullable=False),
        sa.Column("sport", sa.String(32), nullable=False),
        sa.Column("start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("share_grosze", sa.Integer(), nullable=False),
        sa.Column("cut_off", sa.DateTime(timezone=True), nullable=False),
        sa.Column("game_id", UUIDType(binary=False), nullable=False),
        sa.Column("booked_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ux_bookings_court_id_start", "bookings", ["court_id", "start"], unique=True
    )
    op.create_index("ix_bookings_club_id_start", "bookings", ["club_id", "start"])
    op.create_table(
        "booking_seats",
        sa.Column(
            "booking_id",
            UUIDType(binary=False),
            sa.ForeignKey("bookings.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("player_id", UUIDType(binary=False), primary_key=True),
        sa.Column("side", sa.String(1), nullable=False),
    )
    op.create_index("ix_booking_seats_player_id", "booking_seats", ["player_id"])
    op.create_table(
        "seat_charges",
        sa.Column("charge_id", UUIDType(binary=False), primary_key=True),
        sa.Column("player_id", UUIDType(binary=False), nullable=False),
        sa.Column("game_id", UUIDType(binary=False), nullable=False),
        sa.Column("club_id", UUIDType(binary=False), nullable=False),
        sa.Column("payment_id", sa.String(255), nullable=True),
        sa.Column("amount_grosze", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("taken_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('AUTHORISED', 'FAILED', 'TAKING', 'CAPTURED', 'RELEASING', "
            "'CANCELLED')",
            name="ck_seat_charges_status",
        ),
    )
    op.create_index("ix_seat_charges_game_id", "seat_charges", ["game_id"])
    op.create_index(
        "ix_seat_charges_player_id_taken_at", "seat_charges", ["player_id", "taken_at"]
    )
    op.create_index("ix_seat_charges_payment_id", "seat_charges", ["payment_id"])

    op.drop_constraint(_ENDED, "proposals", type_="check")
    op.create_check_constraint(
        _ENDED,
        "proposals",
        "ended IS NULL OR ended IN ('FILLED', 'EXPIRED', 'WITHDRAWN', "
        "'COURT_HOUR_LOST')",
    )
    op.drop_constraint(_ANSWER, "proposal_people", type_="check")
    op.create_check_constraint(
        _ANSWER,
        "proposal_people",
        "answer IS NULL OR answer IN ('YES', 'NO', 'WITHDRAWN', 'PAUSED')",
    )


def downgrade() -> None:
    # A paused yes is a yes that does not count, which is what a withdrawn one
    # says too; a filled game is over and nothing on the card stands, as an
    # expired one's does not.
    op.execute(
        "UPDATE proposal_people SET answer = 'WITHDRAWN' WHERE answer = 'PAUSED'"
    )
    op.drop_constraint(_ANSWER, "proposal_people", type_="check")
    op.create_check_constraint(
        _ANSWER,
        "proposal_people",
        "answer IS NULL OR answer IN ('YES', 'NO', 'WITHDRAWN')",
    )
    op.execute("UPDATE proposals SET ended = 'EXPIRED' WHERE ended = 'FILLED'")
    op.drop_constraint(_ENDED, "proposals", type_="check")
    op.create_check_constraint(
        _ENDED,
        "proposals",
        "ended IS NULL OR ended IN ('EXPIRED', 'WITHDRAWN', 'COURT_HOUR_LOST')",
    )
    op.drop_table("seat_charges")
    op.drop_table("booking_seats")
    op.drop_table("bookings")
