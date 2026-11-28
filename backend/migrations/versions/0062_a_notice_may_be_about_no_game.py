"""notifications: a notice may be about no game — *Get your level*

**One notice is about no game at all** ([#727](https://github.com/Rakieta02/Rakieta/issues/727);
[ADR-0200](../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §7; the
mechanics §17.2, Q126): *Get your level so your groups can deal you games.*,
once per account, ever, a day after a first group join while rated in nothing.
It names no group and no sport and opens Home, so the six facts of a game the
recent list holds are absent from it:

- **``notices.game_id``, ``pool_id``, ``sport``, ``game_kind``, ``club_id`` and
  ``starts_at``** become nullable.

**Nothing is backfilled**: every row given before is about a game and keeps all
six, and every other kind still writes all six.

Revision ID: 0062_a_notice_may_be_about_no_game
Revises: 0061_no_account_holds_a_player_name
Create Date: 2026-11-04
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0062_a_notice_may_be_about_no_game"
down_revision = "0061_no_account_holds_a_player_name"
branch_labels = None
depends_on = None

#: The six facts of a game, each with the type 0045 gave it.
_A_GAME = (
    ("game_id", UUIDType(binary=False)),
    ("pool_id", UUIDType(binary=False)),
    ("sport", sa.String(16)),
    ("game_kind", sa.String(16)),
    ("club_id", UUIDType(binary=False)),
    ("starts_at", sa.DateTime(timezone=True)),
)


def upgrade() -> None:
    for column, kind in _A_GAME:
        op.alter_column("notices", column, existing_type=kind, nullable=True)


def downgrade() -> None:
    # A notice about no game cannot stand in a table that requires one.
    op.execute("DELETE FROM notices WHERE game_id IS NULL")
    for column, kind in _A_GAME:
        op.alter_column("notices", column, existing_type=kind, nullable=False)
