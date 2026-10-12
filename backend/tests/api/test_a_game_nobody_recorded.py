"""A full booked game nobody recorded was played (#655; ``docs/adr/0195`` §2) —
read from outside.

Marta, Ivan, Oscar and Paula play padel on **Tuesday 13 October at 19:00** at
Bonarka Arena. Each paid 40 zł of the 160 zł court-hour, and they go home
without opening the app. At **20:00 on Wednesday**, a day after the hour's end,
the entry window closes and the game reads **Played · no score** for all four:

- nobody takes a *Shows up* miss, and *Keeps plans* reads it kept, as before;
- no Level moves — an evening with no score is not evidence about skill;
- it is a game they played together, and each of them is asked for the
  others' stars.

Every claim is read where a player reads it: the game (``GET /games``), its
details (Home's status, unshelved), their record, and the cards waiting for
their stars. The clock starts on Monday 5 October, 08:00 in Kraków, and moves.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from app.api.dependencies import get_clock
from app.bootstrap.composition import build_settle_ratings_on_results
from tests.api.players_world import deliver_the_outbox
from tests.api.proposals_world import (
    MONDAY_MORNING,
    a_club_selling,
    a_group,
    a_member,
    makes,
    says_yes,
    the_cut_off_comes,
    warsaw,
)
from tests.unit.fake_clock import MovableClock

#: Tuesday 13 October, 19:00 in Kraków — their hour.
TUESDAY_SEVEN = warsaw(13, 19)
#: Wednesday 14 October, 20:00 — a day after the hour's end: the entry window
#: closes, and with it the last moment anybody could have said *we played*.
WEDNESDAY_EIGHT = warsaw(14, 20)


@pytest.fixture
def clock(app, payments):
    """Monday 5 October 2026, 08:00 in Kraków."""

    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    payments.clock = fixed
    return fixed


@pytest.fixture
async def four(client, session_factory, payments) -> tuple[dict, ...]:
    """Marta, Ivan, Oscar and Paula: padel 2,5, free every hour, competitive,
    each with a card that pays."""

    return tuple(
        [
            await a_member(client, session_factory, payments, name)
            for name in ("marta", "ivan", "oscar", "paula")
        ]
    )


@pytest.fixture
async def booked(client, session_factory, clock, four) -> dict:
    """Their game at Bonarka Arena on Tuesday at 19:00, booked by the four
    yeses, its shares taken at the club's cut-off — 40 zł each."""

    club = await a_club_selling(client, padel_grosze=160_00)
    group = await a_group(client, four[0], club, *four[1:])
    proposal = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=TUESDAY_SEVEN,
        versions=(four,),
    )
    for member in four:
        said = await says_yes(client, member, proposal)
        assert said.status_code == 200, said.text
    game = said.json()["booked"]
    assert game is not None, said.text
    await the_cut_off_comes(
        session_factory, clock, at=TUESDAY_SEVEN - timedelta(hours=24)
    )
    await deliver_the_outbox(session_factory)
    return {"booking": game["booking_id"], "game": game["game_id"]}


def to(clock: MovableClock, moment) -> None:
    clock.move(moment - clock.now())


async def game_of(client, member: dict, game_id: str) -> dict:
    read = await client.get("/api/v1/games", headers=member["headers"])
    assert read.status_code == 200, read.text
    [found] = [g for g in read.json()["games"] if g["game_id"] == game_id]
    return found


async def details_of(client, member: dict, booking: str) -> dict:
    """The booked game's details — Home's status for it, **unshelved**: Home
    sends an ended card only until a day after its hour, which is the moment
    this game's entry window closes."""

    read = await client.get(f"/api/v1/bookings/{booking}", headers=member["headers"])
    assert read.status_code == 200, read.text
    return read.json()


async def record_of(client, member: dict) -> dict:
    read = await client.get(
        "/api/v1/players/me/record",
        params={"sport": "PADEL"},
        headers=member["headers"],
    )
    assert read.status_code == 200, read.text
    return read.json()


