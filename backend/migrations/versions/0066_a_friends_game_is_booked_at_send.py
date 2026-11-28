"""bookings: a friends game's sender and its invited seats

**A friends game is booked the moment it is sent**
([#751](https://github.com/Rakieta02/Rakieta/issues/751);
[ADR-0202](../../docs/adr/0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md)
§5–§6). Its stream is the Booking's, in ``event_store``; these are its rows,
written by the repository's ``save`` in the same transaction:

- **``bookings.sender_id``** — the friends game's sender, ``NULL`` on every game
  a fill booked: how *at most 2 friends games waiting for answers* is counted.
- **``booking_invitations``** — one row per invited seat: the friend, the side
  the card drew them on, until when they may answer, and how they did
  (``WAITING``, ``ACCEPTED``, ``DECLINED``, ``RAN_OUT``). Read by the friend's
  Home (indexed on the player) and by the invitations job, which runs out the
  ones whose time is up (indexed on the answer and the time).

**Nothing is backfilled**: no friends game exists before this revision.

Revision ID: 0066_a_friends_game_is_booked_at_send
Revises: 0065_friend_level_asks
Create Date: 2026-11-07
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0066_a_friends_game_is_booked_at_send"
down_revision = "0065_friend_level_asks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "bookings",
        sa.Column("sender_id", UUIDType(binary=False), nullable=True),
    )
    op.create_index("ix_bookings_sender_id", "bookings", ["sender_id"])
    op.create_table(
        "booking_invitations",
        sa.Column(
            "booking_id",
            UUIDType(binary=False),
            sa.ForeignKey("bookings.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("player_id", UUIDType(binary=False), primary_key=True),
        sa.Column("side", sa.String(1), nullable=False),
        sa.Column("until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("answer", sa.String(16), nullable=False),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_booking_invitations_player_id", "booking_invitations", ["player_id"]
    )
    op.create_index(
        "ix_booking_invitations_answer_until",
        "booking_invitations",
        ["answer", "until"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_booking_invitations_answer_until", table_name="booking_invitations"
    )
    op.drop_index("ix_booking_invitations_player_id", table_name="booking_invitations")
    op.drop_table("booking_invitations")
    op.drop_index("ix_bookings_sender_id", table_name="bookings")
    op.drop_column("bookings", "sender_id")
