"""**Every ending and fall-back of a full game is told in its own words** (#623;
the mechanics §13, §17.2, Q104, Q108; the screens A9).

Everybody still in a full game is told when it ends or falls back to filling,
and never whose card failed, whose week filled or who no longer fits; a named
leaver keeps their name. A player who left is told only when it touches them —
the call-off their empty seat caused, or the club's cancel that refunds them —
in a leaver's words, never promised a new game.

A full game falls back while it waits for one payment (#625): Ewa's bank wants
her to confirm every payment, so the last yes leaves her share refused and the
game waiting for it, and a seat opening meanwhile sends it back to filling.

Every act is taken over HTTP as the phone and the desk take it; the outbox is
drained the way the worker drains it, and every claim is read off the list
behind the bell and the mailbox.

The clock stands on **Monday 5 October 2026, 08:00 in Kraków**; the game is
**Saturday 10 October, 17:00** at Bonarka Arena, which books at once — 40 zł a
seat, a book-by two hours before and a 24-hour cut-off.
"""

from __future__ import annotations

from datetime import timedelta
from uuid import UUID

import pytest

from app.api.dependencies import get_clock
from app.bootstrap.composition import build_propose_games, build_the_cut_off
from app.core.config import get_settings
from app.modules.payments.domain.entered_cards import A_CARD_THE_BANK_ALWAYS_CHECKS
from tests.api.club_courts_world import EXCEPTIONS
from tests.api.proposals_world import (
    MONDAY_MORNING,
    SATURDAY_FIVE,
    a_club_and_its_desk,
    a_club_selling,
    a_group,
    a_member,
    makes,
    runs_out,
    saves_a_card,
    says_yes,
    sweeps,
    warsaw,
    withdraws,
)
from tests.unit.fake_clock import MovableClock

NOTICES = "/api/v1/players/me/notices"
#: Saturday's book-by at Bonarka Arena: two hours' notice before the hour.
BOOK_BY = SATURDAY_FIVE - timedelta(hours=2)
#: Bonarka Arena's cut-off: a day before the hour.
CUT_OFF = SATURDAY_FIVE - timedelta(hours=24)
#: Thirty minutes from the last yes on Monday morning: Ewa's time to fix her
#: card ends at 08:30 in Kraków.
EWA_S_TIME_ENDS = MONDAY_MORNING + timedelta(minutes=30)

FILLING_AGAIN = (
    "Your Sat 17:00 at Bonarka Arena is filling again",
    "A seat opened — nobody paid.",
)


@pytest.fixture
def clock(app):
    """Monday 5 October 2026, 08:00 in Kraków."""

    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


@pytest.fixture
async def four(client, session_factory, payments) -> list[dict]:
    """Marta, Oscar, Ewa and Sergio: padel 2,5, free every hour, each with a
    card that pays."""

    return [
        await a_member(client, session_factory, payments, name)
        for name in ("marta", "oscar", "ewa", "sergio")
    ]


@pytest.fixture
async def bonarka(client) -> tuple[str, dict]:
    """Bonarka Arena, Instant, padel at 160 zł — 40 zł a seat."""

    return await a_club_and_its_desk(client, way="INSTANT", padel_grosze=160_00)


async def a_full_game(client, session_factory, clock, club: str, four) -> UUID:
    """The four's game on Saturday at 17:00, every one of them In: booked — or
    waiting for one payment, when a share is refused."""

    group = await a_group(client, four[0], club, *four[1:])
    proposal = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    for player in four:
        said = await says_yes(client, player, proposal)
        assert said.status_code == 200, said.text
    return proposal


@pytest.fixture
async def waiting(
    client, session_factory, clock, payments, bonarka, four, mailbox
) -> UUID:
    """Saturday's game at Bonarka Arena, full with Sergio's yes and waiting for
    Ewa's payment, which her bank wants her to confirm — and delivered, so what
    a test does next is told after it."""

    club, _ = bonarka
    ewa = four[2]
    await saves_a_card(client, payments, ewa["headers"], A_CARD_THE_BANK_ALWAYS_CHECKS)
    proposal = await a_full_game(client, session_factory, clock, club, four)
    await mailbox.drain()
    return proposal


