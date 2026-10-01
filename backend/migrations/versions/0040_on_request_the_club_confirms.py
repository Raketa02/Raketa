"""on request: a booking waits for the club, and a game it turned down ends

**At an On request club a full game waits for the club's answer** — nobody pays
until it accepts ([#543](https://github.com/Raketa02/Raketa/issues/543); the
mechanics §16.3, §16.8; ADR-0189 §3, §5). The Booking stream records it; its
projections learn it:

- **``bookings.state``** — ``WAITING_FOR_THE_CLUB``, ``BOOKED`` or
  ``CALLED_OFF``; every booking before this one was booked. **A request holds
  its court as a booking does, and a called-off booking holds nothing**, so the
  court hour's unique index becomes partial: the hour is the club's to sell
  again the moment a request is refused, unanswered or withdrawn, and the
  called-off row stays for its players to read why.
- **``bookings.answer_by``** — when the club's answer is due, indexed with the
  state for the timeout job's read.
- **``bookings.game_id`` and ``bookings.booked_at``** become nullable: a
  request has no Game until the club says yes, and a refused one never has.

And the proposal projection learns the wait: ``proposals.waiting_for_the_club``
— every seat In and the club still to answer, which the book-by no longer ends —
and ``proposals.ended`` gains ``TURNED_DOWN``.

Revision ID: 0040_on_request_the_club_confirms
Revises: 0039_the_fill_books_a_court
Create Date: 2026-10-01
"""

import sqlalchemy as sa
from alembic import op

revision = "0040_on_request_the_club_confirms"
down_revision = "0039_the_fill_books_a_court"
branch_labels = None
depends_on = None

_ENDED = "ck_proposals_ended"
_COURT_HOUR = "ux_bookings_court_id_start"
_HOLDS_ITS_COURT = "state <> 'CALLED_OFF'"


def upgrade() -> None:
    op.add_column(
        "bookings",
        sa.Column("state", sa.String(32), nullable=False, server_default="BOOKED"),
    )
    op.add_column(
        "bookings",
        sa.Column("answer_by", sa.DateTime(timezone=True), nullable=True),
    )
    op.alter_column("bookings", "game_id", nullable=True)
    op.alter_column("bookings", "booked_at", nullable=True)
    op.drop_index(_COURT_HOUR, table_name="bookings")
    op.create_index(
        _COURT_HOUR,
        "bookings",
        ["court_id", "start"],
        unique=True,
        postgresql_where=sa.text(_HOLDS_ITS_COURT),
    )
    op.create_index("ix_bookings_state_answer_by", "bookings", ["state", "answer_by"])

    op.add_column(
        "proposals",
        sa.Column(
            "waiting_for_the_club",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.drop_constraint(_ENDED, "proposals", type_="check")
    op.create_check_constraint(
        _ENDED,
        "proposals",
        "ended IS NULL OR ended IN ('FILLED', 'EXPIRED', 'WITHDRAWN', "
        "'COURT_HOUR_LOST', 'TURNED_DOWN')",
    )


def downgrade() -> None:
    # A game its club turned down is over and nobody paid, which is what an
    # expired one says too.
    op.execute("UPDATE proposals SET ended = 'EXPIRED' WHERE ended = 'TURNED_DOWN'")
    op.drop_constraint(_ENDED, "proposals", type_="check")
    op.create_check_constraint(
        _ENDED,
        "proposals",
        "ended IS NULL OR ended IN ('FILLED', 'EXPIRED', 'WITHDRAWN', "
        "'COURT_HOUR_LOST')",
    )
    op.drop_column("proposals", "waiting_for_the_club")

    # A booking that never booked has no Game to keep a row for: the stream is
    # the record, and its projection before this one knew only booked games.
    op.execute("DELETE FROM bookings WHERE game_id IS NULL")
    op.drop_index("ix_bookings_state_answer_by", table_name="bookings")
    op.drop_index(_COURT_HOUR, table_name="bookings")
    op.create_index(_COURT_HOUR, "bookings", ["court_id", "start"], unique=True)
    op.alter_column("bookings", "booked_at", nullable=False)
    op.alter_column("bookings", "game_id", nullable=False)
    op.drop_column("bookings", "answer_by")
    op.drop_column("bookings", "state")
