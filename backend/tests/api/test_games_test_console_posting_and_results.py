"""Posting and after the game in the games test console (#593;
``docs/adr/0194`` §3, §4).

A person's row gains *Post a game* — read off the sheet their phone reads, at a
court hour it lists — and *Join* on a post they were never dealt, which is their
yes; and after the game a score entered, agreed with or countered — and, at the
court, *isn't here yet*, *I'm here*, *they're here*, *I was there* and *yes,
they were here*, the first three from the club or away (#657). Each runs the use
case their own button runs, so each is held to the player's route over the same
cases, **refusals included**.
And two situations: *A posted game* (9), hers, going at the next full hour a
book-by can fall on; and *Just played* (10), her game whose hour has just ended —
or, given minutes, one a score was stated on as if earlier, so silence confirms
it that many minutes from now.

Every claim is read where somebody would read it: Home, *You're In*, the deck,
the games list and the record through the player surface; what only a job acts
on, through the console's own state pane and *Run it now*.

The world is ``console_world.SeedWorld``: Bonarka Arena, Instant, a 24-hour
cut-off and two hours' notice, and nine members the seed could have made. The
clock stands on **Monday 5 October 2026, 08:00 in Kraków**.
"""

from __future__ import annotations

from datetime import timedelta
from uuid import UUID, uuid4

import pytest

from app.api.dependencies import get_clock
from tests.api.console_world import (
    CONSOLE,
    PLAYER,
    SeedWorld,
    a_seed_world,
    at,
    board_of,
    code_of,
    deck_ids,
    her_situation,
    home_of,
    pane_of,
    presses,
    rows_of,
    runs,
    says,
)
from tests.api.proposals_world import (
    MONDAY_MORNING,
    SATURDAY_FIVE,
    a_player,
    live_ids,
    makes,
    says_yes,
    warsaw,
)
from tests.unit.fake_clock import MovableClock

SATURDAY = "2026-10-10"
#: Side A takes it.
A_WINS = [{"a": 6, "b": 4}, {"a": 6, "b": 3}]
#: Side B takes it.
B_WINS = [{"a": 4, "b": 6}, {"a": 3, "b": 6}]
#: Saturday 19:00 — Saturday's game over an hour ago.
AFTER_SATURDAY_S_GAME = SATURDAY_FIVE - MONDAY_MORNING + timedelta(hours=2)


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


# --------------------------------------------------------------------------- #
# Presses, as the phone and as the row
# --------------------------------------------------------------------------- #


def posting(**overrides) -> dict:
    return {"sport": "PADEL", "kind": "COMPETITIVE", "who": "ANYONE", **overrides}


async def reads_the_sheet(client, via: str, member: dict, world: SeedWorld):
    params = {**posting(), "day": SATURDAY, "range": "EVENING"}
    if via == PLAYER:
        return await client.get(
            f"/api/v1/pools/{world.group}/posting-grid/slot",
            params=params,
            headers=member["headers"],
        )
    return await client.get(
        f"/dev/as/{member['id']}/pools/{world.group}/posting-grid/slot",
        params=params,
    )


async def posts(client, via: str, member: dict, world: SeedWorld, **overrides):
    body = {
        **posting(**overrides),
        "club_id": world.club,
        "starts_at": SATURDAY_FIVE.isoformat(),
    }
    if via == PLAYER:
        return await client.post(
            f"/api/v1/pools/{world.group}/posts", json=body, headers=member["headers"]
        )
    return await client.post(
        f"/dev/as/{member['id']}/pools/{world.group}/posts", json=body
    )


async def on_the_game(
    client, via: str, member: dict, game_id: str, tail: str, body=None
):
    """A press on a game — ``result``, ``result/acceptance`` or one of the
    ``attendance/…`` taps — as ``member``."""

    if via == PLAYER:
        return await client.post(
            f"/api/v1/games/{game_id}/{tail}", json=body, headers=member["headers"]
        )
    return await client.post(
        f"/dev/as/{member['id']}/games/{game_id}/{tail}", json=body
    )


async def states(client, via: str, member: dict, game_id: str, sets: list[dict]):
    return await on_the_game(
        client, via, member, game_id, "result", {"score": {"sets": sets}}
    )


