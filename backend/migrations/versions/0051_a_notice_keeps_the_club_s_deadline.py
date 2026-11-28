"""notifications: a notice keeps the club's deadline

**It's a game! at a club that confirms, and Your new game**
([#622](https://github.com/Rakieta02/Rakieta/issues/622); the mechanics Q103,
Q107). Two new kinds of notice, and one fact beside them:

- **``notices.until``** — the deadline a notice names: when the club must
  answer, on *It's a game! · Kazimierz Padel answers by 21:15*. Kept, so the
  notice says the same whenever it is read. Every notice given before it was
  asked names none.

Revision ID: 0051_a_notice_keeps_the_club_s_deadline
Revises: 0050_the_bell_counts_what_is_new
Create Date: 2026-10-10
"""

import sqlalchemy as sa
from alembic import op

revision = "0051_a_notice_keeps_the_club_s_deadline"
down_revision = "0050_the_bell_counts_what_is_new"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "notices",
        sa.Column("until", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    # The day streams still say each deadline; the projection forgets them.
    op.drop_column("notices", "until")
