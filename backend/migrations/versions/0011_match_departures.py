"""create match_departures: a leaver, her quote, her money and her outcome

ADR-0033: *"a departure's settlement and its vacancy are independent facts."*
`0009_matches` created `match_vacancies` and said in its own docstring that the
hole *"carries no amount and no outcome: what a leaver recovered is her
departure's fact, on an axis of its own, and `Raketa02/Raketa#67` is the ticket
that adds it."* This is that ticket.

**A fourth table rather than four more columns on the third**, because the two
facts have two lifecycles. A hole closes when anybody takes the seat; a
settlement closes when nobody can any more, and a filler routinely closes one
hole while settling a *different* leaver's money — ADR-0033's worked example is
a transfer whose vacancy is open and whose departure is already settled, in
front of somebody who is genuinely owed. One row could not hold both answers.

**`amount_grosze` is nullable and must never be written as zero.** ADR-0072
carries a leaver's money in **two forms** rather than one with an optional
amount, and null is how the second form is spelled here: *nothing was taken* and
*nothing has come back yet* are opposite sentences, and a zero blurs them into a
blank a reader has to interpret. The domain refuses the two rows that could not
mean anything — an amount on a reversal, and a reversal with no amount is the
only reversal there is.

**`outcome` is nullable while the departure is unsettled and only ever moves
upward afterwards.** Nothing in the schema enforces the direction and nothing
can: a `CHECK` cannot see the old value. It is a property of the domain type,
which has no operation that lowers one.

**No unique index on `(match_id, player_id)`.** A player may leave, be talked
back in, and leave again; each is its own departure with its own money. The
primary key is derived from the match, the seat and the instant, which is
already exactly *one leaving*.

Nothing here is PostgreSQL-only.

Revision ID: 0011_match_departures
Revises: 0010_match_schedule
Create Date: 2026-08-22
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0011_match_departures"
down_revision = "0010_match_schedule"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "match_departures",
        sa.Column("id", UUIDType(binary=False), primary_key=True),
        sa.Column(
            "match_id",
            UUIDType(binary=False),
            sa.ForeignKey("matches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("seat_index", sa.Integer(), nullable=False),
        # Not a foreign key, for the reason `match_seats.player_id` is not one:
        # a player lives behind a projection in another context.
        sa.Column("player_id", UUIDType(binary=False), nullable=False),
        sa.Column("departed_at", sa.DateTime(timezone=True), nullable=False),
        # The outcome label she acted on (ADR-0033's Quote).
        sa.Column("quoted", sa.String(16), nullable=False),
        # What she paid in, or null because nothing was taken. Never zero.
        sa.Column("amount_grosze", sa.Integer(), nullable=True),
        # Null until settled. Monotonic upward thereafter.
        sa.Column("outcome", sa.String(16), nullable=True),
        sa.Column("settled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_match_departures_match_id", "match_departures", ["match_id"])
    op.create_index("ix_match_departures_player_id", "match_departures", ["player_id"])


def downgrade() -> None:
    op.drop_table("match_departures")