async def accepts(client, via: str, member: dict, game_id: str):
    return await on_the_game(client, via, member, game_id, "result/acceptance")


#: Bonarka Arena's own point — where the phone at the club reads itself.
BONARKA = (50.06, 19.95)


async def at_the_court(
    client,
    via: str,
    member: dict,
    game_id: str,
    tail: str,
    about: dict,
    *,
    where: str = "AT_THE_CLUB",
):
    """*Isn't here yet* (``not-here-yet``) or an arrival (``arrival``) about
    ``about`` — the phone sending a fix on the club's point or two kilometres
    north of it, the console naming where."""

    if via == PLAYER:
        north = 0.0 if where == "AT_THE_CLUB" else 0.018
        body: dict = {
            "player_id": str(about["id"]),
            "location": {
                "latitude": BONARKA[0] + north,
                "longitude": BONARKA[1],
                "accuracy_m": 10,
            },
        }
    else:
        body = {"player_id": str(about["id"]), "where": where}
    return await on_the_game(client, via, member, game_id, f"attendance/{tail}", body)


async def claims(client, via: str, member: dict, game_id: str):
    return await on_the_game(client, via, member, game_id, "attendance/claim")


async def confirms(client, via: str, member: dict, game_id: str, claimant: dict):
    return await on_the_game(
        client,
        via,
        member,
        game_id,
        "attendance/confirmation",
        {"player_id": str(claimant["id"])},
    )


# --------------------------------------------------------------------------- #
# What the phone reads
# --------------------------------------------------------------------------- #


async def game_of(client, member: dict, game_id: str) -> dict:
    read = await client.get("/api/v1/games", headers=member["headers"])
    assert read.status_code == 200, read.text
    [found] = [g for g in read.json()["games"] if g["game_id"] == game_id]
    return found


async def home_game(client, member: dict, booking: str) -> dict:
    [found] = [g for g in await home_of(client, member) if g["booking_id"] == booking]
    return found


async def record_of(client, member: dict) -> dict:
    read = await client.get(
        "/api/v1/players/me/record",
        params={"sport": "PADEL"},
        headers=member["headers"],
    )
    assert read.status_code == 200, read.text
    return read.json()["skill"]


# --------------------------------------------------------------------------- #
# A played game
# --------------------------------------------------------------------------- #


async def a_booked_game(client, session_factory, clock, world: SeedWorld) -> dict:
    """Her game with the three on Saturday at 17:00, booked by her yes — its
    booking, its Game, and who sits on which side."""

    game = await makes(
        session_factory,
        clock,
        pool_id=world.group,
        club_id=world.club,
        versions=(world.four,),
    )
    for member in (*world.three, world.marta):
        said = await says_yes(client, member, game)
        assert said.status_code == 200, said.text
    booked = said.json()["booked"]
    seats = (await game_of(client, world.marta, booked["game_id"]))["seats"]
    side_of = {seat["player_id"]: seat["side"] for seat in seats}
    hers = side_of[str(world.marta["id"])]
    by_id = {str(member["id"]): member for member in world.four}
    return {
        "booking": booked["booking_id"],
        "game": booked["game_id"],
        "partner": next(
            by_id[p]
            for p, side in side_of.items()
            if side == hers and p in by_id and by_id[p] is not world.marta
        ),
        "across": [by_id[p] for p, side in side_of.items() if side != hers],
        "her_side_wins": A_WINS if hers == "A" else B_WINS,
    }


# --------------------------------------------------------------------------- #
# Post a game
# --------------------------------------------------------------------------- #


async def test_the_sheet_reads_as_the_player_s_own(client, clock, world):
    phone = await reads_the_sheet(client, PLAYER, world.marta, world)
    row = await reads_the_sheet(client, CONSOLE, world.marta, world)

    assert phone.status_code == row.status_code == 200, (phone.text, row.text)
    assert row.json() == phone.json()
    assert at(SATURDAY_FIVE) in {c["starts_at"] for c in row.json()["free_courts"]}


