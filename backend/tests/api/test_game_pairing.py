"""The game's pairing read, end to end over HTTP — ``docs/adr/0161``.

**The game screen draws its court's pairing, and this is the read it draws it
from.** One route answers, for one game and for the person reading it: the
forecast, the split, what is at stake, and each seat's Level — computed when
read, behind a port ``games`` publishes and the matcher answers.

**It answers from the balance forecast directly** (#575). A booked game's court
is already seated, so it is read side against side from the people's Levels —
no search, no candidate index, no interest ledger. Nothing here searches, and
nothing overrides the port: what is exercised is the production wiring.

Seven things are asserted here and nowhere else.

**Only the court may read it, and a stranger is told nothing.** One code for two
cases — no such game, or not your game — because separating them would answer
*is this id real* about four strangers' evening.

**It is read in the reader's direction.** Two readers on opposite sides see the
split's sign flip and the same percentage.

**It is the group deck's number.** The forecast a Games card drew for these
sides is the forecast the game draws once they are booked — same Levels, same
ruleset, one engine function.

**A friendly prices nothing, and says so by omission.** *Meaningless rather than
unavailable*: the forecast is drawn, the stakes are not.

**An unrated seat empties the forecast and keeps the others' Levels.** Omitted,
never provisional — a half-read forecast on a game is exactly the thing #346
argued against.

**It stops the moment the game has happened.** After *we played* the values are
a claim about people made from a stale record, and the route refuses.

**Two processes price the court alike**, whatever their hash seeds.
"""

from __future__ import annotations

import json
import random
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

import pytest
from sqlalchemy import func, select

from app.bootstrap.composition import (
    build_balance_forecasts,
    build_domain_event_store,
    build_event_publisher,
    build_game_repository,
)
from app.kernel import Sport, instant
from app.modules.games.application.commands import VacateSeatCommand
from app.modules.games.application.vacate_seat import VacateSeat
from app.modules.games.domain.lineup import GameKind
from app.modules.matchmaking.infrastructure.search_model import SearchORM
from app.modules.proposals.domain.deck import Sides
from tests.api import players_world as players

#: `backend/`, so a probe is importable exactly as it is under pytest.
ROOT = Path(__file__).resolve().parents[2]


async def _four(client, *, sport: Sport = players.SPORT) -> dict:
    """Four whole players, each rated through a real assessment."""

    return {
        name: await players.a_rated_player(client, name, sport=sport)
        for name in ("me", "partner", "left", "right")
    }


async def _a_booked_game(
    session_factory,
    *,
    side_a: tuple[UUID, ...],
    side_b: tuple[UUID, ...],
    kind: GameKind = GameKind.COUNTED,
    sport: Sport = players.SPORT,
    starts_in: timedelta = timedelta(days=1),
) -> str:
    """A booked game whose hour is ``starts_in`` from now — its id."""

    booked = await players.a_booked_game(
        session_factory,
        side_a=side_a,
        side_b=side_b,
        kind=kind,
        sport=sport,
        starts_at=datetime.now(timezone.utc) + starts_in,
    )
    return str(booked["game_id"])


async def _a_padel_four(session_factory, four: dict, **booked) -> str:
    return await _a_booked_game(
        session_factory,
        side_a=(four["me"]["id"], four["partner"]["id"]),
        side_b=(four["left"]["id"], four["right"]["id"]),
        **booked,
    )


async def _pairing(client, token: str, game_id: str):
    return await client.get(
        f"/api/v1/games/{game_id}/pairing", headers=players.auth(token)
    )


def _without_the_trace(response) -> str:
    """One refusal's body, minus the one field that is per-request — the text
    rather than a parsed dictionary, because key order is part of what a client
    sees."""

    body = json.loads(response.text)
    assert body.pop("trace_id"), "a refusal with no trace is a refusal nobody can chase"
    return json.dumps(body, sort_keys=False)


# ---------------------------------------------------------------------------
# No search behind it
# ---------------------------------------------------------------------------


