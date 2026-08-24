"""create match_offers and match_cascade_waves: the invitation ladder's two stores

ADR-0061 replaced ADR-0052's exclusive offer with one open call at every
distance from the match, and `Raketa02/Raketa#82` is the ticket that builds it.
Two tables, because ADR-0061's *"all-at-once puts every piece of state on the
vacancy — an eligible set computed once, two dispatch jobs, first-to-accept
wins"* is exactly two things: what was told to whom, and what is left to tell.

**They belong to Now, which has never owned a table before.** Every other write
on that screen goes through another context's aggregate; these do not, because
**the match is unchanged by an offer** — no rung reads one, no deadline moves,
no seat changes state. That is ADR-0091's argument for keeping the standby queue
out of the aggregate, and it is stronger here: routing an offer through ``Match``
would bump ADR-0034's version column on every dispatch and invalidate the
scoring-context cache keyed ``matchId : recordVersion``, so forty people told
about a seat would cost forty misses on the busiest read in the product.

**`match_offers` is keyed on the hole and not on the match.** Rung 3 of the
ladder is *offered an earlier vacancy on this match and did not get it*, which is
a comparison of holes: filed under the match alone, a second hole could not be
told from the first and that rung would answer *everybody already told* — every
rung below it collapsed into one. The key is also the database's half of
ADR-0061's *"a lapse resumes them and nobody is told twice"*; the caller filters
first, so the key only ever fires on a genuine race.

**Nothing is withdrawn and nothing is deleted.** ADR-0061 keeps a taken seat
honest by the wording — *"a seat just opened, first to take it"* stays true after
somebody else takes it — and ADR-0062 adds that nothing is ever removed from a
lock screen. So there is no `withdrawn_at` and no status column: an offer is a
fact about the past, and *is the seat still there* is a question about the match,
asked live.

**`match_cascade_waves` is its own queue and not the match's schedule.**
`next_wake_at` is computed by the kernel from the record on every write
(ADR-0076), and a dispatch is not a boundary the ladder reads — nothing about the
match resolves differently at vacancy + 10 minutes. Putting it there would be a
threshold in the timekeeper, which ADR-0076 forbids by name and
`tests/unit/test_timekeeper_holds_no_thresholds.py` reddens on. It is the same
line `#84` draws for the push sends.

`dispatched_at` is the whole of the state: null is outstanding, set is done — and
a dispatch that reached **nobody** is still done, because an empty rung is a real
answer and a row left due would re-run the whole pool every tick for a hole
nobody can fill. Its index is **partial over the outstanding rows**, like
`ix_matches_next_wake_at`: the done rows are the ones that accumulate, and an
index carrying them all would grow without bound for a query that never reads
them.

Neither table announces anything, on ADR-0091's rule. Nothing here is
PostgreSQL-only — the partial index is expressed for both dialects, and SQLite
has supported partial indexes since 3.8.

Revision ID: 0018_match_offers_and_cascade_waves
Revises: 0017_match_score_proposed_at
Create Date: 2026-08-24
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0018_match_offers_and_cascade_waves"
down_revision = "0017_match_score_proposed_at"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "match_offers",
        sa.Column("vacancy_id", UUIDType(binary=False), nullable=False),
        # Not a foreign key, for the reason `match_seats.player_id` is not one:
        # a player lives behind a projection in another context.
        sa.Column("player_id", UUIDType(binary=False), nullable=False),
        sa.Column(
            "match_id",
            UUIDType(binary=False),
            sa.ForeignKey("matches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rung", sa.SmallInteger(), nullable=False),
        sa.Column("fit", sa.SmallInteger(), nullable=False),
        sa.Column("price_grosze", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("offered_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("vacancy_id", "player_id", name="pk_match_offers"),
    )
    # Rung 3 asks *who has been told about any hole in this match*, and the
    # offers region asks *what has been offered to this player*. The composite
    # key answers neither from its own left edge.
    op.create_index("ix_match_offers_match_id", "match_offers", ["match_id"])
    op.create_index("ix_match_offers_player_id", "match_offers", ["player_id"])

    op.create_table(
        "match_cascade_waves",
        sa.Column("vacancy_id", UUIDType(binary=False), nullable=False),
        sa.Column("wave", sa.SmallInteger(), nullable=False),
        sa.Column(
            "match_id",
            UUIDType(binary=False),
            sa.ForeignKey("matches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint(
            "vacancy_id", "wave", name="pk_match_cascade_waves"
        ),
    )
    op.create_index(
        "ix_match_cascade_waves_due_at",
        "match_cascade_waves",
        ["due_at"],
        postgresql_where=sa.text("dispatched_at IS NULL"),
        sqlite_where=sa.text("dispatched_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_table("match_cascade_waves")
    op.drop_table("match_offers")
