"""The search record: one row per engine invocation, and its candidates.

`docs/adr/0104` makes every invocation durable and unexpiring, written in the
request's own transaction and committed before the response returns. **Every fact
is search-time and cannot be reconstructed afterwards — there is no backfill**,
so a column added later is a column that is null for every search before it, for
every rate the engine is judged by, forever. That is why this table is wide on
day one.

**Nothing deletes.** Erasure is the only path that ever removes a row and it does
not exist yet; when it does, it removes a player's `search` rows and their
`search_candidate` rows **in both roles**. There is deliberately no `deleted_at`
and no retention column.

**Three text arrays, and the reason is `degraded_terms`.** It is lifted out of
the opaque `terms` blob so that a per-term `NoEvidence` rate is an array query
with a GIN index rather than a JSONB scan — a term quietly dying is invisible
otherwise. `liveness_reasons` and `missing_terms` are arrays for the same shape
of query. The GIN index is **not** created here: it is a PostgreSQL index over a
table with no rows on a platform with no deployed environment, and it belongs
with the first query that needs it rather than with a guess about which.

**The columns three later tickets add are not stubbed here.** Relaxation's
`rung_offers`, `offered_by_search_id` and `rung_taken`, and the deck's
`n_excluded_by_suppression` and `suppression_lapsed`, arrive with the routes that
can write them — a nullable column nothing writes is indistinguishable from one
whose writer is broken.

Revision ID: 0010_search_telemetry
Revises: 0009_block_pair_lookup
Create Date: 2026-08-28
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0010_search_telemetry"
down_revision = "0009_block_pair_lookup"
branch_labels = None
depends_on = None

# `text[]` where the queries that need it will run, JSON where the test suite
# runs. The model declares the same variant, so the two cannot disagree.
CODE_ARRAY = postgresql.ARRAY(sa.String()).with_variant(sa.JSON(), "sqlite")

# An opaque blob: JSONB where it will be queried, JSON where the test suite runs.
# The same variant `event_store`'s own payload column uses, and for the same
# reason — `JSON` on PostgreSQL stores the text and indexes nothing.
BLOB = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")

# The same BIGINT-on-PostgreSQL / INTEGER-on-SQLite variant `event_store`'s own
# `sequence_no` uses: a watermark that could not hold every value the column it
# watermarks can hold would be a watermark with a ceiling.
SNAPSHOT_SEQUENCE = sa.BigInteger().with_variant(sa.Integer(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "search",
        sa.Column("id", UUIDType(binary=False), primary_key=True),
        sa.Column("searcher_id", UUIDType(binary=False), nullable=False),
        sa.Column("sport", sa.String(50), nullable=False),
        sa.Column("mode", sa.String(20), nullable=True),
        sa.Column("intent_read", sa.String(20), nullable=True),
        sa.Column("surface", sa.String(20), nullable=False),
        sa.Column("initiation", sa.String(20), nullable=False),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("engine_version", sa.String(50), nullable=False),
        sa.Column("ruleset_version", sa.String(50), nullable=False),
        sa.Column("snapshot_version", SNAPSHOT_SEQUENCE, nullable=False),
        sa.Column("trace_id", sa.String(64), nullable=False),
        sa.Column("index_stale", sa.Boolean(), nullable=False),
        sa.Column("n_generated", sa.Integer(), nullable=False),
        sa.Column("excluded_by_gate", BLOB, nullable=False),
        sa.Column("n_scored", sa.Integer(), nullable=False),
        sa.Column("n_cleared_floor", sa.Integer(), nullable=False),
        sa.Column("n_returned", sa.Integer(), nullable=False),
        sa.Column("n_near_miss_recorded", sa.Integer(), nullable=False),
        sa.Column("best_withheld_fit", sa.Float(), nullable=True),
        sa.Column("pool_description", BLOB, nullable=False),
        sa.Column("searcher_slot_count", sa.Integer(), nullable=False),
        sa.Column("radius_clamp_bit", sa.Boolean(), nullable=False),
        sa.Column("latency_ms_by_stage", BLOB, nullable=False),
        # **A check constraint, not a convention** (`search-telemetry.md` §2).
        # `mode` is null exactly on the deck and `intent_read` is non-null
        # exactly on the deck, and the two are mirrors — a row that broke either
        # would be a search nobody could tell the weight vector of, which is the
        # one thing an unexpiring record may not be.
        sa.CheckConstraint(
            "(mode IS NULL) = (surface = 'DECK')",
            name="ck_search_mode_null_exactly_on_the_deck",
        ),
        sa.CheckConstraint(
            "(intent_read IS NOT NULL) = (surface = 'DECK')",
            name="ck_search_intent_read_set_exactly_on_the_deck",
        ),
    )
    # Time ordering comes from here, which is why a `uuid4` id is enough and a
    # time-ordered UUID buys nothing.
    op.create_index("ix_search_searcher_at", "search", ["searcher_id", "at"])

    op.create_table(
        "search_candidate",
        sa.Column(
            "search_id",
            UUIDType(binary=False),
            sa.ForeignKey("search.id"),
            primary_key=True,
        ),
        sa.Column("band", sa.String(20), primary_key=True),
        sa.Column("position", sa.Integer(), primary_key=True),
        sa.Column("player_id", UUIDType(binary=False), nullable=False),
        sa.Column("fit", sa.Float(), nullable=False),
        sa.Column("terms", BLOB, nullable=False),
        sa.Column("degraded_terms", CODE_ARRAY, nullable=False),
        sa.Column("modifiers", BLOB, nullable=False),
        sa.Column("liveness_reasons", CODE_ARRAY, nullable=False),
        sa.Column("liveness_signals", BLOB, nullable=False),
        sa.Column("shared_count", sa.Integer(), nullable=False),
        sa.Column("their_slot_count", sa.Integer(), nullable=False),
        sa.Column("days_away", sa.Integer(), nullable=True),
        sa.Column("inclusion_reason", sa.String(30), nullable=True),
        sa.Column("withheld_reason", sa.String(30), nullable=True),
        sa.Column("missing_terms", CODE_ARRAY, nullable=False),
        sa.Column("reliability_penalty_applied", sa.Boolean(), nullable=False),
        sa.Column("reliability_penalty_decisive", sa.Boolean(), nullable=False),
    )
    # For erasure, which is the only thing that will ever delete one of these.
    op.create_index("ix_search_candidate_player", "search_candidate", ["player_id"])


def downgrade() -> None:
    op.drop_index("ix_search_candidate_player", table_name="search_candidate")
    op.drop_table("search_candidate")
    op.drop_index("ix_search_searcher_at", table_name="search")
    op.drop_table("search")
