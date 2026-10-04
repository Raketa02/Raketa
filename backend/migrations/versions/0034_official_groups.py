"""official groups: a group with no Owner, run by an Administrator

Administrators create and run their club's official groups from the app
([#509](https://github.com/Raketa02/Raketa/issues/509),
[ADR-0183](../../docs/adr/0183-a-group-is-a-crowd-at-a-home-club-and-its-link-never-changes.md)
§3). One aggregate holds both kinds, so its projection gains the kind and the
three facts only an official group has:

- **``kind``** — ``PLAYER`` or ``OFFICIAL``. Every row written before this is a
  player group, which is what the server default says of them.
- **``owner_id`` becomes nullable**: an official group has no Owner.
- **``administrator_id``** — the Administrator who runs it, indexed, because an
  administrator's Groups tab lists exactly theirs.
- **``whatsapp_size``** and **``declared_sports``** — the size of the WhatsApp
  group it mirrors, and what it plays, as registry codes.

A check constraint holds the two shapes, so a row that is neither is refused by
the database as well as by the aggregate.

Revision ID: 0034_official_groups
Revises: 0033_administrators
Create Date: 2026-09-26
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0034_official_groups"
down_revision = "0033_administrators"
branch_labels = None
depends_on = None

_SHAPE = (
    "(kind = 'PLAYER' AND owner_id IS NOT NULL AND administrator_id IS NULL"
    " AND whatsapp_size IS NULL AND declared_sports IS NULL)"
    " OR (kind = 'OFFICIAL' AND owner_id IS NULL"
    " AND administrator_id IS NOT NULL AND whatsapp_size IS NOT NULL"
    " AND declared_sports IS NOT NULL)"
)


def upgrade() -> None:
    op.add_column(
        "groups",
        sa.Column(
            "kind", sa.String(16), nullable=False, server_default=sa.text("'PLAYER'")
        ),
    )
    op.alter_column(
        "groups", "owner_id", existing_type=UUIDType(binary=False), nullable=True
    )
    op.add_column(
        "groups",
        sa.Column(
            "administrator_id",
            UUIDType(binary=False),
            sa.ForeignKey(
                "administrators.id",
                ondelete="RESTRICT",
                name="fk_groups_administrator_id_administrators",
            ),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_groups_administrator_id", "groups", ["administrator_id"], unique=False
    )
    op.add_column("groups", sa.Column("whatsapp_size", sa.Integer(), nullable=True))
    op.add_column("groups", sa.Column("declared_sports", sa.JSON(), nullable=True))
    op.create_check_constraint("ck_groups_kind_shape", "groups", _SHAPE)


def downgrade() -> None:
    op.drop_constraint("ck_groups_kind_shape", "groups", type_="check")
    op.execute("DELETE FROM groups WHERE kind = 'OFFICIAL'")
    op.drop_column("groups", "declared_sports")
    op.drop_column("groups", "whatsapp_size")
    op.drop_index("ix_groups_administrator_id", table_name="groups")
    op.drop_column("groups", "administrator_id")
    op.alter_column(
        "groups", "owner_id", existing_type=UUIDType(binary=False), nullable=False
    )
    op.drop_column("groups", "kind")