async def test_the_pairing_answers_with_no_search_in_existence(
    client, session_factory
):
    """**The forecast straight from the Levels** (#575). Nothing in this
    database was ever searched for, and the process holds no candidate index —
    and the game screen still draws its forecast, its split, its stakes and four
    Levels, because the court is read side against side and nothing else."""

    four = await _four(client)
    game_id = await _a_padel_four(session_factory, four)

    response = await _pairing(client, four["me"]["token"], game_id)

    async with session_factory() as session:
        searches = await session.scalar(select(func.count()).select_from(SearchORM))
    assert searches == 0
    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == {"read_at", "seats", "forecast", "split", "at_stake"}
    assert 0 <= body["forecast"]["pct"] <= 100
    assert body["forecast"]["sigma_group"] > 0
    assert len(body["seats"]) == 4


# ---------------------------------------------------------------------------
# Who may read it
# ---------------------------------------------------------------------------


async def test_everybody_on_the_court_reads_the_pairing_and_nobody_else_does(
    client, session_factory
):
    """**The court is the whole of the permission** (``docs/adr/0141``).

    Each member reads it; a stranger and an unknown id are told the same thing,
    byte for byte, because a `404` that differed would answer *is this id real*
    about four strangers' evening.
    """

    four = await _four(client)
    game_id = await _a_padel_four(session_factory, four)
    _, stranger = await players.register(client, "stranger")

    for person in four.values():
        response = await _pairing(client, person["token"], game_id)
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["read_at"]
        assert {seat["player_id"] for seat in body["seats"]} == {
            str(one["id"]) for one in four.values()
        }

    theirs = await _pairing(client, stranger, game_id)
    nothing = await _pairing(client, four["me"]["token"], str(four["me"]["id"]))

    assert theirs.status_code == 404
    assert theirs.json()["code"] == "game_not_found"
    assert nothing.status_code == 404
    assert _without_the_trace(theirs) == _without_the_trace(nothing)


# ---------------------------------------------------------------------------
# What it draws, and in whose direction
# ---------------------------------------------------------------------------


async def test_the_pairing_is_read_in_the_readers_direction(client, session_factory):
    """**`gap` is `your_side − their_side`, and the sign flips across the net.**

    Two readers on opposite sides see the same percentage — a forecast is a
    fact about the game — and mirror-image strengths, because *your side* is
    theirs wherever they sit. The gap is served, not subtracted: it is the
    split's own property, and the client does no arithmetic.
    """

    four = await _four(client)
    game_id = await _a_padel_four(session_factory, four)

    mine = (await _pairing(client, four["me"]["token"], game_id)).json()
    theirs = (await _pairing(client, four["left"]["token"], game_id)).json()
    beside = (await _pairing(client, four["partner"]["token"], game_id)).json()

    split = mine["split"]
    assert split["gap"] == split["your_side"] - split["their_side"]
    assert theirs["split"]["your_side"] == mine["split"]["their_side"]
    assert theirs["split"]["their_side"] == mine["split"]["your_side"]
    assert theirs["split"]["gap"] == -mine["split"]["gap"]
    assert theirs["forecast"]["pct"] == mine["forecast"]["pct"]
    assert beside["split"] == mine["split"]
    assert mine["forecast"]["provisional"] is False
    assert mine["forecast"]["assumption"] is None


async def test_every_rated_seat_carries_the_four_figures_and_nothing_else(
    client, session_factory
):
    """**A seat here is a Level and not a card.** The four fields the record
    and the card already publish, in the court's own order — and none of the
    card's furniture: no area, no photograph, no Player Score, no run of form."""

    four = await _four(client)
    game_id = await _a_padel_four(session_factory, four)

    body = (await _pairing(client, four["me"]["token"], game_id)).json()

    assert [seat["player_id"] for seat in body["seats"]] == [
        str(four[name]["id"]) for name in ("me", "partner", "left", "right")
    ]
    for seat in body["seats"]:
        assert set(seat) == {"player_id", "level", "band", "range", "confidence"}
        assert seat["range"]["low"] <= seat["level"] <= seat["range"]["high"]
        assert 0 <= seat["confidence"] <= 100
        assert seat["band"]


async def test_a_counted_game_prices_what_is_at_stake_for_the_reader(
    client, session_factory
):
    """The rule read forward, side against side: signed, never zero, and the
    same pair for both people on a side — because a result is a statement about
    one pair against another."""

    four = await _four(client)
    game_id = await _a_padel_four(session_factory, four)

    mine = (await _pairing(client, four["me"]["token"], game_id)).json()
    theirs = (await _pairing(client, four["partner"]["token"], game_id)).json()

    assert mine["at_stake"]["win_delta"] > 0 > mine["at_stake"]["loss_delta"]
    assert theirs["at_stake"] == mine["at_stake"]


