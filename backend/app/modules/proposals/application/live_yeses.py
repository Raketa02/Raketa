"""A player's live yeses — You › Payments' **LIVE YESES · n** (the screens A7.3,
mock 48): every yes on a game that has not filled, **across pools**, each with
the share it would charge.

**Across pools** because the cap is the player's and not a group's: ten per
sport, wherever they were said. **Soonest game first**, which is the order a
player would withdraw them in.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.kernel import Clock, instant
from app.modules.proposals.domain.limits import LIVE_YESES_PER_SPORT
from app.modules.proposals.domain.ports import ClubNames, LiveYes, ProposalDirectory


@final
@dataclass(frozen=True, slots=True)
class NamedLiveYes:
    """A live yes and the name of the club it is at — ``None`` for a club that
    no longer exists, with the row kept."""

    yes: LiveYes
    club_name: str | None


@final
@dataclass(frozen=True, slots=True)
class LiveYeses:
    yeses: tuple[NamedLiveYes, ...]
    #: The cap per sport, so a client can say *up to 10 per sport* without
    #: holding the number.
    cap_per_sport: int


@final
class ReadLiveYeses:
    def __init__(
        self, *, directory: ProposalDirectory, clubs: ClubNames, clock: Clock
    ) -> None:
        self._directory = directory
        self._clubs = clubs
        self._clock = clock

    async def execute(self, player_id: UUID) -> LiveYeses:
        yeses = await self._directory.live_yeses_of(
            player_id, now=instant(self._clock.now())
        )
        names = await self._clubs.names_of({yes.club_id for yes in yeses})
        return LiveYeses(
            yeses=tuple(
                NamedLiveYes(yes=yes, club_name=names.get(yes.club_id)) for yes in yeses
            ),
            cap_per_sport=LIVE_YESES_PER_SPORT,
        )