@pytest.mark.parametrize("via", [PLAYER, CONSOLE])
async def test_a_post_is_their_yes_and_is_dealt_alike(client, clock, world, via):
    posted = await posts(client, via, world.marta, world)

    assert posted.status_code == 201, posted.text
    post = posted.json()
    assert post["dealt_to"] >= 3
    assert post["proposal_id"] in await live_ids(client, world.marta)


@pytest.mark.parametrize("via", [PLAYER, CONSOLE])
async def test_a_post_whose_who_leaves_them_out_is_refused_alike(
    client, clock, world, via
):
    posted = await posts(client, via, world.marta, world, who="MEN")

    assert posted.status_code == 409, posted.text
    assert code_of(posted) == "who_leaves_you_out"
    assert await live_ids(client, world.marta) == []


@pytest.mark.parametrize("via", [PLAYER, CONSOLE])
async def test_a_post_whose_level_range_is_upside_down_is_refused_alike(
    client, clock, world, via
):
    posted = await posts(client, via, world.marta, world, level_low=2.7, level_high=2.3)

    assert posted.status_code == 400, posted.text
    assert code_of(posted) == "level_range_inverted"
    assert await live_ids(client, world.marta) == []


@pytest.mark.parametrize("via", [PLAYER, CONSOLE])
async def test_a_post_inside_a_narrowed_level_range_is_dealt_alike(
    client, clock, world, via
):
    posted = await posts(client, via, world.marta, world, level_low=2.4, level_high=2.6)

    assert posted.status_code == 201, posted.text
    assert posted.json()["dealt_to"] >= 3


@pytest.mark.parametrize("via", [PLAYER, CONSOLE])
async def test_a_member_never_dealt_a_post_joins_it_alike(client, clock, world, via):
    post = (await posts(client, PLAYER, world.marta, world)).json()["proposal_id"]
    waiting = [
        member
        for member in world.rest
        if post not in await deck_ids(client, member, world.group)
    ][0]

    joined = await says(client, via, "yes", waiting, UUID(post))

    assert joined.status_code == 200, joined.text
    assert post in await live_ids(client, waiting)


@pytest.mark.parametrize("via", [PLAYER, CONSOLE])
async def test_a_join_dealing_would_not_make_is_refused_alike(
    client, session_factory, clock, world, via
):
    """Lena plays one game a week, and Sunday's is booked: the post was not
    dealt to her, and she may not join it."""

    lena = world.named("lena")
    capped = await client.put(
        "/api/v1/players/me/games-and-money",
        json={"games_per_week": 1, "most_ill_pay_grosze": None},
        headers=lena["headers"],
    )
    assert capped.status_code == 200, capped.text
    sunday = await makes(
        session_factory,
        clock,
        pool_id=world.group,
        club_id=world.club,
        start=warsaw(11, 17),
        versions=(
            (world.named("ola"), world.named("tomek"), world.named("ewa"), lena),
        ),
    )
    for name in ("ola", "tomek", "ewa", "lena"):
        said = await says_yes(client, world.named(name), sunday)
        assert said.status_code == 200, said.text
    post = (await posts(client, PLAYER, world.marta, world)).json()["proposal_id"]

    joined = await says(client, via, "yes", lena, UUID(post))

    assert joined.status_code == 409, joined.text
    assert code_of(joined) == "post_not_open_to_you"
    assert post not in await live_ids(client, lena)


async def test_a_row_offers_join_on_every_post_it_was_never_dealt(client, clock, world):
    post = (await posts(client, PLAYER, world.marta, world)).json()["proposal_id"]

    rows = rows_of(await board_of(client, world.group))

    answers = {
        name: [card["answer"] for card in row["cards"] if card["proposal_id"] == post]
        for name, row in rows.items()
    }
    assert answers["marta"] == ["IN"]
    assert {answer for [answer] in answers.values()} >= {"DEALT", "NOT_DEALT"}


