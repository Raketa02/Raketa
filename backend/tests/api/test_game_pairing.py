"""The game's pairing read, end to end over HTTP — ``docs/adr/0161``.

**The game screen draws its court's pairing, and this is the read it draws it
from.** One route answers, for one game and for the person reading it: the
forecast, the split, what is at stake, and each seat's Level — computed when
read, behind a port ``games`` publishes and the matcher answers, fail-closed.

Six things are asserted here and nowhere else.

**Only the court may read it, and a stranger is told nothing.** One code for two
cases — no such game, or not your game — because separating them would answer
*is this id real* about four strangers' evening.

**It is read in the reader's direction.** Two readers on opposite sides see the
split's sign flip and the same percentage.

**It is the challenge card's number.** The forecast the challenge screen drew
while the court was being arranged is the forecast the game draws once the
line-up completes — same people, same ruleset, one apparatus.

**A friendly prices nothing, and says so by omission.** *Meaningless rather than
unavailable*: the forecast is drawn, the stakes are not.

**An unrated seat empties the forecast and keeps the others' Levels.** Omitted,
never provisional — a half-read forecast on a game is exactly the thing #346
argued against.

**It stops the moment the game has happened.** After *we played* the values are
a claim about people made from a stale record, and the route refuses.
"""

from __future__ import annotations

import json
import random
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.api.dependencies import (
    ClockDep,
    DbSession,
    DomainEventStoreDep,
    EventPublisherDep,
    SettingsDep,
    UnitOfWorkDep,
)
from app.bootstrap.composition import (
    build_domain_event_store,
    build_event_publisher,
    build_game_court_pairing_over,
    build_game_repository,
)
from app.kernel import Sport, instant
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.games.presentation.dependencies import get_court_pairing
from app.modules.player_profile.domain.availability import Window
from app.shared.ids import new_uuid
from tests.api import matchmaking_world as world

#: `backend/`, so a probe is importable exactly as it is under pytest.
ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
async def searcher(client):
    return await world.a_searcher(client)


def draw_real_pairings(client, candidate_source, exposure_ledger) -> None:
    """Wire the **real** port over this test's own index and ledger.

    ``world.draw_real_cards``'s shape, one context over: the production
    declaration reaches for the process's index and the Redis pool, neither of
    which exists under ``ASGITransport``, and that default is the right one for
    the outage test below and the wrong one for every test about a number
    actually being drawn.
    """

    def _pairings(
        db: DbSession,
        clock: ClockDep,
        uow: UnitOfWorkDep,
        event_store: DomainEventStoreDep,
        events: EventPublisherDep,
        settings: SettingsDep,
    ):
        return build_game_court_pairing_over(
            session=db,
            workbench=world.a_real_workbench(
                db,
                clock,
                uow,
                event_store,
                events,
                settings,
                exposure_ledger=exposure_ledger,
                candidate_source=candidate_source,
            ),
        )

    world.override(client, get_court_pairing, _pairings)


async def _a_city(
    client, session_factory, candidate_source, mu: float, *, sport: Sport = world.SPORT
) -> dict:
    """Three other players, each a **whole** player with a token of their own.

    Through the routes, because the pairing is computed **for** a reader and
    ``searcher_facts`` reads a profile, a rating and a declaration live from the
    aggregates — and everything under test here is something only somebody on
    the court can do.
    """

    people = {}
    for name in ("ana", "bo", "cy"):
        person = await world.a_searcher(client, name, sport=sport)
        people[name] = {"id": person["id"], "token": person["token"]}
    await world.fold_the_log(session_factory, candidate_source)
    return people


async def _a_sent_challenge(
    client, searcher, *, mode: str = "COMPETITIVE", sport: Sport = world.SPORT
) -> tuple[str, list[dict]]:
    response = await world.lineup(client, searcher["token"], mode, sport)
    assert response.status_code == 200, response.text
    body = response.json()
    court = [
        {
            "side": seat["side"],
            "player_id": seat.get("player_id", str(searcher["id"])),
        }
        for seat in body["lineup"]["seats"]
    ]
    sent = await client.post(
        "/api/v1/challenges",
        json={"search_id": body["search"]["search_id"], "court": court},
        headers=world.auth(searcher["token"]),
    )
    assert sent.status_code == 201, sent.text
    return sent.json()["challenge_id"], court


