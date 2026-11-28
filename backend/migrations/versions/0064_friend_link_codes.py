"""friends: every code a Friend link ever carried — ``friend_link_codes``

**The Friend link** ([#748](https://github.com/Rakieta02/Rakieta/issues/748);
[ADR-0202](../../docs/adr/0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md)
§1; the mechanics §4). A player's link is event-sourced, one stream per player,
in ``event_store``; this is the projection beside it, written by the
repository's ``save`` in the same transaction:

- **``friend_link_codes``** — one row per code, **kept after New link replaced
  it** (``current`` false), so no code is ever handed out twice. The code is the
  primary key: the minter's check and an opening's lookup are one question on it.

**Nothing is backfilled**: a link is made on its owner's first read.

Revision ID: 0064_friend_link_codes
Revises: 0063_friend_relations
Create Date: 2026-11-06
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0064_friend_link_codes"
down_revision = "0063_friend_relations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "friend_link_codes",
        sa.Column("code", sa.String(8), nullable=False),
        sa.Column("owner_id", UUIDType(binary=False), nullable=False),
        sa.Column("current", sa.Boolean(), nullable=False),
        sa.Column("made_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("code"),
    )
    op.create_index("ix_friend_link_codes_owner_id", "friend_link_codes", ["owner_id"])


def downgrade() -> None:
    op.drop_index("ix_friend_link_codes_owner_id", table_name="friend_link_codes")
    op.drop_table("friend_link_codes")
