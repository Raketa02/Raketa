"""create push_lines and push_devices: the notification channel's whole state

ADR-0062 makes a notification *a prompt to look, not a record*, and
`Raketa02/Raketa#84` is the ticket that builds the channel. Two tables, because
what the channel holds is exactly two things: **the one line a player's lock
screen currently shows**, and **where that lock screen is**.

**`push_lines` is one row per player, and that is ADR-0062's rule expressed as a
key.** A new seat's message *takes the previous one's place* rather than
stacking beside it — with no frequency cap in v1, the collapse is the frequency
control — so a table keyed on the player says on this side of the wire what the
collapse id says on the device, and no caller can break it.

**Its queue is a nullable column, not a second table.** `due_at` is the whole of
*a send is owed*, exactly as `dispatched_at` is the whole of the cascade's
state, and its index is **partial over the owed rows**, like
`ix_match_cascade_waves_due_at`: every player who has ever been sent a message
keeps a row, and an index carrying all of them would grow with the platform for
a query that never reads them. A separate queue table would be joined to this
one on this same key and could disagree with it about a player.

**`named_match_id` is a match and not a seat**, on ADR-0062's own rule —
*"Marek's seat and Zofia's seat are not distinguishable to somebody who was told
'a padel seat just opened'"* — and it is deliberately **not a foreign key**: it
is what her phone *says*, which is a fact about the past. A cascade would
rewrite that history when a match row went, and a restrict would make deleting a
match depend on whose lock screen mentioned it.

**Nothing in either table is ever withdrawn.** No platform offers server-side
removal of a delivered alert as a guarantee, so the retraction is carried by the
past-tense wording instead, and a settled send leaves the naming columns exactly
as they were: her phone still shows that line, and forgetting it here would send
it to her again.

**`push_devices` is keyed `(player_id, token)`**, so a player with two phones has
two rows and both are written to — under one collapse id, so each phone still
shows one message. `ix_push_devices_token` exists for the one question the key
cannot answer from its own left edge: *who else holds this token*. A phone signed
into a second account still answers to the same token, and a row left behind
would put one player's seats on somebody else's lock screen, which is the one
failure in this channel worse than silence.

`time_sensitive` is stored and **branched on by nothing** (ADR-0065): a player
who has revoked Time Sensitive keeps her standby priority and still gets the
seat. It is observability, and `notSupported` is a fourth value rather than a
synonym for a refusal.

Neither table announces anything, on ADR-0091's rule: the outbox is the trail a
support agent reads for a game somebody **paid for**, and a message moves no
money and confers no place. Nothing here is PostgreSQL-only — the partial index
is expressed for both dialects, and SQLite has supported partial indexes since
3.8.

Revision ID: 0019_push_lines_and_devices
Revises: 0018_match_offers_and_cascade_waves
Create Date: 2026-08-24
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0019_push_lines_and_devices"
down_revision = "0018_match_offers_and_cascade_waves"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "push_lines",
        # Not a foreign key, for the reason `match_offers.player_id` is not one:
        # a player lives behind a projection in another context.
        sa.Column("player_id", UUIDType(binary=False), nullable=False),
        sa.Column("named_match_id", UUIDType(binary=False), nullable=True),
        sa.Column("named_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("player_id", name="pk_push_lines"),
    )
    op.create_index(
        "ix_push_lines_due_at",
        "push_lines",
        ["due_at"],
        postgresql_where=sa.text("due_at IS NOT NULL"),
        sqlite_where=sa.text("due_at IS NOT NULL"),
    )

    op.create_table(
        "push_devices",
        sa.Column("player_id", UUIDType(binary=False), nullable=False),
        # Long, because an Expo token, an APNs token and an FCM registration id
        # are all different lengths and this table outlives the choice between
        # them (ADR-0062: the transport is untouched by any of these records).
        sa.Column("token", sa.String(length=512), nullable=False),
        sa.Column("platform", sa.String(length=16), nullable=False),
        sa.Column("time_sensitive", sa.String(length=16), nullable=False),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("player_id", "token", name="pk_push_devices"),
    )
    op.create_index("ix_push_devices_token", "push_devices", ["token"])


def downgrade() -> None:
    op.drop_table("push_devices")
    op.drop_table("push_lines")
