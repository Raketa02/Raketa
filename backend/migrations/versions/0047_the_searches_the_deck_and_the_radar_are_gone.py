"""the searches, the deck and the radar are gone, and their six tables with them

**Find a game, the Players deck and its radar were removed** ([#579](https://github.com/Rakieta02/Rakieta/issues/579),
PRD #569): a game is made one way now — a group's Games deck books it — and
nothing reads or writes a search, a *Let's play*, a pass, a prompt's *not now*
or a *Show them again* any more. The six tables those records lived in go:

- ``search`` and ``search_candidate`` — the record of every shortlist, line-up,
  deal and reading (``0010`` and the columns ``0011``–``0027`` added);
- ``interest`` — *Let's play* (``0013``);
- ``player_pass`` — a pass on the deck (``0014``);
- ``prompt_decline`` — a prompt's *not now* (``0018``);
- ``deck_reset`` — *Show them again* (``0023``).

**Dropped, not emptied**: nothing will write them again, and a table nothing
writes is indistinguishable from one whose writer is broken. ``interest``,
``player_pass`` and ``search_candidate`` name ``search`` by foreign key, so they
go first. Only ``local`` runs, and its store is reset with this change
(``make down-v && make up && make seed``), so no player loses a row.

**The downgrade recreates the six tables empty**, in the shape their models
last declared, so an older checkout migrated back to ``0046`` finds the schema
it expects. The rows are not restored — nothing kept them.

Revision ID: 0047_searches_deck_and_radar_gone
Revises: 0046_a_room_is_filed_under_its_booking
Create Date: 2026-10-06
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0047_searches_deck_and_radar_gone"
down_revision = "0046_a_room_is_filed_under_its_booking"
branch_labels = None
depends_on = None

# The variants the dropped models declared, so the downgrade builds the columns
# the upgrade drops — the same spellings ``0010`` uses.
CODE_ARRAY = postgresql.ARRAY(sa.String()).with_variant(sa.JSON(), "sqlite")
BLOB = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")
NULLABLE_BLOB = sa.JSON(none_as_null=True).with_variant(
    postgresql.JSONB(none_as_null=True), "postgresql"
)
SNAPSHOT_SEQUENCE = sa.BigInteger().with_variant(sa.Integer(), "sqlite")

#: Children before ``search``, which they name by foreign key.
_DROPPED = (
    "interest",
    "player_pass",
    "search_candidate",
    "search",
    "prompt_decline",
    "deck_reset",
)


def upgrade() -> None:
    for table in _DROPPED:
        op.drop_table(table)


def downgrade() -> None:
    op.create_table(
        "search",
        sa.Column("id", UUIDType(binary=False), nullable=False),
        sa.Column("searcher_id", UUIDType(binary=False), nullable=False),
        sa.Column("sport", sa.String(length=50), nullable=False),
        sa.Column("mode", sa.String(length=20), nullable=True),
        sa.Column("intent_read", sa.String(length=20), nullable=True),
        sa.Column("surface", sa.String(length=20), nullable=False),
        sa.Column("initiation", sa.String(length=20), nullable=False),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("engine_version", sa.String(length=50), nullable=False),
        sa.Column("ruleset_version", sa.String(length=50), nullable=False),
        sa.Column("snapshot_version", SNAPSHOT_SEQUENCE, nullable=False),
        sa.Column("trace_id", sa.String(length=64), nullable=False),
        sa.Column("index_stale", sa.Boolean(), nullable=False),
        sa.Column("n_generated", sa.Integer(), nullable=False),
        sa.Column("excluded_by_gate", BLOB, nullable=False),
        sa.Column("n_scored", sa.Integer(), nullable=False),
        sa.Column("n_cleared_floor", sa.Integer(), nullable=False),
        sa.Column("n_returned", sa.Integer(), nullable=False),
        sa.Column("n_near_miss_recorded", sa.Integer(), nullable=False),
        sa.Column("best_withheld_fit", sa.Float(), nullable=True),
        sa.Column("pool_description", BLOB, nullable=False),
        sa.Column("searcher_grid", CODE_ARRAY, nullable=False),
        sa.Column("searcher_slot_count", sa.Integer(), nullable=False),
        sa.Column("searcher_area_code", sa.String(length=14), nullable=True),
        sa.Column("radius_clamp_bit", sa.Boolean(), nullable=False),
        sa.Column("rung_offers", BLOB, nullable=True),
        sa.Column("offered_by_search_id", UUIDType(binary=False), nullable=True),
        sa.Column("rung_taken", sa.String(length=1), nullable=True),
        sa.Column("latency_ms_by_stage", BLOB, nullable=False),
        sa.Column("n_excluded_by_suppression", sa.Integer(), nullable=True),
        sa.Column("lineup", NULLABLE_BLOB, nullable=True),
        sa.CheckConstraint(
            "(intent_read IS NULL) OR (surface IN ('DECK', 'RADAR'))",
            name="ck_search_intent_read_only_under_one_ruler",
        ),
        sa.CheckConstraint(
            "(lineup IS NOT NULL) = (surface IN ('LINEUP', 'FILL_SEATS'))",
            name="ck_search_lineup_only_where_seats_were_filled",
        ),
        sa.CheckConstraint(
            "(mode IS NULL) = (surface IN ('DECK', 'RADAR'))",
            name="ck_search_mode_null_exactly_under_one_ruler",
        ),
        sa.CheckConstraint(
            "(n_excluded_by_suppression IS NOT NULL) = (surface = 'DECK')",
            name="ck_search_suppression_count_only_on_the_deck",
        ),
        sa.CheckConstraint(
            "(rung_taken IS NULL) = (offered_by_search_id IS NULL)",
            name="ck_search_rung_taken_cites_its_offer",
        ),
        sa.ForeignKeyConstraint(
            ["offered_by_search_id"], ["search.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "search_candidate",
        sa.Column("search_id", UUIDType(binary=False), nullable=False),
        sa.Column("band", sa.String(length=20), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("player_id", UUIDType(binary=False), nullable=False),
        sa.Column("fit", sa.Float(), nullable=False),
        sa.Column("terms", BLOB, nullable=False),
        sa.Column("degraded_terms", CODE_ARRAY, nullable=False),
        sa.Column("degraded_reasons", CODE_ARRAY, nullable=False),
        sa.Column("modifiers", BLOB, nullable=False),
        sa.Column("liveness_reasons", CODE_ARRAY, nullable=False),
        sa.Column("liveness_signals", BLOB, nullable=False),
        sa.Column("shared_count", sa.Integer(), nullable=False),
        sa.Column("their_slot_count", sa.Integer(), nullable=False),
        sa.Column("days_away", sa.Integer(), nullable=True),
        sa.Column("inclusion_reason", sa.String(length=30), nullable=True),
        sa.Column("withheld_reason", sa.String(length=30), nullable=True),
        sa.Column("missing_terms", CODE_ARRAY, nullable=False),
        sa.Column("reliability_penalty_applied", sa.Boolean(), nullable=False),
        sa.Column("reliability_penalty_decisive", sa.Boolean(), nullable=False),
        sa.Column("concerns", CODE_ARRAY, nullable=False),
        sa.Column("distance_km", sa.Float(), nullable=True),
        sa.Column("player_card", BLOB, nullable=True),
        sa.Column("at_stake", BLOB, nullable=True),
        sa.Column("suppression_lapsed", sa.Boolean(), nullable=True),
        sa.Column("bearing_deg", sa.Integer(), nullable=True),
        sa.Column("ratings", NULLABLE_BLOB, nullable=True),
        sa.ForeignKeyConstraint(
            ["search_id"],
            ["search.id"],
        ),
        sa.PrimaryKeyConstraint("search_id", "band", "position"),
    )
    op.create_table(
        "interest",
        sa.Column("from_player_id", UUIDType(binary=False), nullable=False),
        sa.Column("to_player_id", UUIDType(binary=False), nullable=False),
        sa.Column("sport", sa.String(length=50), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("origin_search_id", UUIDType(binary=False), nullable=False),
        sa.Column("origin_position", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "expires_at > sent_at", name="ck_interest_expires_after_it_was_sent"
        ),
        sa.CheckConstraint(
            "from_player_id <> to_player_id", name="ck_interest_not_to_yourself"
        ),
        sa.CheckConstraint(
            "origin_position >= 1", name="ck_interest_origin_position_is_a_rank"
        ),
        sa.ForeignKeyConstraint(
            ["origin_search_id"], ["search.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("from_player_id", "to_player_id", "sport"),
    )
    op.create_table(
        "player_pass",
        sa.Column("id", UUIDType(binary=False), nullable=False),
        sa.Column("passer_id", UUIDType(binary=False), nullable=False),
        sa.Column("passed_id", UUIDType(binary=False), nullable=False),
        sa.Column("sport", sa.String(length=50), nullable=False),
        sa.Column("passed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("origin_search_id", UUIDType(binary=False), nullable=False),
        sa.Column("origin_position", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "origin_position >= 1", name="ck_player_pass_origin_position_is_a_rank"
        ),
        sa.CheckConstraint(
            "passer_id <> passed_id", name="ck_player_pass_not_on_yourself"
        ),
        sa.ForeignKeyConstraint(
            ["origin_search_id"], ["search.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "prompt_decline",
        sa.Column("id", UUIDType(binary=False), nullable=False),
        sa.Column("player_id", UUIDType(binary=False), nullable=False),
        sa.Column("prompt", sa.String(length=50), nullable=False),
        sa.Column("sport", sa.String(length=50), nullable=True),
        sa.Column("declined_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "deck_reset",
        sa.Column("id", UUIDType(binary=False), nullable=False),
        sa.Column("player_id", UUIDType(binary=False), nullable=False),
        sa.Column("sport", sa.String(length=50), nullable=False),
        sa.Column("reset_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_search_searcher_at", "search", ["searcher_id", "at"], unique=False
    )
    op.create_index(
        "ix_search_candidate_player", "search_candidate", ["player_id"], unique=False
    )
    op.create_index("ix_interest_expires_at", "interest", ["expires_at"], unique=False)
    op.create_index(
        "ix_interest_towards",
        "interest",
        ["to_player_id", "sport", "expires_at"],
        unique=False,
    )
    op.create_index(
        "ix_player_pass_passer",
        "player_pass",
        ["passer_id", "sport", "passed_id"],
        unique=False,
    )
    op.create_index(
        "ix_prompt_decline_player",
        "prompt_decline",
        ["player_id", "declined_at"],
        unique=False,
    )
    op.create_index(
        "ix_deck_reset_player",
        "deck_reset",
        ["player_id", "sport", "reset_at"],
        unique=False,
    )