async def test_the_games_forecast_is_the_group_decks_forecast(
    client, session_factory
):
    """**One engine function, and a test that says so.** The forecast a Games
    card draws for these sides is the forecast the game draws once they are
    booked — the same Levels, the same ruleset — because both read the court
    side against side through the engine's own forecast."""

    four = await _four(client)
    game_id = await _a_padel_four(session_factory, four)
    async with session_factory() as session:
        [on_the_card] = await build_balance_forecasts(session).forecasts(
            [
                Sides(
                    yours=(four["me"]["id"], four["partner"]["id"]),
                    theirs=(four["left"]["id"], four["right"]["id"]),
                )
            ],
            sport=players.SPORT,
        )
    assert on_the_card is not None

    on_the_game = (await _pairing(client, four["me"]["token"], game_id)).json()

    assert on_the_game["forecast"]["pct"] == on_the_card.pct
    assert on_the_game["forecast"]["provisional"] is on_the_card.provisional


# ---------------------------------------------------------------------------
# The three absences
# ---------------------------------------------------------------------------


async def test_a_friendly_draws_the_forecast_and_prices_nothing(
    client, session_factory
):
    """**Meaningless rather than unavailable.** A friendly is a thing people
    chose, and what a counted result would do to a Level is not a question
    about it — so `at_stake` is omitted, not zeroed, while the forecast is
    drawn exactly as on a counted game."""

    four = await _four(client)
    game_id = await _a_padel_four(session_factory, four, kind=GameKind.FRIENDLY)

    body = (await _pairing(client, four["me"]["token"], game_id)).json()

    assert "at_stake" not in body
    assert 0 <= body["forecast"]["pct"] <= 100
    assert "split" in body
    assert len(body["seats"]) == 4


async def test_an_unrated_reader_is_drawn_no_forecast_and_the_others_levels(
    client, session_factory
):
    """**Absent, never provisional, and never a reason.** Somebody on the court
    who holds no rating in the sport leaves nothing to forecast against, so the
    forecast and the split go together and `at_stake` with them — while the
    seats still name the Levels of the people who have one."""

    four = await _four(client)
    unrated_id, unrated = await players.register(client, "unrated")
    await players.commit_profile(client, unrated)
    game_id = await _a_booked_game(
        session_factory,
        side_a=(four["me"]["id"], unrated_id),
        side_b=(four["left"]["id"], four["right"]["id"]),
    )

    response = await _pairing(client, unrated, game_id)

    assert response.status_code == 200, response.text
    body = response.json()
    assert {seat["player_id"] for seat in body["seats"]} == {
        str(four[name]["id"]) for name in ("me", "left", "right")
    }
    assert set(body) == {"read_at", "seats"}


async def test_an_unrated_seat_empties_the_forecast_for_everybody_else_too(
    client, session_factory
):
    """The same absence read from a rated seat: a side short of a Level is not
    read *as if the missing player matched the one beside them* — that is
    honest on a card still filling and a half-read forecast on a game whose
    line-up is booked.

    **The stakes stay**, because they are the rule read forward and the rule
    prices this court: a side is folded over the people on it who hold a
    rating, so a counted result here would move the reader against the one
    rated opponent, and that is the pair drawn.
    """

    four = await _four(client)
    unrated_id, unrated = await players.register(client, "unrated")
    await players.commit_profile(client, unrated)
    game_id = await _a_booked_game(
        session_factory,
        side_a=(four["me"]["id"], four["partner"]["id"]),
        side_b=(four["left"]["id"], unrated_id),
    )

    body = (await _pairing(client, four["me"]["token"], game_id)).json()

    assert set(body) == {"read_at", "seats", "at_stake"}
    assert len(body["seats"]) == 3
    assert body["at_stake"]["win_delta"] > 0 > body["at_stake"]["loss_delta"]


async def test_the_pairing_is_history_once_the_game_has_happened(
    client, session_factory
):
    """**A pairing is a claim about a game that has not happened.** After *we
    played* the route refuses with `409 pairing_is_history` — the values would
    be a claim about people made from a record that has moved on."""

    four = await _four(client)
    game_id = await _a_padel_four(
        session_factory, four, starts_in=-timedelta(hours=2)
    )
    assert (await _pairing(client, four["me"]["token"], game_id)).status_code == 200
    played = await client.post(
        f"/api/v1/games/{game_id}/result",
        json={"score": {"sets": [{"a": 6, "b": 4}, {"a": 6, "b": 3}]}},
        headers=players.auth(four["me"]["token"]),
    )
    assert played.status_code == 200, played.text

    response = await _pairing(client, four["me"]["token"], game_id)

    assert response.status_code == 409
    assert response.json()["code"] == "pairing_is_history"


