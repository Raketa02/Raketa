"""*Remove this card.* A called-off game's card, cleared from the reader's own
rail (``docs/adr/0172`` §5).

**A per-player act on ``games``, recorded once and derived on every read.** The
card must be gone on the reader's other phone and after a reinstall, so it is
not the client's; it is a fact about *this game's card for this reader*, so it
belongs on the game and is read where the rail is folded — ``docs/adr/0168``
§2's shape for the room's one membership fact: stored once, subtraction only,
effect derived against the record on every read. A per-user *hidden games*
table would be a projection with no fold behind it, and the first list this
context kept that its aggregates did not.

**It removes a court from the reader's own lists, not a fact.** The record is
untouched, nobody else's rail moves, and there is no undo — which is why the
trash has no sheet, and why this answers nothing: the thing a redraw would draw
is the thing that was removed. The challenge's row goes with the card
(``docs/adr/0173``): the inbox subtracts its reader off the same set this
writes to, so one act clears one court from both lists.

**The permission is the one rule every act here shares** — the people who may
act are the people on the court — and a stranger is refused as one, on the
aggregate's own refusal; the standing is the aggregate's question too. What is
here is the load, the act, the save and the commit, and nothing decided.
"""

from __future__ import annotations

from typing import final

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant
from app.modules.games.application.commands import DismissGameCommand
from app.modules.games.domain.errors import YouWereNotOnThisCourt
from app.modules.games.domain.ports import GameRepository


@final
class DismissGame:
    """*Remove this card* → the game records that this reader has cleared it."""

    def __init__(
        self, *, games: GameRepository, uow: UnitOfWork, clock: Clock
    ) -> None:
        self._games = games
        self._uow = uow
        self._clock = clock

    async def execute(self, command: DismissGameCommand) -> None:
        """Record the dismissal, or refuse it — and answer nothing.

        **No such game and a game you were not on the court of are one
        refusal**, as they are for every act here: an answer that separated
        them would tell a caller whether a stranger's game id is real.

        **It commits**, as the two result acts do, because the act is the whole
        request — unlike the three the hand-over runs inline, whose transaction
        is the challenge's.
        """

        game = await self._games.load(command.game_id)
        if game is None:
            raise YouWereNotOnThisCourt()
        game.dismiss(by=command.player_id, occurred_at=instant(self._clock.now()))
        await self._games.save(game)
        await self._uow.commit()


__all__ = ["DismissGame"]
