"""the rest count: ``discovery_rest_counts``

**A card the reader keeps scrolling past rests**: once it has come on screen on
five different Warsaw days while the two were unconnected, the player is a gap
in that row, not fresh — *Same competitive level* and *Same vibe* each keep
their own count
([#796](https://github.com/Rakieta02/Rakieta/issues/796);
[ADR-0204](../../docs/adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md)
§7, §10, the third stated exception to *derived, never stored*). One row per
viewer, row and player seen: how many different days, and the last of them.
Written by the phone's on-screen reports; a gone account's rows go on either
side. Indexed by the player seen, for forgetting one.

**Created empty**, and owed no rebuild: the reports are the phone's, and no
stream holds them. The downgrade loses every count, so every rested player is
fresh again — nothing else.

Revision ID: 0075_discovery_rest_counts
Revises: 0074_discovery_levels
Create Date: 2026-11-15
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0075_discovery_rest_counts"
down_revision = "0074_discovery_levels"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "discovery_rest_counts",
        sa.Column("viewer_id", UUIDType(binary=False), nullable=False),
        sa.Column("row", sa.String(length=16), nullable=False),
        sa.Column("player_id", UUIDType(binary=False), nullable=False),
        sa.Column("days", sa.Integer(), nullable=False),
        sa.Column("last_day", sa.Date(), nullable=False),
        sa.PrimaryKeyConstraint("viewer_id", "row", "player_id"),
    )
    op.create_index(
        "ix_discovery_rest_counts_player_id",
        "discovery_rest_counts",
        ["player_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_discovery_rest_counts_player_id", table_name="discovery_rest_counts"
    )
    op.drop_table("discovery_rest_counts")
