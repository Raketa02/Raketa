"""*New in Rakieta* — the players who joined in the last 30 days, newest first
(``docs/adr/0204`` §5; the home-rows mechanics §7).

Pure: every rule here takes ``now`` and the facts as inputs.

- **Who**: joined **strictly** inside the last 30 days — new while ``now −
  joined < 30 days`` — rolling, unrated included. Nobody older fills a quiet
  month.
- **The row**: **the 10 newest**, then ordered — the unconnected first (someone
  who asked the reader among them), then those the reader sent a request to,
  then friends — newest first within each (§7.2). An 11th sign-up pushes the
  oldest card off; they stay in See all until their 30 days end.
- **See all**: every joiner, newest first, friends where they fall, in pages
  of 20, a page named by the key of the card before it.
- **Newest first** is *joined* descending, then the player id, so two players
  who joined in one instant always stand in one order.
- **Days since joining are Warsaw days** (call 8 of #790): *Joined today* on
  the day of the commit, *yesterday* on the next, whatever the hours between.
  The backend counts; the phone words it (the words §31.7).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import timedelta
from typing import Final, final
from uuid import UUID

from app.kernel import Instant, Zone, invariant
from app.modules.discovery.domain.relation import Relation

#: How long a player is new for.
NEW_FOR: Final = timedelta(days=30)
#: Cards on Home's row.
ON_THE_ROW: Final = 10
#: Cards in a See all page (a call made while writing PRD #789).
A_PAGE: Final = 20
#: Where a day is counted — every day in the app is a Warsaw day.
DAYS_IN: Final[Zone] = Zone("Europe/Warsaw")


def new_since(now: Instant) -> Instant:
    """The instant a joiner must have joined **after** to be new now."""

    return now - NEW_FOR


def is_new(joined_at: Instant, now: Instant) -> bool:
    return now - joined_at < NEW_FOR


def days_since(joined_at: Instant, now: Instant) -> int:
    """Warsaw days from the day they joined to today: 0 is *Joined today*."""

    return (now.astimezone(DAYS_IN).date() - joined_at.astimezone(DAYS_IN).date()).days


@final
@dataclass(frozen=True, slots=True, order=False)
class JoinerKey:
    """Where a joiner stands in *newest first*: *joined*, then the id. **A
    page cursor is one**, so a page is everybody strictly behind the last card
    of the page before, as the list stands now."""

    joined_at: Instant
    player_id: UUID

    def is_behind(self, other: "JoinerKey") -> bool:
        """Whether this key comes **after** ``other`` in newest-first order."""

        if self.joined_at != other.joined_at:
            return self.joined_at < other.joined_at
        return self.player_id.int > other.player_id.int


@final
@dataclass(frozen=True, slots=True)
class Joiner:
    """A player inside their 30 days, as the directory lists them."""

    player_id: UUID
    nickname: str
    photo_id: UUID | None
    joined_at: Instant

    @property
    def key(self) -> JoinerKey:
        return JoinerKey(joined_at=self.joined_at, player_id=self.player_id)


def newest_first(joiners: Iterable[Joiner]) -> tuple[Joiner, ...]:
    by_id = sorted(joiners, key=lambda one: one.player_id.int)
    return tuple(sorted(by_id, key=lambda one: one.joined_at, reverse=True))


#: The row's three groups, in the row's order (§7.2).
_UNCONNECTED: Final = 0
_SENT: Final = 1
_FRIENDS: Final = 2

_STANDING: Final[Mapping[Relation, int]] = {
    Relation.NONE: _UNCONNECTED,
    Relation.ASKED_YOU: _UNCONNECTED,
    Relation.SENT: _SENT,
    Relation.FRIEND: _FRIENDS,
}


def on_the_row(
    newest: Sequence[Joiner], relations: Mapping[UUID, Relation]
) -> tuple[Joiner, ...]:
    """The 10 newest, unconnected first, then sent, then friends — newest first
    within each. ``newest`` is the 10, newest first; a person nobody answered
    about reads unconnected."""

    invariant(len(newest) <= ON_THE_ROW, "the row is the 10 newest")
    ordered = newest_first(newest)
    return tuple(
        sorted(
            ordered,
            key=lambda one: _STANDING[relations.get(one.player_id, Relation.NONE)],
        )
    )


@final
@dataclass(frozen=True, slots=True)
class Page:
    joiners: tuple[Joiner, ...]
    #: The last card's key, while anybody stands behind it; ``None`` at the end.
    next: JoinerKey | None


def page_after(
    newest: Sequence[Joiner], after: JoinerKey | None, *, size: int = A_PAGE
) -> Page:
    """The ``size`` joiners strictly behind ``after`` — the first page with
    none. ``newest`` is newest first."""

    behind = [one for one in newest if after is None or one.key.is_behind(after)]
    page = tuple(behind[:size])
    return Page(
        joiners=page,
        next=page[-1].key if len(behind) > size else None,
    )
