"""notifications: *Game moved* by a club's cancel names the court it left

**A club's cancel moves the game when a free court of the same club absorbs it**
([#672](https://github.com/Raketa02/Raketa/issues/672); the mechanics §16.9,
§17.2, Q122), and the players are told why: *Bonarka Arena moved your game to
Court 3 · Thu 19:00* / *Court 2 can't be played · Padel · indoor · nothing else
changes*. A notice records facts, never words, and the court the game left is
one — kept on the row so it reads the same after a second move, as the court it
moved to is (0059):

- **``notices.moved_from``** — what the club calls the court the game left.

The cancel's reason rides on the existing ``notices.reason``. ``NULL`` on every
other kind, and on every row given before: no cancel had moved a game until
now.

Revision ID: 0060_a_notice_names_the_court_a_cancel_left
Revises: 0059_a_notice_names_the_court_it_moved_to
Create Date: 2026-10-12
"""

import sqlalchemy as sa
from alembic import op

revision = "0060_a_notice_names_the_court_a_cancel_left"
down_revision = "0059_a_notice_names_the_court_it_moved_to"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("notices", sa.Column("moved_from", sa.String(40), nullable=True))


def downgrade() -> None:
    op.drop_column("notices", "moved_from")
