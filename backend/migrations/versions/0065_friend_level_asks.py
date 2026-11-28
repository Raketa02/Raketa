"""friends: every Ask for a level — ``friend_level_asks``

**Ask for a level** ([#749](https://github.com/Rakieta02/Rakieta/issues/749);
[ADR-0202](../../docs/adr/0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md)
§4; the mechanics §5). An ask is recorded on the pair's **Friendship** stream in
``event_store``; this is its projection, rewritten for the pair by the
repository's ``save`` in the same transaction:

- **``friend_level_asks``** — one row per asker, friend and sport, **ever**: the
  primary key is the rule *once per friend per sport*. The group whose picker it
  was asked from, when, and when the friend's first level in the sport answered
  it. Keyed on the asker first, for the picker's *Asked*; indexed on the friend
  and the sport, for the answer.

**Nothing is backfilled**: no ask exists before this revision.

Revision ID: 0065_friend_level_asks
Revises: 0064_friend_link_codes
Create Date: 2026-11-07
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0065_friend_level_asks"
down_revision = "0064_friend_link_codes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "friend_level_asks",
        sa.Column("asker_id", UUIDType(binary=False), nullable=False),
        sa.Column("friend_id", UUIDType(binary=False), nullable=False),
        sa.Column("sport", sa.String(16), nullable=False),
        sa.Column("group_id", UUIDType(binary=False), nullable=False),
        sa.Column("asked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("got_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("asker_id", "friend_id", "sport"),
    )
    op.create_index(
        "ix_friend_level_asks_friend_id_sport",
        "friend_level_asks",
        ["friend_id", "sport"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_friend_level_asks_friend_id_sport", table_name="friend_level_asks"
    )
    op.drop_table("friend_level_asks")
