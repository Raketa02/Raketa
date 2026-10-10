"""payments: a share is held until the cut-off

**The fill holds the shares and the cut-off takes them**
([#637](https://github.com/Raketa02/Raketa/issues/637); the mechanics Q113;
ADR-0189's 2026-10-10 amendment). A game that books before its club's cut-off
keeps each seat's hold for the booked game and takes nothing; the cut-off job
takes it. Two changes to the ``seat_charges`` projection, written from the
aggregate on every save:

- **``status`` may be ``HELD``** — a share held for the booked game until the
  cut-off, not paid.
- **``seat_charges.held_until``** — the cut-off a held share is taken at. The
  cut-off job reads the shares still held whose moment has come, by it.

Every charge recorded before was taken at the fill, and holds nothing.

Revision ID: 0054_a_share_is_held_until_the_cut_off
Revises: 0053_a_game_waits_for_one_payment
Create Date: 2026-10-10
"""

import sqlalchemy as sa
from alembic import op

revision = "0054_a_share_is_held_until_the_cut_off"
down_revision = "0053_a_game_waits_for_one_payment"
branch_labels = None
depends_on = None

_BEFORE = (
    "status IN ('AUTHORISED', 'FAILED', 'TAKING', 'CAPTURED', 'RELEASING', "
    "'CANCELLED')"
)
_NOW = (
    "status IN ('AUTHORISED', 'FAILED', 'HELD', 'TAKING', 'CAPTURED', "
    "'RELEASING', 'CANCELLED')"
)


def upgrade() -> None:
    op.drop_constraint("ck_seat_charges_status", "seat_charges", type_="check")
    op.create_check_constraint("ck_seat_charges_status", "seat_charges", _NOW)
    op.add_column(
        "seat_charges",
        sa.Column("held_until", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_seat_charges_status_held_until", "seat_charges", ["status", "held_until"]
    )


def downgrade() -> None:
    # The code before this knows no held share: the old check refuses to be
    # put back while any row is ``HELD``, so take or let go of every held share
    # before going back.
    op.drop_index("ix_seat_charges_status_held_until", table_name="seat_charges")
    op.drop_column("seat_charges", "held_until")
    op.drop_constraint("ck_seat_charges_status", "seat_charges", type_="check")
    op.create_check_constraint("ck_seat_charges_status", "seat_charges", _BEFORE)
