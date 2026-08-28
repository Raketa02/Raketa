"""The interest table. **One row per live yes, and the origin key is two columns.**

``search-telemetry.md`` §4: the origin key — the search a yes came from and the
position it sat at — rides on the record that expresses the interest. There is no
``search_outcome_link``: the link is 1:1, a table buys a join for nothing, and
when ``matches`` lands the chain is ``match ← interest ← search``, still foreign
keys, still no third table.

**The primary key is the idempotency rule.** ``(from_player_id, to_player_id,
sport)`` is the key, so a second yes cannot become a second row even if two taps
race — the database refuses it rather than a use case remembering to check. That
is also why a yes cannot be *extended*: there is no update path here, so the
expiry the row was born with is the expiry it dies with.

**The row is deleted at expiry, and it is the only table in this context that is
ever deleted from.** ``docs/adr/0104``'s *nothing deletes a row* is about the
search record; ``the-engine.md`` §12 draws the line the other way for the two
ledgers beside it — *an interest expires, a pass record does not* — and this is
the one that expires. There is deliberately no ``expired_at`` and no ``state``
column: a yes is live or it is gone (``docs/adr/0127`` §5).

**No event stream and no outbox.** Interest is durable *without* being an
aggregate with a life story: it is a small fact with an expiry date, and nothing
downstream reacts to one being written. A mutual is not an event either — it is
what two rows facing each other already say.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils.types.uuid import UUIDType

from app.infrastructure.database.base import Base


class InterestORM(Base):
    """One *Let's play* yes, with the search it came from on the same row."""

    __tablename__ = "interest"
    __table_args__ = (
        # The lift's read and the mutual read are both *towards* somebody, and
        # neither is served by the primary key's leading column.
        Index("ix_interest_towards", "to_player_id", "sport", "expires_at"),
        # The expiry loop's sweep, and the only index a background job needs.
        Index("ix_interest_expires_at", "expires_at"),
        # **A check constraint, not a convention.** A yes to yourself is not a
        # state this product has; the write path cannot produce one — your own
        # search never returns you — and this refuses one that arrived any other
        # way.
        CheckConstraint(
            "from_player_id <> to_player_id",
            name="ck_interest_not_to_yourself",
        ),
        CheckConstraint(
            "expires_at > sent_at",
            name="ck_interest_expires_after_it_was_sent",
        ),
        CheckConstraint(
            "origin_position >= 1",
            name="ck_interest_origin_position_is_a_rank",
        ),
    )

    from_player_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False), primary_key=True
    )
    to_player_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False), primary_key=True
    )
    #: Sport-scoped, because a yes is about an evening of one game.
    sport: Mapped[str] = mapped_column(String(50), primary_key=True)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    #: **Dated at birth, never announced at death** (``docs/adr/0127`` §5). It is
    #: stored rather than derived from ``sent_at`` plus the ruleset's TTL so that
    #: a released change to the TTL cannot reach backwards and shorten a yes
    #: somebody already sent.
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    #: The **Origin key**, half one. Non-nullable and a foreign key: an interest
    #: citing an unknown or foreign search is refused rather than linked as null,
    #: because a silently dropped link is a denominator that lies.
    origin_search_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False),
        ForeignKey("search.id", ondelete="RESTRICT"),
        nullable=False,
    )
    #: The **Origin key**, half two: where in that search this person sat. It
    #: always resolves against ``band = RETURNED``, because no route ever returns
    #: a near-miss row for a player to act on.
    origin_position: Mapped[int] = mapped_column(Integer, nullable=False)
