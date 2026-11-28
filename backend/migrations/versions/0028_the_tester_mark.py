"""a player may carry the tester mark, and every account starts without it

A **Tester** is a player whose account carries the tester mark — a real player
who may be given a feature before anyone else
([#478](https://github.com/Rakieta02/Rakieta/issues/478),
[ADR-0180](../../docs/adr/0180-a-feature-is-turned-on-by-a-pull-request-and-decided-on-the-device.md)
§9). The mark is two events on the ``User`` stream, and the projection row gains
an ``is_tester`` column beside ``is_admin`` and ``is_active`` — **beside
``authority`` and never a value of it**, because being shown something early
grants no power over anyone.

**On the row, and not only on the stream**, because every ``User`` a route is
handed is read from the row: a mark the projection could not hold would answer
``is_tester: false`` about a Tester, which is the trap ``adult_attested`` is
kept off the aggregate to avoid.

**``false`` for every row that exists**, through the server default, and that is
not a backfill: no stream written before this revision holds a tester event, so
``false`` is what each of them folds to.

Revision ID: 0028_the_tester_mark
Revises: 0027_the_reading
Create Date: 2026-09-23

The revision id fits ``alembic_version.version_num``'s ``VARCHAR(32)``.
"""

import sqlalchemy as sa
from alembic import op

revision = "0028_the_tester_mark"
down_revision = "0027_the_reading"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "is_tester", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "is_tester")
