"""a group at a home club, and its members

Raketa gets groups ([#504](https://github.com/Raketa02/Raketa/issues/504),
[ADR-0183](../../docs/adr/0183-a-group-is-a-crowd-at-a-home-club-and-its-link-never-changes.md)).
Both new tables are **projections**, written beside the group's events in the same
transaction; the streams live in ``event_store`` beside everybody else's.

- **``groups``** is one row per group: its name, **a folded copy of the name**
  for join search (folded by ``clubs/domain/folding.py``, which SQL cannot do, so
  it is written from the first event rather than backfilled later), its home
  club, its join policy, its Owner and its **code** — unique, and never changed.
- **``group_members``** is one row per Group member, with the instant they joined
  and the stream version of the event that admitted them, which is the exact
  order they joined in.

The join requests' projection, the third ADR-0183 §1 names, arrives with
requests (#505).

Revision ID: 0030_groups
Revises: 0029_clubs
Create Date: 2026-09-25
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0030_groups"
down_revision = "0029_clubs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "groups",
        sa.Column("id", UUIDType(binary=False), primary_key=True),
        sa.Column("name", sa.String(length=40), nullable=False),
        sa.Column("name_folded", sa.String(length=255), nullable=False),
        sa.Column(
            "home_club_id",
            UUIDType(binary=False),
            sa.ForeignKey("clubs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("join_policy", sa.String(length=32), nullable=False),
        sa.Column("owner_id", UUIDType(binary=False), nullable=False),
        sa.Column("code", sa.String(length=8), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("code", name="uq_groups_code"),
    )
    op.create_index("ix_groups_home_club_id", "groups", ["home_club_id"])

    op.create_table(
        "group_members",
        sa.Column(
            "group_id",
            UUIDType(binary=False),
            sa.ForeignKey("groups.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("player_id", UUIDType(binary=False), primary_key=True),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("joined_version", sa.Integer(), nullable=False),
    )
    op.create_index("ix_group_members_player_id", "group_members", ["player_id"])


def downgrade() -> None:
    op.drop_index("ix_group_members_player_id", table_name="group_members")
    op.drop_table("group_members")
    op.drop_index("ix_groups_home_club_id", table_name="groups")
    op.drop_table("groups")
