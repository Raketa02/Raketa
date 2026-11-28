"""proposals: a game waits for one payment

**Time to pay** ([#625](https://github.com/Rakieta02/Rakieta/issues/625),
[#626](https://github.com/Rakieta02/Rakieta/issues/626); the mechanics §12.2,
Q109–Q112). A share refused as a full game fills — or as its On request club
says yes — holds that player's seat for thirty minutes, never past the book-by,
and the game waits for the payment. Two facts on the proposals row, each written
from the aggregate on every save:

- **``proposals.paying_until``** — the earliest deadline among the payments the
  game waits for, ``NULL`` while it waits for none. The job that runs a time to
  pay out reads it, by deadline; and the book-by sweep leaves a game with one,
  since that job is what ends it.
- **``proposals.payment_awaited_at``** — when a game at a club that books at
  once first waited for a payment. Such a game has no booking until it books,
  and is on its players' Home from that moment: *Waiting for one payment*, then
  *Seat open* if the time runs out.

Every proposal recorded before it waited for nobody's payment.

Revision ID: 0053_a_game_waits_for_one_payment
Revises: 0052_a_notice_knows_its_reader_left
Create Date: 2026-10-10
"""

import sqlalchemy as sa
from alembic import op

revision = "0053_a_game_waits_for_one_payment"
down_revision = "0052_a_notice_knows_its_reader_left"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "proposals",
        sa.Column("paying_until", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "proposals",
        sa.Column("payment_awaited_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_proposals_paying_until", "proposals", ["paying_until"])


def downgrade() -> None:
    # The proposal streams still say whose payment was awaited, and until
    # when; the projection forgets it.
    op.drop_index("ix_proposals_paying_until", table_name="proposals")
    op.drop_column("proposals", "payment_awaited_at")
    op.drop_column("proposals", "paying_until")
