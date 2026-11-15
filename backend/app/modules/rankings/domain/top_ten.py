"""Top 10 on Home: the first ten of General in one sport (#797;
``docs/adr/0204`` §8; the home-rows mechanics §10).

**The true top of the Rankings page**, everybody counted, so it is a slice of
the sport's General order and nothing of its own: places 1 to 10, or fewer
while fewer are listed. The number 3 plays no part anywhere (Q37).

**Which sport**: one the reader asks for exactly — the pill — or one they
prefer — the trophy's, on opening — which **falls through to the next sport in
the app's order where anybody is listed, going round** to the first after the
last (the mechanics' call 10). **A card draws the week's move alone**: *▲ n* or
*▼ n*, and nothing for no change or *New* (§10.1).
"""

from __future__ import annotations

from typing import Final

from app.kernel import Sport
from app.modules.rankings.domain.general_order import Slice
from app.modules.rankings.domain.ranking import Chip, ChipKind

#: How many places the row holds.
TOP_TEN: Final = 10


def the_top_ten(listed: int) -> Slice:
    """Where the row sits in the order: its first ten rows, or every row while
    fewer are listed."""

    return Slice(start=0, stop=min(listed, TOP_TEN))


def sports_from(preferred: Sport) -> tuple[Sport, ...]:
    """Every sport, ``preferred`` first, then the rest in the app's order,
    going round — the order a preference falls through in."""

    order = list(Sport)
    at = order.index(preferred)
    return (*order[at:], *order[:at])


def drawn_chip(chip: Chip) -> Chip | None:
    """The chip a Top 10 card draws: a move up or down, and ``None`` for no
    change and for *New*."""

    return chip if chip.kind in (ChipKind.UP, ChipKind.DOWN) else None