# --------------------------------------------------------------------------- #
# The score
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("via", [PLAYER, CONSOLE])
async def test_a_score_entered_is_on_the_table_alike(
    client, session_factory, clock, world, via
):
    game = await a_booked_game(client, session_factory, clock, world)
    clock.move(AFTER_SATURDAY_S_GAME)

    stated = await states(client, via, world.marta, game["game"], game["her_side_wins"])

    assert stated.status_code == 200, stated.text
    assert stated.json()["standing"] == "AWAITING_ANSWER"
    # Across the net, their phone has her score to answer.
    theirs = await game_of(client, game["across"][0], game["game"])
    [proposal] = theirs["proposals"]
    assert proposal["proposed_by"] == str(world.marta["id"])
    assert (await home_game(client, game["across"][0], game["booking"]))[
        "status"
    ] == "CONFIRM_THE_RESULT"


@pytest.mark.parametrize("via", [PLAYER, CONSOLE])
async def test_an_agreement_from_across_the_net_alike(
    client, session_factory, clock, world, via
):
    game = await a_booked_game(client, session_factory, clock, world)
    clock.move(AFTER_SATURDAY_S_GAME)
    stated = await states(
        client, PLAYER, world.marta, game["game"], game["her_side_wins"]
    )
    assert stated.status_code == 200, stated.text

    agreed = await accepts(client, via, game["across"][0], game["game"])

    assert agreed.status_code == 200, agreed.text
    assert agreed.json()["standing"] == "CONFIRMED", "*That's right* settles at once"
    read = await game_of(client, world.marta, game["game"])
    assert (read["standing"], read["score"]["sets"]) == (
        "CONFIRMED",
        game["her_side_wins"],
    )


@pytest.mark.parametrize("via", [PLAYER, CONSOLE])
async def test_a_counter_from_across_the_net_disputes_it_alike(
    client, session_factory, clock, world, via
):
    game = await a_booked_game(client, session_factory, clock, world)
    clock.move(AFTER_SATURDAY_S_GAME)
    await states(client, PLAYER, world.marta, game["game"], game["her_side_wins"])
    theirs = B_WINS if game["her_side_wins"] == A_WINS else A_WINS

    countered = await states(client, via, game["across"][0], game["game"], theirs)

    assert countered.status_code == 200, countered.text
    assert len((await game_of(client, world.marta, game["game"]))["proposals"]) == 2


@pytest.mark.parametrize("via", [PLAYER, CONSOLE])
async def test_agreeing_with_your_own_side_is_refused_alike(
    client, session_factory, clock, world, via
):
    game = await a_booked_game(client, session_factory, clock, world)
    clock.move(AFTER_SATURDAY_S_GAME)
    await states(client, PLAYER, world.marta, game["game"], game["her_side_wins"])

    agreed = await accepts(client, via, game["partner"], game["game"])

    assert agreed.status_code == 409, agreed.text
    assert code_of(agreed) == "accepting_your_own_sides_result"


@pytest.mark.parametrize("via", [PLAYER, CONSOLE])
async def test_a_score_from_somebody_off_the_court_is_refused_alike(
    client, session_factory, clock, world, via
):
    game = await a_booked_game(client, session_factory, clock, world)
    clock.move(AFTER_SATURDAY_S_GAME)

    stated = await states(client, via, world.named("tomek"), game["game"], A_WINS)

    assert stated.status_code == 403, stated.text
    assert code_of(stated) == "you_were_not_on_this_court"


@pytest.mark.parametrize(
    ("tail", "body"),
    [
        ("result", {"score": {"sets": A_WINS}}),
        ("result/acceptance", None),
        ("attendance/not-here-yet", "absent"),
        ("attendance/arrival", "absent"),
        ("attendance/claim", None),
        ("attendance/confirmation", "absent"),
    ],
)
async def test_each_game_press_refuses_an_id_that_is_nobody_s(
    client, session_factory, clock, world, tail, body
):
    game = await a_booked_game(client, session_factory, clock, world)
    clock.move(AFTER_SATURDAY_S_GAME)
    if body == "absent":
        body = {"player_id": str(game["across"][0]["id"]), "where": "AT_THE_CLUB"}

    pressed = await on_the_game(
        client, CONSOLE, {"id": uuid4()}, game["game"], tail, body
    )

    assert pressed.status_code == 403, pressed.text
    assert code_of(pressed) == "not_a_seed_account"
    read = await game_of(client, world.marta, game["game"])
    assert (read["standing"], read["attendance"]) == ("AWAITING_ENTRY", [])


