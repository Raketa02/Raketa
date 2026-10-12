"""A score is asked once, and settled by one tap or by silence (#654;
``docs/adr/0195`` §5) — read from outside.

Marta's padel game with Kuba, Zofia and Marek at Bonarka Arena, Saturday 10 Oct
17:00–18:00, booked by the four yeses. The clock starts on Monday 5 October,
08:00 in Kraków, and moves.

Every claim is read where a player reads it: the game (``GET /games``), Home,
and the Level on their record. A result an agreement settled moves the Levels
from the outbox; a result a window closing settled, from the catch-up — each run
the way the worker and the job run them.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from app.api.dependencies import get_clock
from app.bootstrap.composition import build_settle_ratings_on_results
from app.engines.matchfit.core import SearchMode
from tests.api.console_world import SeedWorld, a_seed_world, home_of
from tests.api.players_world import deliver_the_outbox
from tests.api.proposals_world import (
    MONDAY_MORNING,
    SATURDAY_FIVE,
    makes,
    says_yes,
)
from tests.unit.fake_clock import MovableClock

#: 18:05 on Saturday — the hour over, Marta puts the score up.
STATED = SATURDAY_FIVE + timedelta(hours=1, minutes=5)


@pytest.fixture
def clock(app, payments):
    """Monday 5 October 2026, 08:00 in Kraków."""

    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    payments.clock = fixed
    return fixed


@pytest.fixture
async def world(client, session_factory, payments, clock) -> SeedWorld:
    return await a_seed_world(client, session_factory, payments)


async def a_booked_game(
    client,
    session_factory,
    clock,
    world: SeedWorld,
    *,
    kind: SearchMode = SearchMode.COMPETITIVE,
) -> dict:
    """Her game with the three on Saturday at 17:00, booked by their yeses — its
    booking, its Game, who is on her side and who is across the net, and the
    sets in which her side wins and loses."""

    proposal = await makes(
        session_factory,
        clock,
        pool_id=world.group,
        club_id=world.club,
        kind=kind,
        versions=(world.four,),
    )
    for member in (*world.three, world.marta):
        said = await says_yes(client, member, proposal)
        assert said.status_code == 200, said.text
    booked = said.json()["booked"]
    seats = (await game_of(client, world.marta, booked["game_id"]))["seats"]
    side_of = {seat["player_id"]: seat["side"] for seat in seats}
    hers = side_of[str(world.marta["id"])]
    others = {str(member["id"]): member for member in world.three}
    return {
        "booking": booked["booking_id"],
        "game": booked["game_id"],
        "partner": next(m for p, m in others.items() if side_of[p] == hers),
        "across": [m for p, m in others.items() if side_of[p] != hers],
        "she_wins": _sets(hers, ((6, 4), (6, 3))),
        "she_wins_closer": _sets(hers, ((7, 5), (6, 4))),
        "she_loses": _sets(hers, ((4, 6), (3, 6))),
    }


def _sets(side: str, games: tuple[tuple[int, int], ...]) -> list[dict]:
    """Sets her side takes ``ours``–``theirs``, written absolutely — side A's
    games first — as the wire carries them."""

    if side == "A":
        return [{"a": ours, "b": theirs} for ours, theirs in games]
    return [{"a": theirs, "b": ours} for ours, theirs in games]


async def states(client, member: dict, game_id: str, sets: list[dict]):
    return await client.post(
        f"/api/v1/games/{game_id}/result",
        json={"score": {"sets": sets}},
        headers=member["headers"],
    )


async def accepts(client, member: dict, game_id: str):
    return await client.post(
        f"/api/v1/games/{game_id}/result/acceptance", headers=member["headers"]
    )


async def game_of(client, member: dict, game_id: str) -> dict:
    read = await client.get("/api/v1/games", headers=member["headers"])
    assert read.status_code == 200, read.text
    [found] = [g for g in read.json()["games"] if g["game_id"] == game_id]
    return found


async def home_card(client, member: dict, booking: str) -> dict:
    [found] = [g for g in await home_of(client, member) if g["booking_id"] == booking]
    return found


async def details_of(client, member: dict, booking: str) -> dict:
    """The booked game's details — Home's status for it, **unshelved**: Home
    sends an ended card only until a day after its hour, and two scores settle
    a day after the later one."""

    read = await client.get(f"/api/v1/bookings/{booking}", headers=member["headers"])
    assert read.status_code == 200, read.text
    return read.json()


async def skill_of(client, member: dict) -> dict:
    """Their padel Level and how many counted results it has taken, as their
    record reads it."""

    read = await client.get(
        "/api/v1/players/me/record",
        params={"sport": "PADEL"},
        headers=member["headers"],
    )
    assert read.status_code == 200, read.text
    skill = read.json()["skill"]
    return {"level": skill["level"], "counted_games": skill["counted_games"]}


async def the_catch_up_runs(session_factory, clock) -> int:
    """The rating catch-up, as its job runs it — on the clock the test moved."""

    async with session_factory() as session:
        settled = await build_settle_ratings_on_results(session, clock=clock).execute()
    return settled.games


def to(clock: MovableClock, moment) -> None:
    clock.move(moment - clock.now())


# --------------------------------------------------------------------------- #
# No score before the hour, and a last day for corrections
# --------------------------------------------------------------------------- #


async def test_a_score_before_the_hour_is_refused_in_a_plain_sentence(
    client, session_factory, clock, world
):
    game = await a_booked_game(client, session_factory, clock, world)
    to(clock, SATURDAY_FIVE - timedelta(minutes=1))

    refused = await states(client, world.marta, game["game"], game["she_wins"])

    assert refused.status_code == 409, refused.text
    assert refused.json()["code"] == "the_game_has_not_started"
    assert refused.json()["message"] == "This game hasn't started yet."
    read = await game_of(client, world.marta, game["game"])
    assert (read["standing"], read["played_at"]) == ("AWAITING_ENTRY", None)


async def test_a_correction_after_the_entry_window_has_closed_is_refused(
    client, session_factory, clock, world
):
    """The window closes Sunday 18:00, a day after the hour ended. Marta's score
    went up a minute before; at 18:00 her partner tries to correct it and is
    refused, and her score still waits its day."""

    game = await a_booked_game(client, session_factory, clock, world)
    closes = SATURDAY_FIVE + timedelta(hours=25)
    to(clock, closes - timedelta(minutes=1))
    stated = await states(client, world.marta, game["game"], game["she_wins"])
    assert stated.status_code == 200, stated.text

    to(clock, closes)
    refused = await states(
        client, game["partner"], game["game"], game["she_wins_closer"]
    )

    assert refused.status_code == 409, refused.text
    assert refused.json()["code"] == "corrections_have_closed"
    read = await game_of(client, world.marta, game["game"])
    assert read["standing"] == "AWAITING_ANSWER"
    [proposal] = read["proposals"]
    assert proposal["score"]["sets"] == game["she_wins"]


# --------------------------------------------------------------------------- #
# That's right settles at once, and Levels move within a minute
# --------------------------------------------------------------------------- #


async def test_that_s_right_settles_the_result_at_once_and_closes_the_game(
    client, session_factory, clock, world
):
    game = await a_booked_game(client, session_factory, clock, world)
    to(clock, STATED)
    await states(client, world.marta, game["game"], game["she_wins"])
    one, other = game["across"]
    before = {m["name"]: await skill_of(client, m) for m in (world.marta, one)}

    clock.move(timedelta(minutes=5))
    agreed = await accepts(client, one, game["game"])

    assert agreed.status_code == 200, agreed.text
    body = agreed.json()
    assert (body["standing"], body["score"]["sets"], body["proposals"]) == (
        "CONFIRMED",
        game["she_wins"],
        [],
    )
    assert "acceptance" not in body, "an agreement is never pending"
    hers = await game_of(client, world.marta, game["game"])
    assert (hers["standing"], hers["outcome"]) == ("CONFIRMED", "WIN")
    for member in world.four:
        card = await home_card(client, member, game["booking"])
        assert (card["status"], card["needs_you"]) == ("COUNTED", False)

    # The other opponent's different score at 20:00 is refused…
    clock.move(timedelta(hours=1, minutes=50))
    countered = await states(client, other, game["game"], game["she_loses"])
    assert countered.status_code == 409, countered.text
    assert countered.json()["code"] == "the_result_is_settled"

    # …and the agreement's delivery moved the Levels, with no catch-up run.
    await deliver_the_outbox(session_factory)
    after = {m["name"]: await skill_of(client, m) for m in (world.marta, one)}
    assert after[world.marta["name"]]["level"] > before[world.marta["name"]]["level"]
    assert after[one["name"]]["level"] < before[one["name"]]["level"]
    assert after[world.marta["name"]]["counted_games"] == 1
    assert await the_catch_up_runs(session_factory, clock) == 0, (
        "the outbox already settled it"
    )


async def test_silence_settles_a_lone_score_a_day_after_it_went_up(
    client, session_factory, clock, world
):
    """Had nobody answered, it is final at 18:05 on Sunday, and the catch-up
    moves the Levels then."""

    game = await a_booked_game(client, session_factory, clock, world)
    to(clock, STATED)
    await states(client, world.marta, game["game"], game["she_wins"])
    one = game["across"][0]
    before = await skill_of(client, world.marta)

    to(clock, STATED + timedelta(hours=24) - timedelta(seconds=1))
    assert (await game_of(client, one, game["game"]))["standing"] == ("AWAITING_ANSWER")
    card = await home_card(client, one, game["booking"])
    assert (card["status"], card["needs_you"]) == ("CONFIRM_THE_RESULT", True)
    assert await the_catch_up_runs(session_factory, clock) == 0

    clock.move(timedelta(seconds=1))
    read = await game_of(client, one, game["game"])
    assert (read["standing"], read["outcome"]) == ("CONFIRMED", "LOSS")
    assert await the_catch_up_runs(session_factory, clock) == 1
    after = await skill_of(client, world.marta)
    assert after["level"] > before["level"]
    assert after["counted_games"] == 1


# --------------------------------------------------------------------------- #
# Two standing scores when the answer window closes
# --------------------------------------------------------------------------- #


async def test_two_scores_naming_the_same_winner_count_with_the_closer(
    client, session_factory, clock, world
):
    game = await a_booked_game(client, session_factory, clock, world)
    to(clock, STATED)
    await states(client, world.marta, game["game"], game["she_wins"])
    one = game["across"][0]
    clock.move(timedelta(minutes=25))
    countered = await states(client, one, game["game"], game["she_wins_closer"])
    assert countered.status_code == 200, countered.text
    card = await home_card(client, world.marta, game["booking"])
    assert (card["status"], card["needs_you"]) == ("CONFIRM_THE_RESULT", True)
    before = await skill_of(client, world.marta)

    to(clock, STATED + timedelta(minutes=25, hours=24))

    read = await game_of(client, world.marta, game["game"])
    assert (read["standing"], read["score"]["sets"], read["outcome"]) == (
        "CONFIRMED",
        game["she_wins_closer"],
        "WIN",
    )
    assert (await details_of(client, world.marta, game["booking"]))["status"] == (
        "COUNTED"
    )
    assert await the_catch_up_runs(session_factory, clock) == 1
    assert (await skill_of(client, world.marta))["level"] > before["level"]


async def test_two_scores_naming_different_winners_end_disputed_and_move_no_level(
    client, session_factory, clock, world
):
    game = await a_booked_game(client, session_factory, clock, world)
    to(clock, STATED)
    await states(client, world.marta, game["game"], game["she_wins"])
    one = game["across"][0]
    clock.move(timedelta(minutes=25))
    await states(client, one, game["game"], game["she_loses"])
    card = await home_card(client, world.marta, game["booking"])
    assert (card["status"], card["needs_you"]) == ("CONFIRM_THE_RESULT", True)
    before = {m["name"]: await skill_of(client, m) for m in world.four}

    to(clock, STATED + timedelta(minutes=25, hours=24))

    for member in world.four:
        read = await game_of(client, member, game["game"])
        assert (read["standing"], read["score"], read["outcome"]) == (
            "DISPUTED",
            None,
            None,
        )
        assert read["proposals"] == []
        card = await details_of(client, member, game["booking"])
        assert (card["status"], card["uncounted_reason"], card["needs_you"]) == (
            "UNCOUNTED",
            None,
            False,
        )
    refused = await accepts(client, game["partner"], game["game"])
    assert refused.json()["code"] == "the_result_is_settled"
    assert await the_catch_up_runs(session_factory, clock) == 0
    await deliver_the_outbox(session_factory)
    assert {m["name"]: await skill_of(client, m) for m in world.four} == before


# --------------------------------------------------------------------------- #
# For fun asks nothing
# --------------------------------------------------------------------------- #


async def needing_you(client, member: dict) -> int:
    read = await client.get("/api/v1/home", headers=member["headers"])
    assert read.status_code == 200, read.text
    return read.json()["needing_you"]


@pytest.mark.parametrize(
    ("kind", "asked"),
    [(SearchMode.FOR_FUN, False), (SearchMode.COMPETITIVE, True)],
)
async def test_after_its_hour_a_for_fun_game_with_no_score_asks_nobody(
    client, session_factory, clock, world, kind, asked
):
    """For fun asks nothing (#654, #656): past its hour with no score it still
    reads *needs result* — a score may be added — but it needs nobody and is
    not on the badge. A Competitive game in the same state still asks all four.
    """

    game = await a_booked_game(client, session_factory, clock, world, kind=kind)
    to(clock, STATED)

    for member in world.four:
        card = await home_card(client, member, game["booking"])
        assert (card["status"], card["needs_you"]) == ("NEEDS_RESULT", asked)
        assert await needing_you(client, member) == int(asked)


async def test_a_for_fun_score_settles_at_once_asks_nobody_and_moves_no_level(
    client, session_factory, clock, world
):
    game = await a_booked_game(
        client, session_factory, clock, world, kind=SearchMode.FOR_FUN
    )
    to(clock, STATED)
    before = {m["name"]: await skill_of(client, m) for m in world.four}

    stated = await states(client, world.marta, game["game"], game["she_wins"])

    assert stated.status_code == 200, stated.text
    body = stated.json()
    assert (body["kind"], body["standing"], body["proposals"]) == (
        "FRIENDLY",
        "CONFIRMED",
        [],
    )
    assert body["score"]["sets"] == game["she_wins"]
    for member in world.four:
        card = await home_card(client, member, game["booking"])
        assert card["status"] != "CONFIRM_THE_RESULT"
        assert card["needs_you"] is False
    answered = await accepts(client, game["across"][0], game["game"])
    assert answered.json()["code"] == "the_result_is_settled"

    await deliver_the_outbox(session_factory)
    to(clock, STATED + timedelta(days=2))
    assert await the_catch_up_runs(session_factory, clock) == 0
    assert {m["name"]: await skill_of(client, m) for m in world.four} == before
