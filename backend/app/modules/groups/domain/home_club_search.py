"""Home-club search's order: nearest first, then by name, twenty to a page.

``docs/adr/0183`` §9 and ``docs/adr/0182`` §6. **The distance is measured from
the reader's Location area to the club's point and printed by
``shown_kilometres``** — one decimal, never below a tenth, the print the radar
and the shortlist already use — so a club is never *0,0 km* away and a card and
a list cannot print two readings of one distance.

**The order is by the printed distance, then by the name.** Two clubs a reader
sees at *1,2 km* are in A–Z order between themselves, rather than in an order
set by metres the screen does not show. A reader with no Location area gets
A–Z and no distance at all.

**The name is compared folded**, by the fold search matches with, so *Łobzów*
sorts among the *l*s where a reader looks for it rather than after *z*.

**Two pure functions are borrowed from other contexts' domains, and nothing
else is.** ``clubs``' ``fold``, because a query, a stored copy and an order must
agree about what a letter is (``docs/adr/0182`` §2); and the matcher's
``distance_km`` and ``shown_kilometres``, because a distance printed here and on
a card must be one reading (``docs/adr/0182`` §6). Both are stateless arithmetic
over values this module already holds — the arrow ``conversations`` → ``games``
takes for ``entry_closes_at``, and neither context is thereby read.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, final

from app.modules.clubs.domain.folding import fold
from app.modules.groups.domain.ports import GroupListing, HomeClub, ReaderArea
from app.modules.matchmaking.domain.geography import (
    Point,
    distance_km,
    shown_kilometres,
)

#: Clubs to a page (#500 story 17: *20 clubs at a time, with more loading as I
#: scroll*).
PAGE_SIZE: Final = 20


@final
@dataclass(frozen=True, slots=True)
class PlacedClub:
    """A club, and how far it is printed from the reader — ``None`` for a reader
    with no Location area."""

    club: HomeClub
    distance_km: float | None


@final
@dataclass(frozen=True, slots=True)
class ClubPage:
    clubs: tuple[PlacedClub, ...]
    #: The page after this one, or ``None`` when this is the last.
    next_page: int | None


def in_search_order(
    clubs: Sequence[HomeClub], reader: ReaderArea | None
) -> list[PlacedClub]:
    """Every club, placed and ordered for this reader. The id breaks what the
    name leaves tied, so the order is total and a page boundary never moves."""

    if reader is None:
        return [
            PlacedClub(club=club, distance_km=None)
            for club in sorted(
                clubs, key=lambda club: (fold(club.name), club.name, club.id)
            )
        ]
    here = Point(latitude=reader.latitude, longitude=reader.longitude)
    placed = [
        PlacedClub(
            club=club,
            distance_km=shown_kilometres(
                distance_km(
                    here, Point(latitude=club.latitude, longitude=club.longitude)
                )
            ),
        )
        for club in clubs
    ]
    return sorted(
        placed,
        key=lambda entry: (
            entry.distance_km,
            fold(entry.club.name),
            entry.club.name,
            entry.club.id,
        ),
    )


def page_of(placed: Sequence[PlacedClub], page: int) -> ClubPage:
    """Page ``page`` (from one) of ``placed``. A page past the end is empty."""

    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    return ClubPage(
        clubs=tuple(placed[start:end]),
        next_page=page + 1 if len(placed) > end else None,
    )


def in_card_order(groups: Sequence[GroupListing]) -> list[GroupListing]:
    """The groups at one club, **the biggest crowd first**, then by name.

    A player choosing a home club is shown the groups already there so that
    they can join the existing crowd instead of splitting it
    (``docs/adr/0183`` §2), and the biggest crowd is the one to put first.
    """

    return sorted(
        groups,
        key=lambda group: (
            -group.member_count,
            fold(group.name.value),
            group.name.value,
            group.id,
        ),
    )
