"""``PushLines`` and ``PushDevices`` over the two tables the channel owns.

One file for both, because they are one mechanism read from two ends — *what
does her lock screen say* and *where is her lock screen* — and a reader
following a send should not have to open two adapters to see all of it. They are
two **ports** because their writers differ: a dispatch owes a line and a phone
registers itself, and a use case holding an object that can do both is one
autocomplete away from doing the wrong one.

**Neither commits.** Owing a line belongs to the transaction that wrote the
offers — an offer with no send owed behind it is a seat nobody hears about — and
a send belongs to its own, which ``SendTheLine`` closes.

**Statements rather than ``session.add``**, on the rule ADR-0091's seed run
found the hard way: this app's sessions are ``autoflush=False``, so a pending
object is invisible to the very next ``SELECT`` in its own transaction — and a
dispatch owes a line and may then read it back in the same transaction.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence
from uuid import UUID

from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.kernel import Instant, instant

from app.modules.now.domain.push import (
    LiveLine,
    Platform,
    PushDevice,
    TimeSensitiveSetting,
)
from app.modules.now.infrastructure.sqlalchemy_push_models import (
    PushDeviceORM,
    PushLineORM,
)


class SqlAlchemyPushLines:
    """One row per player: what her lock screen says, and what it owes."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def owe(self, player_ids: Sequence[UUID], *, at: Instant) -> None:
        """Say that these players may have something new to be told.

        Read-then-write rather than an ``ON CONFLICT`` clause, which is the
        shape ``SqlAlchemyOffers.record`` and ``SqlAlchemyCascadeWaves.open``
        already take: the clause would be spelled once per dialect, and the fast
        suite would then exercise a different statement from PostgreSQL's.

        **The moment moves to the latest dispatch's**, and that is what
        ``replaced`` and ``settled`` compare against: a send already in flight
        clears the debt it read and never a debt incurred behind its back. It
        cannot push anybody's send into the future, because every moment written
        here is a dispatch's own instant and is therefore already past.
        """

        if not player_ids:
            return
        wanted = sorted(set(player_ids), key=str)
        known = await self._known(wanted)
        fresh = [player_id for player_id in wanted if player_id not in known]
        if fresh:
            await self._session.execute(
                insert(PushLineORM).values(
                    [
                        {
                            "player_id": player_id,
                            "named_match_id": None,
                            "named_at": None,
                            "due_at": at,
                        }
                        for player_id in fresh
                    ]
                )
            )
        if known:
            await self._session.execute(
                update(PushLineORM)
                .where(PushLineORM.player_id.in_(sorted(known, key=str)))
                .values(due_at=at)
            )

    async def due(self, *, now: Instant, limit: int) -> tuple[LiveLine, ...]:
        """Owed sends whose moment has come, oldest first.

        Ordered by ``due_at`` and broken by the player, which is total: two
        dispatches in one millisecond would otherwise be taken in whatever order
        the plan chose, and a batch that is not deterministic is one whose
        truncation at ``limit`` is not either.
        """

        rows = await self._session.execute(
            select(PushLineORM)
            .where(
                PushLineORM.due_at.is_not(None),
                PushLineORM.due_at <= now,
            )
            .order_by(PushLineORM.due_at, PushLineORM.player_id)
            .limit(limit)
        )
        return tuple(_line(row) for row in rows.scalars().all())

    async def replaced(
        self, line: LiveLine, *, named_match_id: UUID, at: Instant
    ) -> None:
        """A message went out: her line names this match, and owes nothing.

        **Two statements, because the two halves have different conditions.**
        The naming columns move whatever the debt has done — the message really
        did reach her phone, and forgetting that would send it to her again — and
        the debt is cleared only if it is still the one this send read, which is
        exactly what ``settled`` does.
        """

        await self._session.execute(
            update(PushLineORM)
            .where(PushLineORM.player_id == line.player_id)
            .values(named_match_id=named_match_id, named_at=at)
        )
        await self.settled(line)

    async def settled(self, line: LiveLine) -> None:
        """Nothing was sent. **The two naming columns are not touched.**

        Clearing them would be this module retracting a lock screen it cannot
        reach: her phone still shows the line, and forgetting that here would
        make the next dispatch send it to her again.

        The compare-and-set is in the ``WHERE``: a debt owed while this send was
        deciding is a debt the next tick still owes.
        """

        await self._session.execute(
            update(PushLineORM)
            .where(
                PushLineORM.player_id == line.player_id,
                PushLineORM.due_at == line.due_at,
            )
            .values(due_at=None)
        )

    async def _known(self, player_ids: Sequence[UUID]) -> frozenset[UUID]:
        rows = await self._session.execute(
            select(PushLineORM.player_id).where(
                PushLineORM.player_id.in_(player_ids)
            )
        )
        return frozenset(rows.scalars().all())