async def _accepts(client, challenge_id: str, *people: dict) -> None:
    for person in people:
        answered = await client.post(
            f"/api/v1/challenges/{challenge_id}/accept",
            headers=world.auth(person["token"]),
        )
        assert answered.status_code == 200, answered.text


async def _the_game(client, token: str) -> dict:
    response = await client.get("/api/v1/games", headers=world.auth(token))
    assert response.status_code == 200, response.text
    (game,) = response.json()["games"]
    return game


async def _pairing(client, token: str, game_id: str):
    return await client.get(
        f"/api/v1/games/{game_id}/pairing", headers=world.auth(token)
    )


async def _an_arranged_game(
    client, session_factory, candidate_source, searcher, *, mode: str = "COMPETITIVE"
) -> tuple[dict, dict, list[dict]]:
    """A padel four: the searcher's court, sent, and accepted by everybody."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id, court = await _a_sent_challenge(client, searcher, mode=mode)
    await _accepts(client, challenge_id, *people.values())
    game = await _the_game(client, searcher["token"])
    assert game["standing"] == "AWAITING_ENTRY"
    return people, game, court


async def _a_game_opened_on(
    session_factory, *, side_a: tuple, side_b: tuple, sport: Sport = world.SPORT
) -> str:
    """A game whose court was never sent as a challenge, opened through the
    aggregate — the one way to seat somebody the matcher would never have
    found, which is what *a court with an unrated member* needs. Written through
    the aggregate rather than as rows, on every suite's rule about somebody
    else's context."""

    game = Game.planned(
        game_id=new_uuid(),
        challenge_id=new_uuid(),
        sport=sport,
        kind=GameKind.COUNTED,
        window=Window.TODAY,
        line_up=LineUp.of(
            (
                *(Seating(side=GameSide.A, player_id=one) for one in side_a),
                *(Seating(side=GameSide.B, player_id=one) for one in side_b),
            )
        ),
        occurred_at=instant(datetime.now(timezone.utc)),
    )
    async with session_factory() as session:
        await build_game_repository(
            session=session,
            event_store=build_domain_event_store(session),
            events=build_event_publisher(session),
        ).save(game)
        await session.commit()
    return str(game.id)


def _side_of(court: list[dict], player_id) -> str:
    return next(seat["side"] for seat in court if seat["player_id"] == str(player_id))


def _without_the_trace(response) -> str:
    """One refusal's body, minus the one field that is per-request — the text
    rather than a parsed dictionary, because key order is part of what a client
    sees."""

    body = json.loads(response.text)
    assert body.pop("trace_id"), "a refusal with no trace is a refusal nobody can chase"
    return json.dumps(body, sort_keys=False)


# ---------------------------------------------------------------------------
# Who may read it
# ---------------------------------------------------------------------------


async def test_everybody_on_the_court_reads_the_pairing_and_nobody_else_does(
    client, session_factory, candidate_source, exposure_ledger, searcher
):
    """**The court is the whole of the permission** (``docs/adr/0141``).

    Each member reads it; a stranger and an unknown id are told the same thing,
    byte for byte, because a `404` that differed would answer *is this id real*
    about four strangers' evening.
    """

    draw_real_pairings(client, candidate_source, exposure_ledger)
    people, game, _ = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )
    _, stranger = await world.register(client, "stranger")

    for token in [searcher["token"]] + [one["token"] for one in people.values()]:
        response = await _pairing(client, token, game["game_id"])
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["read_at"]
        assert {seat["player_id"] for seat in body["seats"]} == {
            str(searcher["id"]),
            *(str(one["id"]) for one in people.values()),
        }

    theirs = await _pairing(client, stranger, game["game_id"])
    nothing = await _pairing(client, searcher["token"], str(searcher["id"]))

    assert theirs.status_code == 404
    assert theirs.json()["code"] == "game_not_found"
    assert nothing.status_code == 404
    assert _without_the_trace(theirs) == _without_the_trace(nothing)


# ---------------------------------------------------------------------------
# What it draws, and in whose direction
# ---------------------------------------------------------------------------