@pytest.mark.parametrize("via", ["sheet", "post"])
async def test_each_posting_press_refuses_an_id_that_is_nobody_s(
    client, clock, world, via
):
    nobody = {"id": uuid4()}

    pressed = (
        await reads_the_sheet(client, CONSOLE, nobody, world)
        if via == "sheet"
        else await posts(client, CONSOLE, nobody, world)
    )

    assert pressed.status_code == 403, pressed.text
    assert code_of(pressed) == "not_a_seed_account"


# --------------------------------------------------------------------------- #
# Who turned up, caught at the court (#657)
# --------------------------------------------------------------------------- #

#: Saturday 17:10 — the first half hour of her game.
TEN_PAST = SATURDAY_FIVE - MONDAY_MORNING + timedelta(minutes=10)


@pytest.mark.parametrize("via", [PLAYER, CONSOLE])
async def test_isn_t_here_yet_from_the_club_is_noted_alike(
    client, session_factory, clock, world, via
):
    game = await a_booked_game(client, session_factory, clock, world)
    clock.move(TEN_PAST)
    absent = game["across"][0]

    tapped = await at_the_court(
        client, via, world.marta, game["game"], "not-here-yet", absent
    )

    assert tapped.status_code == 200, tapped.text
    assert tapped.json()["standing"] == "NOT_HERE_YET"
    [row] = (await game_of(client, absent, game["game"]))["attendance"]
    assert (row["player_id"], row["state"]) == (str(absent["id"]), "WAITING")


@pytest.mark.parametrize("via", [PLAYER, CONSOLE])
async def test_isn_t_here_yet_from_away_is_refused_alike(
    client, session_factory, clock, world, via
):
    game = await a_booked_game(client, session_factory, clock, world)
    clock.move(TEN_PAST)

    tapped = await at_the_court(
        client,
        via,
        world.marta,
        game["game"],
        "not-here-yet",
        game["across"][0],
        where="AWAY",
    )

    assert tapped.status_code == 409, tapped.text
    assert code_of(tapped) == "not_at_the_club"


@pytest.mark.parametrize("via", [PLAYER, CONSOLE])
async def test_a_tap_before_the_hour_is_refused_alike(
    client, session_factory, clock, world, via
):
    game = await a_booked_game(client, session_factory, clock, world)

    tapped = await at_the_court(
        client, via, world.marta, game["game"], "not-here-yet", game["across"][0]
    )

    assert tapped.status_code == 409, tapped.text
    assert code_of(tapped) == "the_game_has_not_started"


@pytest.mark.parametrize("via", [PLAYER, CONSOLE])
async def test_i_m_here_and_they_re_here_are_arrivals_alike(
    client, session_factory, clock, world, via
):
    game = await a_booked_game(client, session_factory, clock, world)
    clock.move(TEN_PAST)
    first, second = game["across"]
    await at_the_court(client, PLAYER, world.marta, game["game"], "not-here-yet", first)
    await at_the_court(
        client, PLAYER, world.marta, game["game"], "not-here-yet", second
    )
    clock.move(timedelta(minutes=5))

    mine = await at_the_court(client, via, first, game["game"], "arrival", first)
    theirs = await at_the_court(
        client, via, world.marta, game["game"], "arrival", second
    )

    assert (mine.status_code, theirs.status_code) == (200, 200), theirs.text
    assert theirs.json()["standing"] == "AWAITING_ENTRY"
    assert [row["state"] for row in theirs.json()["attendance"]] == [
        "CAME_LATE",
        "CAME_LATE",
    ]


@pytest.mark.parametrize("via", [PLAYER, CONSOLE])
async def test_i_was_there_and_yes_they_were_here_alike(
    client, session_factory, clock, world, via
):
    game = await a_booked_game(client, session_factory, clock, world)
    clock.move(TEN_PAST)
    absent = game["across"][0]
    await at_the_court(
        client, PLAYER, world.marta, game["game"], "not-here-yet", absent
    )
    clock.move(timedelta(hours=16))

    claimed = await claims(client, via, absent, game["game"])
    confirmed = await confirms(client, via, game["partner"], game["game"], absent)

    assert claimed.status_code == 200, claimed.text
    assert claimed.json()["standing"] == "DIDNT_COME"
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["standing"] == "AWAITING_ENTRY"
    [row] = (await game_of(client, world.marta, game["game"]))["attendance"]
    assert row["state"] == "CONFIRMED"


