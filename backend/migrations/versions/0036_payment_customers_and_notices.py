"""payments: whose customer is whose, and which notices were read

A player saves a payment method once, after terms naming the club as the one
charging ([#536](https://github.com/Rakieta02/Rakieta/issues/536),
[ADR-0189](../../docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md)
§4–§5). The **Payment method** itself is a stream in ``event_store`` and needs
no table; two things beside it do
([ADR-0190](../../docs/adr/0190-money-goes-through-one-port-and-a-notice-is-read-once.md)):

- **``payment_customers``** — a projection of those streams: which player a
  customer at the payment provider is, written in the transaction that opened
  it, so a notice naming a customer finds the player's stream.
- **``payment_notices``** — the webhook's inbox: the id of every provider notice
  already read, written in the transaction that acted on it, so a notice
  delivered again is read once.

**Renumbered on landing.** This chain was written as ``0035``–``0044`` on
``0034_official_groups`` beside ``0035_handover_notices``, which reached
``main`` first; it landed second, so it follows that one, one number on.

Revision ID: 0036_payment_customers_and_notices
Revises: 0035_handover_notices
Create Date: 2026-09-30
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0036_payment_customers_and_notices"
down_revision = "0035_handover_notices"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "payment_customers",
        sa.Column("customer_id", sa.String(255), primary_key=True),
        sa.Column("player_id", UUIDType(binary=False), nullable=False, unique=True),
    )
    op.create_table(
        "payment_notices",
        sa.Column("notice_id", sa.String(255), primary_key=True),
        sa.Column("kind", sa.String(128), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("payment_notices")
    op.drop_table("payment_customers")