async def test_the_pairing_is_read_in_the_readers_direction(
    client, session_factory, candidate_source, exposure_ledger, searcher
):
    """**`gap` is `your_side − their_side`, and the sign flips across the net.**

    Two readers on opposite sides see the same percentage — a forecast is a
    fact about the game — and mirror-image strengths, because *your side* is
    theirs wherever they sit. The gap is served, not subtracted: it is the
    split's own property, and the client does no arithmetic.
    """

    draw_real_pairings(client, candidate_source, exposure_ledger)
    people, game, court = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )
    mine_side = _side_of(court, searcher["id"])
    across = next(
        one for one in people.values() if _side_of(court, one["id"]) != mine_side
    )

    mine = (await _pairing(client, searcher["token"], game["game_id"])).json()
    theirs = (await _pairing(client, across["token"], game["game_id"])).json()

    split = mine["split"]
    assert split["gap"] == split["your_side"] - split["their_side"]
    assert theirs["split"]["your_side"] == mine["split"]["their_side"]
    assert theirs["split"]["their_side"] == mine["split"]["your_side"]
    assert theirs["split"]["gap"] == -mine["split"]["gap"]
    assert theirs["forecast"]["pct"] == mine["forecast"]["pct"]
    assert mine["forecast"]["provisional"] is False
    assert mine["forecast"]["assumption"] is None


async def test_every_rated_seat_carries_the_four_figures_and_nothing_else(
    client, session_factory, candidate_source, exposure_ledger, searcher
):
    """**A seat here is a Level and not a card.** The four fields the record
    and the card already publish, in the court's own order — and none of the
    card's furniture: no area, no photograph, no Player Score, no run of form."""

    draw_real_pairings(client, candidate_source, exposure_ledger)
    people, game, court = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )

    body = (await _pairing(client, searcher["token"], game["game_id"])).json()

    assert [seat["player_id"] for seat in body["seats"]] == [
        seat["player_id"] for seat in game["seats"]
    ]
    for seat in body["seats"]:
        assert set(seat) == {"player_id", "level", "band", "range", "confidence"}
        assert seat["range"]["low"] <= seat["level"] <= seat["range"]["high"]
        assert 0 <= seat["confidence"] <= 100
        assert seat["band"]


async def test_a_counted_game_prices_what_is_at_stake_for_the_reader(
    client, session_factory, candidate_source, exposure_ledger, searcher
):
    """The rule read forward, side against side: signed, never zero, and the
    same pair for both people on a side — because a result is a statement about
    one pair against another."""

    draw_real_pairings(client, candidate_source, exposure_ledger)
    people, game, court = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )
    mine_side = _side_of(court, searcher["id"])
    partner = next(
        one for one in people.values() if _side_of(court, one["id"]) == mine_side
    )

    mine = (await _pairing(client, searcher["token"], game["game_id"])).json()
    theirs = (await _pairing(client, partner["token"], game["game_id"])).json()

    assert mine["at_stake"]["win_delta"] > 0 > mine["at_stake"]["loss_delta"]
    assert theirs["at_stake"] == mine["at_stake"]


async def test_the_games_forecast_is_the_challenge_cards_forecast(
    client, session_factory, candidate_source, exposure_ledger, searcher
):
    """**One apparatus, and a test that says so.** The forecast the challenge
    screen drew while the court was being arranged is the forecast the game
    draws once the line-up completes — same people, same ruleset — because the
    game's read goes through the challenge card's own use case rather than a
    second one."""

    world.draw_real_cards(client, candidate_source, exposure_ledger)
    draw_real_pairings(client, candidate_source, exposure_ledger)
    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id, _ = await _a_sent_challenge(client, searcher)
    ana = people["ana"]

    while_arranging = await client.get(
        f"/api/v1/challenges/{challenge_id}", headers=world.auth(ana["token"])
    )
    assert while_arranging.status_code == 200, while_arranging.text
    on_the_card = next(
        seat["card"]["pairing"]["forecast"]
        for seat in while_arranging.json()["seats"]
        if "card" in seat
    )
    await _accepts(client, challenge_id, *people.values())
    game = await _the_game(client, ana["token"])

    on_the_game = (await _pairing(client, ana["token"], game["game_id"])).json()

    assert on_the_game["forecast"] == on_the_card


