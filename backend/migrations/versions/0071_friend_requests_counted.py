"""friends: the requests that count towards the limit — ``friend_requests_counted``

**At most ten requests a Warsaw day to people you share no group with**
([#773](https://github.com/Raketa02/Raketa/issues/773);
[ADR-0203](../../docs/adr/0203-a-ranking-per-sport-sorted-by-the-level.md) §9).
One row per request **sent** that counts — asked of somebody the requester
shared no group with — keyed on the requester and the instant, so *how many
since this Warsaw midnight* is one range on the primary key's prefix.

Written by the Friendship repository's ``save`` from each
``friends.friend_requested`` it appends with ``counted``, in the request's own
transaction, and never deleted: a request taken back was still sent. **Nothing
is backfilled**: no request before this one could count.

Revision ID: 0071_friend_requests_counted
Revises: 0070_ranking_visibility
Create Date: 2026-11-08
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0071_friend_requests_counted"
down_revision = "0070_ranking_visibility"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "friend_requests_counted",
        sa.Column("requester_id", UUIDType(binary=False), nullable=False),
        sa.Column("asked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("addressee_id", UUIDType(binary=False), nullable=False),
        sa.PrimaryKeyConstraint("requester_id", "asked_at", "addressee_id"),
    )


def downgrade() -> None:
    op.drop_table("friend_requests_counted")
