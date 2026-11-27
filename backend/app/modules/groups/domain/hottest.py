"""Hottest groups: the groups with the most going on, whether the reader is in
them or not (#792; the Home rows mechanics §5, ``docs/adr/0204`` §3, §11).

**Worked out on every read and stored nowhere** — the backend's *derived, never
stored*: who is in a group and when they joined are the groups projections',
and its games this week the bookings', both read when Home asks. This module is
the rule over those numbers and nothing else, so it is pure and tested at that
seam.

- **Heat** = 2 × *games this week* + 3 × *new players this month* + *players*,
  counted up to 20 (Q9). The card shows the true count.
- **One ▲ HOTTEST**: the highest heat, and **only if that group had a game this
  week** (call 3) — a top-heat group with none leaves the row with no HOTTEST
  even when a lower one played (a call made while writing #790, so the HOTTEST
  card is always the fullest bar).
- **+ GROWING** on any other with **+4 or more** new players **and** new players
  at least **a quarter** of today's players (Q25): a big group's trickle of
  joiners is not growth.
- **The order**: HOTTEST, then GROWING by heat, then untagged by heat; **six
  cards**, untagged ones dropped first. **Ties in heat** go to more games this
  week, then to the group id (a call).
- **The bar** is each card's heat over the HOTTEST's — or, with no HOTTEST, over
  **the highest heat in the row** (call 15), so no bar is ever more than full.

**The order goes on past the six** (#813; ``docs/adr/0205`` §6, §7): Home's
*Groups heating up* page lists **every** group of three or more in this one
order, twenty to a page, so **the row is exactly the order's first six** —
the same tags, the same places. A page's cards are read after a **place** in
the order (``HeatPlace``), never after a count: heat is worked out on every
read, so a group whose heat moved between two pages can shift place — read
twice, or not at all — and that is accepted, as on the people See all screens.
On the whole order, a bar is over the HOTTEST's heat or, with none, the highest
heat **on it**; it differs from the row's only when six GROWING groups push a
hotter untagged one off the row. **Its total** is every group of three or more,
counted up to 100 — the phone draws *99+* past 99 — and costs nothing, since
the heat already counted every group's members.
"""

from __future__ import annotations

from collections.abc import Collection, Iterable, Sequence
from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum
from typing import Final, final
from uuid import UUID

from app.kernel import invariant

#: A group needs this many players to be in the row at all (§5.1).
AT_LEAST_PLAYERS: Final = 3
#: How many cards the row holds (§5.1).
CARDS: Final = 6
#: *Games this week*: booked games whose court time falls in this window, up to
#: now (§5.2). Rolling, to the minute.
GAMES_WINDOW: Final = timedelta(days=7)
#: *New players this month*: members who joined in this window and are still
#: in (§5.2). Rolling, to the minute.
NEW_WINDOW: Final = timedelta(days=30)
#: *Players* count up to this many in the heat (§5.2).
PLAYERS_COUNTED_UP_TO: Final = 20
#: GROWING needs at least this many new players (§5.3)…
GROWING_AT_LEAST: Final = 4
#: …and new players making up at least this share of today's players, as a
#: whole-number ratio so no float decides a tag: new × 4 ≥ players.
GROWING_SHARE_DENOMINATOR: Final = 4
#: Member faces a group sheet shows; the card draws the first four (§5.6).
FACES: Final = 6
#: Cards on a page of *Groups heating up* (``docs/adr/0205`` §7).
PAGE: Final = 20
#: Where the total stops: the phone draws *99+* past 99 (``docs/adr/0205`` §6).
COUNTED_UP_TO: Final = 100


class HeatTag(StrEnum):
    HOTTEST = "HOTTEST"
    GROWING = "GROWING"


#: The tags in the order's own order, untagged last — what a place's rank is.
TAG_ORDER: Final[tuple[HeatTag | None, ...]] = (HeatTag.HOTTEST, HeatTag.GROWING, None)


@final
@dataclass(frozen=True, slots=True)
class GroupActivity:
    """What a group's heat is made of, as the projections answer it now."""

    group_id: UUID
    games_this_week: int
    new_this_month: int
    #: Members today, every one of them — the card's true count.
    players: int


@final
@dataclass(frozen=True, slots=True)
class HotGroup:
    """One card of the row: its numbers, its heat, its tag (``None`` for an
    untagged card) and its bar, from nought to one."""

    activity: GroupActivity
    heat: int
    tag: HeatTag | None
    share: float


def heat_of(activity: GroupActivity) -> int:
    return (
        2 * activity.games_this_week
        + 3 * activity.new_this_month
        + min(activity.players, PLAYERS_COUNTED_UP_TO)
    )


