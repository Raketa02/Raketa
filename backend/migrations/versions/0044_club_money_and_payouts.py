"""club money and payouts: a club is paid after the game

**The club sees its money, and is paid after the game is played**
([#548](https://github.com/Rakieta02/Rakieta/issues/548); the mechanics §12.6,
§16.11, §16.12; ADR-0189 §4). A new stream — the **Club payout**, one per club
per day it is paid for — and the club's day of new bookings summed up once,
another stream with no projection. The projections need:

- **``seat_charges.starts_at``** — the game's hour, so the payouts job reads as
  candidates only the games of days that have closed. Filled here from each
  charge's first event, which has always carried it.
- **``club_payouts``** — each payout decided, and when the provider took it.
- **``club_payout_games``** — the games a payout carried, **each once**: the
  primary key is what keeps a game from being paid out twice.
- **``ix_bookings_booked_at``** — a day's new bookings, the daily summary's read.

Revision ID: 0044_club_money_and_payouts
Revises: 0043_the_club_runs_its_bookings
Create Date: 2026-10-02
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0044_club_money_and_payouts"
down_revision = "0043_the_club_runs_its_bookings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "seat_charges",
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Every charge's first event — held or refused — has carried its game's
    # hour since #541; a charge it cannot be read for stays a candidate on
    # every run, which the job asks about and steps over.
    op.execute(
        """
        UPDATE seat_charges
        SET starts_at = (event_store.payload ->> 'starts_at')::timestamptz
        FROM event_store
        WHERE event_store.aggregate_type = 'seat_charge'
          AND event_store.aggregate_id = seat_charges.charge_id
          AND event_store.version = 1
        """
    )
    op.create_index("ix_seat_charges_starts_at", "seat_charges", ["starts_at"])
    op.create_table(
        "club_payouts",
        sa.Column("payout_id", UUIDType(binary=False), primary_key=True),
        sa.Column("club_id", UUIDType(binary=False), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("amount_grosze", sa.Integer(), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "club_payout_games",
        sa.Column("game_id", UUIDType(binary=False), primary_key=True),
        sa.Column(
            "payout_id",
            UUIDType(binary=False),
            sa.ForeignKey("club_payouts.payout_id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    op.create_index("ix_bookings_booked_at", "bookings", ["booked_at"])


def downgrade() -> None:
    # A payout's stream still says what it carried; the projection is gone.
    op.drop_index("ix_bookings_booked_at", table_name="bookings")
    op.drop_table("club_payout_games")
    op.drop_table("club_payouts")
    op.drop_index("ix_seat_charges_starts_at", table_name="seat_charges")
    op.drop_column("seat_charges", "starts_at")
