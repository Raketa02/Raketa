"""clubs: which club a payments account is

A club connects payments by filling in the payment provider's hosted pages
([#537](https://github.com/Raketa02/Raketa/issues/537),
[ADR-0189](../../docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md)
§4–§5). The account is recorded on the club's **Club courts** stream in
``event_store`` and needs no table of its own; one thing beside it does:

- **``club_payments_accounts``** — a projection of those streams: which club an
  account at the payment provider is, written in the transaction that opened
  it, so the provider's notice — which names an account and never a club —
  finds the club's stream, as ``payment_customers`` does for a player.

Revision ID: 0038_club_payments_accounts
Revises: 0037_a_card_can_lose_its_court_hour
Create Date: 2026-09-30
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0038_club_payments_accounts"
down_revision = "0037_a_card_can_lose_its_court_hour"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "club_payments_accounts",
        sa.Column("account_id", sa.String(255), primary_key=True),
        sa.Column("club_id", UUIDType(binary=False), nullable=False, unique=True),
    )


def downgrade() -> None:
    op.drop_table("club_payments_accounts")
