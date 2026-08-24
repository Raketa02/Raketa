"""Two tables: the line each player's lock screen holds, and where to reach her.

The push channel's whole state, and it is Now's for the reason the offers table
is: **a message is not a fact about a match**. No rung reads one, no deadline
moves, no seat changes state, so routing either of these through ``Match`` would
bump ADR-0034's version column and invalidate the scoring-context cache every
time somebody's phone was told about a seat.

**Neither announces anything**, on ADR-0091's rule. The outbox is the trail a
support agent reads for a game somebody **paid for**; a notification moves no
money and confers no place, and ADR-0062 is explicit that it is *a prompt to
look, not a record*.

Nothing here is PostgreSQL-only.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils.types.uuid import UUIDType

from app.infrastructure.database.base import Base


class PushLineORM(Base):
    """The one line we occupy on one player's lock screen. **One row, ever.**

    ADR-0062 gives a player exactly one live message and makes the collapse id
    the frequency control; keyed on the player alone, the *table* says the same
    thing the collapse id says on the device, so the invariant cannot be broken
    by a caller.

    **The queue is a nullable column and not a second table.** ``due_at`` is the
    whole of *a send is owed*, exactly as ``dispatched_at`` is the whole of the
    cascade's state, and its index is partial over the owed rows — the settled
    ones are the ones that accumulate. A separate queue table would be joined to
    this one on this same key and could disagree with it about a player.

    Nothing here is ever deleted. A row is a player's lock screen, which does
    not stop existing.
    """

    __tablename__ = "push_lines"

    #: Not a foreign key, for the reason ``match_offers.player_id`` is not one:
    #: a player lives behind a projection in another context.
    player_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False), primary_key=True
    )
    #: Which match the live message names, or null for a lock screen holding
    #: nothing of ours. **A match and not a seat**: what she was told about is
    #: the match having room (ADR-0062).
    #:
    #: **Deliberately not a foreign key.** It is what her phone *says*, which is
    #: a fact about the past — a cascade on the match would rewrite history when
    #: a row went, and a restrict would make deleting a match depend on whose
    #: lock screen mentioned it.
    named_match_id: Mapped[UUID | None] = mapped_column(
        UUIDType(binary=False), nullable=True
    )
    #: When that message went out. Null exactly when ``named_match_id`` is.
    named_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    #: When a send is owed, or null when none is. Set by a dispatch that told
    #: her about something, cleared by the send whatever it decided.
    due_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        # Named, like `pk_match_offers` and `pk_command_log`: a constraint a
        # support agent can find by name in a PostgreSQL error is one somebody
        # can reason about.
        sa.PrimaryKeyConstraint("player_id", name="pk_push_lines"),
        # The tick's one query: rows owing a send whose moment has come. Partial
        # over the owed ones, like `ix_match_cascade_waves_due_at` — every
        # player who has ever been sent a message keeps a row, and an index
        # carrying them all would grow with the platform for a query that never
        # reads them.
        sa.Index(
            "ix_push_lines_due_at",
            "due_at",
            postgresql_where=sa.text("due_at IS NOT NULL"),
            sqlite_where=sa.text("due_at IS NOT NULL"),
        ),
    )


class PushDeviceORM(Base):
    """One phone, and what it last told us about itself.

    Keyed ``(player_id, token)``, so a player with two phones has two rows and
    both are written to — with one collapse id, so each phone still shows one
    message.

    **The token is the phone's identity and a phone has one player at a time.**
    A row is therefore removed from every *other* player when a token is
    registered: a token that survived a sign-out would put one person's seats on
    somebody else's lock screen, which is the one failure in this channel worse
    than silence. That is the only deletion anywhere in the push path, and it is
    about a device rather than about a message.
    """

    __tablename__ = "push_devices"

    player_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False), primary_key=True
    )
    #: What the transport addresses. Long, because an Expo token, an APNs token
    #: and an FCM registration id are all different lengths and this table
    #: outlives the choice between them (ADR-0062).
    token: Mapped[str] = mapped_column(sa.String(512), primary_key=True)
    #: ``ios`` or ``android`` — which fields a message for this phone carries.
    platform: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    #: ``enabled`` / ``disabled`` / ``notSupported``, as reported. **Stored and
    #: never branched on** (ADR-0065): it is observability, and `notSupported`
    #: is a fourth value rather than a synonym for a refusal.
    time_sensitive: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    registered_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )

    __table_args__ = (
        sa.PrimaryKeyConstraint("player_id", "token", name="pk_push_devices"),
        # *Who else holds this token* — the sign-out case above. The composite
        # key cannot answer it from its own left edge.
        sa.Index("ix_push_devices_token", "token"),
    )
