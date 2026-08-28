"""``InterestLedger`` over SQLAlchemy. **It adds rows and it never commits.**

The transaction boundary is the command's decision, exactly as it is for the
search store beside it: a yes and the read that proved its origin key belong to
one request, and a store that committed for itself would take that decision away
from the one place that has to make it.

**Every read here is bounded by ``now``, and the bound is passed in.** A lapsed
row is invisible to every query in this file, so *lapsed* and *never sent* are
the same answer at this seam — which is the port's rule and is why nothing here
reads a clock: the use case holds one, the loop holds one, and an adapter that
held a third would be a third opinion about when a yes died.

**The one delete in this context lives here.** ``docs/adr/0104``'s *nothing
deletes a row* is about the search record; ``the-engine.md`` §12 draws the line
the other way for this one — *an interest expires, a pass record does not* — and
:meth:`lapse` is the whole of that expiry.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Collection, Mapping
from uuid import UUID

from sqlalchemy import delete, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.kernel import Sport
from app.modules.matchmaking.domain.interest import Interest, Lapsed, OriginKey
from app.modules.matchmaking.domain.searches import CandidateBand, InclusionReason
from app.modules.matchmaking.infrastructure.interest_model import InterestORM
from app.modules.matchmaking.infrastructure.search_model import (
    SearchCandidateORM,
    SearchORM,
)


class SqlAlchemyInterestLedger:
    """The durable ledger of every live *Let's play*, over the caller's session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find(
        self,
        *,
        from_player_id: UUID,
        to_player_id: UUID,
        sport: Sport,
        now: datetime,
    ) -> Interest | None:
        """This player's own live yes to that person, if there is one."""

        row = await self._session.scalar(
            select(InterestORM).where(
                InterestORM.from_player_id == from_player_id,
                InterestORM.to_player_id == to_player_id,
                InterestORM.sport == sport.value,
                InterestORM.expires_at > now,
            )
        )
        return None if row is None else _interest(row)

    async def record(self, interest: Interest) -> None:
        """Add one yes. The caller commits."""

        self._session.add(
            InterestORM(
                from_player_id=interest.from_player_id,
                to_player_id=interest.to_player_id,
                sport=interest.sport.value,
                sent_at=interest.at,
                expires_at=interest.expires_at,
                origin_search_id=interest.origin.search_id,
                origin_position=interest.origin.position,
            )
        )
        await self._session.flush()

    async def outstanding(
        self, *, player_id: UUID, sport: Sport, now: datetime
    ) -> int:
        """Sent, unexpired and **not yet mutual** — the cap's own denominator.

        The mutual half is a ``NOT EXISTS`` over the same table facing the other
        way rather than a second query the caller subtracts, because the count on
        the screen and the count the cap is checked against have to be one
        expression: two would drift the first time somebody optimised one.
        """

        theirs = aliased(InterestORM)
        answered = exists().where(
            theirs.from_player_id == InterestORM.to_player_id,
            theirs.to_player_id == InterestORM.from_player_id,
            theirs.sport == InterestORM.sport,
            theirs.expires_at > now,
        )
        count = await self._session.scalar(
            select(func.count())
            .select_from(InterestORM)
            .where(
                InterestORM.from_player_id == player_id,
                InterestORM.sport == sport.value,
                InterestORM.expires_at > now,
                ~answered,
            )
        )
        return int(count or 0)

    async def outgoing(
        self, *, player_id: UUID, now: datetime
    ) -> tuple[Interest, ...]:
        """Every live yes this player sent, newest first."""

        rows = await self._session.scalars(
            select(InterestORM)
            .where(
                InterestORM.from_player_id == player_id,
                InterestORM.expires_at > now,
            )
            .order_by(
                InterestORM.sent_at.desc(),
                # A total order, so two yeses sent in one transaction do not
                # swap places between two renders of the same list.
                InterestORM.to_player_id.asc(),
                InterestORM.sport.asc(),
            )
        )
        return tuple(_interest(row) for row in rows)

    async def mutual(
        self, *, player_id: UUID, now: datetime
    ) -> tuple[Interest, ...]:
        """This player's own live yeses that came back."""

        theirs = aliased(InterestORM)
        rows = await self._session.scalars(
            select(InterestORM)
            .where(
                InterestORM.from_player_id == player_id,
                InterestORM.expires_at > now,
                exists().where(
                    theirs.from_player_id == InterestORM.to_player_id,
                    theirs.to_player_id == InterestORM.from_player_id,
                    theirs.sport == InterestORM.sport,
                    theirs.expires_at > now,
                ),
            )
            .order_by(
                InterestORM.sent_at.desc(),
                InterestORM.to_player_id.asc(),
                InterestORM.sport.asc(),
            )
        )
        return tuple(_interest(row) for row in rows)

    async def days_ago_towards(
        self,
        *,
        player_id: UUID,
        sport: Sport,
        senders: Collection[UUID],
        now: datetime,
    ) -> Mapping[UUID, int]:
        """Which of these people said *Let's play*, and how many days ago.

        One keyed read over the whole candidate set, never a query per row. An
        empty population short-circuits: an ``IN ()`` is a query asking the
        database to answer about nobody.
        """

        if not senders:
            return {}
        rows = await self._session.scalars(
            select(InterestORM).where(
                InterestORM.to_player_id == player_id,
                InterestORM.sport == sport.value,
                InterestORM.expires_at > now,
                InterestORM.from_player_id.in_(list(senders)),
            )
        )
        return {
            row.from_player_id: _interest(row).days_ago_at(now) for row in rows
        }

    async def lapse(self, *, now: datetime) -> Lapsed:
        """Remove every yes whose expiry has passed, counting what it cost.

        The count of yeses that **never lifted anybody** is taken before the
        delete, over the same predicate, because that is the last moment the rows
        exist: a lapsed row leaves no trace by design, so the falsifier
        ``the-five-numbers.md`` §8 names on day one has to be computed here or
        never.

        *Lifted* means a search **that person ran** put this sender in its answer
        with ``inclusion_reason = INTEREST_LIFT`` while the yes stood. That join
        is the definition rather than an approximation of it — the recorded
        reason is written by the same pipeline the ledger feeds.
        """

        due = InterestORM.expires_at <= now
        lifted = (
            select(SearchCandidateORM.search_id)
            .join(SearchORM, SearchORM.id == SearchCandidateORM.search_id)
            .where(
                SearchORM.searcher_id == InterestORM.to_player_id,
                SearchCandidateORM.player_id == InterestORM.from_player_id,
                SearchCandidateORM.band == CandidateBand.RETURNED.value,
                SearchCandidateORM.inclusion_reason
                == InclusionReason.INTEREST_LIFT.value,
                SearchORM.sport == InterestORM.sport,
                SearchORM.at >= InterestORM.sent_at,
                SearchORM.at < InterestORM.expires_at,
            )
        )
        removed = await self._session.scalar(
            select(func.count()).select_from(InterestORM).where(due)
        )
        unfired = await self._session.scalar(
            select(func.count())
            .select_from(InterestORM)
            .where(due, ~exists(lifted))
        )
        await self._session.execute(delete(InterestORM).where(due))
        return Lapsed(removed=int(removed or 0), never_lifted=int(unfired or 0))


def _interest(row: InterestORM) -> Interest:
    return Interest(
        from_player_id=row.from_player_id,
        to_player_id=row.to_player_id,
        sport=Sport(row.sport),
        at=_utc(row.sent_at),
        expires_at=_utc(row.expires_at),
        origin=OriginKey(
            search_id=row.origin_search_id, position=row.origin_position
        ),
    )


def _utc(value: datetime) -> datetime:
    """A stored moment, read back as the UTC it was written as.

    The same seam ``sqlalchemy_search_store`` has, for the same reason:
    PostgreSQL's ``timestamptz`` carries the offset and SQLite does not, and the
    value was written as UTC — so reading it as anything else would move it.
    """

    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value
