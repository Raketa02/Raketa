"""``CourtPairing``'s adapter — the game screen's forecast, split, stakes and seats.

``games`` may not import the matcher, and the game screen wants four things
that are the matcher's and the rating context's: how even the court is forecast
to be, the two side strengths that forecast was read from, what a counted result
would do to the reader's Level, and each seat's published Level. This is the
composing adapter ``.importlinter``'s contract comment names — *it signs the
missing half through an adapter that lives in the matcher's own infrastructure,
and it does not know a matcher exists* (``docs/adr/0161``).

**It answers from the balance forecast directly** (#575). A booked game's court
is already seated, so there is nobody to find and nothing to rank: the court is
read **side against side** from the people's Levels, through the engine's own
``forecast_and_split`` under the released ruleset's balance rules and the group
σ as the matcher composes it. That is the reading a Games card makes of the same
people (``proposals``' ``MatcherBalanceForecasts``), so the card and the game
come to one number for one court because they are one engine function — and no
search workbench, candidate index, match history or interest ledger sits behind
it.

**Levels off rating's estimates, live** — the engine's currency — and the seats'
printed figures off ``rating``'s **published** read, beside them. Both are the
rating streams, read in one go: a court whose Levels cannot be read draws
nothing at all, and that is the one answer that carries nothing.

**Three things are decided here and not in the use case.** A seat with no
rating in the sport leaves the forecast **absent rather than provisional** — a
half-read forecast on a game whose line-up is booked is exactly the figure #346
argued against. The stakes are priced **side against side** through the
court-shaped read on ``AtStakeQuery``, because that is the pair the result will
deliver. And the seats' Levels are ``rating``'s published figures, printed
beside a name — never a band derived here.

**A court with a seat open draws its Levels and nothing else**
(``docs/adr/0162`` §3). A forecast is a claim about a court, and a court somebody
has left is not yet the one that will play; the stakes are priced *side against
side* on the argument that every seat is known, and one is not.

**The absences are one absence on the wire, by decision** (``docs/adr/0161``
§4): the game screen draws nothing and says nothing about why.
"""

from __future__ import annotations

import logging
from typing import Mapping, final
from uuid import UUID

from app.engines.matchfit.ruleset import Ruleset
from app.engines.racketskill.core import SkillEstimate
from app.kernel import Sport, invariant
from app.modules.games.domain.lineup import GameKind, LineUp
from app.modules.games.domain.ports import (
    CourtForecast,
    CourtSplit,
    LevelDeltas,
    Pairing,
    SeatLevel,
)
from app.modules.matchmaking.application.outward_reads import read_demand
from app.modules.matchmaking.domain.balance import forecast_the_sides
from app.modules.matchmaking.domain.ports import AtStakeQuery
from app.modules.rating.domain.ports import RatedPlayerQuery, RatedSport

logger = logging.getLogger(__name__)