# ---------------------------------------------------------------------------
# A seat open
# ---------------------------------------------------------------------------


async def _leaves(session_factory, booking_id: UUID, player_id: UUID) -> None:
    """Somebody leaves the booked game — through games' own ``VacateSeat``,
    which is how the booking's *Leave the game* opens the seat (#544)."""

    async with session_factory() as session:
        games = build_game_repository(
            session=session,
            event_store=build_domain_event_store(session),
            events=build_event_publisher(session),
        )
        await VacateSeat(games=games).execute(
            VacateSeatCommand(challenge_id=booking_id, player_id=player_id),
            occurred_at=instant(datetime.now(timezone.utc)),
        )
        await session.commit()


async def test_the_pairing_omits_the_forecast_and_the_stakes_while_a_seat_is_open(
    client, session_factory
):
    """#411 rule 6, and ``docs/adr/0161`` §4's reserved absence: a forecast is a
    claim about a court, and a court with a seat open is not yet the one that
    will play. The seats that are filled still name their Levels, and the
    leaver is told what a stranger is told."""

    four = await _four(client)
    booked = await players.a_booked_game(
        session_factory,
        side_a=(four["me"]["id"], four["partner"]["id"]),
        side_b=(four["left"]["id"], four["right"]["id"]),
    )
    game_id = str(booked["game_id"])
    whole = await _pairing(client, four["me"]["token"], game_id)
    assert whole.status_code == 200, whole.text
    assert "forecast" in whole.json() and "at_stake" in whole.json()

    await _leaves(session_factory, booked["booking_id"], four["right"]["id"])

    reopened = await _pairing(client, four["me"]["token"], game_id)
    assert reopened.status_code == 200, reopened.text
    body = reopened.json()
    assert "forecast" not in body and "split" not in body and "at_stake" not in body
    assert {seat["player_id"] for seat in body["seats"]} == {
        str(four[name]["id"]) for name in ("me", "partner", "left")
    }
    gone = await _pairing(client, four["right"]["token"], game_id)
    assert gone.status_code == 404, gone.text


# ---------------------------------------------------------------------------
# Singles
# ---------------------------------------------------------------------------


async def test_a_singles_court_is_two_seats_and_one_strength_a_side(
    client, session_factory
):
    """`seats_per_side` comes from the sport: a tennis court is two people, the
    split is two player strengths, and the stakes are the pair reading — a side
    of one is one person, and it is not provisional."""

    me = await players.a_rated_player(client, "me", sport=Sport.TENNIS)
    them = await players.a_rated_player(client, "them", sport=Sport.TENNIS)
    game_id = await _a_booked_game(
        session_factory, side_a=(me["id"],), side_b=(them["id"],), sport=Sport.TENNIS
    )

    mine = (await _pairing(client, me["token"], game_id)).json()
    theirs = (await _pairing(client, them["token"], game_id)).json()

    assert len(mine["seats"]) == 2
    assert mine["split"]["gap"] == -theirs["split"]["gap"]
    assert mine["forecast"]["pct"] == theirs["forecast"]["pct"]
    assert mine["forecast"]["provisional"] is False
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
    chose in advance. A game's court is made of sets, and the one place the read
    could hand two workers two answers is a set walked into an order the engine
    then depends on."""

    first_seed, second_seed = random.sample(range(1, 4294967295), 2)

    first = _run_under(first_seed)
    second = _run_under(second_seed)

    assert first == second, (
        f"two processes disagreed at seeds {first_seed} and {second_seed}"
    )


def test_the_probe_actually_priced_a_court():
    """The guard on the guard: two empty answers are byte-identical too."""

    answer = json.loads(_run_under(1))

    assert len(answer["seats"]) == 4
    assert 0 <= answer["forecast"]["pct"] <= 100
    split = answer["split"]
    assert split["your_side"] - split["their_side"] == pytest.approx(
        split["gap"]
    )
    assert answer["at_stake"]["win_delta"] > 0 > answer["at_stake"]["loss_delta"]
