"""Player reliability made the honest way — out of games on the record (#661).

A figure is folded from history, never set: these games are written through the
Game aggregate, each ``days`` before **Monday 5 October 2026, 08:00 in Kraków**,
the clock the proposals worlds stand on, so every one is final by then.
"""

from __future__ import annotations

from datetime import timedelta
from uuid import UUID

from app.bootstrap.composition import (
    build_domain_event_store,
    build_event_publisher,
    build_game_repository,
)
from app.kernel import Sport, instant
from app.modules.games.domain.attendance import ClubVerdict
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.games.domain.results import Score, SetScore
from app.shared.ids import new_uuid
from tests.api.proposals_world import MONDAY_MORNING

PLAYED, MISSED = "played", "missed"
#: Two evenings she never came to, then three games played through: 100 → 75 →
#: 50 → 55 → 60 → 65. **Medium**, and not New.
SERGIO_AT_65 = ((MISSED, 12), (MISSED, 11), (PLAYED, 8), (PLAYED, 7), (PLAYED, 6))
#: Three played through, then one evening missed: **75 · High**, not New.
AT_75 = ((PLAYED, 20), (PLAYED, 19), (PLAYED, 18), (MISSED, 10))
#: Two evenings missed and nothing played through yet: 50, and **New**.
NEW_AT_50 = ((MISSED, 12), (MISSED, 11))
#: Four evenings missed, then three played through: **15 · Low**, not New.
LOW_AT_15 = (
    (MISSED, 14),
    (MISSED, 13),
    (MISSED, 12),
    (MISSED, 11),
    (PLAYED, 8),
    (PLAYED, 7),
    (PLAYED, 6),
)


async def a_history(session_factory, player_id: UUID, history) -> None:
    """Games on the record, each ``days`` before the clock: *played* a singles
    game whose score settled by silence, or *missed* — a courtmate at the club
    tapped *isn't here yet* ten minutes in and they never came (#657). What the
    figure is folded from, written through the Game aggregate."""

    for happened, days in history:
        starts = instant(MONDAY_MORNING - timedelta(days=days))
        other = new_uuid()
        game = Game.planned(
            game_id=new_uuid(),
            challenge_id=new_uuid(),
            sport=Sport.PADEL,
            kind=GameKind.COUNTED,
            window=None,
            line_up=LineUp.of(
                (
                    Seating(side=GameSide.A, player_id=player_id),
                    Seating(side=GameSide.B, player_id=other),
                )
            ),
            occurred_at=instant(starts - timedelta(days=2)),
            starts_at=starts,
        )
        if happened == MISSED:
            game.note_absent(
                by=other,
                absent=player_id,
                where=ClubVerdict(at_the_club=True, club_name=None),
                occurred_at=instant(starts + timedelta(minutes=10)),
            )
        else:
            game.state_result(
                by=player_id,
                score=Score.of([SetScore(a=6, b=4), SetScore(a=6, b=3)]),
                occurred_at=instant(starts + timedelta(hours=1)),
            )
        async with session_factory() as session:
            await build_game_repository(
                session=session,
                event_store=build_domain_event_store(session),
                events=build_event_publisher(session),
            ).save(game)
            await session.commit()
