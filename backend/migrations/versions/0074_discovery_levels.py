"""every player's current level per sport: ``discovery_levels``

**Same competitive level reads every player's level in every sport they share
with the reader** — the Level, its Uncertainty, the band the rating published
with it and how many results have moved it, one row per player and sport, the
questionnaire's alone included
([#794](https://github.com/Raketa02/Raketa/issues/794);
[ADR-0204](../../docs/adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md)
§10, a stated exception to *derived, never stored*). Written by the Discovery
context's follower on every delivered ``rating.rating_initialised`` and
``rating.moved_on_result``, and by its rebuild; indexed by sport and level for
the row's windows, and by sport and Uncertainty for the least of it, which
bounds how even anybody beyond a window could read.

**Created empty**: a store that already holds ratings is owed one
``make discovery-rebuild``, which now writes the levels beside the directory.
Nothing is lost on the downgrade: every row is a copy of a rating stream.

Revision ID: 0074_discovery_levels
Revises: 0073_player_directory
Create Date: 2026-11-14
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0074_discovery_levels"
down_revision = "0073_player_directory"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "discovery_levels",
        sa.Column("player_id", UUIDType(binary=False), nullable=False),
        sa.Column("sport", sa.String(length=16), nullable=False),
        sa.Column("mu", sa.Float(), nullable=False),
        sa.Column("sigma", sa.Float(), nullable=False),
        sa.Column("band_name", sa.String(length=32), nullable=False),
        sa.Column("band_lower", sa.Float(), nullable=False),
        sa.Column("band_upper", sa.Float(), nullable=False),
        sa.Column("results", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("player_id", "sport"),
    )
    op.create_index(
        "ix_discovery_levels_sport_mu",
        "discovery_levels",
        ["sport", "mu", "player_id"],
    )
    op.create_index(
        "ix_discovery_levels_sport_sigma",
        "discovery_levels",
        ["sport", "sigma"],
    )


def downgrade() -> None:
    op.drop_index("ix_discovery_levels_sport_sigma", table_name="discovery_levels")
    op.drop_index("ix_discovery_levels_sport_mu", table_name="discovery_levels")
    op.drop_table("discovery_levels")