class SqlAlchemyPushDevices:
    """Where a player's phones are, as they last reported themselves."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def register(self, device: PushDevice) -> None:
        """Record this phone, and take the token off everybody else.

        **The delete is the point of the method and not housekeeping.** A token
        addresses a phone; a phone signed into a second account still answers to
        the same token, and a row left behind would put one player's seats on
        another player's lock screen. It is scoped to *this token* and to *other
        players*, so a re-registration by the same player replaces her own row
        rather than deleting it and racing to put it back.
        """

        await self._session.execute(
            delete(PushDeviceORM).where(
                PushDeviceORM.token == device.token,
                PushDeviceORM.player_id != device.player_id,
            )
        )
        values = {
            "platform": device.platform.value,
            "time_sensitive": device.time_sensitive.value,
            "registered_at": device.registered_at,
        }
        held = await self._session.execute(
            select(PushDeviceORM.token).where(
                PushDeviceORM.player_id == device.player_id,
                PushDeviceORM.token == device.token,
            )
        )
        if held.scalars().first() is None:
            await self._session.execute(
                insert(PushDeviceORM).values(
                    player_id=device.player_id, token=device.token, **values
                )
            )
            return
        await self._session.execute(
            update(PushDeviceORM)
            .where(
                PushDeviceORM.player_id == device.player_id,
                PushDeviceORM.token == device.token,
            )
            .values(**values)
        )

    async def for_player(self, player_id: UUID) -> tuple[PushDevice, ...]:
        """Her phones, oldest registration first, off the key's left edge.

        Broken by the token, which is total: two phones registered in the same
        millisecond would otherwise be composed for in the plan's order, and the
        message they get is identical, so the only thing an unstable order costs
        is a test that cannot pin it.
        """

        rows = await self._session.execute(
            select(PushDeviceORM)
            .where(PushDeviceORM.player_id == player_id)
            .order_by(PushDeviceORM.registered_at, PushDeviceORM.token)
        )
        return tuple(_device(row) for row in rows.scalars().all())


def _as_instant(value: datetime) -> Instant:
    """Re-attach UTC to what SQLite dropped, then normalise.

    ``cascade_stores`` carries the identical helper and the two match on
    purpose: ``DateTime(timezone=True)`` is honoured by PostgreSQL and dropped
    by SQLite, so a reader that trusted the column would raise on the fast suite
    and pass in production.
    """

    return instant(value if value.tzinfo else value.replace(tzinfo=timezone.utc))


def _line(row: PushLineORM) -> LiveLine:
    return LiveLine(
        player_id=row.player_id,
        named_match_id=row.named_match_id,
        due_at=None if row.due_at is None else _as_instant(row.due_at),
    )


def _device(row: PushDeviceORM) -> PushDevice:
    return PushDevice(
        player_id=row.player_id,
        token=row.token,
        platform=Platform(row.platform),
        time_sensitive=TimeSensitiveSetting(row.time_sensitive),
        registered_at=_as_instant(row.registered_at),
    )
