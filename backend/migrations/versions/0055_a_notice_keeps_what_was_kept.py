"""notifications: a refund's notice keeps what was kept on the payment

**After the cut-off a leaver whose seat is taken gets the share back less
exactly what was kept on their payment, and is told both**
([#641](https://github.com/Raketa02/Raketa/issues/641); the mechanics §13,
Q113): *You've been refunded 38,24 zł · your seat was taken* / *40 zł less the
1,76 zł kept on your payment.* One fact beside the notices:

- **``notices.kept_grosze``** — what the provider kept on the payment a refund
  gave back less, so the notice says the same whenever it is read. Every notice
  given before it was asked is ``NULL``: its words never named a fee kept.

Revision ID: 0055_a_notice_keeps_what_was_kept
Revises: 0054_a_share_is_held_until_the_cut_off
Create Date: 2026-10-10
"""

import sqlalchemy as sa
from alembic import op

revision = "0055_a_notice_keeps_what_was_kept"
down_revision = "0054_a_share_is_held_until_the_cut_off"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("notices", sa.Column("kept_grosze", sa.Integer(), nullable=True))


def downgrade() -> None:
    # The day streams still say what each refund kept; the projection forgets
    # it.
    op.drop_column("notices", "kept_grosze")
