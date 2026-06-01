"""rename stored event table to event delivery queue

Revision ID: 0005_event_delivery_queue
Revises: 0004_simplify_event_outbox_state
Create Date: 2026-05-28
"""

import sqlalchemy as sa
from alembic import op

revision = "0005_event_delivery_queue"
down_revision = "0004_simplify_event_outbox_state"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.rename_table("event_outbox", "event_delivery_queue")
    op.drop_index("ix_event_outbox_pending", table_name="event_delivery_queue")
    op.drop_index("ix_event_outbox_event_type", table_name="event_delivery_queue")
    op.create_index(
        "ix_event_delivery_queue_pending",
        "event_delivery_queue",
        ["published_at", "created_at"],
        unique=False,
        postgresql_where=sa.text("published_at IS NULL"),
    )
    op.create_index(
        "ix_event_delivery_queue_event_type",
        "event_delivery_queue",
        ["event_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_event_delivery_queue_event_type", table_name="event_delivery_queue"
    )
    op.drop_index("ix_event_delivery_queue_pending", table_name="event_delivery_queue")
    op.create_index(
        "ix_event_outbox_pending",
        "event_delivery_queue",
        ["published_at", "created_at"],
        unique=False,
        postgresql_where=sa.text("published_at IS NULL"),
    )
    op.create_index(
        "ix_event_outbox_event_type",
        "event_delivery_queue",
        ["event_type"],
        unique=False,
    )
    op.rename_table("event_delivery_queue", "event_outbox")
