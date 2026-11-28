"""a room is filed under its booking: conversation.challenge_id becomes booking_id

**A room is opened only by a booked game** ([#575](https://github.com/Rakieta02/Rakieta/issues/575)).
A booked game's room was always filed under its booking's id — the arrangement
the game names — but the column still called it a challenge, from when a
challenge's first acceptance opened rooms too. Nothing opens a room that way any
more, so the column, its unique index and the wire field all say ``booking_id``.

**A rename, not a copy**: every row keeps its value, because for every room a
booking opened that value already *is* the booking's id. The stored opening
events are not rewritten — ``conversations.opened`` v1, which names the id
``challenge_id``, still folds (``domain/events.py``).

Revision ID: 0046_a_room_is_filed_under_its_booking
Revises: 0045_notifications
Create Date: 2026-10-06
"""

from alembic import op

revision = "0046_a_room_is_filed_under_its_booking"
down_revision = "0045_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_conversation_challenge_id", table_name="conversation")
    op.alter_column(
        "conversation", "challenge_id", new_column_name="booking_id"
    )
    op.create_index(
        "ix_conversation_booking_id", "conversation", ["booking_id"], unique=True
    )


def downgrade() -> None:
    op.drop_index("ix_conversation_booking_id", table_name="conversation")
    op.alter_column(
        "conversation", "booking_id", new_column_name="challenge_id"
    )
    op.create_index(
        "ix_conversation_challenge_id", "conversation", ["challenge_id"], unique=True
    )
