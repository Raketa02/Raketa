"""What the proposer and posting read of a pool's members, for one sport (#540,
#546).

**One reading, two readers**: the proposer deals a pool's games from it, and a
member posting a game counts their best fits from it — the same Level, week,
gender, intent, Games & money and booked games, so the grid's number and the
post's versions are dealt from what the proposer would deal.

**Read once per provider where the provider allows**: every member's Level,
week and gender in one question, then each member's intent, Games & money and
booked games — in the pool's order, which is the order a tie is broken in.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from typing import final
from uuid import UUID

from app.kernel import Instant, Sport
from app.modules.player_profile.domain.gender import Gender
from app.modules.proposals.domain.deck import week_window, weeks_ahead
from app.modules.proposals.domain.games_and_money import GamesAndMoney
from app.modules.proposals.domain.ports import (
    BookedGames,
    GamesAndMoneyRepository,
    PlayersInPlay,
    WantedKinds,
)
from app.modules.proposals.domain.post import Who
from app.modules.proposals.domain.proposal import Proposal
from app.modules.proposals.domain.proposer import Member


@final
class ReadMembers:
    def __init__(
        self,
        *,
        players: PlayersInPlay,
        wanted: WantedKinds,
        settings: GamesAndMoneyRepository,
        booked: BookedGames,
    ) -> None:
        self._players = players
        self._wanted = wanted
        self._settings = settings
        self._booked = booked

    async def of(
        self, members: Sequence[UUID], *, sport: Sport, now: Instant
    ) -> list[Member]:
        """These members as the proposer reads them in ``sport`` at ``now``,
        in their order."""

        limits, booked = await self.limits_and_games(members, now=now)
        return await self.in_sport(members, sport=sport, limits=limits, booked=booked)

    async def limits_and_games(
        self, members: Sequence[UUID], *, now: Instant
    ) -> tuple[dict[UUID, GamesAndMoney], dict[UUID, tuple[Instant, ...]]]:
        """Each member's Games & money and the games they have booked in the
        weeks a card dealt now could be in — the same in every sport, so a
        reader dealing several reads them once."""

        start, stop = week_window(weeks_ahead(now))
        limits = {player: await self._settings.load(player) for player in members}
        booked = {
            player: tuple(await self._booked.starts_of(player, start=start, end=stop))
            for player in members
        }
        return limits, booked

    async def in_sport(
        self,
        members: Sequence[UUID],
        *,
        sport: Sport,
        limits: Mapping[UUID, GamesAndMoney],
        booked: Mapping[UUID, tuple[Instant, ...]],
    ) -> list[Member]:
        """These members in ``sport``, with the limits and booked games read
        for them already."""

        in_play = await self._players.of(members, sport=sport)
        found: list[Member] = []
        for player in members:
            facts = in_play[player]
            wanted = await self._wanted.of(player, sport=sport)
            found.append(
                Member(
                    player_id=player,
                    level=facts.level,
                    week=facts.week,
                    wants=wanted or frozenset(),
                    limits=limits[player],
                    booked=booked[player],
                    gender=facts.gender,
                    preference=facts.preference,
                )
            )
        return found


async def genders_of(
    players: PlayersInPlay, people: Collection[UUID], *, sport: Sport
) -> dict[UUID, Gender | None]:
    """Each of these people's gender, for a *Mixed pairs* post's two of each —
    read only where one is on the table, and never said."""

    if not people:
        return {}
    read = await players.of(sorted(people, key=str), sport=sport)
    return {person: read[person].gender for person in people}


async def genders_on(
    players: PlayersInPlay, proposal: Proposal, people: Collection[UUID]
) -> dict[UUID, Gender | None]:
    """These people's genders where ``proposal`` is a *Mixed pairs* post, whose
    two of each they decide — and nothing on any other game, which needs
    none."""

    if proposal.who is not Who.MIXED_PAIRS:
        return {}
    return await genders_of(players, people, sport=proposal.sport)
