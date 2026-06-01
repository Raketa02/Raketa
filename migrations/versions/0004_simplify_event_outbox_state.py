"""simplify transactional outbox delivery state

Revision ID: 0004_simplify_event_outbox_state
Revises: 0003_outbox_delivery_leases
Create Date: 2026-05-28
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0004_simplify_event_outbox_state"
down_revision = "0003_outbox_delivery_leases"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_event_outbox_claim_expiry", table_name="event_outbox")
    op.drop_index("ix_event_outbox_eligible", table_name="event_outbox")
    op.create_index(
        "ix_event_outbox_pending",
        "event_outbox",
        ["published_at", "created_at"],
        unique=False,
        postgresql_where=sa.text("published_at IS NULL"),
    )
    op.drop_column("event_outbox", "dead_lettered_at")
    op.drop_column("event_outbox", "claimed_until")
    op.drop_column("event_outbox", "claimed_by")
    op.drop_column("event_outbox", "claim_token")
    op.drop_column("event_outbox", "next_attempt_at")
    op.drop_column("event_outbox", "status")


def downgrade() -> None:
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
