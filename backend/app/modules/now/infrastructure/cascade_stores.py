"""``Offers`` and ``CascadeWaves`` over the two tables the cascade owns.

One file for both, because they are one mechanism read from two ends — *what is
left to tell* and *what was told* — and a reader following a dispatch should not
have to open two adapters to see all of it. They are two **ports** because their
readers differ: the offers region will take ``Offers`` alone
(``Raketa02/Raketa#83``), and a composer holding an object that can bring a
dispatch forward is a composer one autocomplete away from doing it.

**Neither commits.** Opening the waves belongs to the transaction that wrote the
departure — a hole with no cascade behind it is a seat nobody will ever be told
about — and a dispatch belongs to its own, which ``RunCascade`` closes.

**Statements rather than ``session.add``**, on the rule ADR-0091's seed run
found the hard way: this app's sessions are ``autoflush=False``, so a pending
object is invisible to the very next ``SELECT`` in its own transaction. A
dispatch writes offers and the *same* transaction may read them back — the
second wave's own filter does exactly that when a first wave ran moments
earlier — so every write here is a statement.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence
from uuid import UUID

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.kernel import Instant, OfferKind, SeatShare, grosze, instant

from app.modules.now.domain.cascade import Offer, PendingWave, Rung, Wave
from app.modules.now.infrastructure.sqlalchemy_cascade_models import (
    MatchCascadeWaveORM,
    MatchOfferORM,
)


class SqlAlchemyOffers:
    """What the cascade told whom, as one write and two reads."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(self, offers: Sequence[Offer]) -> None:
        """Write these offers, saying nothing about one already made.

        Read-then-insert rather than an ``ON CONFLICT`` clause, which is the
        shape ``SqlAlchemyStandbyPlaces.join`` and ``_write_vacancies`` already
        take: the clause would have to be spelled once per dialect, and the fast
        suite would then exercise a different statement from the one PostgreSQL
        runs.

        **The row that is already there is left exactly as it was**, rather than
        re-stamped with a new instant. ADR-0061's *"a lapse resumes them and
        nobody is told twice"* is about the person, and an offer whose
        ``offered_at`` moved is the same person told again as far as ADR-0065's
        *one live message per player* can tell.
        """

        if not offers:
            return
        held = await self._offered_for_all(
            {offer.vacancy_id for offer in offers}
        )
        fresh = [
            offer
            for offer in offers
            if (offer.vacancy_id, offer.player_id) not in held
        ]
        if not fresh:
            return
        await self._session.execute(
            insert(MatchOfferORM).values(
                [
                    {
                        "vacancy_id": offer.vacancy_id,
                        "player_id": offer.player_id,
                        "match_id": offer.match_id,
                        "rung": offer.player_rung.value,
                        "fit": offer.fit,
                        "price_grosze": int(offer.price),
                        "kind": offer.kind.value,
                        "offered_at": offer.offered_at,
                    }
                    for offer in fresh
                ]
            )
        )

    async def offered_for(self, *, vacancy_id: UUID) -> frozenset[UUID]:
        """Who has already been told about this hole, off the key's left edge."""

        rows = await self._session.execute(
            select(MatchOfferORM.player_id).where(
                MatchOfferORM.vacancy_id == vacancy_id
            )
        )
        return frozenset(rows.scalars().all())

    async def held_by(self, player_id: UUID) -> tuple[Offer, ...]:
        """Her offers, newest first, off ``ix_match_offers_player_id``.

        Ordered by the instant and broken by the hole, which is total: two
        offers written by one dispatch share ``offered_at`` to the microsecond,
        and a region whose order is the query plan reshuffles under her thumb —
        the defect ``FEED_ORDER``'s fourth comparator exists for.
        """

        rows = await self._session.execute(
            select(MatchOfferORM)
            .where(MatchOfferORM.player_id == player_id)
            .order_by(
                MatchOfferORM.offered_at.desc(), MatchOfferORM.vacancy_id
            )
        )
        return tuple(offer_of(row) for row in rows.scalars().all())

    async def reached_on(self, *, match_id: UUID) -> frozenset[UUID]:
        """Who has been told about any hole in this match — **rung 3**.

        Off ``ix_match_offers_match_id``, which exists for this: the composite
        key is on the hole, and a rung about *this match's earlier holes* cannot
        be answered from it.
        """

        rows = await self._session.execute(
            select(MatchOfferORM.player_id).where(MatchOfferORM.match_id == match_id)
        )
        return frozenset(rows.scalars().all())

    async def _offered_for_all(
        self, vacancy_ids: set[UUID]
    ) -> frozenset[tuple[UUID, UUID]]:
        """Every ``(hole, player)`` already written among these holes.

        One read for the whole write, rather than one per hole: a dispatch is
        always about a single hole today, and the batch shape is what keeps that
        an observation about the caller rather than an assumption in the store.
        """

        rows = await self._session.execute(
            select(MatchOfferORM.vacancy_id, MatchOfferORM.player_id).where(
                MatchOfferORM.vacancy_id.in_(sorted(vacancy_ids, key=str))
            )
        )
        return frozenset((vacancy, player) for vacancy, player in rows.all())