def is_growing(activity: GroupActivity) -> bool:
    return (
        activity.new_this_month >= GROWING_AT_LEAST
        and activity.new_this_month * GROWING_SHARE_DENOMINATOR >= activity.players
    )


@final
@dataclass(frozen=True, slots=True)
class HeatPlace:
    """Where a card stands in the order — what a page's cursor names. A page
    reads the cards **behind** a place, wherever its group stands now."""

    tag: HeatTag | None
    heat: int
    games_this_week: int
    group_id: UUID


def hottest_groups(activities: Iterable[GroupActivity]) -> tuple[HotGroup, ...]:
    """The row: up to six cards in the row's order, each tagged and with its
    bar. Groups under three players are left out; with none of three, the row
    is empty and Home hides it."""

    return _with_bars(_tagged_in_order(activities)[:CARDS])


def heat_order(activities: Iterable[GroupActivity]) -> tuple[HotGroup, ...]:
    """**Every** group of three or more in the row's order, each tagged and
    with its bar over the whole order — *Groups heating up*'s list, whose first
    six are the row."""

    return _with_bars(_tagged_in_order(activities))


def total_of(activities: Iterable[GroupActivity]) -> int:
    """How many groups the order holds — every group of three or more —
    counted up to ``COUNTED_UP_TO``."""

    return min(
        sum(1 for one in activities if one.players >= AT_LEAST_PLAYERS),
        COUNTED_UP_TO,
    )


def place_of(hot: HotGroup) -> HeatPlace:
    return HeatPlace(
        tag=hot.tag,
        heat=hot.heat,
        games_this_week=hot.activity.games_this_week,
        group_id=hot.activity.group_id,
    )


def page_after(
    order: Sequence[HotGroup], after: HeatPlace | None, *, size: int = PAGE
) -> tuple[tuple[HotGroup, ...], HeatPlace | None]:
    """The ``size`` cards of ``order`` behind ``after`` — from the top for
    ``None`` — and the place the next page is read after, ``None`` when no card
    is behind this page."""

    invariant(size >= 1, f"a page holds at least one card, not {size}")
    behind = [
        hot for hot in order if after is None or _key(place_of(hot)) > _key(after)
    ]
    page = tuple(behind[:size])
    return page, (place_of(page[-1]) if len(behind) > size else None)


def faces_to_show(
    members: Sequence[UUID],
    *,
    friends: Collection[UUID],
    reader: UUID,
    at_most: int = FACES,
) -> tuple[UUID, ...]:
    """Whose faces a card and its sheet draw (call 5): **the reader's friends
    first, then the longest-standing members**, each in the order they joined
    — ``members`` is that order — and **never the reader's own face**, as
    nobody is in their own people rows (a call made while writing #790)."""

    others = [member for member in members if member != reader]
    first = [member for member in others if member in friends]
    rest = [member for member in others if member not in friends]
    return tuple([*first, *rest][:at_most])


def _tagged_in_order(
    activities: Iterable[GroupActivity],
) -> list[tuple[GroupActivity, HeatTag | None]]:
    """The one order: HOTTEST, then GROWING by heat, then untagged by heat."""

    candidates = sorted(
        (one for one in activities if one.players >= AT_LEAST_PLAYERS),
        key=_hotter_first,
    )
    if not candidates:
        return []
    top = candidates[0]
    hottest = top if top.games_this_week >= 1 else None
    growing = [one for one in candidates if one is not hottest and is_growing(one)]
    untagged = [one for one in candidates if one is not hottest and not is_growing(one)]
    return [
        *([(hottest, HeatTag.HOTTEST)] if hottest is not None else []),
        *((one, HeatTag.GROWING) for one in growing),
        *((one, None) for one in untagged),
    ]


def _with_bars(
    tagged: Sequence[tuple[GroupActivity, HeatTag | None]],
) -> tuple[HotGroup, ...]:
    """Each card's bar: over the HOTTEST's heat, which leads when there is one,
    and otherwise over the highest heat among ``tagged``."""

    if not tagged:
        return ()
    first, tag = tagged[0]
    full = (
        heat_of(first)
        if tag is HeatTag.HOTTEST
        else max(heat_of(one) for one, _ in tagged)
    )
    return tuple(
        HotGroup(activity=one, heat=heat_of(one), tag=tag, share=heat_of(one) / full)
        for one, tag in tagged
    )


def _key(place: HeatPlace) -> tuple[int, int, int, UUID]:
    """A place as the order sorts it — so a later place is a greater key."""

    return (
        TAG_ORDER.index(place.tag),
        -place.heat,
        -place.games_this_week,
        place.group_id,
    )


def _hotter_first(activity: GroupActivity) -> tuple[int, int, UUID]:
    return (-heat_of(activity), -activity.games_this_week, activity.group_id)
