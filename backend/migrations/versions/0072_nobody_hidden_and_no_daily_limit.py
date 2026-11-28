"""who sees whom: drop ``ranking_visibility`` and ``friend_requests_counted``

**The ranking hides nobody, and a friend request has no daily limit**
([#791](https://github.com/Rakieta02/Rakieta/issues/791);
[ADR-0204](../../docs/adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md)
§2). *Show me in General* is replaced by *Show me to new people*, which the
record and the ask read live off the profile, so the rows' copy of the old
switch (``ranking_visibility``, 0070) has no reader; and the daily limit's count
(``friend_requests_counted``, 0071) went with the limit. **Nothing is lost**:
both were copies of events the streams still hold — the profile's
``ranking_visibility_set`` now folds into the new switch, and a request's
``counted`` is decoded and never read.

The downgrade makes both tables again, empty: the rebuild of 0070's was the
ranking rebuild, and 0071's counted a Warsaw day that has passed.

Revision ID: 0072_nobody_hidden_and_no_daily_limit
Revises: 0071_friend_requests_counted
Create Date: 2026-11-14
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0072_nobody_hidden_and_no_daily_limit"
down_revision = "0071_friend_requests_counted"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("friend_requests_counted")
    op.drop_table("ranking_visibility")


def downgrade() -> None:
    op.create_table(
        "ranking_visibility",
        sa.Column("player_id", UUIDType(binary=False), nullable=False),
        sa.Column("hidden", sa.Boolean(), nullable=False),
        sa.Column("profile_version", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("player_id"),
    )
    op.create_table(
        "friend_requests_counted",
        sa.Column("requester_id", UUIDType(binary=False), nullable=False),
        sa.Column("asked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("addressee_id", UUIDType(binary=False), nullable=False),
        sa.PrimaryKeyConstraint("requester_id", "asked_at", "addressee_id"),
    )
