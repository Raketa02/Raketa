"""A sport's General order, worked out once and kept for a minute (#770;
``docs/adr/0203`` §10; the mechanics §15–§16).

**The order, every place and every chip are worked out together**, from one
database pass — every listed row with its level-history point 7 days back —
and kept per sport, so a page is a slice of one order rather than a fold of
every listed player per reader. ``work_out`` is the whole of it: the rows in
the order the pass returns them, places counted over every one, and
``chips_of`` over the set.

**Kept for at most a minute** (``ORDER_KEPT_FOR``), judged against the read's
own clock: who is listed and every chip are decided against the instant the
order was worked out, so a player crossing the 90 days drops off within the
minute. **A ranking write in the sport forgets it** — the next read works it
out again — so a result settling is reflected on that read.

**It keeps the whole order**, every listed row and none of the reader's
filtering, so whatever a reader may not see is left out of the slice and
leaves its gap (the mechanics §5).

**A page is named by a row's place in the order, never by an offset**: a
cursor is the key a row stood at (``OrderKey``, the four keys of
``ix_ranking_rows_order``), and *after* it is every row strictly behind that
key in the order as it stands now. A row that moved between two reads is not
shown twice for the rows it passed.
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Final, final
from uuid import UUID

from app.kernel import Instant, Sport, instant, invariant
from app.modules.rankings.domain.ranking import (
    PAGE_SIZE,
    Chip,
    LevelPoint,
    Outcome,
    RankingRow,
    RankingView,
    chips_of,
    order_of,
)

#: How long a worked-out order is read before it is worked out again (Q130's
#: *at most a minute*; the mechanics §15).
ORDER_KEPT_FOR: Final = timedelta(minutes=1)

#: **What a key can say**: a Level in hundredths and a count of results never
#: negative and never wider than a kept order writes them, and a Level reached
#: since the epoch. A cursor outside them is no row's key — never this
#: server's — and is refused before anything reads it.
MOST_HUNDREDTHS: Final = 99_999
MOST_RESULTS: Final = 999_999_999
_EPOCH: Final = instant(datetime(1970, 1, 1, tzinfo=timezone.utc))
#: Microseconds since the epoch fit seventeen digits until the year 5138.
MOST_MICROS: Final = 10**17 - 1


def micros_of(at: Instant) -> int:
    """An instant as whole microseconds since the epoch — how a key writes it."""

    delta = at - _EPOCH
    return (delta.days * 86_400 + delta.seconds) * 1_000_000 + delta.microseconds


def instant_of_micros(micros: int) -> Instant:
    """The instant :func:`micros_of` wrote."""

    return instant(_EPOCH + timedelta(microseconds=micros))


@final
@dataclass(frozen=True, slots=True)
class OrderKey:
    """Where a row stands in General's order: the Level, then more results,
    then who reached that Level first, then the player id (Q20). **A page's
    cursor**: unique, because the player id is in it."""

    hundredths: int
    results: int
    level_reached_at: Instant
    player_id: UUID

    def sort_key(self) -> tuple[int, int, Instant, UUID]:
        """The key as a tuple that sorts best first — ``ranking.order_of``'s."""

        return order_of(self)

    def can_be_written(self) -> bool:
        """Whether a kept order could hold a row at this key (``MOST_…``)."""

        return (
            0 <= self.hundredths <= MOST_HUNDREDTHS
            and 0 <= self.results <= MOST_RESULTS
            and 0 <= micros_of(self.level_reached_at) <= MOST_MICROS
        )


@final
@dataclass(frozen=True, slots=True)
class ListedAndThen:
    """A listed row, and the player's level-history point at the chip's
    instant — their latest at or before it, else their first; ``None`` for a
    row with no point at all."""

    row: RankingRow
    then: LevelPoint | None


@final
@dataclass(frozen=True, slots=True)
class ListedRow:
    """One row of the order: its true place, what a row on the page draws —
    the form, the chip and the Level — and what the gap line measures with."""

    place: int
    player_id: UUID
    sport: Sport
    hundredths: int
    #: Prices one win on the gap line.
    sigma: float
    results: int
    level_reached_at: Instant
    #: The last results, oldest first.
    form: tuple[Outcome, ...]
    chip: Chip

    @property
    def key(self) -> OrderKey:
        return OrderKey(
            hundredths=self.hundredths,
            results=self.results,
            level_reached_at=self.level_reached_at,
            player_id=self.player_id,
        )