class SqlAlchemyCascadeWaves:
    """The dispatch queue: two rows per hole, and the tick's one query."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def open(self, waves: Sequence[PendingWave]) -> None:
        """Put these dispatches on the queue, or leave the ones already there.

        Idempotent per ``(hole, wave)`` for the reason the join is: a departure
        replayed under its own request key must not double the queue, and
        ADR-0030 makes a replay return the first outcome rather than refusing.
        """

        if not waves:
            return
        held = await self._known({wave.vacancy_id for wave in waves})
        fresh = [
            wave for wave in waves if (wave.vacancy_id, wave.wave.value) not in held
        ]
        if not fresh:
            return
        await self._session.execute(
            insert(MatchCascadeWaveORM).values(
                [
                    {
                        "vacancy_id": wave.vacancy_id,
                        "wave": wave.wave.value,
                        "match_id": wave.match_id,
                        "due_at": wave.due_at,
                        "dispatched_at": None,
                    }
                    for wave in fresh
                ]
            )
        )

    async def due(self, *, now: Instant, limit: int) -> tuple[PendingWave, ...]:
        """Outstanding dispatches whose moment has come, oldest first.

        Ordered by ``due_at`` and broken by the key, which is total: two holes
        opened in the same millisecond would otherwise be taken in whatever
        order the plan chose, and a batch that is not deterministic is one whose
        truncation at ``limit`` is not either.
        """

        rows = await self._session.execute(
            select(MatchCascadeWaveORM)
            .where(
                MatchCascadeWaveORM.dispatched_at.is_(None),
                MatchCascadeWaveORM.due_at <= now,
            )
            .order_by(
                MatchCascadeWaveORM.due_at,
                MatchCascadeWaveORM.vacancy_id,
                MatchCascadeWaveORM.wave,
            )
            .limit(limit)
        )
        return tuple(_wave(row) for row in rows.scalars().all())

    async def dispatched(
        self, *, vacancy_id: UUID, wave: Wave, at: Instant
    ) -> None:
        """Mark one dispatch done. A dispatch that reached nobody is still done."""

        await self._session.execute(
            update(MatchCascadeWaveORM)
            .where(
                MatchCascadeWaveORM.vacancy_id == vacancy_id,
                MatchCascadeWaveORM.wave == wave.value,
            )
            .values(dispatched_at=at)
        )

    async def bring_forward(
        self, *, vacancy_id: UUID, wave: Wave, to: Instant
    ) -> None:
        """Pull a pending dispatch earlier, and **never later**.

        The ``due_at > to`` predicate is the *never later* half, in the
        statement rather than in the caller: ADR-0061's empty-rung rule is the
        only thing that moves a dispatch at all, and the only direction it may
        move is towards now. A dispatch already done is untouched, because a
        second wave that has run has nothing left to bring forward.
        """

        await self._session.execute(
            update(MatchCascadeWaveORM)
            .where(
                MatchCascadeWaveORM.vacancy_id == vacancy_id,
                MatchCascadeWaveORM.wave == wave.value,
                MatchCascadeWaveORM.dispatched_at.is_(None),
                MatchCascadeWaveORM.due_at > to,
            )
            .values(due_at=to)
        )

    async def _known(self, vacancy_ids: set[UUID]) -> frozenset[tuple[UUID, int]]:
        rows = await self._session.execute(
            select(
                MatchCascadeWaveORM.vacancy_id, MatchCascadeWaveORM.wave
            ).where(
                MatchCascadeWaveORM.vacancy_id.in_(sorted(vacancy_ids, key=str))
            )
        )
        return frozenset((vacancy, wave) for vacancy, wave in rows.all())


def _as_instant(value: datetime) -> Instant:
    """Re-attach UTC to what SQLite dropped, then normalise.

    `SqlAlchemyMatchRepository` carries the identical helper and the two match
    on purpose: `DateTime(timezone=True)` is honoured by PostgreSQL and dropped
    by SQLite, so a reader that trusted the column would raise on the fast suite
    and pass in production — which is the wrong direction for a discrepancy to
    point.
    """

    return instant(value if value.tzinfo else value.replace(tzinfo=timezone.utc))


def _wave(row: MatchCascadeWaveORM) -> PendingWave:
    return PendingWave(
        match_id=row.match_id,
        vacancy_id=row.vacancy_id,
        wave=Wave(row.wave),
        due_at=_as_instant(row.due_at),
    )


def offer_of(row: MatchOfferORM) -> Offer:
    """One stored row as the ladder's own value.

    Public because the offers region reads these rows and must not build a
    second reading of them (``Raketa02/Raketa#83``): a rung stored as an integer
    and mapped back in two places is two answers to *which rung was she on*.
    """

    return Offer(
        match_id=row.match_id,
        vacancy_id=row.vacancy_id,
        player_id=row.player_id,
        player_rung=Rung(row.rung),
        fit=row.fit,
        price=SeatShare(grosze(row.price_grosze)),
        kind=OfferKind(row.kind),
        offered_at=_as_instant(row.offered_at),
    )
