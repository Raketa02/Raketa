"""The ranking's test world: games played and settled through the player
routes, Levels moved through the rating's own aggregate, and the two reads
(#768, #769).

``plays`` is the honest path — a booked game, its score stated and answered
through the player routes, the outbox delivered as the worker delivers it.
``moves_to`` is for a test that needs an exact Level: the rating's own
``move_on_result`` records the same ``rating.moved_on_result`` a settled game
does, on the same outbox, because no route takes dictation for a chosen Level.
"""

from __future__ import annotations

from datetime import timedelta
from uuid import UUID

from sqlalchemy import select

from app.bootstrap.composition import (
    build_domain_event_store,
    build_event_publisher,
    build_settle_ratings_on_results,
    build_skill_rating_repository,
)
from app.engines.assessment import BandView
from app.engines.racketskill.core import SkillEstimate
from app.engines.racketskill.update_v1 import MovedRating, Stakes
from app.kernel import Instant, Sport, instant
from app.modules.games.domain.lineup import GameKind
from app.modules.rankings.infrastructure.ranking_model import (
    LevelPointORM,
    RankingRowORM,
)
from app.shared.ids import new_uuid
from tests.api import players_world as players
from tests.api.players_world import deliver_the_outbox

WINS = {"score": {"sets": [{"a": 6, "b": 4}, {"a": 6, "b": 3}]}}
LOSES = {"score": {"sets": [{"a": 4, "b": 6}, {"a": 3, "b": 6}]}}


async def ranking(client, player: dict, sport: str = "PADEL", **params) -> dict:
    read = await client.get(
        f"/api/v1/rankings/{sport}",
        params=params,
        headers=players.auth(player["token"]),
    )
    assert read.status_code == 200, read.text
    return read.json()


async def home_ranking(client, player: dict) -> dict | None:
    read = await client.get("/api/v1/home", headers=players.auth(player["token"]))
    assert read.status_code == 200, read.text
    return read.json()["ranking"]


async def plays(
    client,
    session_factory,
    clock,
    winners: tuple[dict, ...],
    losers: tuple[dict, ...],
    *,
    kind: GameKind = GameKind.COUNTED,
    sport: Sport = Sport.PADEL,
    ending: str = "agreed",
) -> None:
    """One booked game that ended an hour ago: the winners' side states the
    score, and the losers' side accepts it (``agreed``), counters it
    (``disputed``), or nobody says anything (``unrecorded``). Then the outbox
    is delivered and the clock moves on an hour."""

    starts = instant(clock.now() - timedelta(hours=2))
    booked = await players.a_booked_game(
        session_factory,
        side_a=tuple(player["id"] for player in winners),
        side_b=tuple(player["id"] for player in losers),
        sport=sport,
        kind=kind,
        starts_at=starts,
        booked_at=instant(starts - timedelta(days=2)),
    )
    game = f"/api/v1/games/{booked['game_id']}/result"
    if ending != "unrecorded":
        stated = await client.post(
            game, json=WINS, headers=players.auth(winners[0]["token"])
        )
        assert stated.status_code == 200, stated.text
    # A for-fun score is settled by its statement: nobody is asked to agree.
    if ending == "agreed" and kind is GameKind.COUNTED:
        accepted = await client.post(
            f"{game}/acceptance", headers=players.auth(losers[0]["token"])
        )
        assert accepted.status_code == 200, accepted.text
    if ending == "disputed":
        countered = await client.post(
            game, json=LOSES, headers=players.auth(losers[0]["token"])
        )
        assert countered.status_code == 200, countered.text
    await deliver_the_outbox(session_factory)
    clock.move(timedelta(hours=1))


async def the_catch_up_runs(session_factory, clock) -> None:
    async with session_factory() as session:
        await build_settle_ratings_on_results(session, clock=clock).execute()
    await deliver_the_outbox(session_factory)


