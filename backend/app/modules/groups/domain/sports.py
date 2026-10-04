"""What a group can play: its sport dots, and each sport's *N of M*.

**Both are computed when read and never stored** (``docs/adr/0183`` §6). A
rating earned or a member leaving moves them on the next read, with nothing to
keep in step. Walked in the ``Sport`` registry's own order, so a list of dots is
the same list whoever reads it and a fifth sport is read without anybody widening
a list (``docs/adr/0105``).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final, final
from uuid import UUID

from app.kernel import SPORT_SPECS, Sport

#: A player group has a dot for a sport once **this many** of its members hold a
#: Skill rating in it — two, because that is the fewest who can play anything
#: (``docs/adr/0183`` §6).
MEMBERS_FOR_A_DOT: Final = 2


@final
@dataclass(frozen=True, slots=True)
class SportRoster:
    """One sport in one group: how many members are rated in it, and the first
    of them to join — **as many as the sport seats**, which is what the Games
    tab's *N of M* draws its faces from (``docs/adr/0183`` §13)."""

    sport: Sport
    rated_count: int
    first_rated: tuple[UUID, ...]


def rosters(
    members: Sequence[UUID], rated: Mapping[Sport, frozenset[UUID]]
) -> tuple[SportRoster, ...]:
    """Every sport, in the registry's order — the ones nobody here plays too,
    because a reader rated in a sport the group has no dot for still opens its
    Games tab on it and sees *just you so far*.

    ``members`` is in joining order, so *the first to join* is the first of them
    who are rated.
    """

    rosters: list[SportRoster] = []
    for sport in Sport:
        who = rated.get(sport, frozenset())
        in_order = tuple(member for member in members if member in who)
        rosters.append(
            SportRoster(
                sport=sport,
                rated_count=len(in_order),
                first_rated=in_order[: SPORT_SPECS[sport].players],
            )
        )
    return tuple(rosters)


def sport_dots(
    members: Sequence[UUID], rated: Mapping[Sport, frozenset[UUID]]
) -> tuple[Sport, ...]:
    """The sports at least ``MEMBERS_FOR_A_DOT`` of these members are rated in —
    a sport's roster, counted, so a dot and an *N of M* cannot disagree."""

    return tuple(
        roster.sport
        for roster in rosters(members, rated)
        if roster.rated_count >= MEMBERS_FOR_A_DOT
    )
