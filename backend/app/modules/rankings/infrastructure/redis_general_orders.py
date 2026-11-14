"""``GeneralOrders`` in the ephemeral store, and the wrapper that makes it
lossy (#770; ``docs/adr/0093``, ``docs/adr/0203`` §10).

**A kept order is a generation of three keys**, so a read is always of one
order whatever was kept after it:

- ``rankings:general:{SPORT}`` — the pointer: which generation is the sport's,
  when it was worked out, how many it lists, and the forget count its pass
  began at — **a pointer at an older count than the sport's is held by
  nobody** (``…:forgotten``, an ``INCR`` on every forget, never expiring);
- ``…:{generation}:order`` — a sorted set, every score ``0``, so its members
  sort **by their bytes**: each is a row's key written to sort exactly as
  General's order does (``_sortable``), then ``|`` and what else the row
  draws. A page is ``ZRANGE`` by index, and a cursor's position one
  ``ZLEXCOUNT`` — so a page read moves 50 rows and never the order;
- ``…:{generation}:places`` — a hash, player id to place.

**The pointer is written last**, swapped in one ``SET … GET`` in the same
pipeline as the generation it names, so nobody reads a generation half
written. The generation it replaces — or a forget's — is left
``_RETIRED_FOR`` to finish whatever read is on it, then expires; every key
expires on its own anyway (``_POINTER_FOR``, ``_GENERATION_FOR``), because
whether an order is fresh is judged by the read's clock, never by the store's.

**An empty order is a pointer alone**: Redis keeps no empty set, so a listing
of nobody reads nothing back.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Awaitable, Sequence
from datetime import datetime
from typing import Final, TypeVar
from uuid import UUID, uuid4

from redis.asyncio import Redis

from app.kernel import Instant, Sport, instant, invariant
from app.modules.rankings.domain.general_order import (
    MOST_HUNDREDTHS,
    MOST_MICROS,
    MOST_RESULTS,
    ORDER_KEPT_FOR,
    GeneralOrder,
    ListedRow,
    OrderKey,
    instant_of_micros,
    micros_of,
)
from app.modules.rankings.domain.ports import (
    GeneralOrderLost,
    GeneralOrders,
    HeldOrder,
)
from app.modules.rankings.domain.ranking import Chip, ChipKind, Outcome, marks_of

logger = logging.getLogger(__name__)

_PREFIX: Final = "rankings:general"
#: Every key expires on its own, well after the minute a read may read it.
_POINTER_FOR: Final = int(2 * ORDER_KEPT_FOR.total_seconds())
_GENERATION_FOR: Final = _POINTER_FOR + 60
#: How long a replaced or forgotten generation stays for the reads on it.
_RETIRED_FOR: Final = 10
#: Members and fields per command, so keeping 50,000 rows is a few hundred
#: commands of a few kilobytes, never one of megabytes.
_CHUNK: Final = 1000

#: The widths a key is written at, so the keys of two rows compare digit by
#: digit: a Level in hundredths, a count of results, microseconds since the
#: epoch, then the id's 32 hex digits — the domain's own bounds on a key.
_LEVEL_DIGITS: Final = len(str(MOST_HUNDREDTHS))
_RESULT_DIGITS: Final = len(str(MOST_RESULTS))
_MICRO_DIGITS: Final = len(str(MOST_MICROS))
#: Between a member's key and its row, and above every character a key holds,
#: so ``[key~`` is past every member at that key and before every one after it.
_SEPARATOR: Final = "|"
_PAST_THE_KEY: Final = "~"


def _sortable(key: OrderKey) -> str:
    """The key as a string that sorts, byte by byte, the way General's order
    does: the Level descending, the results descending, who reached the Level
    first, then the id. **Only a key that can be written**: a cursor is
    refused before it gets here (``OrderKey.can_be_written``)."""

    invariant(key.can_be_written(), f"a key the store can't sort: {key!r}")
    return (
        f"{MOST_HUNDREDTHS - key.hundredths:0{_LEVEL_DIGITS}d}"
        f"{MOST_RESULTS - key.results:0{_RESULT_DIGITS}d}"
        f"{micros_of(key.level_reached_at):0{_MICRO_DIGITS}d}{key.player_id.hex}"
    )


def _unsortable(text: str) -> tuple[int, int, Instant, UUID]:
    results_at = _LEVEL_DIGITS + _RESULT_DIGITS
    micros_at = results_at + _MICRO_DIGITS
    return (
        MOST_HUNDREDTHS - int(text[:_LEVEL_DIGITS]),
        MOST_RESULTS - int(text[_LEVEL_DIGITS:results_at]),
        instant_of_micros(int(text[results_at:micros_at])),
        UUID(hex=text[micros_at:]),
    )


def _member(row: ListedRow) -> str:
    chip = f"{row.chip.kind.value}{row.chip.places}"
    return _SEPARATOR.join(
        (_sortable(row.key), repr(row.sigma), marks_of(row.form), chip)
    )


def _listed_row(member: str, *, place: int, sport: Sport) -> ListedRow:
    # A generation kept before #791 carries a fifth field, *Show me in
    # General*: read past it until the generation expires on its own.
    key, sigma, form, chip, *_ = member.split(_SEPARATOR)
    hundredths, results, reached, player_id = _unsortable(key)
    kind = next(kind for kind in ChipKind if chip.startswith(kind.value))
    return ListedRow(
        place=place,
        player_id=player_id,
        sport=sport,
        hundredths=hundredths,
        sigma=float(sigma),
        results=results,
        level_reached_at=reached,
        form=Outcome.of_marks(form),
        chip=Chip(kind, int(chip[len(kind.value) :])),
    )


def _pointer(sport: Sport) -> str:
    return f"{_PREFIX}:{sport.value}"


def _forgotten(sport: Sport) -> str:
    return f"{_PREFIX}:{sport.value}:forgotten"


def _keys(sport: Sport, generation: str) -> tuple[str, str]:
    return (
        f"{_PREFIX}:{sport.value}:{generation}:order",
        f"{_PREFIX}:{sport.value}:{generation}:places",
    )


class RedisGeneralOrders:
    def __init__(self, client: Redis) -> None:
        self._client = client

    async def held(self, sport: Sport) -> HeldOrder | None:
        pipe = self._client.pipeline(transaction=False)
        pipe.get(_pointer(sport))
        pipe.get(_forgotten(sport))
        pointer, forgotten = await pipe.execute()
        if pointer is None:
            return None
        named = json.loads(pointer)
        if named["forgotten"] != int(forgotten or 0):
            return None
        return _RedisHeldOrder(
            self._client,
            sport=sport,
            generation=named["generation"],
            worked_out_at=instant(datetime.fromisoformat(named["worked_out_at"])),
            listed=int(named["listed"]),
        )

    async def forgotten(self, sport: Sport) -> int:
        return int(await self._client.get(_forgotten(sport)) or 0)

    async def keep(self, order: GeneralOrder, *, forgotten: int) -> None:
        generation = uuid4().hex
        ordered, places = _keys(order.sport, generation)
        members = [_member(row) for row in order.rows]
        pipe = self._client.pipeline(transaction=False)
        for start in range(0, len(members), _CHUNK):
            pipe.zadd(
                ordered, {member: 0 for member in members[start : start + _CHUNK]}
            )
            pipe.hset(
                places,
                mapping={
                    row.player_id.hex: row.place
                    for row in order.rows[start : start + _CHUNK]
                },
            )
        if members:
            pipe.expire(ordered, _GENERATION_FOR)
            pipe.expire(places, _GENERATION_FOR)
        pipe.set(
            _pointer(order.sport),
            json.dumps(
                {
                    "generation": generation,
                    "worked_out_at": order.worked_out_at.isoformat(),
                    "listed": len(order.rows),
                    "forgotten": forgotten,
                }
            ),
            ex=_POINTER_FOR,
            get=True,
        )
        replaced = (await pipe.execute())[-1]
        await self._retire(order.sport, replaced)

    async def forget(self, sport: Sport) -> None:
        pipe = self._client.pipeline(transaction=False)
        pipe.incr(_forgotten(sport))
        pipe.get(_pointer(sport))
        pipe.delete(_pointer(sport))
        await self._retire(sport, (await pipe.execute())[1])

    async def _retire(self, sport: Sport, pointer: str | None) -> None:
        if pointer is None:
            return
        pipe = self._client.pipeline(transaction=False)
        for key in _keys(sport, json.loads(pointer)["generation"]):
            pipe.expire(key, _RETIRED_FOR)
        await pipe.execute()


class _RedisHeldOrder:
    """One generation, read where it is kept. **A generation that is gone** —
    retired and expired under a read that took too long — **is lost**, said
    so, and the read works the order out again."""

    def __init__(
        self,
        client: Redis,
        *,
        sport: Sport,
        generation: str,
        worked_out_at: Instant,
        listed: int,
    ) -> None:
        self._client = client
        self._sport = sport
        self._worked_out_at = worked_out_at
        self._listed = listed
        self._ordered, self._places = _keys(sport, generation)

    @property
    def worked_out_at(self) -> Instant:
        return self._worked_out_at

    @property
    def listed(self) -> int:
        return self._listed

    async def rows(self, start: int, stop: int) -> tuple[ListedRow, ...]:
        start, stop = max(0, start), min(self._listed, stop)
        if start >= stop:
            return ()
        members: Sequence[str] = await self._client.zrange(
            self._ordered, start, stop - 1
        )
        if len(members) != stop - start:
            raise GeneralOrderLost(f"{self._ordered} is gone")
        return tuple(
            _listed_row(member, place=start + index + 1, sport=self._sport)
            for index, member in enumerate(members)
        )

    async def place_of(self, player_id: UUID) -> int | None:
        if not self._listed:
            return None
        pipe = self._client.pipeline(transaction=False)
        pipe.hget(self._places, player_id.hex)
        pipe.exists(self._places)
        place, held = await pipe.execute()
        if not held:
            raise GeneralOrderLost(f"{self._places} is gone")
        return None if place is None else int(place)

    async def ahead_of(self, key: OrderKey) -> int:
        return await self._count(f"({_sortable(key)}")

    async def up_to(self, key: OrderKey) -> int:
        return await self._count(f"[{_sortable(key)}{_PAST_THE_KEY}")

    async def _count(self, bound: str) -> int:
        if not self._listed:
            return 0
        pipe = self._client.pipeline(transaction=False)
        pipe.zlexcount(self._ordered, "-", bound)
        pipe.exists(self._ordered)
        counted, held = await pipe.execute()
        if not held:
            raise GeneralOrderLost(f"{self._ordered} is gone")
        return int(counted)


class FailSoftGeneralOrders:
    """``GeneralOrders`` that never fails a read: **a store that can't answer
    holds nothing and keeps nothing**, and an order it loses mid-read is
    ``GeneralOrderLost``, which the read answers by working it out again. It
    complains on the way into an outage and again after every recovery — a
    request's instance once at most, the delivery worker's (one a process)
    once an outage."""

    def __init__(self, inner: GeneralOrders) -> None:
        self._inner = inner
        self._degraded = False

    def _complain(self, doing: str, sport: Sport) -> None:
        if not self._degraded:
            self._degraded = True
            logger.warning(
                "the ephemeral store is unavailable, the general order is "
                "worked out on every read",
                extra={"doing": doing, "sport": sport.value},
                exc_info=True,
            )

    async def held(self, sport: Sport) -> HeldOrder | None:
        try:
            held = await self._inner.held(sport)
        except Exception:
            self._complain("held", sport)
            return None
        self._degraded = False
        return None if held is None else _FailSoftHeldOrder(held)

    async def forgotten(self, sport: Sport) -> int:
        try:
            forgotten = await self._inner.forgotten(sport)
        except Exception:
            self._complain("forgotten", sport)
            return 0
        self._degraded = False
        return forgotten

    async def keep(self, order: GeneralOrder, *, forgotten: int) -> None:
        try:
            await self._inner.keep(order, forgotten=forgotten)
        except Exception:
            self._complain("keep", order.sport)
            return
        self._degraded = False

    async def forget(self, sport: Sport) -> None:
        try:
            await self._inner.forget(sport)
        except Exception:
            self._complain("forget", sport)
            return
        self._degraded = False


_T = TypeVar("_T")


class _FailSoftHeldOrder:
    """A held order whose store failing under a read is the order lost."""

    def __init__(self, inner: HeldOrder) -> None:
        self._inner = inner

    async def _lost_if_failed(self, read: Awaitable[_T]) -> _T:
        try:
            return await read
        except GeneralOrderLost:
            raise
        except Exception as error:
            raise GeneralOrderLost("the ephemeral store is unavailable") from error

    @property
    def worked_out_at(self) -> Instant:
        return self._inner.worked_out_at

    @property
    def listed(self) -> int:
        return self._inner.listed

    async def rows(self, start: int, stop: int) -> tuple[ListedRow, ...]:
        return await self._lost_if_failed(self._inner.rows(start, stop))

    async def place_of(self, player_id: UUID) -> int | None:
        return await self._lost_if_failed(self._inner.place_of(player_id))

    async def ahead_of(self, key: OrderKey) -> int:
        return await self._lost_if_failed(self._inner.ahead_of(key))

    async def up_to(self, key: OrderKey) -> int:
        return await self._lost_if_failed(self._inner.up_to(key))