# ---------------------------------------------------------------------------
# The three absences
# ---------------------------------------------------------------------------


async def test_a_friendly_draws_the_forecast_and_prices_nothing(
    client, session_factory, candidate_source, exposure_ledger, searcher
):
    """**Meaningless rather than unavailable.** A friendly is a thing people
    chose, and what a counted result would do to a Level is not a question
    about it — so `at_stake` is omitted, not zeroed, while the forecast is
    drawn exactly as on a counted game."""

    draw_real_pairings(client, candidate_source, exposure_ledger)
    people, game, _ = await _an_arranged_game(
        client, session_factory, candidate_source, searcher, mode="FOR_FUN"
    )
    assert game["kind"] == "FRIENDLY"

    body = (await _pairing(client, searcher["token"], game["game_id"])).json()

    assert "at_stake" not in body
    assert 0 <= body["forecast"]["pct"] <= 100
    assert "split" in body
    assert len(body["seats"]) == 4


async def test_an_unrated_reader_is_drawn_no_forecast_and_the_others_levels(
    client, session_factory, candidate_source, exposure_ledger, searcher
):
    """**Absent, never provisional, and never a reason.** Somebody on the court
    who holds no rating in the sport leaves nothing to forecast against, so the
    forecast and the split go together and `at_stake` with them — while the
    seats still name the Levels of the people who have one.

    The unrated person is the **reader** here, which is the case that reaches
    *nothing to compute* in the matcher's own words: a pairing is computed
    **for** somebody, and this somebody has nothing to compute against.
    """

    draw_real_pairings(client, candidate_source, exposure_ledger)
    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    unrated_id, unrated = await world.register(client, "unrated")
    await world.commit_profile(client, unrated)
    game_id = await _a_game_opened_on(
        session_factory,
        side_a=(searcher["id"], unrated_id),
        side_b=(people["bo"]["id"], people["cy"]["id"]),
    )

    response = await _pairing(client, unrated, game_id)

    assert response.status_code == 200, response.text
    body = response.json()
    assert {seat["player_id"] for seat in body["seats"]} == {
        str(searcher["id"]),
        str(people["bo"]["id"]),
        str(people["cy"]["id"]),
    }
    assert set(body) == {"read_at", "seats"}


async def test_an_unrated_seat_empties_the_forecast_for_everybody_else_too(
    client, session_factory, candidate_source, exposure_ledger, searcher
):
    """The same absence read from a rated seat: a side short of a Level is not
    read *as if the missing player matched the one beside them* — that is
    honest on a court still filling and a half-read forecast on a game whose
    line-up is frozen.

    **The stakes stay**, because they are the rule read forward and the rule
    prices this court: a side is folded over the people on it who hold a
    rating, so a counted result here would move the reader against the one
    rated opponent, and that is the pair drawn.
    """

    draw_real_pairings(client, candidate_source, exposure_ledger)
    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    unrated_id, unrated = await world.register(client, "unrated")
    await world.commit_profile(client, unrated)
    game_id = await _a_game_opened_on(
        session_factory,
        side_a=(searcher["id"], people["bo"]["id"]),
        side_b=(people["cy"]["id"], unrated_id),
    )

    body = (await _pairing(client, searcher["token"], game_id)).json()

    assert set(body) == {"read_at", "seats", "at_stake"}
    assert len(body["seats"]) == 3
    assert body["at_stake"]["win_delta"] > 0 > body["at_stake"]["loss_delta"]


async def test_the_pairing_is_history_once_the_game_has_happened(
    client, session_factory, candidate_source, exposure_ledger, searcher
):
    """**A pairing is a claim about a game that has not happened.** After *we
    played* the route refuses with `409 pairing_is_history` — the values would
    be a claim about people made from a record that has moved on."""

    draw_real_pairings(client, candidate_source, exposure_ledger)
    people, game, _ = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )
    played = await client.post(
        f"/api/v1/games/{game['game_id']}/result",
        json={"score": {"sets": [{"a": 6, "b": 4}, {"a": 6, "b": 3}]}},
        headers=world.auth(searcher["token"]),
    )
    assert played.status_code == 200, played.text

    response = await _pairing(client, searcher["token"], game["game_id"])

    assert response.status_code == 409
    assert response.json()["code"] == "pairing_is_history"


