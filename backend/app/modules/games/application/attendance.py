"""Who turned up to a booked game, caught at the court (#657; ``docs/adr/0195``
§3, the mechanics §15.1).

**Four acts, the aggregate's own**: *isn't here yet* and the arrival — *I'm
here*, *they're here* — made at the club in the first half hour, and *I was
there* and its confirmation within a day after it. None of them confirms an
outcome: *Didn't come* is the tap window closing on nobody, which is a clock,
and is proved by moving one.

**The two acts made in the tap window carry a fix, and the Game is handed only
the verdict.** The fix is measured against the booking's club through
``GameClubs`` — a demand on ``bookings``, where the Game's club is known — and
dropped: nothing here keeps it, logs it or passes it on.
"""

from __future__ import annotations

from typing import final

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant
from app.modules.games.application.answer_result import ActOnAGame
from app.modules.games.application.commands import (
    ClaimPresenceCommand,
    ConfirmPresenceCommand,
    NoteAbsentCommand,
    NoteArrivalCommand,
)
from app.modules.games.application.read_games import StandingGame
from app.modules.games.domain.attendance import ClubVerdict, LocationFix
from app.modules.games.domain.game import Game
from app.modules.games.domain.ports import GameClubs, GameRepository, PlayerNames


class ActAtTheCourt(ActOnAGame):
    """An act made at the club: what ``ActOnAGame`` shares, and where the
    game's club is."""

    def __init__(
        self,
        *,
        games: GameRepository,
        names: PlayerNames,
        uow: UnitOfWork,
        clock: Clock,
        clubs: GameClubs,
    ) -> None:
        super().__init__(games=games, names=names, uow=uow, clock=clock)
        self._clubs = clubs

    async def _verdict(self, game: Game, fix: LocationFix) -> ClubVerdict:
        """**At the club, at that time** — the fix measured against the
        booking's club map point, and nothing about the fix kept."""

        found = await self._clubs.metres_from(
            game.challenge_id, latitude=fix.latitude, longitude=fix.longitude
        )
        return ClubVerdict.of(
            metres=None if found is None else found.metres,
            accuracy_m=fix.accuracy_m,
            club_name=None if found is None else found.club_name,
        )


@final
class NoteAbsent(ActAtTheCourt):
    """*Oscar isn't here yet* — by a player at the club."""

    async def execute(self, command: NoteAbsentCommand) -> StandingGame:
        at = instant(self._clock.now())
        game = await self._yours(game_id=command.game_id, player_id=command.player_id)
        names = await self._named(game)
        where = await self._verdict(game, command.fix)
        game.note_absent(
            by=command.player_id,
            absent=command.absent_id,
            where=where,
            occurred_at=at,
        )
        return await self._saved(game, at, names)


@final
class NoteArrival(ActAtTheCourt):
    """*I'm here*, or *they're here* — at the club."""

    async def execute(self, command: NoteArrivalCommand) -> StandingGame:
        at = instant(self._clock.now())
        game = await self._yours(game_id=command.game_id, player_id=command.player_id)
        names = await self._named(game)
        where = await self._verdict(game, command.fix)
        game.note_arrival(
            by=command.player_id,
            arrived=command.arrived_id,
            where=where,
            occurred_at=at,
        )
        return await self._saved(game, at, names)


@final
class ClaimPresence(ActOnAGame):
    """*I was there* — by the player who Didn't come, within a day."""

    async def execute(self, command: ClaimPresenceCommand) -> StandingGame:
        at = instant(self._clock.now())
        game = await self._yours(game_id=command.game_id, player_id=command.player_id)
        names = await self._named(game)
        game.claim_presence(by=command.player_id, occurred_at=at)
        return await self._saved(game, at, names)


@final
class ConfirmPresence(ActOnAGame):
    """*Yes, they were here* — by somebody else on the court."""

    async def execute(self, command: ConfirmPresenceCommand) -> StandingGame:
        at = instant(self._clock.now())
        game = await self._yours(game_id=command.game_id, player_id=command.player_id)
        names = await self._named(game)
        game.confirm_presence(
            by=command.player_id, claimant=command.claimant_id, occurred_at=at
        )
        return await self._saved(game, at, names)


__all__ = [
    "ActAtTheCourt",
    "ClaimPresence",
    "ConfirmPresence",
    "NoteAbsent",
    "NoteArrival",
]
