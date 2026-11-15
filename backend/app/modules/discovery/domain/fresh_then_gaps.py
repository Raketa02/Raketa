"""**Keeping a row alive**: fresh good matches first, then the gaps at the
right (``docs/adr/0204`` §7; the home-rows mechanics §9.1, Q33).

One rule for *Same competitive level players* and *Same vibe players*, each
naming what a **good match** is in its own words — 70% even or more, two shared
tags or more — and handing its cards **best first**:

1. **Fresh good matches first**: a good match the reader hasn't sent a request
   to, isn't friends with, and who hasn't rested. Somebody who asked the reader
   counts as fresh (call 7 of #790).
2. **The places left are gaps**, in the same order: friends, people the reader
   asked, rested players and weaker matches, all one order.
3. **Worked out on every read**, so each new fresh match takes a gap's place
   and the weakest gap leaves the row.

Pure: who is connected and who has rested are handed in.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Final, Generic, TypeVar

from app.modules.discovery.domain.relation import Relation

#: Cards on Home's row.
ON_THE_ROW: Final = 10

T = TypeVar("T")


def is_fresh(*, good: bool, relation: Relation, rested: bool) -> bool:
    """A good match the reader is not connected with, who hasn't rested."""

    return good and not relation.connected and not rested


class FreshThenGaps(Generic[T]):
    """The row, filled from the cards **best first**, ``good`` saying which
    card is a good match in the row's own words — each row's ``RowOfTen`` is
    this with its line.

    **Full** once ten fresh are taken, or once a card that is no good match has
    come — after it no card can be fresh, the order being best first — with
    ten taken in all. Until then a later fresh match would still take a gap's
    place."""

    def __init__(self, *, good: Callable[[T], bool]) -> None:
        self._good = good
        self._fresh: list[T] = []
        self._gaps: list[T] = []
        self._no_more_fresh = False

    def may_be_fresh(self, one: T, *, relation: Relation) -> bool:
        """Whether the card is fresh unless it has rested — the only cards a
        row asks the rest count about (``rest``)."""

        return is_fresh(good=self._good(one), relation=relation, rested=False)

    def take(self, one: T, *, relation: Relation, rested: bool) -> None:
        good = self._good(one)
        if not good:
            self._no_more_fresh = True
        if is_fresh(good=good, relation=relation, rested=rested):
            self._fresh.append(one)
        else:
            self._gaps.append(one)

    @property
    def full(self) -> bool:
        return len(self._fresh) >= ON_THE_ROW or (
            self._no_more_fresh and len(self._fresh) + len(self._gaps) >= ON_THE_ROW
        )

    def row(self) -> tuple[T, ...]:
        fresh = self._fresh[:ON_THE_ROW]
        return (*fresh, *self._gaps[: ON_THE_ROW - len(fresh)])
