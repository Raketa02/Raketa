"""``ConfirmedResultLedger`` over the event log.

**A second adapter rather than a third method on ``EventSourcedGameHistory``**,
and the line between them is which read they start from. Every read there begins
*which streams seat this person* and folds the answer four ways; this one starts
from nobody and reads every game, because the caller has no player to ask about
until it has folded the result. One class over two different scans would run the
wrong one half the time.

**Nothing is projected, here least of all.** *Confirmed* is folded from the record
against the caller's clock, and so is the moment it became confirmed — which is
what makes the order this returns the same order on every process, with no column
anybody has to keep current. A ``confirmed_at`` column would be wrong for the whole
gap between a deadline passing and a sweep, and it would be the one a catch-up
believed.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.events import EventCodec
from app.kernel import Instant
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind
from app.modules.games.domain.ports import ConfirmedGame
from app.modules.games.infrastructure.game_streams import every_stream, streams_of


@final
class EventSourcedConfirmedResults:
    """``ConfirmedResultLedger`` over ``event_store``."""

    def __init__(self, session: AsyncSession, codec: EventCodec) -> None:
        self._session = session
        self._codec = codec

    async def confirmed_counted_results(
        self, *, now: Instant
    ) -> tuple[ConfirmedGame, ...]:
        found: list[ConfirmedGame] = []
        for events in (await every_stream(self._session, self._codec)).values():
            game = Game.from_history(events)
            confirmed = _confirmed_counted(game, now)
            if confirmed is not None:
                found.append(confirmed)
        # **Settlement order, and the game id breaks the tie.** Two results whose
        # windows closed in the same instant would otherwise be walked in
        # whatever order the scan produced, and a Level moved against the Levels
        # as they stood is a Level that depends on that order
        # (``docs/adr/0105``).
        found.sort(key=lambda one: (one.confirmed_at, one.game_id))
        return tuple(found)

    async def confirmed_counted_result(
        self, game_id: UUID, *, now: Instant
    ) -> ConfirmedGame | None:
        streams = await streams_of(self._session, self._codec, (game_id,))
        events = streams.get(game_id)
        if not events:
            return None
        return _confirmed_counted(Game.from_history(events), now)


def _confirmed_counted(game: Game, now: Instant) -> ConfirmedGame | None:
    """One game as a result, or ``None`` if it is not one that may move a Level.

    Three things are asked and each of them is a decision recorded elsewhere: a
    **friendly** was never evidence about anybody, by the choice of the people who
    arranged it; an **unscored** or **disputed** game is an evening and not
    evidence; and a game still inside its windows has not settled on anything to
    apply.
    """

    if game.kind is not GameKind.COUNTED:
        return None
    confirmed_at = game.confirmed_at(now)
    if confirmed_at is None:
        return None
    score = game.confirmed_score_at(now)
    if score is None or game.played_at is None:
        return None

    winning = score.winner
    # The line-up's own order on each side, so the walk is the same on every
    # process — a ``frozenset`` here would be the set-iteration hazard
    # ``docs/adr/0105`` is written about, one layer below where it would show.
    # A confirmed result is on a court every seat of which is filled — a
    # score is refused while one is open (``docs/adr/0162``) — so the filter
    # on the occupant is the type's and never drops anybody.
    winners = tuple(
        seating.player_id
        for seating in game.line_up.seatings
        if seating.side is winning and seating.player_id is not None
    )
    losers = tuple(
        seating.player_id
        for seating in game.line_up.seatings
        if seating.side is not winning and seating.player_id is not None
    )
    return ConfirmedGame(
        game_id=game.id,
        sport=game.sport,
        winners=winners,
        losers=losers,
        played_at=game.played_at,
        confirmed_at=confirmed_at,
    )


__all__ = ["EventSourcedConfirmedResults"]
