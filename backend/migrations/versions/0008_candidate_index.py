"""create the candidate index — three tables, and no shard key in any of them

The platform's first read model. It is fed by **tailing** `event_store` in
`sequence_no` order (ADR-0110), never by the outbox: the outbox orders by
`(created_at, id)` — both of the non-orders ADR-0097 rejected by name — and mints
a row id unrelated to the event's, so an outbox subscriber cannot name a
`sequence_no`. Two subscriptions, two guarantees.

Three tables, because a search reads `(player, sport)` and a player edits their
profile once. `candidate_player_facts` holds what a person says about themselves;
`candidate_row` holds what is true of them in one sport; `candidate_index_cursor`
holds the single watermark row, taken `FOR UPDATE` for a tick so a concurrent
reader blocks rather than racing — no leader election and no lease to leak.

**There is no partition or shard-key column anywhere here, and that is the
decision** (ADR-0101): the partition is derived from the row, so there is no
field for a future matching conjunct to attach itself to. A schema test asserts
it absent.

The cursor row is seeded at 0 by this migration rather than by the first tick, so
that *the projection has never run* and *the projection is broken* are not the
same observation.

Revision ID: 0008_candidate_index
Revises: 0007_event_store_append_order
Create Date: 2026-08-27
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0008_candidate_index"
down_revision = "0007_event_store_append_order"
branch_labels = None
depends_on = None

_SEED_CURSOR = sa.text(
    """
    INSERT INTO candidate_index_cursor (projection, applied_through_sequence_no)
    VALUES ('candidate_index', 0)
    """
)


def upgrade() -> None:
    op.create_table(
        "candidate_player_facts",
        sa.Column("player_id", UUIDType(binary=False), primary_key=True),
        sa.Column("profile_created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("social_tags", sa.JSON(), nullable=True),
        sa.Column("tags_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("availability", sa.JSON(), nullable=True),
        sa.Column("grid_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("area_latitude", sa.Float(), nullable=True),
        sa.Column("area_longitude", sa.Float(), nullable=True),
        sa.Column("search_radius_km", sa.Integer(), nullable=True),
        sa.Column("proposals_opt_in", sa.Boolean(), nullable=True),
        sa.Column("gender", sa.String(length=32), nullable=True),
        sa.Column("gender_preference", sa.String(length=32), nullable=True),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("applied_through_sequence_no", sa.BigInteger(), nullable=False),
    )
    op.create_table(
        "candidate_row",
        sa.Column("player_id", UUIDType(binary=False), primary_key=True),
        sa.Column("sport", sa.String(length=32), primary_key=True),
        sa.Column("mu", sa.Float(), nullable=True),
        sa.Column("sigma", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Integer(), nullable=True),
        sa.Column("band", sa.String(length=64), nullable=True),
        sa.Column("band_lower", sa.Float(), nullable=True),
        sa.Column("band_upper", sa.Float(), nullable=True),
        sa.Column("rating_status", sa.String(length=32), nullable=True),
        sa.Column("calibration_priority", sa.String(length=32), nullable=True),
        sa.Column("declared_intent", sa.String(length=32), nullable=True),
        sa.Column("applied_through_sequence_no", sa.BigInteger(), nullable=False),
    )
    # The delta refresh's only question — *which rows moved* — asked every two
    # seconds in every worker.
    op.create_index(
        "ix_candidate_row_applied_through_sequence_no",
        "candidate_row",
        ["applied_through_sequence_no"],
    )
    op.create_table(
        "candidate_index_cursor",
        sa.Column("projection", sa.String(length=64), primary_key=True),
        sa.Column(
            "applied_through_sequence_no",
            sa.BigInteger(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("hole_at_sequence_no", sa.BigInteger(), nullable=True),
        sa.Column("hole_settles_at", sa.BigInteger(), nullable=True),
        sa.Column(
            "caught_up_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.execute(_SEED_CURSOR)


def downgrade() -> None:
    op.drop_table("candidate_index_cursor")
    op.drop_index(
        "ix_candidate_row_applied_through_sequence_no", table_name="candidate_row"
    )
    op.drop_table("candidate_row")
    op.drop_table("candidate_player_facts")
