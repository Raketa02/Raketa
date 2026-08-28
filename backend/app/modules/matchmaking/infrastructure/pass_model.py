"""The pass table. **Append-only, unexpiring, and returned by no route.**

``search-telemetry.md`` §6 makes the pass a durable row —
``(passer, passed, sport, at, search_id, position)`` — while the 30-day
suppression stays a Redis key derived from it. **The gate is the cache; the
evidence is the row**, and the split is exactly why the row is here: a lapsed
suppression leaves no trace the pair was ever passed, so at the moment a re-show
happens the fact that makes it one has expired.

**An interest expires; a pass record does not.** The table beside this one is the
only table in this context that is deleted from; this one joins the search
record's rule that erasure is the only path that will ever remove a row
(``docs/adr/0104`` §3).

**The primary key is a surrogate, and that is the escalation rule made
structural.** ``(passer, passed, sport)`` would collapse a second pass into the
first, and a pass **never escalates** — a second one buys the same thirty days
and no more (``docs/adr/0128`` §3) — so nothing here counts them, and there is
nothing for a penalty to be grown out of. What two rows are is two facts with two
moments and two origins, which is what the falsifier wants.

**No event and no outbox**, on the same argument the interest row is exempt
under: a small fact with no life story, and nothing downstream reacts to one
being written. The suppression the deck reads is a cache write the use case makes
after the commit, not a subscriber.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils.types.uuid import UUIDType

from app.infrastructure.database.base import Base


class PassORM(Base):
    """One *not today*, with the card it was made on named on the same row."""

    __tablename__ = "player_pass"
    __table_args__ = (
        # The deal's read: *which of these has this player ever passed on, in
        # this sport*. One keyed read over a deal of ten, and the only index the
        # request path needs.
        Index("ix_player_pass_passer", "passer_id", "sport", "passed_id"),
        # **A check constraint, not a convention.** The write path cannot produce
        # a pass on yourself — your own search never returns you — and this
        # refuses one that arrived any other way.
        CheckConstraint(
            "passer_id <> passed_id",
            name="ck_player_pass_not_on_yourself",
        ),
        CheckConstraint(
            "origin_position >= 1",
            name="ck_player_pass_origin_position_is_a_rank",
        ),
    )

    #: A surrogate, because the fact is the **event** and not the pair. See the
    #: module docstring: a natural key on the pair would make a second pass
    #: unrepresentable, and two passes a month apart are two facts.
    id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    passer_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), nullable=False)
    passed_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), nullable=False)
    #: Sport-scoped, because the card was a card about one game. The
    #: **suppression** key beside it is not: ``suppress:{from}:{to}`` is one
    #: deck's courtesy, and the deck is per player rather than per sport.
    sport: Mapped[str] = mapped_column(String(50), nullable=False)
    passed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    #: The **Origin key**, half one. Non-nullable and a foreign key, on the
    #: interest row's own rule: a pass citing an unknown or foreign search is
    #: refused rather than linked as null, because *pass rate per deal* is a
    #: denominator and a dropped link makes it lie.
    origin_search_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False),
        ForeignKey("search.id", ondelete="RESTRICT"),
        nullable=False,
    )
    #: The **Origin key**, half two: where in that search this person sat. It
    #: always resolves against ``band = RETURNED``, because no route ever returns
    #: a near-miss row for a player to act on.
    origin_position: Mapped[int] = mapped_column(Integer, nullable=False)
