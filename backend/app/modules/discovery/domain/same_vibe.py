"""*Same vibe players* — whose social tags overlap the reader's
(``docs/adr/0204`` §6, §7; the home-rows mechanics §8, §9).

Pure: the tags are handed in, each player's in the vocabulary's order.

- **Who**: anyone sharing **at least one** tag with the reader. Every tag
  counts the same, and no tag is special — *Open to meet someone* is one tag
  like any other (Q15). **Skill plays no part**: no level is read.
- **The vibe %** is 1 − ½ⁿ for n shared tags, rounded to a whole percent —
  each shared tag closes half of what is left (Q24): 50, 75, 88, 94, 97, 98.
- **The order**: more shared first; ties to **fewer of their tags not shared**
  (counting the reader's unshared too orders the same, theirs being the same
  for everyone), then the player id.
- **The row of 10** is §9's rule (``fresh_then_gaps``), a good match being
  **two shared tags or more**.
- **Tags order this row and score nothing else** (``docs/adr/0204`` §6): no
  proposal, card, forecast or level reads one.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Final, final
from uuid import UUID

from app.kernel import invariant
from app.modules.discovery.domain import fresh_then_gaps
from app.modules.discovery.domain.fresh_then_gaps import FreshThenGaps
from app.modules.discovery.domain.relation import Relation

#: A good match: this many shared tags or more (Q33).
GOOD_MATCH: Final = 2
#: Cards on Home's row — §9's, which both rows keep.
ON_THE_ROW: Final = fresh_then_gaps.ON_THE_ROW
#: Cards in a See all page (a call made while writing PRD #789).
A_PAGE: Final = 20


def vibe_percent(in_common: int) -> int:
    """1 − ½ⁿ as a whole percent, a half rounded up: 87,5 reads 88."""

    invariant(in_common >= 1, f"a vibe % is for a shared tag or more: {in_common}")
    return math.floor(100 * (1 - 0.5**in_common) + 0.5)


@final
@dataclass(frozen=True, slots=True)
class VibeKey:
    """Where a card stands in *most in common first*. **A See all cursor is
    one**: a page is everybody strictly behind the last card of the page
    before, as the list stands now."""

    in_common: int
    not_shared: int
    player_id: UUID

    @property
    def order(self) -> tuple[int, int, int]:
        return (-self.in_common, self.not_shared, self.player_id.int)

    def is_behind(self, other: "VibeKey") -> bool:
        """Whether this key comes **after** ``other`` in the order."""

        return self.order > other.order


@final
@dataclass(frozen=True, slots=True)
class VibePlayer:
    """One person on the row: their face, and what the two have in common."""

    player_id: UUID
    nickname: str
    photo_id: UUID | None
    #: The tags both hold, in the vocabulary's order — the tile's green chips.
    shared_tags: tuple[str, ...]
    #: How many of their tags the reader doesn't hold.
    not_shared: int

    @property
    def in_common(self) -> int:
        return len(self.shared_tags)

    @property
    def percent(self) -> int:
        return vibe_percent(self.in_common)

    @property
    def key(self) -> VibeKey:
        return VibeKey(
            in_common=self.in_common,
            not_shared=self.not_shared,
            player_id=self.player_id,
        )


def vibe_player(
    player_id: UUID,
    nickname: str,
    photo_id: UUID | None,
    tags: Iterable[str],
    *,
    mine: frozenset[str],
) -> VibePlayer | None:
    """The card, from all of their tags and the reader's — ``None`` when the
    two share none."""

    theirs = tuple(tags)
    shared = tuple(tag for tag in theirs if tag in mine)
    if not shared:
        return None
    return VibePlayer(
        player_id=player_id,
        nickname=nickname,
        photo_id=photo_id,
        shared_tags=shared,
        not_shared=len(theirs) - len(shared),
    )


def is_good_match(in_common: int) -> bool:
    """Two shared tags or more."""

    return in_common >= GOOD_MATCH


def is_fresh(in_common: int, relation: Relation, *, rested: bool) -> bool:
    """A good match the reader is not connected with, who hasn't rested."""

    return fresh_then_gaps.is_fresh(
        good=is_good_match(in_common), relation=relation, rested=rested
    )


class RowOfTen(FreshThenGaps[VibePlayer]):
    """§9's row (``fresh_then_gaps``), a good match being two shared tags or
    more."""

    def __init__(self) -> None:
        super().__init__(good=lambda one: is_good_match(one.in_common))
