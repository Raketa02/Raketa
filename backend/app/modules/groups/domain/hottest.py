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
"""

from __future__ import annotations

from collections.abc import Collection, Iterable, Sequence
from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum
from typing import Final, final
from uuid import UUID

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


class HeatTag(StrEnum):
    HOTTEST = "HOTTEST"
    GROWING = "GROWING"


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


def hottest_groups(activities: Iterable[GroupActivity]) -> tuple[HotGroup, ...]:
    """The row: up to six cards in the row's order, each tagged and with its
    bar. Groups under three players are left out; with none of three, the row
    is empty and Home hides it."""

    candidates = sorted(
        (one for one in activities if one.players >= AT_LEAST_PLAYERS),
        key=_hotter_first,
    )
    if not candidates:
        return ()
    top = candidates[0]
    hottest = top if top.games_this_week >= 1 else None
    growing = [one for one in candidates if one is not hottest and is_growing(one)]
    untagged = [one for one in candidates if one is not hottest and not is_growing(one)]
    tagged: list[tuple[GroupActivity, HeatTag | None]] = [
        *([(hottest, HeatTag.HOTTEST)] if hottest is not None else []),
        *((one, HeatTag.GROWING) for one in growing),
    ]
    row = [*tagged, *((one, None) for one in untagged)][:CARDS]
    full = (
        heat_of(hottest) if hottest is not None else max(heat_of(one) for one, _ in row)
    )
    return tuple(
        HotGroup(activity=one, heat=heat_of(one), tag=tag, share=heat_of(one) / full)
        for one, tag in row
    )


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


def _hotter_first(activity: GroupActivity) -> tuple[int, int, UUID]:
    return (-heat_of(activity), -activity.games_this_week, activity.group_id)
