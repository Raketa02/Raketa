"""create match_standby_places: who asked to be told if a seat frees

ADR-0087 gives leaving standby a write, and `Raketa02/Raketa#81` is the ticket
that discovers there was never anything to leave: `kernel.Viewer` has carried an
`on_standby` flag since the ladder shipped, `NotOnStandby` has been one of the
eight eligibility rules since the funnel did, and **nothing anywhere in the
product recorded that a player had asked**. This is the store.

**A membership row and not a column on `match_seats`.** A standby place is
attached to no seat — that is the whole of what `CONTEXT.md` means by *priority,
not a place* — so there is no seat for a column to hang on, and the queue's
length is not bounded by the seat count.

**Not part of the `Match` aggregate, and the reason is the version column.**
ADR-0034 makes `matches.version` the concurrency guard, bumped by every write
that goes through the aggregate; a standby join changes nothing a rung reads
about the match, and routing it through the aggregate would bump that version,
serialise joins against seat payments, and invalidate the scoring-context cache
keyed `matchId : recordVersion` every time somebody queued. It is a sixth table
beside the match for the same reason the seat claims are a fifth.

**Unique over `(match_id, player_id)`, and here that is right where it was
wrong for the departures.** A player may leave a match, be talked back in and
leave again, so each departure is its own row; a standby place has no such
history to keep — asking twice is asking once, which is exactly what makes the
`DELETE` idempotent by nature and lets ADR-0087 refuse an idempotency key. The
uniqueness is the database's half of that sentence.

**Deleted, not ended**, which is the opposite of every other child table here
and is a deliberate departure. A vacancy, a departure and a seat claim are all
kept because *what happened at 18:03* is a support question about money or
about a seat somebody could not take. Standby confers no place and moves no
money: there is no fact a tombstone would preserve, and ADR-0087's *"rejoining
costs what joining cost, which is nothing"* is only true if the platform is not
quietly keeping a record of every time she changed her mind.

`joined_at` is stored because nothing derives it and the cascade may one day
want to break a tie by it — it is **not** read today, and rung 1 is fit-ordered
(ADR-0061), so it is a fact rather than an ordering.

Nothing here is PostgreSQL-only.

Revision ID: 0016_match_standby_places
Revises: 0015_command_log
Create Date: 2026-08-23
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0016_match_standby_places"
down_revision = "0015_command_log"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "match_standby_places",
        sa.Column(
            "match_id",
            UUIDType(binary=False),
            sa.ForeignKey("matches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Not a foreign key, for the reason `match_seats.player_id` is not one:
        # a player lives behind a projection in another context.
        sa.Column("player_id", UUIDType(binary=False), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        # Named, like `pk_command_log`, because this key is the thing the
        # decision rests on: a constraint a support agent can find by name in a
        # PostgreSQL error is one somebody can reason about.
        sa.PrimaryKeyConstraint(
            "match_id", "player_id", name="pk_match_standby_places"
        ),
    )
    # The cascade asks *who is queued for this match* and the strip asks *what
    # is this player queued for*. The composite primary key answers the first
    # from its own left edge; the second needs its own index, and it is the one
    # a home screen pays on every compose.
    op.create_index(
        "ix_match_standby_places_player_id", "match_standby_places", ["player_id"]
    )


def downgrade() -> None:
    op.drop_table("match_standby_places")
