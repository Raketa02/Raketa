"""bookings, notifications: a refused rescuer keeps a seat for thirty minutes

**A rescuer whose share was refused keeps a seat for themselves alone**
([#640](https://github.com/Rakieta02/Rakieta/issues/640); the mechanics §10.1,
Q113): their time to fix the card before the cut-off, or to pay after it, never
past the game's start, and offered to nobody else meanwhile. Two changes to
the projections, written from the streams on every save:

- **``booking_keeps``** — one row per rescuer a seat was kept for, until when,
  and whether its running out is recorded, from the Booking stream. Not a seat
  of theirs, so never a ``booking_seats`` row. The time-to-pay job reads the
  keeps run out by ``until``, and a rescuer's *To confirm* rows theirs by
  ``player_id`` — run out too, while their refused payment is still theirs to
  confirm.
- **``notices.rescue``** — a notice about a seat its player went for and does
  not hold, so it says *Fix your card by 14:40 to take the seat* rather than
  *to keep your seat*.

No seat was ever kept before: the table starts empty, and every notice given
before was about a seat its player held, or says *to take the seat* already.

Revision ID: 0057_a_refused_rescuer_keeps_a_seat
Revises: 0056_a_far_ahead_share_is_checked
Create Date: 2026-10-10
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0057_a_refused_rescuer_keeps_a_seat"
down_revision = "0056_a_far_ahead_share_is_checked"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "booking_keeps",
        sa.Column(
            "booking_id",
            UUIDType(binary=False),
            sa.ForeignKey("bookings.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("player_id", UUIDType(binary=False), primary_key=True),
        sa.Column("until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ran_out", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_booking_keeps_player_id", "booking_keeps", ["player_id"])
    op.create_index("ix_booking_keeps_until", "booking_keeps", ["until"])
    op.add_column(
        "notices",
        sa.Column("rescue", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("notices", "rescue")
    op.drop_index("ix_booking_keeps_until", table_name="booking_keeps")
    op.drop_index("ix_booking_keeps_player_id", table_name="booking_keeps")
    op.drop_table("booking_keeps")
