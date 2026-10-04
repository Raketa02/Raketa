"""The one refusal a details edit meets from outside the club: **a sport an
official group declares cannot be unticked** (``docs/adr/0182`` §5).

Pure: the sports the club offers now, the sports the desk is saving, and what
each official group at the club declares, in; the refusal, or nothing, out. The
groups are read by the use case, because what a group plays is a fact about
groups and not this aggregate's to know.
"""

from __future__ import annotations

from collections.abc import Collection, Sequence

from app.kernel import Sport
from app.modules.clubs.domain.errors import ClubSportDeclaredByGroup
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
