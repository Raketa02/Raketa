"""One game's pairing, computed from fixed inputs, printed as JSON.

Run under two ``PYTHONHASHSEED``s by ``test_game_pairing.py``, because the one
place the pairing read could hand two processes two answers to one question is
a set walked into an order (``docs/adr/0105``) — and a game's court is made of
sets: ``LineUp.players_on`` is a ``frozenset``, and the partner and the
opponents the engine is handed have to come out of it in one order everywhere.

**Below the routes, with fixed ids, on purpose.** The whole HTTP flow cannot be
compared across two processes: every player id is minted at random, ties break
on it, and two runs would disagree for a reason that has nothing to do with
hash seeds. So the probe walks the pure path the adapter takes — the sides off
the line-up, the court arranged and priced by the engine, the stakes priced
side against side by the rule — over ids that are the same in both processes.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import asdict
from typing import Collection, Mapping
from uuid import UUID

from app.bootstrap.composition import build_ruleset
from app.engines.racketskill.core import SkillEstimate
from app.kernel import Sport
from app.modules.games.domain.lineup import GameSide, LineUp, Seating
from app.modules.matchmaking.application.pair_with_a_court import arrange_the_court
from app.modules.matchmaking.infrastructure.games_court_pairing import sides_of
from app.modules.matchmaking.infrastructure.rating_at_stake import (
    RatingResultUpdateRule,
)
from app.modules.rating.domain.ports import RatedSport
from tests.unit.matchfit_builders import searcher, seated

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
    """``RatedPlayerQuery`` over a dict — the engine's currency and nothing read."""

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
        return {}


async def _the_pairing() -> dict:
    line_up = LineUp.of(
        (
            Seating(side=GameSide.A, player_id=READER),
            Seating(side=GameSide.A, player_id=PARTNER),
            Seating(side=GameSide.B, player_id=LEFT),
            Seating(side=GameSide.B, player_id=RIGHT),
        )
    )
    partners, opponents = sides_of(line_up, READER)
    court = {
        one: seated(player_id=str(one), mu=LEVELS[one][0], sigma=LEVELS[one][1])
        for one in (*partners, *opponents)
    }
    arranged = arrange_the_court(
        searcher(mu=LEVELS[READER][0], sigma=LEVELS[READER][1]),
        court,
        partners=frozenset(partners),
        sport=Sport.PADEL,
        ruleset=build_ruleset(),
    )
    assert arranged is not None
    at_stake = await RatingResultUpdateRule(_Ratings()).counted_game_deltas_on_court(
        player_id=READER,
        own_side=[READER, *partners],
        opposing_side=opponents,
        sport=Sport.PADEL,
    )
    assert at_stake is not None
    return {
        "partners": [str(one) for one in partners],
        "opponents": [str(one) for one in opponents],
        "forecast": {
            "pct": arranged.forecast.pct,
            "sigma_group": arranged.forecast.sigma_group,
            "provisional": arranged.forecast.provisional,
        },
        "split": {
            "your_side": arranged.split.your_side,
            "their_side": arranged.split.their_side,
            "gap": arranged.split.gap,
        },
        "at_stake": asdict(at_stake),
    }


if __name__ == "__main__":
    print(json.dumps(asyncio.run(_the_pairing()), sort_keys=False))
