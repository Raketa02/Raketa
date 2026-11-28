"""the player directory: ``discovery_players`` and ``discovery_player_tags``

**The people rows read a directory of every account** — the nickname, the
first photograph, the area cell, when sign-up finished (*joined*), the social
tags one row per tag, *Show me to new people* and whether the account plays
([#793](https://github.com/Rakieta02/Rakieta/issues/793);
[ADR-0204](../../docs/adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md)
§10, a stated exception to *derived, never stored*). Written by the Discovery
context's follower on every delivered user or Player profile event that changes
an entry, and by its rebuild.

**Created empty**: a store that already holds players is owed one
``make discovery-rebuild`` (every entry written from the accounts the event
store holds). Nothing is lost on the downgrade: both tables are copies of what
the user and profile streams hold.

Revision ID: 0073_player_directory
Revises: 0072_nobody_hidden_and_no_daily_limit
Create Date: 2026-11-14
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0073_player_directory"
down_revision = "0072_nobody_hidden_and_no_daily_limit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "discovery_players",
        sa.Column("player_id", UUIDType(binary=False), nullable=False),
        sa.Column("nickname", sa.String(length=64), nullable=True),
        sa.Column("plays", sa.Boolean(), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("photo_id", UUIDType(binary=False), nullable=True),
        sa.Column("area_latitude", sa.Float(), nullable=True),
        sa.Column("area_longitude", sa.Float(), nullable=True),
        sa.Column("open_to_new_people", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("player_id"),
    )
    op.create_index(
        "ix_discovery_players_joined_at",
        "discovery_players",
        ["joined_at", "player_id"],
    )
    op.create_table(
        "discovery_player_tags",
        sa.Column("player_id", UUIDType(binary=False), nullable=False),
        sa.Column("tag", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(
            ["player_id"], ["discovery_players.player_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("player_id", "tag"),
    )
    op.create_index(
        "ix_discovery_player_tags_tag",
        "discovery_player_tags",
        ["tag", "player_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_discovery_player_tags_tag", table_name="discovery_player_tags")
    op.drop_table("discovery_player_tags")
    op.drop_index("ix_discovery_players_joined_at", table_name="discovery_players")
    op.drop_table("discovery_players")
