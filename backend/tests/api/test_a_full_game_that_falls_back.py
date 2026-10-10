"""**A full game that falls back stays on Home as *Seat open*** (#624; the
mechanics §13, §14.1, Q106; the screens A8).

At an On request club a full game waits for the club's yes. When a seat opens
before it answers — a player leaves, a player's week fills with another game,
or two of the four stop fitting at the club's yes — the request is taken back
and the game is filling again. **It stays on the Home of the people still In**
as *Seat open*: nobody paid, *1 seat open · Kazimierz Padel is asked again when
it's full · nobody paid*, and nothing it asks of them. Full again, it is
*Waiting for the club* again; past its book-by, *Called off · nobody paid*. A
player who withdraws their own yes no longer finds it there, and the leaver
never does.

Every act is taken over HTTP as the phone and the desk take it, and every claim
is read where a player reads it: Home and the booking's details.

The clock stands on **Monday 5 October 2026, 08:00 in Kraków**; the game is
**Saturday 10 October, 17:00** at Kazimierz Padel — On request, padel at 120 zł
(30 zł a seat), thirty minutes to confirm, a book-by two hours before.
"""

from __future__ import annotations

from datetime import timedelta
from uuid import UUID

import pytest

from app.api.dependencies import get_clock
from app.bootstrap.composition import build_propose_games
from tests.api import players_world as players
from tests.api.club_courts_world import EXCEPTIONS
from tests.api.proposals_world import (
    MONDAY_MORNING,
    SATURDAY_FIVE,
    a_club_and_its_desk,
    a_club_selling,
    a_group,
    a_member,
    live_ids,
    makes,
    says_yes,
    sweeps,
    warsaw,
    withdraws,
)
from tests.unit.fake_clock import MovableClock

HOME = "/api/v1/home"
#: Saturday's book-by: the club's two hours' notice before the hour.
BOOK_BY = SATURDAY_FIVE - timedelta(hours=2)


@pytest.fixture
def clock(app):
    """Monday 5 October 2026, 08:00 in Kraków."""

    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


@pytest.fixture
async def kazimierz(client) -> tuple[str, dict]:
    """Kazimierz Padel, On request: the club and its desk's session."""

    return await a_club_and_its_desk(client, name="Kazimierz Padel", way="ON_REQUEST")


@pytest.fixture
async def four(client, session_factory, payments) -> list[dict]:
    """Marta, Oscar, Ewa and Sergio: padel 2,5, free every hour, each with a
    card that pays."""

    return [
        await a_member(client, session_factory, payments, name)
        for name in ("marta", "oscar", "ewa", "sergio")
    ]


@pytest.fixture
async def group(client, kazimierz, four) -> UUID:
    club, _ = kazimierz
    return await a_group(client, four[0], club, *four[1:])


@pytest.fixture
async def waiting(client, session_factory, clock, kazimierz, group, four) -> UUID:
    """Saturday's game, every seat In and put to Kazimierz Padel by Sergio's
    yes."""

    club, _ = kazimierz
    proposal = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    for player in four:
        said = await says_yes(client, player, proposal)
        assert said.status_code == 200, said.text
    assert said.json()["waiting_for_the_club"] is True, said.text
    return proposal