@final
class GamesCourtPairing:
    """What the engine and the rating context make of a game's court, for the
    reader."""

    def __init__(
        self,
        *,
        ratings: RatedPlayerQuery,
        ruleset: Ruleset,
        at_stake: AtStakeQuery,
    ) -> None:
        self._ratings = ratings
        self._ruleset = ruleset
        self._at_stake = at_stake

    async def pairing_for(
        self,
        *,
        sport: Sport,
        kind: GameKind,
        line_up: LineUp,
        reader_id: UUID,
    ) -> Pairing | None:
        partners, opponents = sides_of(line_up, reader_id)
        try:
            published = await self._ratings.published_for(
                line_up.players, sport=sport
            )
            levels = await self._ratings.estimates_for(line_up.players, sport=sport)
        except Exception:
            # The one answer that carries nothing: the Levels themselves could
            # not be read. Logged, because a screen with no numbers on it is
            # indistinguishable from a court nobody is rated on.
            logger.warning("the court's Levels could not be read", exc_info=True)
            return None
        seats = _seats(line_up, published)
        if not line_up.is_complete:
            # **A seat is open, so there is no court to price yet.** The
            # Levels of the people on it are still theirs.
            return Pairing(seats=seats)
        read = self._read(
            sport, levels, ours=[reader_id, *partners], theirs=opponents
        )
        # **Never asked on a friendly.** A counted result there is meaningless
        # rather than unavailable, and the port's own name refuses the
        # question; here the refusal is not asking it.
        at_stake = (
            await self._deltas(
                sport, reader_id, ours=[reader_id, *partners], theirs=opponents
            )
            if kind is GameKind.COUNTED
            else None
        )
        return Pairing(
            seats=seats,
            forecast=None if read is None else read[0],
            split=None if read is None else read[1],
            at_stake=at_stake,
        )

    def _read(
        self,
        sport: Sport,
        levels: Mapping[UUID, SkillEstimate],
        *,
        ours: list[UUID],
        theirs: list[UUID],
    ) -> tuple[CourtForecast, CourtSplit] | None:
        """The court read side against side, **in the reader's direction**.

        ``None`` where anybody on it holds no rating in the sport: a side short
        of a Level is not read *as if the missing player matched the one beside
        them* — that is honest on a card still filling, and a half-read forecast
        on a booked game.
        """

        sides = forecast_the_sides(
            ours, theirs, levels, sport=sport, rules=self._ruleset.balance
        )
        if sides is None:
            return None
        forecast, split = sides
        return (
            CourtForecast(
                pct=forecast.pct,
                sigma_group=forecast.sigma_group,
                provisional=forecast.provisional,
                assumption=(
                    None
                    if forecast.assumption is None
                    else forecast.assumption.value
                ),
            ),
            CourtSplit(your_side=split.your_side, their_side=split.their_side),
        )

    async def _deltas(
        self,
        sport: Sport,
        reader_id: UUID,
        *,
        ours: list[UUID],
        theirs: list[UUID],
    ) -> LevelDeltas | None:
        """The rule read forward for this court, and it fails **soft** like every
        at-stake read: a Level store that cannot answer costs the block and never
        the screen, which is the posture ``AtStakeQuery`` declared."""

        at_stake = await read_demand(
            AtStakeQuery,
            lambda: self._at_stake.counted_game_deltas_on_court(
                player_id=reader_id,
                own_side=ours,
                opposing_side=theirs,
                sport=sport,
            ),
            stood_down=None,
        )
        if at_stake is None:
            return None
        return LevelDeltas(
            win_delta=at_stake.win_delta, loss_delta=at_stake.loss_delta
        )


def sides_of(line_up: LineUp, reader_id: UUID) -> tuple[list[UUID], list[UUID]]:
    """The reader's partners and their opponents, **each sorted.**

    A line-up's sides are sets, and this is the one place the court is turned
    into an order the engine walks — so it is stated here, on the collection,
    rather than left to what a ``frozenset`` happens to yield on one process
    (``docs/adr/0105``). The determinism probe beside the pairing read calls it
    for exactly that reason.
    """

    mine = invariant(
        line_up.side_of(reader_id), "a pairing read for somebody not on the court"
    )
    return (
        sorted(line_up.players_on(mine) - {reader_id}),
        sorted(line_up.players_on(mine.other)),
    )


def _seats(
    line_up: LineUp, published: Mapping[UUID, RatedSport]
) -> tuple[SeatLevel, ...]:
    """Each rated seat's published figures, **in the line-up's own order.**

    A seat whose person holds no rating in this sport is absent from the answer
    and so from the seats — the Levels of the rated ones are still named,
    because a Level is a fact about a person and not about the pairing that
    could not be computed.
    """

    return tuple(
        SeatLevel(
            player_id=seating.player_id,
            level=rated.mu,
            band=rated.band_name,
            range_low=rated.range_low,
            range_high=rated.range_high,
            confidence=rated.confidence,
        )
        for seating in line_up.seatings
        if seating.player_id is not None
        and (rated := published.get(seating.player_id)) is not None
    )


__all__ = ["GamesCourtPairing", "sides_of"]
