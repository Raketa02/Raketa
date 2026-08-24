"""``StandbyPlaces`` over one table with a composite key.

The store ADR-0087 discovered was missing. ``kernel.Viewer`` has carried
``on_standby`` since the ladder shipped and ``NotOnStandby`` has been one of the
eight eligibility rules since the funnel did; nothing anywhere recorded that a
player had asked (``Raketa02/Raketa#81``).

**Both writes are idempotent**, which is what lets ADR-0087 refuse a key: a
repeated delete of a place she no longer holds is the state she asked for. The
leave is a delete whose row count nobody reads, so it is idempotent by the
statement itself; the join reads first and inserts if absent, which is the
append-and-update shape ``_write_vacancies`` already uses one file over. The
composite primary key is what refuses a genuinely simultaneous second join, and
losing that race is an error rather than a duplicate — there is no join surface
in v1 for two taps to arrive through.

**It announces nothing**, which is the one place Matches departs from ADR-0034's
*every change is its own named event*. That obligation is about a match — the
outbox is the only trail a support agent has for a game somebody paid for. A
standby place moves no money and confers no place, and its one reader is the
invitation cascade, which reads the list when a seat frees rather than
following it.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.kernel import Instant

from app.modules.matches.infrastructure.sqlalchemy_match_models import (
    MatchStandbyPlaceORM,
)


class SqlAlchemyStandbyPlaces:
    """The queue, as two writes and one read over ``match_standby_places``."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def join(self, *, match_id: UUID, player_id: UUID, at: Instant) -> None:
        """Queue her, or leave her queued.

        Read then insert, which is the shape ``_write_vacancies`` already uses
        one file over, rather than an ``ON CONFLICT`` clause that would have to
        be spelled twice — once per dialect — and would make the fast suite
        exercise a different statement from the one PostgreSQL runs.

        A statement rather than ``session.add``, and the difference is
        visibility: this app's sessions are ``autoflush=False``, so a pending
        object is invisible to the very next ``SELECT`` in its own transaction.
        Both writes here are statements, so a caller that joins and then asks —
        which is exactly what the seed's own name check does — sees what it
        wrote without anybody having to remember to flush.

        A second join deliberately does **not** move ``joined_at``. Nothing
        reads it today (rung 1 is fit-ordered, ADR-0061), and of the two
        answers the honest one is *when she first asked*.
        """

        if await self._holds(match_id=match_id, player_id=player_id):
            return
        await self._session.execute(
            insert(MatchStandbyPlaceORM).values(
                match_id=match_id, player_id=player_id, joined_at=at
            )
        )

    async def leave(self, *, match_id: UUID, player_id: UUID) -> None:
        """Take her off, or leave the queue as it already is.

        **Deleted rather than ended**, which is the opposite of every other
        child table in this context and is the decision rather than an
        oversight: a vacancy, a departure and a seat claim are all kept because
        *what happened at 18:03* is a support question about money or about a
        seat somebody could not take, and neither is true here.

        The row count is not read. *And it was there* has exactly one honest
        use — telling her she had already left — and ADR-0087 refuses to tell
        her anything at all: nothing was lost, so there is nothing to report.
        """

        await self._session.execute(
            delete(MatchStandbyPlaceORM).where(
                MatchStandbyPlaceORM.match_id == match_id,
                MatchStandbyPlaceORM.player_id == player_id,
            )
        )

    async def held_by(self, player_id: UUID) -> frozenset[UUID]:
        """Which matches she is queued for, off the index that exists for it.

        The composite primary key answers *who is queued for this match* from
        its own left edge; this is the other direction, and it is the one a home
        screen pays on every compose, so it has an index of its own.
        """

        rows = await self._session.execute(
            select(MatchStandbyPlaceORM.match_id).where(
                MatchStandbyPlaceORM.player_id == player_id
            )
        )
        return frozenset(rows.scalars().all())

    async def _holds(self, *, match_id: UUID, player_id: UUID) -> bool:
        """Whether the pair is already there, off the primary key itself."""

        row = await self._session.execute(
            select(MatchStandbyPlaceORM.player_id).where(
                MatchStandbyPlaceORM.match_id == match_id,
                MatchStandbyPlaceORM.player_id == player_id,
            )
        )
        return row.scalars().one_or_none() is not None
