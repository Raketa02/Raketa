"""One game's pairing, computed from fixed inputs, printed as JSON.

Run under two ``PYTHONHASHSEED``s by ``test_game_pairing.py``, because the one
place the pairing read could hand two processes two answers to one question is
a set walked into an order (``docs/adr/0105``) — and a game's court is made of
sets: ``LineUp.players_on`` is a ``frozenset``, and the sides the engine reads
have to come out of it in one order everywhere.

**Below the routes, with fixed ids, on purpose.** The whole HTTP flow cannot be
compared across two processes: every player id is minted at random, ties break
on it, and two runs would disagree for a reason that has nothing to do with
hash seeds. So the probe runs the adapter the route runs — the sides off the
line-up, the court read side against side by the engine, the stakes priced
side against side by the rule — over Levels and ids that are the same in both
processes.
"""

from __future__ import annotations

import asyncio
import json
from typing import Collection, Mapping
from uuid import UUID

from app.bootstrap.composition import build_ruleset
from app.engines.racketskill.core import SkillEstimate
from app.kernel import Sport
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.matchmaking.infrastructure.games_court_pairing import (
    GamesCourtPairing,
)
from app.modules.matchmaking.infrastructure.rating_at_stake import (
    RatingResultUpdateRule,
)
from app.modules.rating.domain.ports import RatedSport

#: Four people, fixed. The reader is on side A with a partner; two across.
READER = UUID("00000000-0000-4000-8000-000000000001")
PARTNER = UUID("00000000-0000-4000-8000-000000000002")
LEFT = UUID("00000000-0000-4000-8000-000000000003")
RIGHT = UUID("00000000-0000-4000-8000-000000000004")

LEVELS = {
    READER: (3.00, 0.30),
    PARTNER: (2.70, 0.35),
    LEFT: (3.10, 0.25),
    RIGHT: (2.90, 0.40),
}


class _Ratings:
    """``RatedPlayerQuery`` over a dict — the engine's currency and the
    published figures beside it, and nothing read."""

    async def estimates_for(
        self, player_ids: Collection[UUID], *, sport: Sport
    ) -> Mapping[UUID, SkillEstimate]:
        return {
            one: SkillEstimate(*LEVELS[one]) for one in player_ids if one in LEVELS
        }

    async def ratings_of(self, player_id: UUID) -> Mapping[Sport, RatedSport]:
        return {}

    async def published_for(
        self, player_ids: Collection[UUID], *, sport: Sport
    ) -> Mapping[UUID, RatedSport]:
        return {
            one: RatedSport(
                sport=sport,
                mu=LEVELS[one][0],
                confidence=60,
                range_low=LEVELS[one][0] - 0.3,
                range_high=LEVELS[one][0] + 0.3,
                band_name="Improver",
                counted_results=0,
            )
            for one in player_ids
            if one in LEVELS
        }


async def _the_pairing() -> dict:
    line_up = LineUp.of(
        (
            Seating(side=GameSide.A, player_id=READER),
            Seating(side=GameSide.A, player_id=PARTNER),
            Seating(side=GameSide.B, player_id=LEFT),
            Seating(side=GameSide.B, player_id=RIGHT),
        )
    )
    ratings = _Ratings()
    pairing = await GamesCourtPairing(
        ratings=ratings,
        ruleset=build_ruleset(),
        at_stake=RatingResultUpdateRule(ratings),
    ).pairing_for(
        sport=Sport.PADEL,
        kind=GameKind.COUNTED,
        line_up=line_up,
        reader_id=READER,
    )
    assert pairing is not None
    assert pairing.forecast is not None and pairing.split is not None
    assert pairing.at_stake is not None
    return {
        "seats": [str(seat.player_id) for seat in pairing.seats],
        "forecast": {
            "pct": pairing.forecast.pct,
            "sigma_group": pairing.forecast.sigma_group,
            "provisional": pairing.forecast.provisional,
        },
        "split": {
            "your_side": pairing.split.your_side,
            "their_side": pairing.split.their_side,
            "gap": pairing.split.gap,
        },
        "at_stake": {
            "win_delta": pairing.at_stake.win_delta,
            "loss_delta": pairing.at_stake.loss_delta,
        },
    }


if __name__ == "__main__":
    print(json.dumps(asyncio.run(_the_pairing()), sort_keys=False))