async def move_on(
    session,
    player_id: UUID,
    mu: float,
    *,
    at: Instant,
    won: bool = True,
    sport: Sport = Sport.PADEL,
    sigma: float = 0.3,
) -> UUID:
    """One result moving the player's Level to ``mu`` and its uncertainty to
    ``sigma`` — every other figure a fixed one — recorded by the rating's own
    aggregate and committed. Its game."""

    ratings = build_skill_rating_repository(
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )
    rating = await ratings.find_for(player_id=player_id, sport=sport)
    assert rating is not None
    game_id = new_uuid()
    rating.move_on_result(
        game_id=game_id,
        moved=MovedRating(
            mu=mu,
            sigma=sigma,
            confidence=60,
            range_low=round(mu - sigma, 2),
            range_high=round(mu + sigma, 2),
            band=BandView(name="Improver", lower=2.5, upper=3.0),
            status="DEVELOPING",
            stakes=Stakes(win=0.03, loss=-0.03),
        ),
        won=won,
        opposition=SkillEstimate(mu=mu, sigma=0.3),
        information_share=0.5,
        occurred_at=at,
    )
    await ratings.save(rating)
    await session.commit()
    return game_id


async def moves_to(
    session_factory,
    player: dict,
    mu: float,
    *,
    at: Instant,
    won: bool = True,
    sport: Sport = Sport.PADEL,
    sigma: float = 0.3,
) -> None:
    """:func:`move_on`, then the outbox delivered — the move folded into the
    player's row."""

    async with session_factory() as session:
        await move_on(
            session, player["id"], mu, at=at, won=won, sport=sport, sigma=sigma
        )
    await deliver_the_outbox(session_factory)


async def stored_rows(session_factory) -> list[tuple]:
    """Every ranking row, every column — what a write twice, or a rebuild that
    disagreed with live delivery, would show in."""

    async with session_factory() as session:
        rows = await session.scalars(
            select(RankingRowORM).order_by(RankingRowORM.player_id, RankingRowORM.sport)
        )
        return [
            (
                row.player_id,
                row.sport,
                row.hundredths,
                row.sigma,
                row.results,
                row.last_result_at,
                row.level_reached_at,
                row.general_entered_at,
                row.friends_entered_at,
                row.form,
            )
            for row in rows.all()
        ]


async def stored_points(session_factory) -> list[tuple]:
    """Every level-history point, every column."""

    async with session_factory() as session:
        points = await session.scalars(
            select(LevelPointORM).order_by(LevelPointORM.event_id)
        )
        return [
            (
                point.event_id,
                point.player_id,
                point.sport,
                point.at,
                point.hundredths,
                point.results,
                point.level_reached_at,
            )
            for point in points.all()
        ]


def chips(read: dict) -> dict[str, dict]:
    """Each row's chip, by nickname — what the list draws beside each Level."""

    return {row["nickname"]: row["chip"] for row in read["rows"]}


async def results_at(session_factory, player: dict, levels: list[float], clock) -> None:
    """A run of results, an hour apart, ending at each of ``levels``."""

    for mu in levels:
        await moves_to(session_factory, player, mu, at=instant(clock.now()))
        clock.move(timedelta(hours=1))


async def a_listed_crowd(
    client, session_factory, clock, count: int, *, top: float = 6.0
) -> list[dict]:
    """``count`` players listed in padel, best first and a hundredth apart:
    each filed on the log at their own Level, then five results there settled
    eight days ago — so nobody is *New* — and the outbox delivered once. Their
    ids, tokens and nicknames, in place order."""

    crowd = []
    for n in range(count):
        name = f"crowd{n:03d}"
        player_id, token = await players.a_player_on_the_log(
            client, session_factory, name, mu=round(top - n / 100, 2)
        )
        crowd.append({"id": player_id, "token": token, "nickname": name})
    settled = instant(clock.now() - timedelta(days=8))
    async with session_factory() as session:
        for n, player in enumerate(crowd):
            for result in range(5):
                await move_on(
                    session,
                    player["id"],
                    round(top - n / 100, 2),
                    at=instant(settled + timedelta(minutes=result)),
                )
    await deliver_the_outbox(session_factory, rounds=count)
    return crowd


async def general_rows(client, player: dict, sport: str = "PADEL", **params) -> dict:
    read = await client.get(
        f"/api/v1/rankings/{sport}/general/rows",
        params=params,
        headers=players.auth(player["token"]),
    )
    assert read.status_code == 200, read.text
    return read.json()


def places(read: dict) -> list[int]:
    return [row["place"] for row in read["rows"]]


async def level_of(client, player: dict) -> float:
    read = await client.get(
        "/api/v1/players/me/record",
        params={"sport": "PADEL"},
        headers=players.auth(player["token"]),
    )
    assert read.status_code == 200, read.text
    return read.json()["skill"]["level"]