@pytest.fixture
async def booked(client, session_factory, clock, bonarka, four, mailbox) -> UUID:
    """Saturday's game, booked at Bonarka Arena by Sergio's yes, delivered."""

    club, _ = bonarka
    proposal = await a_full_game(client, session_factory, clock, club, four)
    await mailbox.drain()
    return proposal


async def told(client, mailbox, player: dict) -> list[tuple[str, str]]:
    """Every notice in the player's list, newest first: its title and body."""

    await mailbox.drain()
    read = await client.get(NOTICES, headers=player["headers"])
    assert read.status_code == 200, read.text
    return [(notice["title"], notice["body"]) for notice in read.json()["notices"]]


async def last_told(client, mailbox, player: dict) -> tuple[str, str]:
    return (await told(client, mailbox, player))[0]


async def subjects_to(mailbox, player: dict) -> list[str]:
    return [
        email.subject for email in await mailbox.to(f"{player['name']}@example.com")
    ]


async def leaves(client, player: dict, booking: UUID) -> None:
    left = await client.post(
        f"/api/v1/bookings/{booking}/departure", headers=player["headers"]
    )
    assert left.status_code == 200, left.text


async def cuts_off(session_factory, clock):
    async with session_factory() as session:
        return await build_the_cut_off(
            session, clock=clock, settings=get_settings()
        ).execute()


# --------------------------------------------------------------------------- #
# Falling back to filling, while a payment is awaited
# --------------------------------------------------------------------------- #


async def test_a_named_leave_before_the_book_by_keeps_its_name(
    client, four, waiting, mailbox
):
    marta, oscar, ewa, sergio = four

    assert (await withdraws(client, oscar, waiting)).status_code == 204

    for player in (marta, ewa, sergio):
        assert await last_told(client, mailbox, player) == (
            "oscar left your game",
            "Padel at Bonarka Arena · Sat 10 Oct, 17:00 — it's filling again.",
        )


async def test_a_week_that_fills_with_another_game_is_told_as_filling_again(
    client, session_factory, clock, payments, four, waiting, mailbox
):
    """Sergio plays one game a week, and another of his games books while
    Saturday's waits for Ewa's payment: his yes pauses and the game falls back.
    The others are told it is filling again — never whose week filled."""

    marta, oscar, ewa, sergio = four
    capped = await client.put(
        "/api/v1/players/me/games-and-money",
        json={"games_per_week": 1, "most_ill_pay_grosze": None},
        headers=sergio["headers"],
    )
    assert capped.status_code == 200, capped.text
    told_sergio = await told(client, mailbox, sergio)

    await a_game_that_books_elsewhere(
        client, session_factory, clock, payments, sergio, start=warsaw(9, 18)
    )

    for player in (marta, oscar, ewa):
        notice = await last_told(client, mailbox, player)
        assert notice == FILLING_AGAIN
        assert "sergio" not in " ".join(notice)
    # Sergio is told of his own other game, and nothing of this one.
    assert [
        title for title, _ in (await told(client, mailbox, sergio))[: -len(told_sergio)]
    ] == ["It's a game! · 30 zł held"]


async def test_a_paused_yes_that_comes_back_and_fills_it_is_told_as_any_fill(
    client, session_factory, clock, payments, bonarka, four, mailbox
):
    """Sergio plays one game a week. He said yes to Saturday's game, then
    another of his games booked and paused that yes, and Ewa's yes left
    Saturday's one seat short. He leaves his other game, his week has room
    again, and his paused yes comes back and fills Saturday's. All four are told
    *It's a game!*, as at any fill — Sergio's copy too, since no act of his own
    filled it."""

    club, _ = bonarka
    marta, oscar, ewa, sergio = four
    capped = await client.put(
        "/api/v1/players/me/games-and-money",
        json={"games_per_week": 1, "most_ill_pay_grosze": None},
        headers=sergio["headers"],
    )
    assert capped.status_code == 200, capped.text
    group = await a_group(client, marta, club, oscar, ewa, sergio)
    proposal = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    for player in (marta, oscar, sergio):
        assert (await says_yes(client, player, proposal)).status_code == 200
    elsewhere = await a_game_that_books_elsewhere(
        client, session_factory, clock, payments, sergio, start=warsaw(9, 18)
    )
    assert (await says_yes(client, ewa, proposal)).json()["open_seats"] == 1
    await mailbox.drain()
    clock.move(timedelta(minutes=5))

    await leaves(client, sergio, elsewhere)
    await mailbox.drain()

    booked = (
        "It's a game! · 40 zł held",
        "Padel at Bonarka Arena · Sat 10 Oct, 17:00.",
    )
    for player in four:
        notices = await client.get(NOTICES, headers=player["headers"])
        [newest, *_] = notices.json()["notices"]
        assert (newest["title"], newest["body"]) == booked
        assert newest["your_own"] is False


