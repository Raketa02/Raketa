"""A player's live yeses — You › Payments' **LIVE YESES · n** (the screens A7.3,
mock 48): every yes on a game that has not filled, **across pools**, each with
the share it would charge.

**Across pools** because what a yes can book is the player's and not a
group's: games per week and one game per hour bind them wherever they were
said. There is no cap on how many (removed 2026-10-05). **Soonest game first**,
which is the order a player would withdraw them in.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.kernel import Clock, instant
from app.modules.proposals.domain.ports import (
    ClubNames,
    CourtKinds,
    LiveYes,
    ProposalDirectory,
)


@final
@dataclass(frozen=True, slots=True)
class NamedLiveYes:
    """A live yes and the name of the club it is at — ``None`` for a club that
    no longer exists, with the row kept — and the kind of court it promises:
    *indoor* or *outdoor* when every free court it could be booked on is of
    that kind, ``None`` when they are mixed (#706; Q122), read as the deck's
    card reads it."""

    yes: LiveYes
    club_name: str | None
    indoor: bool | None


@final
@dataclass(frozen=True, slots=True)
class LiveYeses:
    yeses: tuple[NamedLiveYes, ...]


@final
class ReadLiveYeses:
    def __init__(
        self,
        *,
        directory: ProposalDirectory,
        clubs: ClubNames,
        kinds: CourtKinds,
        clock: Clock,
    ) -> None:
        self._directory = directory
        self._clubs = clubs
        self._kinds = kinds
        self._clock = clock

    async def execute(self, player_id: UUID) -> LiveYeses:
        yeses = await self._directory.live_yeses_of(
            player_id, now=instant(self._clock.now())
        )
        names = await self._clubs.names_of({yes.club_id for yes in yeses})
        # The same free-court read the deck's cards take their kind from.
        kinds = await self._kinds.of(
            {(yes.club_id, yes.sport, yes.start) for yes in yeses}
        )
        return LiveYeses(
            yeses=tuple(
                NamedLiveYes(
                    yes=yes,
                    club_name=names.get(yes.club_id),
                    indoor=kinds.get((yes.club_id, yes.sport, yes.start)),
                )
                for yes in yeses
            ),
        )
