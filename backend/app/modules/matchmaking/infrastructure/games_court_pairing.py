"""``CourtPairing``'s adapter — the game screen's forecast, split, stakes and seats.

``games`` may not import the matcher, and the game screen wants four things
that are the matcher's and the rating context's: how even the court is forecast
to be, the two side strengths that forecast was read from, what a counted result
would do to the reader's Level, and each seat's published Level. This is the
composing adapter ``.importlinter``'s contract comment names — *it signs the
missing half through an adapter that lives in the matcher's own infrastructure,
and it does not know a matcher exists* — one screen later than
``challenge_court_cards.py`` and on the same seam (``docs/adr/0161``).

**It reads the provider's own use case and never the provider's store.**
``pair_with_a_court.py`` decides what a pairing *is* — recomputed for the
reader, ungated, unranked, unrecorded — and this adapter asks it and translates.
That is the whole of *do not build a second forecast apparatus*: the challenge
card and the game screen come to one number for one court because they are one
computation, and the identity is by construction rather than by test.

**Two providers, and each fails on its own.** The forecast and the split need
the matcher — the candidate index and the ledger behind Redis, which the
workbench binds — and a process with neither, or an outage in either, costs
exactly those two blocks. The seats and the stakes need the rating streams and
nothing else, so they are read whatever the matcher's state: a Level is a fact
about a person, and a screen that dropped four Levels because an index was
behind would be conflating two providers' availability. So ``arranger`` may be
``None`` — that is what a process with no index hands over — and the read still
answers the seats and, on a counted game, the stakes.

**Three things are decided here and not in the use case.** A seat the index
cannot describe leaves the forecast **absent rather than provisional** — the
use case reads a short side as if the missing player matched the one beside
them, which is honest on a court still filling and a half-read forecast on a
game that has its whole line-up. The stakes are priced **side against side**
through the court-shaped read on ``AtStakeQuery``, because a game's line-up is
frozen and that is the pair the result will deliver; the card's head-to-head
figure is for a court whose other seats are unknown. And the seats' Levels come
from ``rating``'s **published** read, live, and never from the index — the index
is the matcher's projection for ranking, and this is a fact about a person
printed beside their name.

**A court with a seat open draws its Levels and nothing else**
(``docs/adr/0162`` §3). A forecast is a claim about a court, and a court somebody
has left is not yet the one that will play; the stakes are priced *side against
side* on the argument that every seat is known, and one is not. So both are the
absence ADR-0161 §4 reserved for the day a seat could be open, rather than a
provisional figure read over a short side — and the seats that are filled still
name their Levels, because a Level is a fact about a person.

**The absences are one absence on the wire, by decision** (``docs/adr/0161``
§4). The reader's own three conflicts mean *there is nothing to compute*;
anything else on the matcher's side means *it could not be read*; both leave
the forecast and the split absent with no reason beside them, because the game
screen draws nothing and says nothing. What keeps the outage from being silent
is the warning below.
"""

from __future__ import annotations

import logging
from typing import final
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.engines.matchfit.grouping import Arranged
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
from app.modules.matchmaking.application.pair_with_a_court import (
    NOTHING_TO_COMPUTE,
    PairWithACourt,
    PairWithACourtCommand,
)
from app.modules.matchmaking.domain.ports import AtStakeQuery
from app.modules.rating.domain.ports import RatedPlayerQuery

logger = logging.getLogger(__name__)


@final
class GamesCourtPairing:
    """What the matcher and the rating context make of a game's court, for the
    reader."""

    def __init__(
        self,
        *,
        arranger: PairWithACourt | None,
        at_stake: AtStakeQuery,
        ratings: RatedPlayerQuery,
    ) -> None:
        self._arranger = arranger
        self._at_stake = at_stake
        self._ratings = ratings

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
            seats = await self._seats(sport, line_up)
        except Exception:
            # The one answer that carries nothing: the Levels themselves could
            # not be read. Logged, because a screen with no numbers on it is
            # indistinguishable from a court nobody is rated on.
            logger.warning("the court's Levels could not be read", exc_info=True)
            return None
        if not line_up.is_complete:
            # **A seat is open, so there is no court to price yet.** The
            # Levels of the people on it are still theirs.
            return Pairing(seats=seats)
        arranged = await self._arranged(
            sport, kind, reader_id, partners=partners, opponents=opponents
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
            forecast=None if arranged is None else _forecast(arranged),
            split=None if arranged is None else _split(arranged),
            at_stake=at_stake,
        )

    async def _seats(self, sport: Sport, line_up: LineUp) -> tuple[SeatLevel, ...]:
        """Each rated seat's published figures, **in the line-up's own order.**

        One set read over the whole court. A seat whose person holds no rating
        in this sport is absent from the answer and so from the seats — the
        Levels of the rated ones are still named, because a Level is a fact
        about a person and not about the pairing that could not be computed.
        """

        published = await self._ratings.published_for(line_up.players, sport=sport)
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

    async def _arranged(
        self,
        sport: Sport,
        kind: GameKind,
        reader_id: UUID,
        *,
        partners: list[UUID],
        opponents: list[UUID],
    ) -> Arranged | None:
        """The court as the matcher arranges it for this reader, or nothing.

        **The mode is the game's kind and not the reader's declaration.** A
        challenge card resolves ``None`` through the deck's rule because a
        mutual-born challenge asked nobody what kind of evening it was; a game
        has answered that question at the plan — *a friendly is a thing people
        choose* — and the kind is stamped on it. The mode selects a weight
        vector for a Fit this read never prints; the forecast reads Levels
        alone, which is why the card and the game agree about it whatever the
        mode.

        ``None`` on four grounds and each is an absence rather than a number:
        this process has no matcher to ask; the reader holds nothing to compute
        against; a seat the index cannot describe, which would otherwise read as
        a side short and price a provisional figure on a court whose line-up is
        frozen; and an outage on the matcher's side, which is **broad, and
        deliberately so** on ``read_demand``'s precedent — a provider that
        raises and one that answers something this adapter cannot translate are
        the same event to the screen, and the game answers either way.
        """

        if self._arranger is None:
            return None
        try:
            priced = await self._arranger.execute(
                PairWithACourtCommand(
                    reader_id=reader_id,
                    sport=sport,
                    mode=(
                        SearchMode.COMPETITIVE
                        if kind is GameKind.COUNTED
                        else SearchMode.FOR_FUN
                    ),
                    court_ids=tuple((*partners, *opponents)),
                    partners=frozenset(partners),
                )
            )
        except NOTHING_TO_COMPUTE:
            return None
        except Exception:
            logger.warning("the game's pairing could not be read", exc_info=True)
            return None
        if len(priced) != len(partners) + len(opponents):
            return None
        arranged = priced[0].arranged
        if arranged is None or arranged.forecast.provisional:
            return None
        return arranged

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


def _forecast(arranged: Arranged) -> CourtForecast:
    forecast = arranged.forecast
    return CourtForecast(
        pct=forecast.pct,
        sigma_group=forecast.sigma_group,
        provisional=forecast.provisional,
        assumption=(
            None if forecast.assumption is None else forecast.assumption.value
        ),
    )


def _split(arranged: Arranged) -> CourtSplit:
    """The two strengths in the reader's direction — which is the direction the
    use case computed them in, since it arranges the court around the reader."""

    return CourtSplit(
        your_side=arranged.split.your_side, their_side=arranged.split.their_side
    )


__all__ = ["GamesCourtPairing", "sides_of"]