# --------------------------------------------------------------------------- #
# A game gone back to filling that ends before it is full again
# --------------------------------------------------------------------------- #


async def test_a_game_gone_back_to_filling_past_its_book_by_is_called_off(
    client, session_factory, clock, four, waiting, mailbox
):
    """Oscar left while it waited for Ewa's payment, and her time to fix her
    card ran out: her seat reopened. Nobody filled the two seats before the
    book-by."""

    marta, oscar, ewa, sergio = four
    await withdraws(client, oscar, waiting)
    clock.move(EWA_S_TIME_ENDS - MONDAY_MORNING)
    await runs_out(session_factory, clock)
    clock.move(BOOK_BY - EWA_S_TIME_ENDS)

    await sweeps(session_factory, clock)

    for player in (marta, sergio):
        assert await last_told(client, mailbox, player) == (
            "Your Sat 17:00 is called off · nobody paid",
            "It didn't fill again before its last moment to book — Padel at "
            "Bonarka Arena.",
        )
    assert (await last_told(client, mailbox, oscar))[0].startswith("It's a game!")


async def test_a_game_gone_back_to_filling_whose_court_went_is_called_off(
    client, session_factory, clock, bonarka, four, waiting, mailbox
):
    """Oscar left while it waited for Ewa's payment; then Bonarka Arena closes
    Saturday's 17:00 for a repair: no court is left at its hour."""

    _, desk = bonarka
    marta, oscar = four[:2]
    await withdraws(client, oscar, waiting)
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
    clock.move(timedelta(minutes=1))
    group = UUID(
        (
            await client.get(f"/api/v1/proposals/{waiting}", headers=marta["headers"])
        ).json()["pool_id"]
    )

    async with session_factory() as session:
        assert (await build_propose_games(session, clock=clock).execute(group)).lost

    assert await last_told(client, mailbox, marta) == (
        "Your Sat 17:00 is called off · nobody paid",
        "Its court went to another game before it filled again — Padel at "
        "Bonarka Arena.",
    )


# --------------------------------------------------------------------------- #
# A leaver, told only when it touches them (Q108)
# --------------------------------------------------------------------------- #


async def test_a_leaver_whose_empty_seat_calls_the_game_off_is_told_it_counts(
    client, session_factory, clock, four, booked, mailbox
):
    """Oscar left before the cut-off — his hold let go, nothing taken (#637) —
    and nobody took his seat: at the cut-off the game is off, and it counts on
    his record. He is told in the app only: no money moves."""

    marta, oscar, ewa, sergio = four
    await leaves(client, oscar, booked)
    await mailbox.drain()
    emails_before = await subjects_to(mailbox, oscar)
    clock.move(CUT_OFF - MONDAY_MORNING)

    await cuts_off(session_factory, clock)

    assert await last_told(client, mailbox, oscar) == (
        "Saturday's 17:00 at Bonarka Arena, which you left, was called off",
        "Your seat stayed empty, so it counts on your record. Nothing was "
        "taken from you.",
    )
    assert await subjects_to(mailbox, oscar) == emails_before
    for player in (marta, ewa, sergio):
        assert await last_told(client, mailbox, player) == (
            "Game called off · nothing was taken",
            "Padel at Bonarka Arena · Sat 10 Oct, 17:00 was still short at the "
            "club's cut-off.",
        )


