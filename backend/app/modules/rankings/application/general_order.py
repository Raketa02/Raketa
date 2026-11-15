"""A sport's General order, as a read finds it (#770; ``docs/adr/0203`` §10).

**The kept one while it is fresh, or worked out now and kept.** Fresh is the
minute after it was worked out, by the read's own clock (``kept_fresh``); a
ranking write in the sport forgets it before that (``MoveTheRanking``), so the
next read works it out again from one pass over the projection. **A pass
keeps its order at the forget count it began at**, so one that read the
projection before a write and finished after the write forgot is held by
nobody.

**A kept order that disagrees with the reader's own row is older than the
write that changed it**, and is worked out again rather than believed: one
missing a reader the projection lists now, one placing a reader the projection
holds no row of, and one whose row of the reader counts fewer results than the
reader has — the write's forget runs inside its delivery's transaction, so a
read in between can keep what it read. Being listed is only ever made true by
a write, never by time; the one disagreement kept is a reader it still places
whose 90 days ran out since, who drops off within the minute.

**Lossy, all the way down**: a store that is down holds nothing and keeps
nothing, and an order lost half way through a read is worked out again — the
projection can always make one — and every read after the loss is of the new
one, the reader's row included.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Awaitable, Callable, Sequence
from dataclasses import dataclass
from typing import TypeVar, final
from uuid import UUID

from app.kernel import Instant, Sport
from app.modules.rankings.domain.general_order import (
    GeneralOrder,
    ListedRow,
    OrderInHand,
    OrderKey,
    kept_fresh,
    work_out,
)
from app.modules.rankings.domain.ports import (
    GeneralOrderLost,
    GeneralOrders,
    HeldOrder,
    RankingRows,
)
from app.modules.rankings.domain.ranking import (
    GENERAL_ENTRY,
    RankingRow,
    chips_since,
    listed_since,
)

_T = TypeVar("_T")


@final
@dataclass(frozen=True, slots=True)
class OrderRead:
    """The order a read reads, the reader's row of it, and the reader's own
    row in the sport, read live."""

    order: HeldOrder
    mine: ListedRow | None
    own: RankingRow | None


@final
class TheGeneralOrder:
    def __init__(self, *, rows: RankingRows, orders: GeneralOrders) -> None:
        self._rows = rows
        self._orders = orders

    async def read(self, sport: Sport, *, now: Instant, reader: UUID) -> OrderRead:
        """The sport's order for a read at ``now``, and ``reader``'s row of
        it."""

        return await self._read(
            sport, now=now, reader=reader, owned=await self._rows.of_player(reader)
        )

    async def read_each(
        self, sports: Sequence[Sport], *, now: Instant, reader: UUID
    ) -> AsyncGenerator[tuple[Sport, OrderRead], None]:
        """Each of ``sports``' orders in turn, as :meth:`read` reads one —
        **the reader's own rows asked once** for all of them, and a sport's
        order read only when the caller asks for the next (Top 10's
        fall-through, #797)."""

        owned = await self._rows.of_player(reader)
        for sport in sports:
            yield sport, await self._read(sport, now=now, reader=reader, owned=owned)

    async def _read(
        self,
        sport: Sport,
        *,
        now: Instant,
        reader: UUID,
        owned: Sequence[RankingRow],
    ) -> OrderRead:
        own = next((row for row in owned if row.sport is sport), None)
        held = await self._orders.held(sport)
        if held is not None and kept_fresh(held.worked_out_at, now):
            order = _Reading(held, again=lambda: self.work_out_and_keep(sport, now=now))
            mine = await _row_of(order, reader)
            if _agrees(mine, own, now=now):
                return OrderRead(order=order, mine=mine, own=own)
        worked_out = OrderInHand(await self.work_out_and_keep(sport, now=now))
        return OrderRead(
            order=worked_out, mine=await _row_of(worked_out, reader), own=own
        )

    async def work_out_and_keep(self, sport: Sport, *, now: Instant) -> GeneralOrder:
        """The order worked out now, from one pass, and kept at the forget
        count the pass began at."""

        forgotten = await self._orders.forgotten(sport)
        order = work_out(
            sport,
            await self._rows.listed(
                sport,
                at_least=GENERAL_ENTRY,
                since=listed_since(now),
                then=chips_since(now),
            ),
            now=now,
        )
        await self._orders.keep(order, forgotten=forgotten)
        return order


async def _row_of(order: HeldOrder, reader: UUID) -> ListedRow | None:
    """The reader's row of the order, or ``None`` where it doesn't list them —
    the place and the row read off one order, the second read checking the
    first."""

    place = await order.place_of(reader)
    if place is None:
        return None
    found = await order.rows(place - 1, place)
    if found and found[0].player_id == reader:
        return found[0]
    # Lost between the two reads: ask the order now read again.
    place = await order.place_of(reader)
    found = () if place is None else await order.rows(place - 1, place)
    return found[0] if found and found[0].player_id == reader else None


def _agrees(mine: ListedRow | None, own: RankingRow | None, *, now: Instant) -> bool:
    """Whether a kept order may be believed about its reader (the module's
    second paragraph)."""

    if mine is None:
        return own is None or not own.listed_on_general(now)
    return own is not None and own.results <= mine.results


@final
class _Reading:
    """A kept order, read until it is lost — then the same reads of one worked
    out again, so a store that goes away mid-read costs the read a pass and
    never its answer."""

    def __init__(
        self, held: HeldOrder, *, again: Callable[[], Awaitable[GeneralOrder]]
    ) -> None:
        self._held = held
        self._again = again

    async def _or_again(self, read: Callable[[HeldOrder], Awaitable[_T]]) -> _T:
        try:
            return await read(self._held)
        except GeneralOrderLost:
            self._held = OrderInHand(await self._again())
            return await read(self._held)

    @property
    def worked_out_at(self) -> Instant:
        return self._held.worked_out_at

    @property
    def listed(self) -> int:
        return self._held.listed

    async def rows(self, start: int, stop: int) -> tuple[ListedRow, ...]:
        return await self._or_again(lambda held: held.rows(start, stop))

    async def place_of(self, player_id: UUID) -> int | None:
        return await self._or_again(lambda held: held.place_of(player_id))

    async def ahead_of(self, key: OrderKey) -> int:
        return await self._or_again(lambda held: held.ahead_of(key))

    async def up_to(self, key: OrderKey) -> int:
        return await self._or_again(lambda held: held.up_to(key))
