"""**Turning up is caught at the court** (#657; ``docs/adr/0195`` §3, the
mechanics §15.1) — read from outside.

Wednesday 14 October, tennis **17:00–18:00 at Ogrody 33**, Ivan against Oscar,
40 zł each. Only a real absence starts anything:

- Ivan, 40 m from the club, taps *Oscar isn't here yet* at 17:10, and Oscar
  taps *I'm here* at 17:22, 120 m away: **Came late**.
- Oscar never comes: **Didn't come** at 17:30, and the game takes no score.
- Oscar taps *I was there* the next morning and Ivan confirms: **Came late**.
- Oscar walks in at 17:08: nothing is recorded.

Every tap is taken over HTTP as the phone sends it — a one-shot fix in its body
— and every claim is read where a player reads it: the game (``GET /games``),
its details, Home and the record. **The coordinates are never kept**: the event
log, the outbox and the logs are searched for them. The clock starts on Monday 5
October, 08:00 in Kraków, and moves.
"""

from __future__ import annotations

import logging
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.api.dependencies import get_clock
from app.infrastructure.events.event_delivery_model import EventOutboxORM
from app.infrastructure.events.event_store_model import EventStoreORM
from app.kernel import Sport
from tests.api.players_world import deliver_the_outbox
from tests.api.proposals_world import (
    MONDAY_MORNING,
    a_club_selling,
    a_group,
    a_player,
    makes,
    says_yes,
    the_cut_off_comes,
    warsaw,
)
from tests.unit.fake_clock import MovableClock

#: Ogrody 33's map point, as its desk dropped it.
OGRODY = (50.0600, 19.9400)
#: Metres of latitude in a degree, near enough for a test's offsets.
METRES_PER_DEGREE = 111_195.0
#: Wednesday 14 October, 17:00 in Kraków — their hour.
FIVE = warsaw(14, 17)
HALF_PAST = FIVE + timedelta(minutes=30)
#: Thursday 17:30 — the late claim's day is over.
THURSDAY_HALF_PAST = HALF_PAST + timedelta(hours=24)
GAMES = "/api/v1/games"


def north_of_the_club(metres: float, *, accuracy_m: float = 10.0) -> dict:
    """A fix ``metres`` due north of Ogrody 33's point."""

    return {
        "latitude": OGRODY[0] + metres / METRES_PER_DEGREE,
        "longitude": OGRODY[1],
        "accuracy_m": accuracy_m,
    }


AT_THE_CLUB = north_of_the_club(40)


@pytest.fixture
def clock(app, payments):
    """Monday 5 October 2026, 08:00 in Kraków."""

    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    payments.clock = fixed
    return fixed


def to(clock: MovableClock, moment) -> None:
    clock.move(moment - clock.now())


@pytest.fixture
async def ivan_and_oscar(client, payments) -> tuple[dict, dict]:
    return tuple(  # type: ignore[return-value]
        [
            await a_player(client, payments, name, sports=(Sport.TENNIS,))
            for name in ("ivan", "oscar")
        ]
    )


@pytest.fixture
async def booked(client, session_factory, clock, ivan_and_oscar) -> dict:
    """Their singles at Ogrody 33 on Wednesday at 17:00 — tennis at 80 zł, so
    40 zł each — booked, its shares taken at the club's cut-off."""

    ivan, oscar = ivan_and_oscar
    club = await a_club_selling(client, name="Ogrody 33", point=OGRODY)
    group = await a_group(client, ivan, club, oscar)
    proposal = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=FIVE,
        sport=Sport.TENNIS,
        versions=((ivan, oscar),),
    )
    await says_yes(client, ivan, proposal)
    said = await says_yes(client, oscar, proposal)
    game = said.json()["booked"]
    assert game is not None, said.text
    await the_cut_off_comes(session_factory, clock, at=FIVE - timedelta(hours=24))
    await deliver_the_outbox(session_factory)
    return {"booking": game["booking_id"], "game": game["game_id"]}


async def not_here_yet(client, by: dict, game: str, absent: dict, *, fix=AT_THE_CLUB):
    return await client.post(
        f"{GAMES}/{game}/attendance/not-here-yet",
        json={"player_id": str(absent["id"]), "location": fix},
        headers=by["headers"],
    )


async def arrived(client, by: dict, game: str, who: dict, *, fix=AT_THE_CLUB):
    return await client.post(
        f"{GAMES}/{game}/attendance/arrival",
        json={"player_id": str(who["id"]), "location": fix},
        headers=by["headers"],
    )


async def i_was_there(client, by: dict, game: str):
    return await client.post(f"{GAMES}/{game}/attendance/claim", headers=by["headers"])


