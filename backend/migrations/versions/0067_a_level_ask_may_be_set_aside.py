"""friends: an Ask for a level may be set aside — ``friend_level_asks.set_aside_at``

**A friend's ask for a level waits on their Home** ([#764](https://github.com/Rakieta02/Rakieta/issues/764);
[ADR-0202](../../docs/adr/0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md)
§4's 2026-11-07 amendment; the friends mechanics §5.1). **Not now** on the
ask's Home card records ``friends.level_ask_set_aside`` on the pair's
Friendship stream; this column is when, rewritten for the pair by the
repository's ``save`` in the same transaction. ``NULL`` while the ask is on the
friend's Home — a set-aside ask still waits for the level, so ``got_at`` is
written whatever this holds.

**Nothing is backfilled**: no ask was set aside before this revision.

Revision ID: 0067_a_level_ask_may_be_set_aside
Revises: 0066_a_friends_game_is_booked_at_send
Create Date: 2026-11-07
"""

import sqlalchemy as sa
from alembic import op

revision = "0067_a_level_ask_may_be_set_aside"
down_revision = "0066_a_friends_game_is_booked_at_send"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "friend_level_asks",
        sa.Column("set_aside_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("friend_level_asks", "set_aside_at")
