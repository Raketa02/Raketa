"""The two refusals a details edit meets over the sports it unticks: **a sport
one of the club's courts plays** (#535, the screens B3), and — from outside the
club — **a sport an official group declares** (``docs/adr/0182`` §5).

Pure: the sports the club offers now, the sports the desk is saving, and what
the club's courts and each official group at the club play, in; the refusal,
or nothing, out. The groups are read by the use case, because what a group
plays is a fact about groups and not this aggregate's to know.
"""

from __future__ import annotations

from collections.abc import Collection, Iterable, Sequence

from app.kernel import Sport
from app.modules.clubs.domain.courts import Court
from app.modules.clubs.domain.errors import ClubSportDeclaredByGroup, ClubSportHasCourts
from app.modules.clubs.domain.ports import DeclaringGroup


def unticked(
    offered: Collection[Sport], saving: Collection[Sport]
) -> frozenset[Sport]:
    """The sports the club offers and will not after this save."""

    return frozenset(sport for sport in offered if sport not in saving)


def refuse_an_untick(
    removed: Collection[Sport], declaring: Sequence[DeclaringGroup]
) -> None:
    """Refuse the save when an official group declares a sport it removes —
    naming **the first such sport in the registry's order, and the first group
    playing it by name**, so the same save is refused the same way whichever
    order the groups were read in (``docs/adr/0105``)."""

    for sport in Sport:
        if sport not in removed:
            continue
        playing = sorted(
            (group.name for group in declaring if sport in group.sports),
            key=lambda name: (name.casefold(), name),
        )
        if playing:
            raise ClubSportDeclaredByGroup(sport=sport.value, group=playing[0])


def refuse_an_untick_of_courts(
    removed: Collection[Sport], courts: Iterable[Court]
) -> None:
    """Refuse the save when a court of the club plays a sport it removes —
    naming **the first such sport in the registry's order, and the first court
    playing it in the club's order**. A switched-off court counts: it is still
    the club's, and switching it on would sell a sport the club no longer
    offers."""

    listed = list(courts)
    for sport in Sport:
        if sport not in removed:
            continue
        playing = [court for court in listed if court.sport == sport]
        if playing:
            raise ClubSportHasCourts(sport=sport.value, court=playing[0].name.value)
