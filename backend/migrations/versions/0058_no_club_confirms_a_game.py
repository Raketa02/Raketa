"""bookings, proposals: no club confirms a game — On request's columns go

**A full game books the moment its last yes lands, at every club**
([#669](https://github.com/Raketa02/Raketa/issues/669); ADR-0196 §1): On
request is removed, so nothing waits for a club's answer and nothing is turned
down. What only its requests used goes with it:

- **``bookings.answer_by``** and its index ``ix_bookings_state_answer_by`` —
  when the club's answer was due, and the timeout job's read of it;
- **``proposals.waiting_for_the_club``** — every seat In and the club still to
  answer, which the book-by no longer ended;
- **``proposals.ended`` no longer allows ``TURNED_DOWN``**.

**What stays, because other features use it**: ``bookings.state`` and the
court hour's partial unique index (a called-off booking holds nothing),
``bookings.game_id`` and ``bookings.booked_at`` nullable as they are, and
``proposals.club_cancelled``.

**A clean cut**: the events that wrote these left without decoders, and the
local store is reset and re-seeded after this change — only ``local`` has ever
run. A row left from before is read as what it says: a game a club turned down
is over, unfilled, nobody paid — ``EXPIRED``, as 0041's downgrade read it — and a
booking still waiting for its club, or for a payment at its yes, is called off,
so it holds no court hour (the partial index ignores ``CALLED_OFF``).

Revision ID: 0058_no_club_confirms_a_game
Revises: 0057_a_refused_rescuer_keeps_a_seat
Create Date: 2026-10-12
"""

import sqlalchemy as sa
from alembic import op

revision = "0058_no_club_confirms_a_game"
down_revision = "0057_a_refused_rescuer_keeps_a_seat"
branch_labels = None
depends_on = None

_ENDED = "ck_proposals_ended"
_ANSWER_BY = "ix_bookings_state_answer_by"


def upgrade() -> None:
    op.execute(
        "UPDATE bookings SET state = 'CALLED_OFF' "
        "WHERE state IN ('WAITING_FOR_THE_CLUB', 'WAITING_FOR_A_PAYMENT')"
    )
    op.drop_index(_ANSWER_BY, table_name="bookings")
    op.drop_column("bookings", "answer_by")

    op.drop_column("proposals", "waiting_for_the_club")
    op.execute("UPDATE proposals SET ended = 'EXPIRED' WHERE ended = 'TURNED_DOWN'")
    op.drop_constraint(_ENDED, "proposals", type_="check")
    op.create_check_constraint(
        _ENDED,
        "proposals",
        "ended IS NULL OR ended IN ('FILLED', 'EXPIRED', 'WITHDRAWN', "
        "'COURT_HOUR_LOST')",
    )


def downgrade() -> None:
    op.drop_constraint(_ENDED, "proposals", type_="check")
    op.create_check_constraint(
        _ENDED,
        "proposals",
        "ended IS NULL OR ended IN ('FILLED', 'EXPIRED', 'WITHDRAWN', "
        "'COURT_HOUR_LOST', 'TURNED_DOWN')",
    )
    op.add_column(
        "proposals",
        sa.Column(
            "waiting_for_the_club",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.add_column(
        "bookings",
        sa.Column("answer_by", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(_ANSWER_BY, "bookings", ["state", "answer_by"])
