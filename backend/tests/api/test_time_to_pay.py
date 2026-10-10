"""**Time to pay** (#625, #626; the mechanics §12.2, Q109–Q112).

A share refused as a full game fills — or as its On request club says yes —
no longer reopens the seat at once. The player has **thirty minutes, never past
the book-by**, their seat theirs alone; every other hold waits on its card, and
at a club that confirms the club's yes and its court are kept too. The four were
matched, so it is *It's a game!* to them — *waiting for one payment until …*,
never saying whose. Paid in time, the game books at once on the kept holds and
nobody's bank is asked again, nor the desk; out of time, the seat reopens, the
holds are let go, and the others read *filling again*.

Every act is taken over HTTP as the phone and the desk take it, against the fake
payment provider; the deadline is run by its job, as the scheduler runs it.

The clock stands on **Monday 5 October 2026, 08:00 in Kraków**; the game is
**Saturday 10 October, 17:00**, padel at 160 zł — 40 zł a seat — at Bonarka
Arena, which books at once, or at Kazimierz Padel, which confirms. Its book-by
is two hours before the hour.
"""

from __future__ import annotations

from datetime import timedelta
from uuid import UUID

import pytest

from app.api.dependencies import get_clock
from app.bootstrap.composition import build_court_hours, build_propose_games
from app.kernel import Sport
from app.modules.payments.domain.entered_cards import A_CARD_THE_BANK_ALWAYS_CHECKS
from tests.api.proposals_world import (
    MONDAY_MORNING,
    SATURDAY_FIVE,
    a_club_and_its_desk,
    a_group,
    a_member,
    live_ids,
    makes,
    runs_out,
    saves_a_card,
    says_yes,
)
from tests.unit.fake_clock import MovableClock

HOME = "/api/v1/home"
NOTICES = "/api/v1/players/me/notices"
TO_CONFIRM = "/api/v1/players/me/payments-to-confirm"
CLUB_BOOKINGS = "/api/v1/club/bookings"
#: Thirty minutes from the last yes on Monday morning: 08:30 in Kraków.
PAY_BY = "2026-10-05T06:30:00Z"
#: The book-by: two hours' notice before the hour.
BOOK_BY = SATURDAY_FIVE - timedelta(hours=2)


@pytest.fixture
def clock(app):
    """Monday 5 October 2026, 08:00 in Kraków."""

    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


@pytest.fixture
async def bonarka(client) -> tuple[str, dict]:
    """Bonarka Arena, which books at once, padel at 160 zł — 40 zł a seat."""

    return await a_club_and_its_desk(client, way="INSTANT", padel_grosze=160_00)


@pytest.fixture
async def kazimierz(client) -> tuple[str, dict]:
    """Kazimierz Padel, which confirms each game, padel at 160 zł."""

    return await a_club_and_its_desk(
        client, name="Kazimierz Padel", way="ON_REQUEST", padel_grosze=160_00
    )


@pytest.fixture
async def four(client, session_factory, payments) -> list[dict]:
    """Paula, Marta, Oscar and Ivan — in the order they say yes, Ivan's the
    last. Paula's bank wants her to confirm every payment."""

    paula, marta, oscar, ivan = [
        await a_member(client, session_factory, payments, name)
        for name in ("paula", "marta", "oscar", "ivan")
    ]
    await saves_a_card(
        client, payments, paula["headers"], A_CARD_THE_BANK_ALWAYS_CHECKS
    )
    return [paula, marta, oscar, ivan]


async def a_game(
    client, session_factory, clock, club: str, four: list[dict], *also: dict
) -> tuple[UUID, dict]:
    """Saturday's game, dealt to the four — and to ``also`` on a version of
    their own — every one of the four In, Ivan's yes last. The game, and the
    answer to that last yes."""

    group = await a_group(client, four[0], club, *four[1:], *also)
    versions = (tuple(four), *((one,) for one in also))
    proposal = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=versions
    )
    for player in four[:3]:
        said = await says_yes(client, player, proposal)
        assert said.status_code == 200, said.text
    last = await says_yes(client, four[3], proposal)
    assert last.status_code == 200, last.text
    return proposal, last.json()


