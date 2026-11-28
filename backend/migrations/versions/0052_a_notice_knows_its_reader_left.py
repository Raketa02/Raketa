"""notifications: a notice knows its reader had left the game

**Every ending of a full game is told, and a leaver only when it touches
them** ([#623](https://github.com/Rakieta02/Rakieta/issues/623); the mechanics
Q104, Q105, Q108). One fact beside the notices:

- **``notices.you_left``** — a notice told to a player who had left the game,
  about what then became of it: the call-off their empty seat caused, or the
  club's cancel that refunded them. It is said in a leaver's words, and never
  promises them a new game. Every notice given before it was asked was told to
  a player still in.

Revision ID: 0052_a_notice_knows_its_reader_left
Revises: 0051_a_notice_keeps_the_club_s_deadline
Create Date: 2026-10-10
"""

import sqlalchemy as sa
from alembic import op

revision = "0052_a_notice_knows_its_reader_left"
down_revision = "0051_a_notice_keeps_the_club_s_deadline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "notices",
        sa.Column("you_left", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    # The day streams still say whose notice was a leaver's; the projection
    # forgets it.
    op.drop_column("notices", "you_left")