@pytest.mark.parametrize("via", [PLAYER, CONSOLE])
async def test_a_claim_nobody_asked_for_is_refused_alike(
    client, session_factory, clock, world, via
):
    game = await a_booked_game(client, session_factory, clock, world)
    clock.move(AFTER_SATURDAY_S_GAME)

    claimed = await claims(client, via, game["across"][0], game["game"])

    assert claimed.status_code == 409, claimed.text
    assert code_of(claimed) == "nobody_said_they_were_not_here"


# --------------------------------------------------------------------------- #
# The pane: the score, and the moment it confirms
# --------------------------------------------------------------------------- #


def moments_of(pane: dict) -> dict[str, tuple[str, str]]:
    return {m["moment"]: (m["at"], m["job"]) for m in pane["moments"]}


async def test_the_pane_counts_down_to_the_score_confirming(
    client, session_factory, clock, world
):
    game = await a_booked_game(client, session_factory, clock, world)
    clock.move(AFTER_SATURDAY_S_GAME)
    stated_at = SATURDAY_FIVE + timedelta(hours=2)
    await states(client, CONSOLE, world.marta, game["game"], game["her_side_wins"])

    pane = pane_of(await board_of(client, world.group), game["booking"])

    result = pane["result"]
    assert (result["game_id"], result["standing"], result["counted"]) == (
        game["game"],
        "AWAITING_ANSWER",
        True,
    )
    [score] = result["scores"]
    assert score["by"]["player_id"] == str(world.marta["id"])
    assert score["sets"] in ("6–4 6–3", "4–6 3–6")
    # A lone score is final after its day of silence…
    assert moments_of(pane)["RESULT_CONFIRMS"] == (
        at(stated_at + timedelta(hours=24)),
        "rating-catch-up",
    )
    # …and, agreed with, at once: nothing is left to count down to (#654).
    await accepts(client, CONSOLE, game["across"][0], game["game"])
    pane = pane_of(await board_of(client, world.group), game["booking"])
    assert pane["result"]["standing"] == "CONFIRMED"
    assert pane["result"]["agreed_by"]["player_id"] == str(game["across"][0]["id"])
    assert "RESULT_CONFIRMS" not in moments_of(pane)


async def test_the_pane_counts_down_to_two_scores_settling_only_when_they_agree_who_won(
    client, session_factory, clock, world
):
    """Two scores settle on the later one's day: with the closer, naming the
    same winner — a moment the catch-up acts at — and disputed, naming
    different winners, which moves no Level and so is no moment of its."""

    game = await a_booked_game(client, session_factory, clock, world)
    clock.move(AFTER_SATURDAY_S_GAME)
    await states(client, CONSOLE, world.marta, game["game"], game["her_side_wins"])
    clock.move(timedelta(minutes=30))
    countered_at = clock.now()
    theirs = B_WINS if game["her_side_wins"] == A_WINS else A_WINS
    await states(client, CONSOLE, game["across"][0], game["game"], theirs)

    pane = pane_of(await board_of(client, world.group), game["booking"])

    assert pane["result"]["standing"] == "AWAITING_ANSWER"
    assert len(pane["result"]["scores"]) == 2
    assert "RESULT_CONFIRMS" not in moments_of(pane)
    clock.move(countered_at + timedelta(hours=24) - clock.now())
    pane = pane_of(await board_of(client, world.group), game["booking"])
    assert pane["result"]["standing"] == "DISPUTED"