async def told(client, mailbox, player: dict) -> list[tuple[str, str]]:
    """Every notice in the player's list, newest first: its title and body."""

    await mailbox.drain()
    read = await client.get(NOTICES, headers=player["headers"])
    assert read.status_code == 200, read.text
    return [(notice["title"], notice["body"]) for notice in read.json()["notices"]]


async def notices_of(client, mailbox, player: dict) -> list[dict]:
    await mailbox.drain()
    read = await client.get(NOTICES, headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()["notices"]


async def subjects_to(mailbox, player: dict) -> list[str]:
    return [
        email.subject for email in await mailbox.to(f"{player['name']}@example.com")
    ]


async def the_card(client, player: dict, proposal: UUID) -> dict:
    read = await client.get(HOME, headers=player["headers"])
    assert read.status_code == 200, read.text
    [card] = [
        card for card in read.json()["games"] if card["booking_id"] == str(proposal)
    ]
    return card


async def home_of(client, player: dict) -> list[dict]:
    read = await client.get(HOME, headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()["games"]


async def to_confirm(client, player: dict) -> list[dict]:
    read = await client.get(TO_CONFIRM, headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()["payments"]


async def confirms(client, payments, player: dict, charge_id: str):
    """The phone passes the bank's check and says so."""

    read = await client.get(
        f"/api/v1/seat-charges/{charge_id}", headers=player["headers"]
    )
    assert read.status_code == 200, read.text
    secret = read.json()["to_confirm"]["client_secret"]
    payments.phone_confirms_payment(secret.split("_secret_")[0])
    return await client.post(
        f"/api/v1/seat-charges/{charge_id}/confirmation", headers=player["headers"]
    )


async def the_court_is_on_sale(session_factory, clock, club: str) -> bool:
    async with session_factory() as session:
        offered = await build_court_hours(session).offered(
            UUID(club), sport=Sport.PADEL, start=SATURDAY_FIVE, now=clock.now()
        )
    return offered is not None


async def the_club_s_day(client, desk: dict) -> list[dict]:
    read = await client.get(CLUB_BOOKINGS, params={"date": "2026-10-10"}, headers=desk)
    assert read.status_code == 200, read.text
    return read.json()["bookings"]


# --------------------------------------------------------------------------- #
# A club that books at once (#625)
# --------------------------------------------------------------------------- #


async def test_a_refused_share_holds_her_seat_and_keeps_every_other_hold(
    client, session_factory, clock, payments, mailbox, bonarka, four
):
    club, _ = bonarka
    paula, marta, oscar, ivan = four

    proposal, answer = await a_game(client, session_factory, clock, club, four)

    assert answer["booked"] is None
    assert answer["open_seats"] == 0
    assert answer["your_payment"] is None
    assert answer["payment_awaited_until"] == PAY_BY
    await mailbox.drain()
    # Nobody paid, and nothing was let go: three holds wait on their cards.
    assert payments.called("capture") == []
    assert payments.called("cancel") == []
    assert len(payments.called("authorise")) == 4
    # She is In, her seat hers alone.
    for player in four:
        assert await live_ids(client, player) == [str(proposal)]
    [owed] = await to_confirm(client, paula)
    assert (owed["proposal_id"], owed["confirm_by"]) == (str(proposal), PAY_BY)
    # The court is not held: the game is still filling.
    assert await the_court_is_on_sale(session_factory, clock, club)


async def test_nobody_else_may_take_her_seat_while_her_time_runs(
    client, session_factory, clock, payments, bonarka, four
):
    club, _ = bonarka
    diego = await a_member(client, session_factory, payments, "diego")
    proposal, _ = await a_game(client, session_factory, clock, club, four, diego)

    late = await says_yes(client, diego, proposal)

    assert late.status_code == 409, late.text
    assert late.json()["code"] == "proposal_is_full"


async def test_her_notice_and_email_name_her_time_and_the_others_never_her(
    client, session_factory, clock, payments, mailbox, bonarka, four
):
    club, _ = bonarka
    paula, marta, oscar, ivan = four

    await a_game(client, session_factory, clock, club, four)

    assert (await told(client, mailbox, paula))[0] == (
        "Confirm your payment by 08:30 to keep your seat",
        "Padel · Sat 17:00 at Bonarka Arena — the others are waiting.",
    )
    assert await subjects_to(mailbox, paula) == [
        "Confirm your payment by 08:30 to keep your seat"
    ]
    waiting = (
        "It's a game! · waiting for one payment until 08:30",
        "Padel · Sat 17:00 at Bonarka Arena. Nobody pays until it's in.",
    )
    for player in (marta, oscar, ivan):
        [notice] = await notices_of(client, mailbox, player)
        assert (notice["title"], notice["body"]) == waiting
        assert notice["kind"] == "WAITING_FOR_A_PAYMENT"
        # Ivan's own yes filled it: his copy is born seen.
        assert notice["your_own"] is (player is ivan)
        assert await subjects_to(mailbox, player) == []


async def test_home_and_the_details_read_waiting_for_one_payment(
    client, session_factory, clock, payments, bonarka, four
):
    club, _ = bonarka
    paula, marta, *_ = four
    proposal, _ = await a_game(client, session_factory, clock, club, four)

    for player in four:
        card = await the_card(client, player, proposal)
        assert card["status"] == "WAITING_FOR_A_PAYMENT"
        assert card["payment_due_by"] == PAY_BY
        assert card["money"]["paid"] is False
        assert (card["court_name"], card["game_id"], card["needs_you"]) == (
            None,
            None,
            False,
        )
        # Her card says the payment is hers; nobody else's names it.
        assert card["your_payment_due_by"] == (PAY_BY if player is paula else None)
    booking = await client.get(f"/api/v1/bookings/{proposal}", headers=marta["headers"])
    assert booking.status_code == 200, booking.text
    assert booking.json()["status"] == "WAITING_FOR_A_PAYMENT"
    assert booking.json()["leaving"]["kind"] == "WHILE_WAITING_FOR_THE_CLUB"
    details = await client.get(
        f"/api/v1/proposals/{proposal}", headers=paula["headers"]
    )
    assert details.json()["status"] == "WAITING_FOR_A_PAYMENT"
    assert details.json()["payment_due_by"] == PAY_BY
    assert details.json()["actions"] == ["CONFIRM_PAYMENT", "LEAVE"]
    assert details.json()["your_payment"]["confirm_by"] == PAY_BY
    # Home's badge counts her payment once, as the payment to confirm it is.
    assert (await client.get(HOME, headers=paula["headers"])).json()["needing_you"] == 1


async def test_her_own_yes_last_answers_with_her_time(
    client, session_factory, clock, payments, bonarka, four
):
    club, _ = bonarka
    paula, marta, oscar, ivan = four

    _, answer = await a_game(
        client, session_factory, clock, club, [ivan, marta, oscar, paula]
    )

    assert answer["your_payment"]["refusal"] == "AUTHENTICATION_REQUIRED"
    assert answer["your_payment"]["confirm_by"] == PAY_BY
    assert answer["payment_awaited_until"] == PAY_BY


async def test_paying_in_time_books_the_game_on_the_kept_holds(
    client, session_factory, clock, payments, mailbox, bonarka, four
):
    club, _ = bonarka
    paula, marta, oscar, ivan = four
    proposal, _ = await a_game(client, session_factory, clock, club, four)
    await mailbox.drain()
    [owed] = await to_confirm(client, paula)
    asked = len(payments.called("authorise"))
    clock.move(timedelta(minutes=12))

    paid = await confirms(client, payments, paula, owed["seat_charge_id"])

    assert paid.status_code == 200, paid.text
    assert paid.json()["booked"]["booking_id"] == str(proposal)
    # Nobody's bank was asked again.
    assert len(payments.called("authorise")) == asked
    await mailbox.drain()
    assert payments.called("cancel") == []
    assert (
        len({call.arguments["payment_id"] for call in payments.called("capture")}) == 4
    )
    for player in (marta, oscar, ivan):
        notices = await notices_of(client, mailbox, player)
        assert (notices[0]["title"], notices[0]["body"]) == (
            "Your Sat 17:00 is booked · you paid 40 zł",
            "Padel at Bonarka Arena.",
        )
        assert "Your Sat 17:00 is booked · you paid 40 zł" in await subjects_to(
            mailbox, player
        )
        # Nobody is told *It's a game!* twice.
        assert sum(n["title"].startswith("It's a game!") for n in notices) == 1
    # Hers is her own *It's a game!* — she sees it on her phone.
    [hers, *_] = await notices_of(client, mailbox, paula)
    assert (hers["title"], hers["your_own"]) == ("It's a game! · you paid 40 zł", True)
    assert "It's a game! · you paid 40 zł" in await subjects_to(mailbox, paula)
    for player in four:
        assert (await the_card(client, player, proposal))["status"] == "BOOKED"
    assert await to_confirm(client, paula) == []


async def test_out_of_time_her_seat_reopens_and_the_holds_are_let_go(
    client, session_factory, clock, payments, mailbox, bonarka, four
):
    club, _ = bonarka
    paula, marta, oscar, ivan = four
    diego = await a_member(client, session_factory, payments, "diego")
    proposal, _ = await a_game(client, session_factory, clock, club, four, diego)
    await mailbox.drain()
    clock.move(timedelta(minutes=29))
    assert (await runs_out(session_factory, clock)).games == 0
    clock.move(timedelta(minutes=1))

    ran = await runs_out(session_factory, clock)

    assert ran.games == 1
    await mailbox.drain()
    # The three holds kept for her are let go; her own payment waits for her.
    assert len(payments.called("cancel")) == 3
    assert await live_ids(client, paula) == []
    [owed] = await to_confirm(client, paula)
    assert owed["confirm_by"] is None
    assert (await told(client, mailbox, paula))[0] == (
        "Your time to pay ran out · Sat 17:00",
        "Your seat is open to others now — confirm your payment to take it back "
        "while it's free.",
    )
    for player in (marta, oscar, ivan):
        assert (await told(client, mailbox, player))[0] == (
            "Your Sat 17:00 at Bonarka Arena is filling again",
            "A seat opened — nobody paid.",
        )
        card = await the_card(client, player, proposal)
        assert (card["status"], card["filling_again"], card["club_confirms"]) == (
            "SEAT_OPEN",
            True,
            False,
        )
        assert card["open_seats"] == 1
    # Her seat is offered as any open seat: the first yes takes it.
    took = await says_yes(client, diego, proposal)
    assert took.json()["booked"]["booking_id"] == str(proposal), took.text


async def test_a_confirmation_past_her_time_runs_it_out_and_takes_the_seat_back(
    client, session_factory, clock, payments, mailbox, bonarka, four
):
    """The job has not run yet: her confirmation runs her time out first, and is
    her yes again on a seat still free — the others asked afresh."""

    club, _ = bonarka
    paula, *_ = four
    proposal, _ = await a_game(client, session_factory, clock, club, four)
    [owed] = await to_confirm(client, paula)
    asked = len(payments.called("authorise"))
    clock.move(timedelta(minutes=31))

    paid = await confirms(client, payments, paula, owed["seat_charge_id"])

    assert paid.status_code == 200, paid.text
    assert paid.json()["booked"]["booking_id"] == str(proposal)
    assert len(payments.called("authorise")) == asked + 3
    assert "Your time to pay ran out · Sat 17:00" in [
        title for title, _ in await told(client, mailbox, paula)
    ]


async def test_a_leave_while_it_waits_lets_the_leaver_s_hold_go_and_her_time_runs_on(
    client, session_factory, clock, payments, mailbox, bonarka, four
):
    club, _ = bonarka
    paula, marta, oscar, ivan = four
    proposal, _ = await a_game(client, session_factory, clock, club, four)
    await mailbox.drain()
    clock.move(timedelta(minutes=5))

    left = await client.post(
        f"/api/v1/bookings/{proposal}/departure", headers=oscar["headers"]
    )

    assert left.status_code == 200, left.text
    assert left.json()["left"] == "WHILE_WAITING_FOR_THE_CLUB"
    await mailbox.drain()
    assert len(payments.called("cancel")) == 1
    for player in (marta, ivan):
        assert (await told(client, mailbox, player))[0] == (
            "oscar left your game",
            "Padel at Bonarka Arena · Sat 10 Oct, 17:00 — it's filling again.",
        )
        card = await the_card(client, player, proposal)
        assert (card["status"], card["filling_again"]) == ("SEAT_OPEN", True)
    # Her time runs on.
    hers = await the_card(client, paula, proposal)
    assert (hers["status"], hers["your_payment_due_by"]) == ("SEAT_OPEN", PAY_BY)
    [owed] = await to_confirm(client, paula)
    assert owed["confirm_by"] == PAY_BY

    paid = await confirms(client, payments, paula, owed["seat_charge_id"])

    # In, her payment held; the game is filling, and the others' holds go.
    assert paid.status_code == 200, paid.text
    assert paid.json()["booked"] is None
    assert paid.json()["open_seats"] == 1
    assert await to_confirm(client, paula) == []
    await mailbox.drain()
    assert len(payments.called("cancel")) == 3
    assert await live_ids(client, paula) == [str(proposal)]


async def test_a_court_lost_while_it_waits_calls_the_game_off(
    client, session_factory, clock, payments, mailbox, bonarka, four
):
    club, _ = bonarka
    paula, marta, oscar, ivan = four
    proposal, _ = await a_game(client, session_factory, clock, club, four)
    await mailbox.drain()
    clock.move(timedelta(minutes=1))
    others = [
        await a_member(client, session_factory, payments, name)
        for name in ("ania", "bart", "cela", "dawid")
    ]
    _, booked = await a_game(client, session_factory, clock, club, others)
    assert booked["booked"] is not None
    our_group = (
        await client.get(f"/api/v1/proposals/{proposal}", headers=marta["headers"])
    ).json()["pool_id"]

    await mailbox.drain()
    clock.move(timedelta(minutes=5))

    async with session_factory() as session:
        await build_propose_games(session, clock=clock).execute(UUID(our_group))

    for player in four:
        assert (await told(client, mailbox, player))[0] == (
            "Your Sat 17:00 is called off · nobody paid",
            "Its court went to another game before the payment came in — Padel at "
            "Bonarka Arena.",
        )
        card = await the_card(client, player, proposal)
        assert (card["status"], card["called_off_reason"]) == (
            "CALLED_OFF",
            "COURT_HOUR_LOST",
        )
    assert await to_confirm(client, paula) == []


async def test_her_time_never_runs_past_the_book_by(
    client, session_factory, clock, payments, mailbox, bonarka, four
):
    club, _ = bonarka
    paula, marta, oscar, ivan = four
    clock.move(BOOK_BY - MONDAY_MORNING - timedelta(minutes=10))

    proposal, answer = await a_game(client, session_factory, clock, club, four)

    assert answer["payment_awaited_until"] == "2026-10-10T13:00:00Z"
    clock.move(timedelta(minutes=10, seconds=20))
    assert (await runs_out(session_factory, clock)).games == 1
    for player in four:
        assert (await told(client, mailbox, player))[0] == (
            "Your Sat 17:00 is called off · nobody paid",
            "A payment didn't go through in time — Padel at Bonarka Arena.",
        )
    card = await the_card(client, marta, proposal)
    assert (card["status"], card["called_off_reason"]) == (
        "CALLED_OFF",
        "PAYMENT_NOT_IN_TIME",
    )


# --------------------------------------------------------------------------- #
# A club that confirms: its yes waits on the payment (#626)
# --------------------------------------------------------------------------- #


async def accepted_at(client, session_factory, clock, kazimierz, four, mailbox):
    """Saturday's game put to Kazimierz Padel at 08:00, accepted at 08:10 —
    and Paula's share refused."""

    club, desk = kazimierz
    proposal, answer = await a_game(client, session_factory, clock, club, four)
    assert answer["waiting_for_the_club"] is True
    await mailbox.drain()
    clock.move(timedelta(minutes=10))
    accepted = await client.post(f"{CLUB_BOOKINGS}/{proposal}/acceptance", headers=desk)
    assert accepted.status_code == 200, accepted.text
    return proposal, accepted.json()


async def test_a_share_refused_at_accept_keeps_the_club_s_yes_and_its_court(
    client, session_factory, clock, payments, mailbox, kazimierz, four
):
    club, desk = kazimierz
    paula, marta, oscar, ivan = four

    proposal, accepted = await accepted_at(
        client, session_factory, clock, kazimierz, four, mailbox
    )

    assert accepted == {
        "outcome": "WAITING_FOR_A_PAYMENT",
        "court_name": None,
        "payment_due_by": "2026-10-05T06:40:00Z",
    }
    assert not await the_court_is_on_sale(session_factory, clock, club)
    waiting = await client.get(f"{CLUB_BOOKINGS}/waiting", headers=desk)
    assert waiting.json()["bookings"] == []
    [row] = await the_club_s_day(client, desk)
    assert (row["status"], row["payment_due_by"]) == (
        "WAITING_FOR_A_PAYMENT",
        "2026-10-05T06:40:00Z",
    )
    for player in four:
        card = await the_card(client, player, proposal)
        assert (card["status"], card["payment_due_by"]) == (
            "WAITING_FOR_A_PAYMENT",
            "2026-10-05T06:40:00Z",
        )
    for player in (marta, oscar, ivan):
        assert (await told(client, mailbox, player))[0] == (
            "Your Sat 17:00 is waiting for one payment, until 08:40",
            "Padel at Kazimierz Padel. Nobody pays until it's in.",
        )
    assert (await told(client, mailbox, paula))[0][0] == (
        "Confirm your payment by 08:40 to keep your seat"
    )
    [owed] = await to_confirm(client, paula)
    assert owed["confirm_by"] == "2026-10-05T06:40:00Z"


async def test_paying_in_time_books_it_without_asking_the_club_again(
    client, session_factory, clock, payments, mailbox, kazimierz, four
):
    _, desk = kazimierz
    paula, marta, oscar, ivan = four
    proposal, _ = await accepted_at(
        client, session_factory, clock, kazimierz, four, mailbox
    )
    asked = len(payments.called("authorise"))
    desk_mail = await mailbox.to("desk@kazimierz.pl")
    [owed] = await to_confirm(client, paula)

    paid = await confirms(client, payments, paula, owed["seat_charge_id"])

    assert paid.status_code == 200, paid.text
    assert paid.json()["booked"]["booking_id"] == str(proposal)
    assert len(payments.called("authorise")) == asked
    await mailbox.drain()
    assert len(payments.called("capture")) == 4
    assert await mailbox.to("desk@kazimierz.pl") == desk_mail
    for player in (marta, oscar, ivan):
        assert (await told(client, mailbox, player))[0][0] == (
            "Kazimierz Padel confirmed your game"
        )
    [hers, *_] = await notices_of(client, mailbox, paula)
    assert (hers["kind"], hers["your_own"]) == ("CLUB_CONFIRMED", True)
    [row] = await the_club_s_day(client, desk)
    assert row["status"] == "BOOKED"
    assert (await the_card(client, marta, proposal))["status"] == "BOOKED"


async def test_out_of_time_the_booking_is_called_off_and_the_desk_emailed(
    client, session_factory, clock, payments, mailbox, kazimierz, four
):
    club, desk = kazimierz
    paula, marta, oscar, ivan = four
    proposal, _ = await accepted_at(
        client, session_factory, clock, kazimierz, four, mailbox
    )
    clock.move(timedelta(minutes=30))

    assert (await runs_out(session_factory, clock)).games == 1

    await mailbox.drain()
    assert len(payments.called("cancel")) == 3
    assert await the_court_is_on_sale(session_factory, clock, club)
    [row] = await the_club_s_day(client, desk)
    assert (row["status"], row["called_off_reason"]) == (
        "CALLED_OFF",
        "PAYMENT_NOT_IN_TIME",
    )
    # Nobody left off the row: that would name whose payment it was.
    assert len(row["players"]) == 4
    [email] = [
        email
        for email in await mailbox.to("desk@kazimierz.pl")
        if email.subject == "A game didn't go ahead"
    ]
    assert "payment didn't come in time" in email.text
    assert "paula" not in email.text.lower()
    assert (await told(client, mailbox, paula))[0][0] == (
        "Your time to pay ran out · Sat 17:00"
    )
    for player in (marta, oscar, ivan):
        assert (await told(client, mailbox, player))[0] == (
            "Your Sat 17:00 at Kazimierz Padel is filling again",
            "A seat opened — nobody paid.",
        )
        card = await the_card(client, player, proposal)
        assert (card["status"], card["filling_again"], card["club_confirms"]) == (
            "SEAT_OPEN",
            True,
            True,
        )


async def test_full_again_after_the_time_ran_out_the_desk_is_asked_again(
    client, session_factory, clock, payments, mailbox, kazimierz, four
):
    _, desk = kazimierz
    paula, *_ = four
    proposal, _ = await accepted_at(
        client, session_factory, clock, kazimierz, four, mailbox
    )
    [owed] = await to_confirm(client, paula)
    clock.move(timedelta(minutes=30))
    await runs_out(session_factory, clock)

    again = await confirms(client, payments, paula, owed["seat_charge_id"])

    assert again.json()["booked"] is None, again.text
    waiting = await client.get(f"{CLUB_BOOKINGS}/waiting", headers=desk)
    assert [b["booking_id"] for b in waiting.json()["bookings"]] == [str(proposal)]


async def test_accept_past_the_book_by_calls_the_game_off_at_once(
    client, session_factory, clock, payments, mailbox, kazimierz, four
):
    club, desk = kazimierz
    paula, marta, oscar, ivan = four
    clock.move(BOOK_BY - MONDAY_MORNING - timedelta(minutes=20))
    proposal, _ = await a_game(client, session_factory, clock, club, four)
    await mailbox.drain()
    clock.move(timedelta(minutes=25))

    accepted = await client.post(f"{CLUB_BOOKINGS}/{proposal}/acceptance", headers=desk)

    assert accepted.json()["outcome"] == "CALLED_OFF", accepted.text
    for player in four:
        assert (await told(client, mailbox, player))[0] == (
            "Your Sat 17:00 is called off · nobody paid",
            "A payment didn't go through in time — Padel at Kazimierz Padel.",
        )
        card = await the_card(client, player, proposal)
        assert (card["status"], card["called_off_reason"]) == (
            "CALLED_OFF",
            "PAYMENT_NOT_IN_TIME",
        )
    # Nothing is left to confirm, so nobody is asked to.
    assert await subjects_to(mailbox, paula) == []
    [email] = [
        email
        for email in await mailbox.to("desk@kazimierz.pl")
        if email.subject == "A game didn't go ahead"
    ]
    assert "won't come back" in email.text
    [row] = await the_club_s_day(client, desk)
    assert row["called_off_reason"] == "PAYMENT_NOT_IN_TIME"


# --------------------------------------------------------------------------- #
# Full again while the payment is awaited
# --------------------------------------------------------------------------- #


async def test_a_seat_taken_back_while_she_pays_waits_for_her_and_asks_no_card(
    client, session_factory, clock, payments, mailbox, bonarka, four
):
    """Oscar leaves while Paula's time runs, and Diego takes his seat: the game
    is full again and **waits for her payment** — nobody's card is asked, hers
    least of all (*Nothing retries a card by itself*, Q109). Her payment books
    it, Diego's share held then."""

    club, _ = bonarka
    paula, marta, oscar, ivan = four
    diego = await a_member(client, session_factory, payments, "diego")
    proposal, _ = await a_game(client, session_factory, clock, club, four, diego)
    clock.move(timedelta(minutes=5))
    left = await client.post(
        f"/api/v1/bookings/{proposal}/departure", headers=oscar["headers"]
    )
    assert left.status_code == 200, left.text
    asked = len(payments.called("authorise"))

    full = await says_yes(client, diego, proposal)

    assert full.status_code == 200, full.text
    assert (full.json()["booked"], full.json()["open_seats"]) == (None, 0)
    assert full.json()["payment_awaited_until"] == PAY_BY
    assert len(payments.called("authorise")) == asked
    assert (await the_card(client, marta, proposal))["status"] == (
        "WAITING_FOR_A_PAYMENT"
    )
    [owed] = await to_confirm(client, paula)

    paid = await confirms(client, payments, paula, owed["seat_charge_id"])

    assert paid.json()["booked"]["booking_id"] == str(proposal), paid.text
    # Diego's share is the one hold asked for: everybody else's was kept.
    assert len(payments.called("authorise")) == asked + 1


async def test_at_a_club_that_confirms_the_club_is_asked_again_only_once_she_pays(
    client, session_factory, clock, payments, mailbox, kazimierz, four
):
    """Oscar leaves while the club's yes waits on Paula: the request goes, and
    the yes with it. Diego refills it — but no club is asked while her payment
    is awaited. Once she pays, it is a new request, her payment held for the
    club's yes."""

    _, desk = kazimierz
    paula, marta, oscar, ivan = four
    diego = await a_member(client, session_factory, payments, "diego")
    club, _ = kazimierz
    proposal, _ = await a_game(client, session_factory, clock, club, four, diego)
    clock.move(timedelta(minutes=10))
    accepted = await client.post(f"{CLUB_BOOKINGS}/{proposal}/acceptance", headers=desk)
    assert accepted.json()["outcome"] == "WAITING_FOR_A_PAYMENT", accepted.text
    assert (
        await client.delete(
            f"/api/v1/proposals/{proposal}/yes", headers=oscar["headers"]
        )
    ).status_code == 204
    assert (await says_yes(client, diego, proposal)).json()["booked"] is None
    waiting = await client.get(f"{CLUB_BOOKINGS}/waiting", headers=desk)
    assert waiting.json()["bookings"] == []
    [owed] = await to_confirm(client, paula)

    paid = await confirms(client, payments, paula, owed["seat_charge_id"])

    assert paid.status_code == 200, paid.text
    assert paid.json()["booked"] is None
    waiting = await client.get(f"{CLUB_BOOKINGS}/waiting", headers=desk)
    assert [b["booking_id"] for b in waiting.json()["bookings"]] == [str(proposal)]
    assert await to_confirm(client, paula) == []
    booked = await client.post(f"{CLUB_BOOKINGS}/{proposal}/acceptance", headers=desk)
    assert booked.json()["outcome"] == "BOOKED", booked.text


async def test_two_refused_one_paying_in_time_keeps_her_payment_when_he_runs_out(
    client, session_factory, clock, payments, mailbox, bonarka, four
):
    club, _ = bonarka
    paula, marta, oscar, ivan = four
    await saves_a_card(
        client, payments, oscar["headers"], A_CARD_THE_BANK_ALWAYS_CHECKS
    )
    proposal, answer = await a_game(client, session_factory, clock, club, four)
    assert answer["payment_awaited_until"] == PAY_BY
    [hers] = await to_confirm(client, paula)

    paid = await confirms(client, payments, paula, hers["seat_charge_id"])

    # Still waiting for Oscar's: her payment is held.
    assert (paid.json()["booked"], paid.json()["open_seats"]) == (None, 0), paid.text
    clock.move(timedelta(minutes=30))
    await runs_out(session_factory, clock)
    await mailbox.drain()
    # Marta's and Ivan's holds go; hers waits for the fill, his for him.
    assert len(payments.called("cancel")) == 2
    assert await live_ids(client, paula) == [str(proposal)]
    assert await live_ids(client, oscar) == []