async def yes_they_were_here(client, by: dict, game: str, claimant: dict):
    return await client.post(
        f"{GAMES}/{game}/attendance/confirmation",
        json={"player_id": str(claimant["id"])},
        headers=by["headers"],
    )


async def a_score(client, by: dict, game: str):
    return await client.post(
        f"{GAMES}/{game}/result",
        json={"score": {"sets": [{"a": 6, "b": 4}, {"a": 6, "b": 3}]}},
        headers=by["headers"],
    )


async def game_of(client, player: dict, game_id: str) -> dict:
    read = await client.get(GAMES, headers=player["headers"])
    assert read.status_code == 200, read.text
    [found] = [g for g in read.json()["games"] if g["game_id"] == game_id]
    return found


async def details_of(client, player: dict, booking: str) -> dict:
    read = await client.get(f"/api/v1/bookings/{booking}", headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()


async def reliability_of(client, player: dict) -> dict:
    """Their own record's Player reliability — the figure and the counts it is
    read beside (#659)."""

    read = await client.get(
        "/api/v1/players/me/record",
        params={"sport": "TENNIS"},
        headers=player["headers"],
    )
    assert read.status_code == 200, read.text
    return read.json()["reliability"]


def figure(reliability: dict) -> tuple:
    """The figure, its band and *Shows up* / *Being late* / *Keeps plans*."""

    return (
        reliability["player_score"],
        reliability["band"],
        (reliability["turned_up"], reliability["turned_up_of"]),
        reliability["late"],
        (reliability["kept"], reliability["kept_of"]),
    )


def refused(response, status: int, code: str) -> str:
    assert (response.status_code, response.json().get("code")) == (status, code), (
        response.text
    )
    return response.json()["message"]


# --------------------------------------------------------------------------- #
# The four outcomes
# --------------------------------------------------------------------------- #


async def test_ivan_taps_at_17_10_oscar_s_i_m_here_at_17_22_is_came_late_and_scored(
    client, clock, ivan_and_oscar, booked
):
    ivan, oscar = ivan_and_oscar
    to(clock, FIVE + timedelta(minutes=10))

    tapped = await not_here_yet(client, ivan, booked["game"], oscar)

    assert tapped.status_code == 200, tapped.text
    assert tapped.json()["standing"] == "NOT_HERE_YET"
    [row] = tapped.json()["attendance"]
    assert (row["player_id"], row["name"], row["state"]) == (
        str(oscar["id"]),
        "oscar",
        "WAITING",
    )
    assert row["arrive_by"] == HALF_PAST.isoformat().replace("+00:00", "Z")
    assert row["arrived_at"] is None
    oscars = await game_of(client, oscar, booked["game"])
    assert oscars["standing"] == "NOT_HERE_YET"

    to(clock, FIVE + timedelta(minutes=22))
    here = await arrived(
        client, oscar, booked["game"], oscar, fix=north_of_the_club(120)
    )

    assert here.status_code == 200, here.text
    assert here.json()["standing"] == "AWAITING_ENTRY"
    [row] = here.json()["attendance"]
    assert row["state"] == "CAME_LATE"
    # **Came late: −10, late once** (#659) — priced at the arrival, and the
    # booking he held to its hour kept.
    assert figure(await reliability_of(client, oscar)) == (
        90,
        "VERY_HIGH",
        (1, 1),
        1,
        (1, 1),
    )
    to(clock, FIVE + timedelta(minutes=65))
    scored = await a_score(client, ivan, booked["game"])
    assert scored.status_code == 200, scored.text
    assert scored.json()["standing"] == "AWAITING_ANSWER"


async def test_oscar_never_comes_he_didn_t_come_at_17_30_and_the_game_takes_no_score(
    client, clock, ivan_and_oscar, booked
):
    ivan, oscar = ivan_and_oscar
    to(clock, FIVE + timedelta(minutes=10))
    await not_here_yet(client, ivan, booked["game"], oscar)

    to(clock, HALF_PAST - timedelta(seconds=1))
    assert (await game_of(client, ivan, booked["game"]))["standing"] == "NOT_HERE_YET"
    to(clock, HALF_PAST)
    game = await game_of(client, ivan, booked["game"])

    assert game["standing"] == "DIDNT_COME"
    assert [row["state"] for row in game["attendance"]] == ["DIDNT_COME"]
    to(clock, FIVE + timedelta(minutes=65))
    refused(await a_score(client, ivan, booked["game"]), 409, "somebody_did_not_come")
    oscars, ivans = (
        await details_of(client, oscar, booked["booking"]),
        await details_of(client, ivan, booked["booking"]),
    )
    assert (oscars["status"], oscars["uncounted_reason"]) == ("UNCOUNTED", "DIDNT_COME")
    # His *I was there* is still his to say; Ivan has nothing to do.
    assert (oscars["needs_you"], ivans["needs_you"]) == (True, False)


async def test_didn_t_come_costs_twenty_five_once_the_late_claim_s_day_is_over(
    client, clock, ivan_and_oscar, booked
):
    """**Priced once** (#659; ``docs/adr/0195`` §1): −25 on *Shows up*, and the
    booking he held to its hour stays kept. Ivan, who came, turned up to a game
    that never counted — and earns nothing for it."""

    ivan, oscar = ivan_and_oscar
    to(clock, FIVE + timedelta(minutes=10))
    await not_here_yet(client, ivan, booked["game"], oscar)

    to(clock, THURSDAY_HALF_PAST - timedelta(seconds=1))
    assert figure(await reliability_of(client, oscar)) == (
        100,
        "VERY_HIGH",
        (0, 0),
        0,
        (1, 1),
    )
    to(clock, THURSDAY_HALF_PAST)

    assert figure(await reliability_of(client, oscar)) == (
        75,
        "HIGH",
        (0, 1),
        0,
        (1, 1),
    )
    assert figure(await reliability_of(client, ivan)) == (
        100,
        "VERY_HIGH",
        (1, 1),
        0,
        (1, 1),
    )


async def test_oscar_s_i_was_there_next_morning_confirmed_by_ivan_is_came_late(
    client, clock, ivan_and_oscar, booked
):
    ivan, oscar = ivan_and_oscar
    to(clock, FIVE + timedelta(minutes=10))
    await not_here_yet(client, ivan, booked["game"], oscar)
    to(clock, warsaw(15, 9))

    claimed = await i_was_there(client, oscar, booked["game"])

    assert claimed.status_code == 200, claimed.text
    assert claimed.json()["standing"] == "DIDNT_COME"
    [row] = claimed.json()["attendance"]
    assert row["state"] == "CLAIMED"
    assert row["claim_by"] == THURSDAY_HALF_PAST.isoformat().replace("+00:00", "Z")
    # Ivan is asked *Were they there?*; Oscar has done his part.
    assert (await details_of(client, ivan, booked["booking"]))["needs_you"] is True
    assert (await details_of(client, oscar, booked["booking"]))["needs_you"] is False

    confirmed = await yes_they_were_here(client, ivan, booked["game"], oscar)

    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["standing"] == "AWAITING_ENTRY"
    assert [row["state"] for row in confirmed.json()["attendance"]] == ["CONFIRMED"]
    scored = await a_score(client, ivan, booked["game"])
    assert scored.status_code == 200, scored.text
    to(clock, THURSDAY_HALF_PAST + timedelta(days=2))
    # Came late: turned up, late once, −10 — and nothing back for the game.
    assert figure(await reliability_of(client, oscar)) == (
        90,
        "VERY_HIGH",
        (1, 1),
        1,
        (1, 1),
    )


async def test_oscar_walking_in_at_17_08_records_nothing(
    client, clock, ivan_and_oscar, booked
):
    ivan, oscar = ivan_and_oscar
    to(clock, FIVE + timedelta(minutes=2))
    await not_here_yet(client, ivan, booked["game"], oscar)
    to(clock, FIVE + timedelta(minutes=8))

    here = await arrived(client, ivan, booked["game"], oscar)

    assert here.status_code == 200, here.text
    assert here.json()["standing"] == "AWAITING_ENTRY"
    assert [row["state"] for row in here.json()["attendance"]] == ["ON_TIME"]
    to(clock, warsaw(15, 18))
    assert (await game_of(client, oscar, booked["game"]))["standing"] == (
        "PLAYED_NO_SCORE"
    )
    # On time: nothing recorded, and a game played through like Ivan's.
    assert figure(await reliability_of(client, oscar)) == (
        100,
        "VERY_HIGH",
        (1, 1),
        0,
        (1, 1),
    )


async def test_nobody_tapping_ends_the_game_as_it_always_did(
    client, clock, ivan_and_oscar, booked
):
    ivan, _ = ivan_and_oscar
    to(clock, warsaw(15, 18))

    game = await game_of(client, ivan, booked["game"])

    assert (game["standing"], game["attendance"]) == ("PLAYED_NO_SCORE", [])


# --------------------------------------------------------------------------- #
# Refusals, in plain sentences
# --------------------------------------------------------------------------- #


async def test_a_tap_from_2_km_away_is_refused_and_names_the_club(
    client, clock, ivan_and_oscar, booked
):
    ivan, oscar = ivan_and_oscar
    to(clock, FIVE + timedelta(minutes=10))

    message = refused(
        await not_here_yet(
            client, ivan, booked["game"], oscar, fix=north_of_the_club(2_000)
        ),
        409,
        "not_at_the_club",
    )

    assert message == "You can say so only from Ogrody 33."
    assert (await game_of(client, ivan, booked["game"]))["attendance"] == []


async def test_a_wandering_fix_inside_a_hall_still_passes(
    client, clock, ivan_and_oscar, booked
):
    """440 m off the point with the phone saying it could be 150 m out: the
    accuracy is allowed for, up to 200 m."""

    ivan, oscar = ivan_and_oscar
    to(clock, FIVE + timedelta(minutes=10))

    tapped = await not_here_yet(
        client,
        ivan,
        booked["game"],
        oscar,
        fix=north_of_the_club(440, accuracy_m=150),
    )

    assert tapped.status_code == 200, tapped.text


async def test_a_tap_at_17_31_is_refused_and_so_is_one_before_the_hour(
    client, clock, ivan_and_oscar, booked
):
    ivan, oscar = ivan_and_oscar
    to(clock, FIVE - timedelta(minutes=1))
    refused(
        await not_here_yet(client, ivan, booked["game"], oscar),
        409,
        "the_game_has_not_started",
    )

    to(clock, FIVE + timedelta(minutes=31))

    message = refused(
        await not_here_yet(client, ivan, booked["game"], oscar),
        409,
        "the_tap_window_has_closed",
    )
    assert message == "That can be said only in the first 30 minutes of the game."


async def test_a_tap_about_yourself_is_refused(client, clock, ivan_and_oscar, booked):
    ivan, _ = ivan_and_oscar
    to(clock, FIVE + timedelta(minutes=10))

    message = refused(
        await not_here_yet(client, ivan, booked["game"], ivan),
        400,
        "not_about_yourself",
    )

    assert message == "You can't say that about yourself."


async def test_a_player_already_arrived_is_refused(
    client, clock, ivan_and_oscar, booked
):
    ivan, oscar = ivan_and_oscar
    to(clock, FIVE + timedelta(minutes=10))
    await not_here_yet(client, ivan, booked["game"], oscar)
    await arrived(client, oscar, booked["game"], oscar)

    message = refused(
        await arrived(client, ivan, booked["game"], oscar), 409, "already_arrived"
    )
    refused(
        await not_here_yet(client, ivan, booked["game"], oscar), 409, "already_arrived"
    )
    assert message == "They're already here."


async def test_the_late_claim_and_its_confirmation_have_their_day_and_no_more(
    client, clock, ivan_and_oscar, booked
):
    ivan, oscar = ivan_and_oscar
    to(clock, FIVE + timedelta(minutes=10))
    await not_here_yet(client, ivan, booked["game"], oscar)
    refused(
        await i_was_there(client, oscar, booked["game"]), 409, "the_tap_window_is_open"
    )
    refused(
        await yes_they_were_here(client, ivan, booked["game"], oscar),
        409,
        "nothing_to_confirm",
    )

    to(clock, THURSDAY_HALF_PAST)

    refused(
        await i_was_there(client, oscar, booked["game"]),
        409,
        "the_late_claim_has_closed",
    )


async def test_somebody_off_the_court_is_told_nothing_about_it(
    client, clock, payments, ivan_and_oscar, booked
):
    _, oscar = ivan_and_oscar
    stranger = await a_player(client, payments, "obcy", sports=(Sport.TENNIS,))
    to(clock, FIVE + timedelta(minutes=10))

    refused(
        await not_here_yet(client, stranger, booked["game"], oscar),
        403,
        "you_were_not_on_this_court",
    )


async def test_a_fix_off_the_map_is_refused_before_anything_is_asked(
    client, clock, ivan_and_oscar, booked
):
    ivan, oscar = ivan_and_oscar
    to(clock, FIVE + timedelta(minutes=10))

    off = await not_here_yet(
        client,
        ivan,
        booked["game"],
        oscar,
        fix={"latitude": 91, "longitude": 0, "accuracy_m": 5},
    )

    assert off.status_code == 422, off.text


async def test_a_player_awaited_says_nothing_about_who_else_is_here(
    client, clock, ivan_and_oscar, booked
):
    ivan, oscar = ivan_and_oscar
    to(clock, FIVE + timedelta(minutes=10))
    await not_here_yet(client, ivan, booked["game"], oscar)

    message = refused(
        await not_here_yet(client, oscar, booked["game"], ivan),
        409,
        "you_are_not_here_yourself",
    )

    assert message == "You're marked as not here yourself."


async def test_a_score_put_up_from_home_at_17_01_does_not_stop_the_tap(
    client, clock, ivan_and_oscar, booked
):
    """A score carries no location, so it could otherwise shield the player it
    names: it waits with the game, and nobody agrees with it meanwhile."""

    ivan, oscar = ivan_and_oscar
    to(clock, FIVE + timedelta(minutes=1))
    assert (await a_score(client, oscar, booked["game"])).status_code == 200
    to(clock, FIVE + timedelta(minutes=10))

    tapped = await not_here_yet(client, ivan, booked["game"], oscar)

    assert tapped.status_code == 200, tapped.text
    assert tapped.json()["standing"] == "NOT_HERE_YET"
    refused(
        await client.post(
            f"{GAMES}/{booked['game']}/result/acceptance", headers=ivan["headers"]
        ),
        409,
        "somebody_is_not_here_yet",
    )


async def test_while_he_is_awaited_only_oscar_is_asked_for_anything(
    client, clock, ivan_and_oscar, booked
):
    ivan, oscar = ivan_and_oscar
    to(clock, FIVE + timedelta(minutes=10))
    await not_here_yet(client, ivan, booked["game"], oscar)

    oscars = await details_of(client, oscar, booked["booking"])
    ivans = await details_of(client, ivan, booked["booking"])

    assert (oscars["status"], oscars["needs_you"]) == ("NEEDS_RESULT", True)
    assert (ivans["status"], ivans["needs_you"]) == ("NEEDS_RESULT", False)


async def test_a_fix_that_is_not_a_number_is_refused(
    client, clock, ivan_and_oscar, booked
):
    """``Infinity`` is not JSON, but a lenient encoder sends it; it is refused
    before anything is measured, never a server error."""

    ivan, oscar = ivan_and_oscar
    to(clock, FIVE + timedelta(minutes=10))

    endless = await client.post(
        f"{GAMES}/{booked['game']}/attendance/not-here-yet",
        content=(
            f'{{"player_id": "{oscar["id"]}", "location": {{"latitude": '
            f'{OGRODY[0]}, "longitude": {OGRODY[1]}, "accuracy_m": Infinity}}}}'
        ),
        headers={**ivan["headers"], "Content-Type": "application/json"},
    )

    assert endless.status_code == 422, endless.text


# --------------------------------------------------------------------------- #
# The coordinates are never kept, and the old report is gone
# --------------------------------------------------------------------------- #


async def test_no_coordinate_is_kept_in_the_log_the_outbox_or_a_log_line(
    client, session_factory, clock, caplog, ivan_and_oscar, booked
):
    caplog.set_level(logging.DEBUG)
    ivan, oscar = ivan_and_oscar
    fix = north_of_the_club(77, accuracy_m=13.25)
    to(clock, FIVE + timedelta(minutes=10))
    await not_here_yet(client, ivan, booked["game"], oscar, fix=fix)
    to(clock, FIVE + timedelta(minutes=12))
    await arrived(client, oscar, booked["game"], oscar, fix=fix)
    await deliver_the_outbox(session_factory)

    async with session_factory() as session:
        games = [
            str(row)
            for row in (
                await session.scalars(
                    select(EventStoreORM.payload).where(
                        EventStoreORM.aggregate_type == "game"
                    )
                )
            ).all()
        ]
        stored = [
            str(row)
            for row in (await session.scalars(select(EventStoreORM.payload))).all()
        ] + [
            str(row)
            for row in (await session.scalars(select(EventOutboxORM.payload))).all()
        ]
    latitude = f"{fix['latitude']}"[:9]

    assert sum("noted_by" in text for text in games) == 2
    for text in games:
        assert not {"latitude", "longitude", "accuracy"} & set(
            word.strip("'\"{}:,") for word in text.split()
        )
    for text in [*stored, caplog.text]:
        assert latitude not in text
        assert "13.25" not in text


async def test_the_no_show_report_and_its_dispute_are_gone(
    client, clock, ivan_and_oscar, booked
):
    ivan, oscar = ivan_and_oscar
    to(clock, FIVE + timedelta(hours=2))

    report = await client.post(
        f"{GAMES}/{booked['game']}/no-shows",
        json={"player_id": str(oscar["id"])},
        headers=ivan["headers"],
    )
    dispute = await client.post(
        f"{GAMES}/{booked['game']}/no-shows/dispute", headers=oscar["headers"]
    )

    assert (report.status_code, dispute.status_code) == (404, 404)
    assert "no_shows" not in await game_of(client, ivan, booked["game"])