async def test_the_pane_counts_down_to_two_scores_naming_one_winner_settling(
    client, session_factory, clock, world
):
    """Two scores naming the same winner settle with the closer on the later
    one's day — a moment the catch-up acts at."""

    game = await a_booked_game(client, session_factory, clock, world)
    clock.move(AFTER_SATURDAY_S_GAME)
    await states(client, CONSOLE, world.marta, game["game"], game["her_side_wins"])
    clock.move(timedelta(minutes=30))
    countered_at = clock.now()
    closer = (
        [{"a": 7, "b": 5}, {"a": 6, "b": 4}]
        if game["her_side_wins"] == A_WINS
        else [{"a": 5, "b": 7}, {"a": 4, "b": 6}]
    )
    await states(client, CONSOLE, game["across"][0], game["game"], closer)

    pane = pane_of(await board_of(client, world.group), game["booking"])

    assert moments_of(pane)["RESULT_CONFIRMS"] == (
        at(countered_at + timedelta(hours=24)),
        "rating-catch-up",
    )
    clock.move(timedelta(hours=24))
    assert (await runs(client, "rating-catch-up"))["done"] == 1
    assert (await game_of(client, world.marta, game["game"]))["score"]["sets"] == closer


async def test_run_it_now_folds_an_agreed_score_at_once(
    client, session_factory, clock, world
):
    """The rating press settles what has become final: an agreement is final
    the moment it is made, so the press folds it straight away — the outbox,
    not run here, would have done the same."""

    game = await a_booked_game(client, session_factory, clock, world)
    clock.move(AFTER_SATURDAY_S_GAME)
    await states(client, CONSOLE, world.marta, game["game"], game["her_side_wins"])
    assert (await runs(client, "rating-catch-up"))["done"] == 0

    await accepts(client, CONSOLE, game["across"][0], game["game"])

    assert (await runs(client, "rating-catch-up"))["done"] == 1
    assert (await record_of(client, world.marta))["counted_games"] == 1
    assert (await runs(client, "rating-catch-up"))["done"] == 0


async def test_run_it_now_leaves_a_score_before_its_day_and_folds_it_after(
    client, session_factory, clock, world
):
    game = await a_booked_game(client, session_factory, clock, world)
    clock.move(AFTER_SATURDAY_S_GAME)
    await states(client, CONSOLE, world.marta, game["game"], game["her_side_wins"])

    clock.move(timedelta(hours=23, minutes=59))
    assert (await runs(client, "rating-catch-up"))["done"] == 0
    assert (await record_of(client, world.marta))["counted_games"] == 0

    clock.move(timedelta(minutes=1))
    assert (await runs(client, "rating-catch-up"))["done"] == 1
    assert (await record_of(client, world.marta))["counted_games"] == 1
    assert (await runs(client, "rating-catch-up"))["done"] == 0


async def test_a_row_lists_its_played_game_with_its_game_s_id(
    client, session_factory, clock, world
):
    game = await a_booked_game(client, session_factory, clock, world)
    clock.move(AFTER_SATURDAY_S_GAME)

    [booked] = rows_of(await board_of(client, world.group))["marta"]["booked"]

    assert (booked["booking_id"], booked["game_id"], booked["standing"]) == (
        game["booking"],
        game["game"],
        "AWAITING_ENTRY",
    )


# --------------------------------------------------------------------------- #
# Situation 9 · A posted game
# --------------------------------------------------------------------------- #


async def test_a_posted_game_is_hers_and_goes_at_the_next_full_hour(
    client, clock, world
):
    """At 08:00 the next book-by a post can have is 09:00 — Monday 11:00, at
    two hours' notice."""

    pressed = await her_situation(client, "a-posted-game", world)

    assert pressed.status_code == 200, pressed.text
    body = pressed.json()
    assert (body["book_by"], body["starts_at"]) == (at(warsaw(5, 9)), at(warsaw(5, 11)))
    assert "fires at 09:00 · 60 min" in body["says"]
    post = body["game_id"]
    # Her phone: the post in her You're In; dealt to her best fits.
    assert post in await live_ids(client, world.marta)
    assert body["dealt"]
    dealt = {person["player_id"] for person in body["dealt"]}
    assert str(world.marta["id"]) not in dealt
    dealt_member = next(m for m in world.rest if str(m["id"]) in dealt)
    assert post in await deck_ids(client, dealt_member, world.group)

    # A row says yes to it…
    said = await says(client, CONSOLE, "yes", dealt_member, UUID(post))
    assert said.status_code == 200, said.text
    # …and, not full by its book-by, it goes, and the sweep records it.
    clock.move(timedelta(minutes=59))
    assert (await runs(client, "proposal-expiry"))["done"] == 0
    assert post in await live_ids(client, world.marta)
    clock.move(timedelta(minutes=1))
    assert post not in await live_ids(client, world.marta)
    assert (await runs(client, "proposal-expiry"))["done"] == 1


