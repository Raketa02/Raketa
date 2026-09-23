"""Reading one game's pairing back, for the person on its court who asked.

**The game screen draws its court's pairing, and this is the read it draws it
from** (``docs/adr/0161``). Four steps, and each is a rule rather than plumbing.

**Load the game of yours**, on ``challenge_of_yours.py``'s one refusal for two
cases: no such game and a game you did not play in answer identically, because a
read keyed on an id is the shape a directory is probed through.

**Refuse by standing, and only ``AWAITING_ENTRY`` answers.** The pairing means
what a card means *because this game has not happened* (``docs/adr/0143``); after
it has, or after the entry window closed on silence, the values would be a claim
about people made from a record that has moved on.

**Ask the port, once.** The clock is read here for the standing, and ``read_at``
names that instant; the pairing is folded against nothing and takes none.

**Hold the open-seat rule here too** (``docs/adr/0162`` §3). A court somebody
has left draws its Levels and neither a forecast nor a stake; the adapter decides
it and this side asserts it, on the friendly rule's own shape.

**Hold the friendly rule here too.** The port is told the kind so that it never
prices a friendly, and this side asserts the same thing on what comes back — a
provider that priced one anyway is a wrong branch made loud rather than a
figure rendered.

**Render nothing.** The use case returns the port's answer beside the instant and
does no arithmetic; the route does none either. The engine's numbers cross
unrounded, and decimal formatting is the client's.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.kernel import Clock, Instant, instant, invariant
from app.modules.games.domain.errors import NoGameOfYoursHasThatId, PairingIsHistory
from app.modules.games.domain.lineup import GameKind
from app.modules.games.domain.ports import CourtPairing, GameRepository, Pairing
from app.modules.games.domain.standing import GameStanding


@final
@dataclass(frozen=True, slots=True)
class GamePairingRead:
    """The instant the game was read at, and what the matcher made of its court.

    ``pairing`` is ``None`` where the Levels themselves could not be read, and a
    ``Pairing`` with the forecast absent where the seats were read and the
    matcher could not price the court. The route draws the same absence for
    both, by decision; the log tells them apart.
    """

    read_at: Instant
    pairing: Pairing | None


@final
class ReadGamePairing:
    """One game's pairing, computed for one reader on its court."""

    def __init__(
        self, *, games: GameRepository, pairings: CourtPairing, clock: Clock
    ) -> None:
        self._games = games
        self._pairings = pairings
        self._clock = clock

    async def execute(self, game_id: UUID, reader_id: UUID) -> GamePairingRead:
        now = instant(self._clock.now())
        game = await self._games.load(game_id)
        if game is None or reader_id not in game.line_up.players:
            raise NoGameOfYoursHasThatId()
        if game.standing_at(now) is not GameStanding.AWAITING_ENTRY:
            raise PairingIsHistory()
        pairing = await self._pairings.pairing_for(
            sport=game.sport,
            kind=game.kind,
            line_up=game.line_up,
            reader_id=reader_id,
        )
        invariant(
            game.kind is GameKind.COUNTED
            or pairing is None
            or pairing.at_stake is None,
            "a friendly priced: a counted result on it is meaningless, and the "
            "port was told the kind so as never to ask",
        )
        invariant(
            game.line_up.is_complete
            or pairing is None
            or (pairing.forecast is None and pairing.at_stake is None),
            "a court with a seat open priced: a forecast is a claim about a "
            "court, and this one is not yet the court that will play "
            "(docs/adr/0162)",
        )
        return GamePairingRead(read_at=now, pairing=pairing)


__all__ = ["GamePairingRead", "ReadGamePairing"]