@final
@dataclass(frozen=True, slots=True)
class GeneralOrder:
    """Every listed row of a sport, best first, as worked out at one instant —
    General's, kept for a minute, or a reader's Friends table, worked out on
    each read and kept nowhere (#771). One shape, so the card, the podium, the
    rows and the gap line read either alike."""

    sport: Sport
    worked_out_at: Instant
    rows: tuple[ListedRow, ...]

    def __post_init__(self) -> None:
        invariant(
            all(row.place == place for place, row in enumerate(self.rows, start=1)),
            f"an order whose places are not 1 to {len(self.rows)}",
        )
        keys = [order_of(row) for row in self.rows]
        invariant(
            all(keys[i] < keys[i + 1] for i in range(len(keys) - 1)),
            "an order that is not General's order",
        )


@final
@dataclass(frozen=True)
class OrderInHand:
    """An order read where it is held in memory — the one a read just worked
    out, and every one the in-memory store keeps. ``ports.HeldOrder``."""

    order: GeneralOrder
    _keys: tuple[tuple[int, int, Instant, UUID], ...] = field(init=False)
    _places: dict[UUID, int] = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "_keys", tuple(order_of(row) for row in self.order.rows)
        )
        object.__setattr__(
            self, "_places", {row.player_id: row.place for row in self.order.rows}
        )

    @property
    def worked_out_at(self) -> Instant:
        return self.order.worked_out_at

    @property
    def listed(self) -> int:
        return len(self.order.rows)

    async def rows(self, start: int, stop: int) -> tuple[ListedRow, ...]:
        return self.order.rows[max(0, start) : max(0, stop)]

    async def place_of(self, player_id: UUID) -> int | None:
        return self._places.get(player_id)

    async def ahead_of(self, key: OrderKey) -> int:
        return bisect_left(self._keys, key.sort_key())

    async def up_to(self, key: OrderKey) -> int:
        return bisect_right(self._keys, key.sort_key())


def work_out(
    sport: Sport,
    passed: Sequence[ListedAndThen],
    *,
    now: Instant,
    view: RankingView = RankingView.GENERAL,
) -> GeneralOrder:
    """The order, its places and its chips, from one pass — in the order the
    pass read the rows, which is the ranking's — **in ``view``**, whose list
    decides what *New* means."""

    listed = [one.row for one in passed]
    chips = chips_of(
        listed,
        {one.row.player_id: one.then for one in passed if one.then is not None},
        now=now,
        view=view,
    )
    return GeneralOrder(
        sport=sport,
        worked_out_at=now,
        rows=tuple(
            ListedRow(
                place=place,
                player_id=row.player_id,
                sport=sport,
                hundredths=row.hundredths,
                sigma=row.sigma,
                results=row.results,
                level_reached_at=row.level_reached_at,
                form=row.form,
                chip=chips[row.player_id],
            )
            for place, row in enumerate(listed, start=1)
        ),
    )


def kept_fresh(worked_out_at: Instant, now: Instant) -> bool:
    """Whether a read at ``now`` may read an order worked out at
    ``worked_out_at``: in the minute after it, and never before it."""

    return worked_out_at <= now < worked_out_at + ORDER_KEPT_FOR


# --------------------------------------------------------------------------- #
# Pages — slices of the order (the screens §5.3)
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class Slice:
    """Where a page sits in the order: rows ``start`` to ``stop``, by index."""

    start: int
    stop: int

    def __post_init__(self) -> None:
        invariant(
            0 <= self.start <= self.stop and self.stop - self.start <= PAGE_SIZE,
            f"a page that is not a slice of at most {PAGE_SIZE}: {self!r}",
        )


def first_page(listed: int) -> Slice:
    return Slice(start=0, stop=min(listed, PAGE_SIZE))


def page_after(up_to_the_key: int, listed: int) -> Slice:
    """The page behind a cursor: ``up_to_the_key`` rows are at or ahead of
    it."""

    return Slice(start=up_to_the_key, stop=min(listed, up_to_the_key + PAGE_SIZE))


def page_before(ahead_of_the_key: int) -> Slice:
    """The page ahead of a cursor, ending right above it: ``ahead_of_the_key``
    rows are strictly ahead of it."""

    return Slice(start=max(0, ahead_of_the_key - PAGE_SIZE), stop=ahead_of_the_key)


def page_around(place: int, listed: int) -> Slice:
    """The page with the reader in the middle — 25 rows above, 24 below — held
    to the list's ends, so at the top it is the first page and at the bottom
    the last 50."""

    invariant(1 <= place <= listed, f"place {place} of {listed}")
    start = min(max(0, place - 1 - PAGE_SIZE // 2), max(0, listed - PAGE_SIZE))
    return Slice(start=start, stop=min(listed, start + PAGE_SIZE))
