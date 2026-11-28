"""the join requests waiting on a group

A *People I approve* group turns a join into a Join request its Owner answers
([#505](https://github.com/Rakieta02/Rakieta/issues/505),
[ADR-0183](../../docs/adr/0183-a-group-is-a-crowd-at-a-home-club-and-its-link-never-changes.md)
§7). **``group_join_requests``** is the third projection ADR-0183 §1 names,
written beside the group's events in the same transaction: one row per request
**while it waits**, deleted when it is approved or declined — the stream
remembers every answer, and this table answers only *who is waiting*. Its key is
the group and the person, so *at most one waiting per player per group* is held
by the database as well as by the aggregate; ``requested_version`` is the stream
version of the ask, which is the exact order people asked in.

Revision ID: 0031_group_join_requests
Revises: 0030_groups
Create Date: 2026-09-25
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0031_group_join_requests"
down_revision = "0030_groups"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "group_join_requests",
        sa.Column(
            "group_id",
            UUIDType(binary=False),
            sa.ForeignKey("groups.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("player_id", UUIDType(binary=False), primary_key=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("requested_version", sa.Integer(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("group_join_requests")