async def test_a_leaver_whose_seat_was_taken_is_told_nothing_of_the_call_off(
    client, session_factory, clock, payments, four, booked, mailbox
):
    """Oscar and Ewa both left before the cut-off; Zosia took the seat that
    opened first, Oscar's. Ewa's empty seat called the game off, so Ewa is
    told — and Oscar, whose seat was taken, is not."""

    marta, oscar, ewa = four[:3]
    zosia = await a_member(client, session_factory, payments, "zosia")
    group = (
        await client.get(f"/api/v1/bookings/{booked}", headers=marta["headers"])
    ).json()["pool_id"]
    joined = await client.post(
        f"/api/v1/groups/{group}/membership", headers=zosia["headers"]
    )
    assert joined.status_code in (200, 201), joined.text
    await leaves(client, oscar, booked)
    await leaves(client, ewa, booked)
    taken = await client.post(
        f"/api/v1/bookings/{booked}/seats", headers=zosia["headers"]
    )
    assert taken.status_code == 200, taken.text
    await mailbox.drain()
    told_oscar = await told(client, mailbox, oscar)
    clock.move(CUT_OFF - MONDAY_MORNING)

    await cuts_off(session_factory, clock)

    assert (await last_told(client, mailbox, ewa))[0] == (
        "Saturday's 17:00 at Bonarka Arena, which you left, was called off"
    )
    assert await told(client, mailbox, oscar) == told_oscar


async def test_a_leaver_whose_game_still_plays_is_told_nothing(
    client, session_factory, clock, four, booked, mailbox
):
    """Oscar left after the cut-off: the game goes ahead short, and nothing
    about it reaches him."""

    oscar = four[1]
    clock.move(CUT_OFF + timedelta(hours=1) - MONDAY_MORNING)
    await leaves(client, oscar, booked)
    told_oscar = await told(client, mailbox, oscar)

    await cuts_off(session_factory, clock)

    assert await told(client, mailbox, oscar) == told_oscar


async def test_a_paid_leaver_the_club_s_cancel_refunds_is_told_as_a_leaver(
    client, session_factory, clock, bonarka, four, booked, mailbox
):
    """Oscar left after the cut-off took his 40 zł; then Bonarka cancels for
    rain and refunds him. He reads a leaver's words, in the notice and the
    email — and is promised no new game. The others keep theirs."""

    _, desk = bonarka
    marta, oscar = four[:2]
    clock.move(CUT_OFF + timedelta(hours=1) - MONDAY_MORNING)
    await cuts_off(session_factory, clock)
    await leaves(client, oscar, booked)

    cancelled = await client.post(
        f"/api/v1/club/bookings/{booked}/cancellation",
        json={"reason": "WEATHER"},
        headers=desk,
    )

    assert cancelled.status_code == 204, cancelled.text
    assert await last_told(client, mailbox, oscar) == (
        "Saturday's 17:00 at Bonarka Arena, which you left, was cancelled",
        "Bonarka Arena cancelled it because of the weather — you're refunded 40 zł.",
    )
    [email] = [
        email
        for email in await mailbox.to("oscar@example.com")
        if "cancelled" in email.subject
    ]
    assert email.subject == "The game you left was cancelled · you're refunded 40 zł"
    assert "because of the weather" in email.text
    assert "another game" not in email.text
    # The players still in keep theirs: the club's reason, the refund, and a
    # new game first.
    assert await last_told(client, mailbox, marta) == (
        "Game called off · you're refunded 40 zł",
        "Bonarka Arena cancelled padel · Sat 10 Oct, 17:00 because of the weather.",
    )
    [theirs] = [
        email
        for email in await mailbox.to("marta@example.com")
        if "cancelled" in email.subject
    ]
    assert theirs.subject == "Game cancelled by Bonarka Arena · you're refunded 40 zł"
    assert "We'll look for another game for you first." in theirs.text


async def test_a_leaver_refunded_already_hears_nothing_of_the_club_s_cancel(
    client, bonarka, four, booked, mailbox
):
    _, desk = bonarka
    oscar = four[1]
    await leaves(client, oscar, booked)
    told_oscar = await told(client, mailbox, oscar)
    emails_before = await subjects_to(mailbox, oscar)

    cancelled = await client.post(
        f"/api/v1/club/bookings/{booked}/cancellation",
        json={"reason": "WEATHER"},
        headers=desk,
    )

    assert cancelled.status_code == 204, cancelled.text
    assert await told(client, mailbox, oscar) == told_oscar
    assert await subjects_to(mailbox, oscar) == emails_before


async def a_game_that_books_elsewhere(
    client, session_factory, clock, payments, player: dict, *, start
) -> UUID:
    """``player`` and three others book a game at Ogrody 33, which books at
    once. Its booking."""

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
    return game
