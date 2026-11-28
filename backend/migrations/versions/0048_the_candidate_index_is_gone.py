"""the candidate index is gone, and its three tables with it

**The "who fits whom" ranking and the candidate index were removed**
([#580](https://github.com/Rakieta02/Rakieta/issues/580), PRD #569). The index
was the matcher's picture of the city — a projection of the event log that a
search scanned — and the searches went in #579; since then a tail reader and a
refresh loop kept it current and nothing read it. Its three tables go:

- ``candidate_player_facts`` — what a player said about themselves (``0008``,
  with ``intro`` from ``0024``);
- ``candidate_row`` — one ``(player, sport)`` row and its Level (``0008``, with
  the likely range from ``0016``);
- ``candidate_index_cursor`` — the one row saying how far the log was folded.

The search telemetry it fed (``search``, ``search_candidate``) went in ``0047``.

**Dropped, not emptied**: nothing will write them again. Only ``local`` runs,
and its store is reset with this change (``make down-v && make up && make
seed``), so no player loses a row — and nothing here was a record of anything:
the index was rebuilt from the log on demand.

**The downgrade recreates the three tables empty and seeds the cursor at
nought**, as ``0008`` did, so an older checkout migrated back to ``0047`` finds
the schema it expects and its tail reader folds the whole log back in from the
first event. That is the index's own repair, which is why no row is restored.

Revision ID: 0048_the_candidate_index_is_gone
Revises: 0047_searches_deck_and_radar_gone
Create Date: 2026-10-06
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0048_the_candidate_index_is_gone"
down_revision = "0047_searches_deck_and_radar_gone"
branch_labels = None
depends_on = None

#: The watermark variant the dropped models declared — ``BIGINT`` on PostgreSQL,
#: ``INTEGER`` on SQLite, the event store's own ``sequence_no`` spelling.
APPLIED_SEQUENCE = sa.BigInteger().with_variant(sa.Integer(), "sqlite")

_SEED_CURSOR = sa.text(
    """
    INSERT INTO candidate_index_cursor (projection, applied_through_sequence_no)
    VALUES ('candidate_index', 0)
    """
)


def upgrade() -> None:
    op.drop_table("candidate_index_cursor")
    op.drop_index(
        "ix_candidate_row_applied_through_sequence_no", table_name="candidate_row"
    )
    op.drop_table("candidate_row")
    op.drop_table("candidate_player_facts")


def downgrade() -> None:
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
        sa.Column("applied_through_sequence_no", APPLIED_SEQUENCE, nullable=False),
        sa.Column("intro", sa.Text(), nullable=True),
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
        sa.Column("applied_through_sequence_no", APPLIED_SEQUENCE, nullable=False),
        sa.Column("range_low", sa.Float(), nullable=True),
        sa.Column("range_high", sa.Float(), nullable=True),
    )
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
            APPLIED_SEQUENCE,
            nullable=False,
            server_default="0",
        ),
        sa.Column("hole_at_sequence_no", APPLIED_SEQUENCE, nullable=True),
        sa.Column("hole_settles_at", sa.BigInteger(), nullable=True),
        sa.Column(
            "caught_up_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.execute(_SEED_CURSOR)
