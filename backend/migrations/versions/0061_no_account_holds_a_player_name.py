"""users: no account holds a player name — the ``name`` column goes

**A player is known by their nickname**
([#724](https://github.com/Rakieta02/Rakieta/issues/724);
[ADR-0199](../../docs/adr/0199-a-player-is-known-by-their-nickname.md) §6). The
Name 0025 added beside the nickname is retired: the naming carries a nickname
and nothing else (``users.user_named`` v2), an account an Invitation opens holds
no player name (``users.account_opened_by_invitation`` v2 — the name the club
typed stays on the Administrator's own row), and every read that names a person
reads the nickname. So the projection drops the column nothing writes or reads:

- **``users.name``**.

**Nothing is backfilled and nothing is moved.** The nickname column was always
the handle, and stays exactly as it is, unique and admitting any number of
nulls. A stream that recorded a name at v1 is read with it ignored, so a store
that outlived this would still replay — but only ``local`` runs, and the local
store may be reset after the re-versioning.

Revision ID: 0061_no_account_holds_a_player_name
Revises: 0060_a_notice_names_the_court_a_cancel_left
Create Date: 2026-11-04
"""

import sqlalchemy as sa
from alembic import op

revision = "0061_no_account_holds_a_player_name"
down_revision = "0060_a_notice_names_the_court_a_cancel_left"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("users", "name")


def downgrade() -> None:
    # The column comes back empty: no name was kept to restore, and an account
    # with a null name reads as one 0025 had not yet named.
    op.add_column("users", sa.Column("name", sa.String(length=64), nullable=True))