async def test_a_posted_game_says_so_when_she_plays_no_kind_of_it(client, clock, world):
    """Nobody in the group is rated in tennis."""

    pressed = await presses(
        client,
        "a-posted-game",
        group_id=world.group,
        sport="TENNIS",
        protagonist_id=world.marta["id"],
    )

    assert pressed.status_code == 409, pressed.text
    assert await live_ids(client, world.marta) == []


# --------------------------------------------------------------------------- #
# Situation 10 · Just played
# --------------------------------------------------------------------------- #


async def test_just_played_is_her_game_whose_hour_has_just_ended(client, clock, world):
    """At 08:00 the hour that ended last is 07:00's."""

    pressed = await her_situation(client, "just-played", world)

    assert pressed.status_code == 200, pressed.text
    body = pressed.json()
    assert body["starts_at"] == at(warsaw(5, 7))
    assert body["stated"] is None
    assert str(world.marta["id"]) in {p["player_id"] for p in body["people"]}
    # Her phone: the game needs its result.
    card = await home_game(client, world.marta, body["booking_id"])
    assert (card["status"], card["needs_you"]) == ("NEEDS_RESULT", True)

    # A row enters a score, and her phone has it to answer or not.
    other = next(
        m
        for m in world.rest
        if str(m["id"]) in {p["player_id"] for p in body["people"]}
    )
    stated = await states(client, CONSOLE, other, body["game_id"], A_WINS)
    assert stated.status_code == 200, stated.text
    assert (await game_of(client, world.marta, body["game_id"]))[
        "standing"
    ] == "AWAITING_ANSWER"


async def test_just_played_with_a_score_that_confirms_in_minutes(client, clock, world):
    """Thirty minutes: a game played the day before, and a score stated across
    the net from her twenty-three and a half hours ago."""

    pressed = await her_situation(
        client, "just-played", world, result_confirms_in_minutes=30
    )

    assert pressed.status_code == 200, pressed.text
    body = pressed.json()
    confirms = MONDAY_MORNING + timedelta(minutes=30)
    assert body["stated"]["confirms_at"] == at(confirms)
    assert "fires at 08:30 · 30 min" in body["says"]
    # Her phone: somebody across the net put a score up, and it waits on her.
    game = await game_of(client, world.marta, body["game_id"])
    [proposal] = game["proposals"]
    assert proposal["answer_by"] == at(confirms)
    assert proposal["proposed_by"] != str(world.marta["id"])
    card = await home_game(client, world.marta, body["booking_id"])
    assert card["status"] == "CONFIRM_THE_RESULT"
    # The pane counts down to it — and the catch-up acts only once it is due.
    pane = pane_of(await board_of(client, world.group), body["booking_id"])
    assert moments_of(pane)["RESULT_CONFIRMS"] == (at(confirms), "rating-catch-up")
    # Not due: the press leaves the score waiting on her, and her Level alone.
    assert (await runs(client, "rating-catch-up"))["done"] == 0
    card = await home_game(client, world.marta, body["booking_id"])
    assert card["status"] == "CONFIRM_THE_RESULT"
    assert (await record_of(client, world.marta))["counted_games"] == 0
    clock.move(timedelta(minutes=30))
    assert (await runs(client, "rating-catch-up"))["done"] == 1
    assert (await record_of(client, world.marta))["counted_games"] == 1


@pytest.mark.parametrize("situation", ["a-posted-game", "just-played"])
async def test_each_situation_refuses_a_protagonist_the_seed_did_not_create(
    client, payments, world, situation
):
    piotr = await a_player(client, payments, "piotr")

    pressed = await presses(
        client,
        situation,
        group_id=world.group,
        sport="PADEL",
        protagonist_id=piotr["id"],
    )

    assert pressed.status_code == 403, pressed.text
    assert code_of(pressed) == "not_a_seed_account"