async def test_a_matcher_this_process_cannot_reach_costs_the_forecast_and_nothing_else(
    client, session_factory, candidate_source, searcher
):
    """**The production wiring, exercised.** Nothing overrides the port here.

    Under ``ASGITransport`` there is no index on the application's state, which
    is exactly the shape of an outage — and the promise is that it costs the
    forecast and never the screen. **Two providers, and each fails on its
    own**: the seats' Levels and the stakes are the rating context's and are
    drawn whatever the matcher's state, so an index that is down does not
    unname four people. What is absent is absent the way an unrated court's
    forecast is, by decision: the screen says nothing about whose gap it is.
    """

    people, game, _ = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )

    response = await _pairing(client, searcher["token"], game["game_id"])

    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == {"read_at", "seats", "at_stake"}
    assert len(body["seats"]) == 4
    assert body["at_stake"]["win_delta"] > 0 > body["at_stake"]["loss_delta"]


# ---------------------------------------------------------------------------
# Singles
# ---------------------------------------------------------------------------


async def test_a_singles_court_is_two_seats_and_one_strength_a_side(
    client, session_factory, candidate_source, exposure_ledger
):
    """`seats_per_side` comes from the sport: a tennis court is two people, the
    split is two player strengths, and the stakes are the pair reading — a side
    of one is one person."""

    draw_real_pairings(client, candidate_source, exposure_ledger)
    me = await world.a_searcher(client, "me", sport=Sport.TENNIS)
    them = await world.a_searcher(client, "them", sport=Sport.TENNIS)
    await world.fold_the_log(session_factory, candidate_source)
    challenge_id, court = await _a_sent_challenge(client, me, sport=Sport.TENNIS)
    assert len(court) == 2
    await _accepts(client, challenge_id, them)
    game = await _the_game(client, me["token"])

    mine = (await _pairing(client, me["token"], game["game_id"])).json()
    theirs = (await _pairing(client, them["token"], game["game_id"])).json()

    assert len(mine["seats"]) == 2
    assert mine["split"]["gap"] == -theirs["split"]["gap"]
    assert mine["forecast"]["pct"] == theirs["forecast"]["pct"]
    assert mine["at_stake"]["win_delta"] > 0 > mine["at_stake"]["loss_delta"]


# ---------------------------------------------------------------------------
# Two processes, two hash seeds, one answer — ``docs/adr/0105``
# ---------------------------------------------------------------------------

PROBE = "tests.api.game_pairing_probe"


def _run_under(seed: int) -> str:
    finished = subprocess.run(
        [sys.executable, "-m", PROBE],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env={
            "PATH": "/usr/bin:/bin",
            "PYTHONHASHSEED": str(seed),
            "PYTHONPATH": str(ROOT),
            "APP_ENV": "local",
            "JWT_SECRET_KEY": "probe-secret-do-not-use-in-prod",
            "WRITER_DB_URL": "sqlite+aiosqlite:///:memory:",
            "DB_SSL_MODE": "disable",
        },
    )
    assert finished.returncode == 0, finished.stderr
    return finished.stdout


def test_two_processes_with_different_hash_seeds_price_the_court_alike():
    """**The same court, the same reader, byte for byte**, under two seeds nobody
    chose in advance — as the ruleset gate does. A game's court is made of sets,
    and the one place the read could hand two workers two answers is a set
    walked into an order the engine then depends on."""

    first_seed, second_seed = random.sample(range(1, 4294967295), 2)

    first = _run_under(first_seed)
    second = _run_under(second_seed)

    assert first == second, (
        f"two processes disagreed at seeds {first_seed} and {second_seed}"
    )


def test_the_probe_actually_priced_a_court():
    """The guard on the guard: two empty answers are byte-identical too."""

    answer = json.loads(_run_under(1))

    assert answer["partners"] and len(answer["opponents"]) == 2
    assert 0 <= answer["forecast"]["pct"] <= 100
    split = answer["split"]
    assert split["gap"] == split["your_side"] - split["their_side"]
    assert answer["at_stake"]["win_delta"] > 0 > answer["at_stake"]["loss_delta"]
