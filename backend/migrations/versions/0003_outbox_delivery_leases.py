"""claim/lease and retry state for transactional outbox

Revision ID: 0003_outbox_delivery_leases
Revises: 0002_event_outbox
Create Date: 2026-05-27
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0003_outbox_delivery_leases"
down_revision = "0002_event_outbox"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Legacy pending rows use class-name identifiers and cannot be delivered
    # through the stable-contract catalog introduced by this release.
    op.execute(sa.text("DELETE FROM event_outbox WHERE published_at IS NULL"))
    op.add_column(
        "event_outbox",
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "event_outbox",
        sa.Column(
            "status", sa.String(length=32), nullable=False, server_default="pending"
        ),
    )
    op.add_column(
        "event_outbox",
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "event_outbox", sa.Column("claim_token", UUIDType(binary=False), nullable=True)
    )
    op.add_column(
        "event_outbox", sa.Column("claimed_by", sa.String(length=255), nullable=True)
    )
    op.add_column(
        "event_outbox",
        sa.Column("claimed_until", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "event_outbox",
        sa.Column("dead_lettered_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        sa.text(
            "UPDATE event_outbox SET status = 'published' "
            "WHERE published_at IS NOT NULL"
        )
    )
    op.drop_index("ix_event_outbox_pending", table_name="event_outbox")
    op.create_index(
        "ix_event_outbox_eligible",
        "event_outbox",
        ["status", "next_attempt_at", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_event_outbox_claim_expiry",
        "event_outbox",
        ["status", "claimed_until"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_event_outbox_claim_expiry", table_name="event_outbox")
    op.drop_index("ix_event_outbox_eligible", table_name="event_outbox")
    op.create_index(
        "ix_event_outbox_pending",
        "event_outbox",
        ["published_at", "created_at"],
        unique=False,
    )
    op.drop_column("event_outbox", "dead_lettered_at")
    op.drop_column("event_outbox", "claimed_until")
    op.drop_column("event_outbox", "claimed_by")
    op.drop_column("event_outbox", "claim_token")
    op.drop_column("event_outbox", "next_attempt_at")
    op.drop_column("event_outbox", "status")
    op.drop_column("event_outbox", "schema_version")
