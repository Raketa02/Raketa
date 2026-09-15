"""a player has a name and a nickname, and both are null until the naming

Sign-up asks for credentials only and a ``User`` is created **unnamed**
([#450](https://github.com/Raketa02/Raketa/issues/450),
[ADR-0171](../../docs/adr/0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md)).
Onboarding's first step then names the player in one act — a **Name**, free text
that every screen says and that is never unique, and the **Nickname**, today's
handle, still unique — so the projection row gains a ``name`` column and its
``nickname`` stops being required.

**The unique constraint on the nickname stays and admits any number of nulls.**
That is the SQL standard's reading and both Postgres and SQLite follow it: two
unnamed accounts share nothing, and the day one of them is named the constraint
is what the naming's own read is backed by.

**No backfill, and no widening for the streams.** Only ``local`` runs, its store
is disposable and a reset seed is the migration; ``users.user_registered`` lost
its ``nickname`` at v1 for the reason the ADR records. An account row that
predates this revision would read ``name IS NULL`` and be sent to the naming
step, which is the honest answer about an account nobody has named under the
new rule. **One more stored shape moved with it and this revision does not
touch it**: the card a search record keeps on each ``search_candidate`` row is
a JSON blob keyed ``name`` where it was keyed ``nickname``
(``matchmaking/infrastructure/sqlalchemy_search_store.py``), so a search
recorded before this branch would not read back. The reset covers it, as it
covers the streams; a store that outlived this would need the blob rewritten
in the same commit as this file.

Revision ID: 0022_the_naming
Revises: 0021_sportsmanship
Create Date: 2026-09-15

The revision id is short because ``alembic_version.version_num`` is
``VARCHAR(32)``; the filename carries the sentence.
"""

import sqlalchemy as sa
from alembic import op

revision = "0022_the_naming"
down_revision = "0021_sportsmanship"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("name", sa.String(length=64), nullable=True))
    op.alter_column(
        "users", "nickname", existing_type=sa.String(length=64), nullable=True
    )


def downgrade() -> None:
    # A row named under the new rule keeps its nickname; an unnamed one cannot
    # satisfy ``NOT NULL`` and the downgrade refuses rather than inventing a
    # handle for somebody. Only ``local`` runs, so a reset is the other way down.
    op.alter_column(
        "users", "nickname", existing_type=sa.String(length=64), nullable=False
    )
    op.drop_column("users", "name")
