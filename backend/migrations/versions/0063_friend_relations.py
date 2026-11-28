"""friends: the reader's relation to each player — ``friend_relations``

**A new bounded context, Friends** ([#745](https://github.com/Rakieta02/Rakieta/issues/745);
[ADR-0202](../../docs/adr/0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md)
§8). Its **Friendship** is event-sourced, one stream per pair, in ``event_store``;
this is the one projection beside it, written by the repository's ``save`` in
the same transaction:

- **``friend_relations``** — two rows per pair while something stands between
  them, one from each side: ``FRIEND`` and ``FRIEND``, or ``SENT`` and
  ``ASKED_YOU``; none once nothing does. Keyed on the reader first, so every
  face's *my relation to these people* is one question on the primary key.

**Nothing is backfilled**: no friendship exists before this revision.

Revision ID: 0063_friend_relations
Revises: 0062_a_notice_may_be_about_no_game
Create Date: 2026-11-06
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0063_friend_relations"
down_revision = "0062_a_notice_may_be_about_no_game"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "friend_relations",
        sa.Column("player_id", UUIDType(binary=False), nullable=False),
        sa.Column("other_id", UUIDType(binary=False), nullable=False),
        sa.Column("relation", sa.String(16), nullable=False),
        sa.Column("since", sa.DateTime(timezone=True), nullable=False),
        sa.Column("set_aside", sa.Boolean(), nullable=False),
        sa.Column("made_from", sa.String(16), nullable=True),
        sa.Column("group_id", UUIDType(binary=False), nullable=True),
        sa.Column("sport", sa.String(16), nullable=True),
        sa.PrimaryKeyConstraint("player_id", "other_id"),
        sa.CheckConstraint(
            "relation IN ('SENT', 'ASKED_YOU', 'FRIEND')",
            name="ck_friend_relations_relation",
        ),
    )


def downgrade() -> None:
    op.drop_table("friend_relations")