async def open_cards_of(client, member: dict) -> list[dict]:
    read = await client.get("/api/v1/sportsmanship", headers=member["headers"])
    assert read.status_code == 200, read.text
    return read.json()["cards"]


async def test_nobody_recording_it_reads_played_no_score_for_all_four(
    client, clock, four, booked
):
    """**Awaiting its entry to the last second, then played.** Nobody said
    *we played*, nobody said anybody did not come, and the court was full."""

    to(clock, WEDNESDAY_EIGHT - timedelta(seconds=1))
    for member in four:
        assert (await game_of(client, member, booked["game"]))[
            "standing"
        ] == "AWAITING_ENTRY"

    to(clock, WEDNESDAY_EIGHT)
    for member in four:
        game = await game_of(client, member, booked["game"])
        assert game["standing"] == "PLAYED_NO_SCORE", member["name"]
        assert game["proposals"] == []


async def test_its_details_read_played_no_score_and_ask_nothing_of_anybody(
    client, clock, four, booked
):
    """Home's status where it read *Never played*: an end, with no reason to
    be uncounted and nothing for anybody to do — and everybody paid, as the
    club was paid for the hour."""

    to(clock, WEDNESDAY_EIGHT)

    for member in four:
        details = await details_of(client, member, booked["booking"])
        assert details["status"] == "PLAYED_NO_SCORE", member["name"]
        assert details["uncounted_reason"] is None
        assert details["needs_you"] is False
        assert details["money"]["paid"] is True
        assert details["money"]["share_grosze"] == 40_00


async def test_nobody_takes_a_shows_up_miss_and_keeps_plans_reads_it_kept(
    client, clock, four, booked
):
    """**The ghost miss goes** (``docs/adr/0195`` §2): the four turned up, as
    far as the record knows, and the booking they held to its hour was kept.
    Nothing was put to anybody, so nothing about answering a score is read."""

    to(clock, WEDNESDAY_EIGHT)

    for member in four:
        strands = {
            row["strand"]: (row["good"], row["opportunities"])
            for row in (await record_of(client, member))["reliability"]["strands"]
        }
        assert strands == {"SHOWS_UP": (1, 1), "KEEPS_PLANS": (1, 1)}, member["name"]


async def test_no_level_moves(client, session_factory, clock, four, booked):
    """An evening with no score is not evidence about skill: the catch-up has
    nothing to fold, and every Level stays where it was."""

    before = [(await record_of(client, member))["skill"] for member in four]
    to(clock, WEDNESDAY_EIGHT + timedelta(minutes=1))

    async with session_factory() as session:
        settled = await build_settle_ratings_on_results(session, clock=clock).execute()
    after = [(await record_of(client, member))["skill"] for member in four]

    assert settled.games == 0
    assert [skill["level"] for skill in after] == [skill["level"] for skill in before]
    assert all(skill["counted_games"] == 0 for skill in after)


async def test_it_is_a_counted_game_they_played_together(client, clock, four, booked):
    """**Played means played** (#655): a counted game, scored or not, is one
    *who they have played with* counts — the three others on the court, for
    each of the four."""

    to(clock, WEDNESDAY_EIGHT)

    for member in four:
        assert (await record_of(client, member))["variety"] == {
            "distinct_opponents": 3,
            "times_on_court": 3,
        }, member["name"]


async def test_each_of_them_is_asked_for_the_others_stars(client, clock, four, booked):
    """**Played for sportsmanship**, as a game with no agreed score is: a card
    for the court, run from the booked hour — the day after it, for a week —
    since nobody said when they played."""

    to(clock, WEDNESDAY_EIGHT)

    for member in four:
        cards = await open_cards_of(client, member)
        assert [card["game_id"] for card in cards] == [booked["game"]]
        assert set(cards[0]["players"]) == {
            str(other["id"]) for other in four if other is not member
        }

    to(clock, TUESDAY_SEVEN + timedelta(days=8))
    assert await open_cards_of(client, four[0]) == []