async def home_of(client, player: dict) -> dict:
    read = await client.get(HOME, headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()


async def cards_of(client, player: dict) -> list[dict]:
    return (await home_of(client, player))["games"]


async def details_of(client, player: dict, booking: UUID):
    return await client.get(f"/api/v1/bookings/{booking}", headers=player["headers"])


def on_the_card(card: dict) -> set[UUID]:
    return {
        UUID(tile["player_id"])
        for side in (card["sides"]["yours"], card["sides"]["theirs"])
        for tile in side
    }


def assert_seat_open_filling_again(card: dict, *, open_seats: int = 1) -> None:
    """*1 seat open · Kazimierz Padel is asked again when it's full · nobody
    paid*, asking nothing of the reader."""

    assert (card["status"], card["filling_again"], card["club_confirms"]) == (
        "SEAT_OPEN",
        True,
        True,
    )
    assert card["open_seats"] == open_seats
    assert card["needs_you"] is False
    assert (card["called_off_reason"], card["answer_by"]) == (None, None)
    assert (card["game_id"], card["court_name"]) == (None, None)
    assert card["money"] == {
        "share_grosze": 30_00,
        "paid": False,
        "free_to_leave_until": None,
        "share_state": None,
        "held_from": None,
        "taken_at": None,
        "refunded_grosze": None,
    }
    assert all(
        tile["paid"] is False
        for side in (card["sides"]["yours"], card["sides"]["theirs"])
        for tile in side
    )


async def falls_back_for(client, player: dict, booking: UUID) -> dict:
    """The game on the player's Home as *Seat open*, nobody paid, uncounted by
    the badge — and so on its details, with no Leave and no code. The card."""

    read = await home_of(client, player)
    [card] = read["games"]
    assert card["booking_id"] == str(booking)
    assert_seat_open_filling_again(card)
    # Home's badge does not count it: it asks nothing of them.
    assert read["needing_you"] == 0
    details = await details_of(client, player, booking)
    assert details.status_code == 200, details.text
    assert_seat_open_filling_again(details.json())
    # Its way out is *Withdraw*, a game still filling's — no Leave, no code.
    assert (details.json()["leaving"], details.json()["check_in"]) == (None, None)
    return card


# --------------------------------------------------------------------------- #
# Into Seat open
# --------------------------------------------------------------------------- #


async def test_a_leave_while_the_club_decides_keeps_the_game_on_the_others_home(
    client, four, waiting
):
    marta, oscar, ewa, sergio = four

    left = await withdraws(client, oscar, waiting)

    assert left.status_code == 204, left.text
    for player in (marta, ewa, sergio):
        card = await falls_back_for(client, player, waiting)
        assert on_the_card(card) == {marta["id"], ewa["id"], sergio["id"]}
        # It is in You're In too.
        assert await live_ids(client, player) == [str(waiting)]
    # The leaver's own Home: gone, as before.
    assert await cards_of(client, oscar) == []
    assert (await details_of(client, oscar, waiting)).status_code == 404


async def test_a_leave_from_the_booking_s_own_details_falls_back_as_well(
    client, four, waiting
):
    marta, oscar = four[:2]

    left = await client.post(
        f"/api/v1/bookings/{waiting}/departure", headers=oscar["headers"]
    )

    assert left.status_code == 200, left.text
    assert left.json() == {"left": "WHILE_WAITING_FOR_THE_CLUB"}
    [card] = await cards_of(client, marta)
    assert_seat_open_filling_again(card)


async def test_a_week_that_fills_with_another_game_falls_back_the_same(
    client, session_factory, clock, payments, four, waiting
):
    """Sergio plays one game a week. Another of his games, at Ogrody 33, books
    first: his yes on Saturday's pauses, and the request is taken back."""

    marta, oscar, ewa, sergio = four
    capped = await client.put(
        "/api/v1/players/me/games-and-money",
        json={"games_per_week": 1, "most_ill_pay_grosze": None},
        headers=sergio["headers"],
    )
    assert capped.status_code == 200, capped.text
    await a_game_that_books_elsewhere(
        client, session_factory, clock, payments, sergio, start=warsaw(9, 18)
    )

    for player in (marta, oscar, ewa):
        card = await falls_back_for(client, player, waiting)
        assert on_the_card(card) == {marta["id"], oscar["id"], ewa["id"]}
    assert str(waiting) not in [
        card["booking_id"] for card in await cards_of(client, sergio)
    ]


async def test_two_players_who_no_longer_fit_at_the_club_s_yes_fall_back_the_same(
    client, kazimierz, four, waiting
):
    """Marta blocked Oscar while the club decided; before the block took her
    yeses back, the club said yes. The later of their two yeses — Oscar's — no
    longer counts: nobody paid, and the game is filling again."""

    _, desk = kazimierz
    marta, oscar, ewa, sergio = four
    blocked = await players.block_between(client, marta["token"], oscar["id"])
    assert blocked.status_code in (200, 201, 204), blocked.text

    accepted = await client.post(
        f"/api/v1/club/bookings/{waiting}/acceptance", headers=desk
    )

    assert accepted.json()["outcome"] == "SEAT_OPENED", accepted.text
    for player in (marta, ewa, sergio):
        await falls_back_for(client, player, waiting)
    assert await cards_of(client, oscar) == []


# --------------------------------------------------------------------------- #
# Out of Seat open
# --------------------------------------------------------------------------- #


async def test_full_again_it_waits_for_the_club_again(
    client, payments, session_factory, clock, group, four, waiting
):
    marta, oscar = four[:2]
    await withdraws(client, oscar, waiting)
    ania = await a_member(client, session_factory, payments, "ania")
    joined = await client.post(
        f"/api/v1/groups/{group}/membership", headers=ania["headers"]
    )
    assert joined.status_code in (200, 201), joined.text
    clock.move(timedelta(minutes=5))

    again = await says_yes(client, oscar, waiting)

    assert again.json()["waiting_for_the_club"] is True, again.text
    for player in four:
        [card] = await cards_of(client, player)
        assert (card["status"], card["filling_again"]) == (
            "WAITING_FOR_THE_CLUB",
            False,
        )
        assert card["open_seats"] == 0


async def test_past_its_book_by_it_is_called_off_and_kept_on_home(
    client, session_factory, clock, four, waiting
):
    marta, oscar = four[:2]
    await withdraws(client, oscar, waiting)
    clock.move(BOOK_BY - MONDAY_MORNING)

    # Read off the clock, before the sweep records it — and after.
    for _ in ("before", "after"):
        [card] = await cards_of(client, marta)
        assert (card["status"], card["called_off_reason"]) == (
            "CALLED_OFF",
            "BOOK_BY_PASSED",
        )
        assert (card["filling_again"], card["open_seats"]) == (True, 0)
        assert (card["money"]["paid"], card["money"]["refunded_grosze"]) == (
            False,
            None,
        )
        assert card["needs_you"] is False
        await sweeps(session_factory, clock)


async def test_a_seat_opening_after_its_book_by_while_the_club_decides_calls_it_off(
    client, clock, four, kazimierz, group, session_factory
):
    """The last yes landed at 14:50 on Saturday, ten minutes before the
    book-by, so the club has until 15:20; at 15:10 Oscar leaves. The game can
    no longer fill: it is called off, nobody paid."""

    club, _ = kazimierz
    proposal = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    for player in four[:3]:
        await says_yes(client, player, proposal)
    clock.move(warsaw(10, 14) + timedelta(minutes=50) - clock.now())
    last = await says_yes(client, four[3], proposal)
    assert last.json()["waiting_for_the_club"] is True, last.text
    clock.move(timedelta(minutes=20))

    left = await withdraws(client, four[1], proposal)

    assert left.status_code == 204, left.text
    for player in (four[0], *four[2:]):
        [card] = await cards_of(client, player)
        assert (card["status"], card["called_off_reason"]) == (
            "CALLED_OFF",
            "BOOK_BY_PASSED",
        )
    assert await cards_of(client, four[1]) == []


async def test_a_player_who_withdraws_their_own_yes_no_longer_finds_it(
    client, four, waiting
):
    marta, oscar, ewa, sergio = four
    await withdraws(client, oscar, waiting)

    withdrawn = await withdraws(client, ewa, waiting)

    assert withdrawn.status_code == 204, withdrawn.text
    assert await cards_of(client, ewa) == []
    assert (await details_of(client, ewa, waiting)).status_code == 404
    for player in (marta, sergio):
        [card] = await cards_of(client, player)
        assert_seat_open_filling_again(card, open_seats=2)
        assert on_the_card(card) == {marta["id"], sergio["id"]}


async def test_leaving_a_game_gone_back_to_filling_withdraws_the_yes(
    client, four, waiting
):
    """A screen opened while the club still decided offers *Leave*: on the game
    gone back to filling it takes the yes back, as *Withdraw* does."""

    marta, oscar, ewa = four[:3]
    await withdraws(client, oscar, waiting)

    left = await client.post(
        f"/api/v1/bookings/{waiting}/departure", headers=ewa["headers"]
    )

    assert left.status_code == 200, left.text
    assert await cards_of(client, ewa) == []
    assert str(waiting) not in await live_ids(client, ewa)
    [card] = await cards_of(client, marta)
    assert card["open_seats"] == 2


async def test_a_game_gone_back_to_filling_that_loses_its_court_is_called_off(
    client, session_factory, clock, kazimierz, group, four, waiting
):
    """Kazimierz Padel closes Saturday's 17:00 for a repair while the game is
    filling again: no court is left at its hour, so the card is over."""

    _, desk = kazimierz
    await withdraws(client, four[1], waiting)
    closed = await client.post(
        EXCEPTIONS,
        json={
            "court_ids": None,
            "first_day": "2026-10-10",
            "last_day": "2026-10-10",
            "from_hour": 17,
            "until_hour": 18,
            "reason": "Repair",
        },
        headers=desk,
    )
    assert closed.status_code == 201, closed.text

    async with session_factory() as session:
        proposed = await build_propose_games(session, clock=clock).execute(group)

    assert proposed.lost == 1
    [card] = await cards_of(client, four[0])
    assert (card["status"], card["called_off_reason"]) == (
        "CALLED_OFF",
        "COURT_HOUR_LOST",
    )


# --------------------------------------------------------------------------- #
# Nobody else's
# --------------------------------------------------------------------------- #


async def test_the_club_s_day_never_lists_a_game_gone_back_to_filling(
    client, kazimierz, four, waiting
):
    _, desk = kazimierz
    await withdraws(client, four[1], waiting)

    day = await client.get(
        "/api/v1/club/bookings", params={"date": "2026-10-10"}, headers=desk
    )

    assert day.status_code == 200, day.text
    assert day.json()["bookings"] == []
    cancelled = await client.post(
        f"/api/v1/club/bookings/{waiting}/cancellation",
        json={"reason": "WEATHER"},
        headers=desk,
    )
    assert cancelled.status_code == 404, cancelled.text


async def a_game_that_books_elsewhere(
    client, session_factory, clock, payments, player: dict, *, start
) -> None:
    """``player`` and three others book a game at Ogrody 33, which books at
    once."""

    ogrody = await a_club_selling(client, name="Ogrody 33", point=(50.07, 19.94))
    others = [
        await a_member(client, session_factory, payments, name)
        for name in ("ania", "piotr", "marek")
    ]
    elsewhere = await a_group(client, player, ogrody, *others)
    game = await makes(
        session_factory,
        clock,
        pool_id=elsewhere,
        club_id=ogrody,
        start=start,
        versions=((player, *others),),
    )
    for one in (*others, player):
        said = await says_yes(client, one, game)
        assert said.status_code == 200, said.text
    assert said.json()["booked"] is not None, said.text
