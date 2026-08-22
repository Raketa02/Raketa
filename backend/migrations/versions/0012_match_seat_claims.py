"""create match_seat_claims: five minutes of exclusive right to buy one seat

ADR-0081. **A seat claim is not a seat state**, and this table is that decision
in the schema: nothing here touches `match_seats`, because the seat under a live
claim is untouched — still empty, still absent from the fill count, still doing
nothing for the hold ladder. Widening the *held* state would have been one word
naming two things with opposite lifetimes, and a fourth seat state would have
grown a branch in every place that switches on one.

**A fifth table rather than three columns on the second.** A seat can be
claimed, let go and claimed again, each with its own five minutes and its own
receipt — a shape a row per seat cannot hold at all.

**Ended, never deleted.** The thirty-second cooldown before the same player may
re-claim the same seat is measured from `ended_at`, so a row that vanished would
take the cooldown with it — and *why could I not take that seat at 18:03* is a
support question a missing row cannot answer.

**`ended_at` is when the claim stopped being live**, which for an expiry is the
moment its five minutes ran out and **not** the moment a scheduled look noticed.
A worker that was down for an hour must not extend anybody's thirty seconds by
an hour.

**One partial index, and it is not unique.** `ix_match_seat_claims_unended`
answers *is this player already buying a seat, anywhere* — the one question no
single match can answer. It is partial over `ended_at IS NULL` because the ended
rows are the overwhelming majority within minutes of a busy evening and none of
them is ever an answer.

It is deliberately **not** unique, on either shape somebody might reach for:

- Over `(player_id)`: *live* is unended **and** not yet expired, and the second
  half cannot be an index predicate because it needs a clock. A unique index
  would have to spell *live* as *unended*, and would then refuse a player on the
  strength of a row nobody had got round to closing.
- Over `(match_id, seat_index)`: two claims on one seat are impossible already,
  and what makes them impossible is the `version` column on `matches` —
  ADR-0034's concurrency answer, doing the job it was chosen for. A unique index
  would additionally refuse the *legitimate* second claim on a seat whose
  previous claim expired and has not been reaped, and the write that would be
  refused is the one that reaps it.

Nothing here is PostgreSQL-only: partial indexes have a SQLite spelling and get
one, so the fast suite enforces what a real database enforces.

Revision ID: 0012_match_seat_claims
Revises: 0011_match_departures
Create Date: 2026-08-22
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0012_match_seat_claims"
down_revision = "0011_match_departures"
branch_labels = None
depends_on = None

#: The predicate, shared by the index below and by the model that declares it —
#: one string, so the two descriptions of this schema cannot drift.
CLAIM_UNENDED = "ended_at IS NULL"


def upgrade() -> None:
    op.create_table(
        "match_seat_claims",
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
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=False),
        # Stored rather than recomputed from `claimed_at`: it is the moment the
        # match's schedule is armed against and the one a client counts down to.
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        # Null while the claim is unended. Written once, never moved.
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_match_seat_claims_match_id", "match_seat_claims", ["match_id"])
    op.create_index(
        "ix_match_seat_claims_unended",
        "match_seat_claims",
        ["player_id", "expires_at"],
        unique=False,
        sqlite_where=sa.text(CLAIM_UNENDED),
        postgresql_where=sa.text(CLAIM_UNENDED),
    )


def downgrade() -> None:
    op.drop_table("match_seat_claims")
