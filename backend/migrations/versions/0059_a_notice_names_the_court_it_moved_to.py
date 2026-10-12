"""notifications: a *Game moved* notice names the court and its kind

**The club's Move tells the players where the game is now**
([#671](https://github.com/Raketa02/Raketa/issues/671); the mechanics §17.2,
Q122): *Bonarka Arena moved your game to Court 3 · Thu 19:00* / *Padel ·
indoor · nothing else changes*. A notice records facts, never words, and the
court it names must read the same after a second move — so the court's name
and its kind are kept on the row, as a refund's fee kept (0055) and a rescue
(0057) are:

- **``notices.court_name``** — what the club calls the court the game moved to;
- **``notices.indoor``** — its kind.

Both are ``NULL`` on every other kind, and on every row given before: no game
had been moved by a notice until now.

Revision ID: 0059_a_notice_names_the_court_it_moved_to
Revises: 0058_no_club_confirms_a_game
Create Date: 2026-10-12
"""

import sqlalchemy as sa
from alembic import op

revision = "0059_a_notice_names_the_court_it_moved_to"
down_revision = "0058_no_club_confirms_a_game"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("notices", sa.Column("court_name", sa.String(40), nullable=True))
    op.add_column("notices", sa.Column("indoor", sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column("notices", "indoor")
    op.drop_column("notices", "court_name")
