"""**Time to pay** (#625, #626; the mechanics §12.2, Q109–Q111).

A share refused as a full game fills no longer reopens the seat at once. The
player has **thirty minutes, never past the book-by**, their seat theirs alone;
every other hold waits on its card. The four were matched, so it is *It's a
game!* to them — *waiting for one payment until …*, never saying whose. Paid in
time, the game books at once on the kept holds and nobody's bank is asked
again; out of time, the seat reopens, the holds are let go, and the others read
*filling again*.

**Before the club's cut-off it is time to fix the card** (#638; Q113): nothing
is taken then, only held, so the player is never asked to pay — *Fix your card
by 08:30 to keep your seat*, nothing paid now, never past the cut-off. **From
the cut-off on**, where money is taken at once, it stays **time to pay** —
*Confirm your payment by 08:30*. The reads say which it is (``time_to``).

Every act is taken over HTTP as the phone takes it, against the fake payment
provider; the deadline is run by its job, as the scheduler runs it.

The clock stands on **Monday 5 October 2026, 08:00 in Kraków**; the game is
**Saturday 10 October, 17:00**, padel at 160 zł — 40 zł a seat — at Bonarka
Arena, which books at once. Its book-by is two hours before the hour, and its
cut-off the clubs' default 24 hours — **Friday 17:00** — so every refusal on
Monday is a card to fix.
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
    SATURDAY_FIVE_S_CUT_OFF,
    a_club_and_its_desk,
    a_group,
    a_member,
    live_ids,
    makes,
    runs_out,
    saves_a_card,
    says_yes,
    the_cut_off_comes,
)
from tests.unit.fake_clock import MovableClock

HOME = "/api/v1/home"
NOTICES = "/api/v1/players/me/notices"
TO_CONFIRM = "/api/v1/players/me/payments-to-confirm"
#: Thirty minutes from the last yes on Monday morning: 08:30 in Kraków.
PAY_BY = "2026-10-05T06:30:00Z"
#: The book-by: two hours' notice before the hour.
BOOK_BY = SATURDAY_FIVE - timedelta(hours=2)
#: Saturday 08:00 in Kraków — after Friday 17:00's cut-off, before the book-by.
SATURDAY_MORNING = SATURDAY_FIVE - timedelta(hours=9)
#: Thirty minutes from a last yes on Saturday morning: 08:30 in Kraków.
PAY_BY_ON_SATURDAY = "2026-10-10T06:30:00Z"


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


# --------------------------------------------------------------------------- #
# A refused share waits for its player (#625)
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
    # Before the cut-off nothing is taken: it is her time to fix her card.
    assert owed["time_to"] == "FIX_THE_CARD"
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


async def test_before_the_cut_off_she_is_told_to_fix_her_card_and_nothing_is_paid(
    client, session_factory, clock, payments, mailbox, bonarka, four
):
    club, _ = bonarka
    paula, marta, oscar, ivan = four

    await a_game(client, session_factory, clock, club, four)

    [hers, *_] = await notices_of(client, mailbox, paula)
    assert (hers["kind"], hers["title"], hers["body"]) == (
        "FIX_YOUR_CARD",
        "Fix your card by 08:30 to keep your seat",
        "Nothing is paid now. Padel · Sat 17:00 at Bonarka Arena — the others "
        "are waiting.",
    )
    [email] = await mailbox.to("paula@example.com")
    assert email.subject == "Fix your card by 08:30 to keep your seat"
    assert "Your bank wants you to confirm the 40 zł hold yourself." in email.text
    assert (
        "Nothing is paid now: fixing your card only places the 40 zł hold on it "
        "again, taken on Fri 17:00, the club's cut-off."
    ) in email.text
    assert "Confirm your payment" not in email.text
    waiting = (
        "It's a game! · waiting for one payment until 08:30",
        "Padel · Sat 17:00 at Bonarka Arena. Nobody pays until it's in.",
    )
    for player in (marta, oscar, ivan):
        [notice] = await notices_of(client, mailbox, player)
        assert (notice["title"], notice["body"]) == waiting
        assert notice["kind"] == "WAITING_FOR_A_PAYMENT"
        # The others' words are the same whatever her time is for.
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
        # Before the cut-off it is a card to fix.
        assert card["time_to"] == "FIX_THE_CARD"
    booking = await client.get(f"/api/v1/bookings/{proposal}", headers=marta["headers"])
    assert booking.status_code == 200, booking.text
    assert booking.json()["status"] == "WAITING_FOR_A_PAYMENT"
    assert booking.json()["leaving"]["kind"] == "WHILE_WAITING_FOR_A_PAYMENT"
    assert booking.json()["time_to"] == "FIX_THE_CARD"
    details = await client.get(
        f"/api/v1/proposals/{proposal}", headers=paula["headers"]
    )
    assert details.json()["status"] == "WAITING_FOR_A_PAYMENT"
    assert details.json()["payment_due_by"] == PAY_BY
    assert details.json()["time_to"] == "FIX_THE_CARD"
    assert details.json()["actions"] == ["CONFIRM_PAYMENT", "LEAVE"]
    assert details.json()["your_payment"]["confirm_by"] == PAY_BY
    assert details.json()["your_payment"]["time_to"] == "FIX_THE_CARD"
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
    assert answer["your_payment"]["time_to"] == "FIX_THE_CARD"
    assert answer["payment_awaited_until"] == PAY_BY


async def test_fixing_her_card_in_time_books_it_and_takes_nothing_till_the_cut_off(
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
    # Held on the kept holds until the cut-off, which takes all four (#637).
    assert payments.called("capture") == []
    await the_cut_off_comes(session_factory, clock)
    await mailbox.drain()
    assert (
        len({call.arguments["payment_id"] for call in payments.called("capture")}) == 4
    )
    for player in (marta, oscar, ivan):
        notices = await notices_of(client, mailbox, player)
        assert (notices[0]["title"], notices[0]["body"]) == (
            "Your Sat 17:00 is booked · 40 zł held",
            "Padel at Bonarka Arena.",
        )
        assert "Your Sat 17:00 is booked · 40 zł held" in await subjects_to(
            mailbox, player
        )
        # Nobody is told *It's a game!* twice.
        assert sum(n["title"].startswith("It's a game!") for n in notices) == 1
    # Hers is her own *It's a game!* — she sees it on her phone.
    [hers, *_] = await notices_of(client, mailbox, paula)
    assert (hers["title"], hers["your_own"]) == ("It's a game! · 40 zł held", True)
    assert "It's a game! · 40 zł held" in await subjects_to(mailbox, paula)
    for player in four:
        assert (await the_card(client, player, proposal))["status"] == "BOOKED"
    assert await to_confirm(client, paula) == []


async def test_out_of_time_to_fix_her_seat_reopens_and_the_holds_are_let_go(
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
    assert (owed["confirm_by"], owed["time_to"]) == (None, None)
    [hers, *_] = await notices_of(client, mailbox, paula)
    assert (hers["kind"], hers["title"], hers["body"]) == (
        "TIME_TO_FIX_RAN_OUT",
        "Your time to fix your card ran out · Sat 17:00",
        "Your seat is open to others now, and you owe nothing — you can still "
        "take it back while it's free.",
    )
    # Nothing was ever taken from anybody.
    assert payments.called("capture") == []
    for player in (marta, oscar, ivan):
        assert (await told(client, mailbox, player))[0] == (
            "Your Sat 17:00 at Bonarka Arena is filling again",
            "A seat opened — nobody paid.",
        )
        card = await the_card(client, player, proposal)
        assert (card["status"], card["filling_again"]) == ("SEAT_OPEN", True)
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
    assert "Your time to fix your card ran out · Sat 17:00" in [
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
    assert left.json()["left"] == "WHILE_WAITING_FOR_A_PAYMENT"
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
    assert (hers["status"], hers["your_payment_due_by"], hers["time_to"]) == (
        "SEAT_OPEN",
        PAY_BY,
        "FIX_THE_CARD",
    )
    # Nobody else's card names a time any more.
    assert (await the_card(client, marta, proposal))["time_to"] is None
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
    # Past Friday's cut-off: hers is a time to pay.
    assert (await the_card(client, paula, proposal))["time_to"] == "PAY"
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


# --------------------------------------------------------------------------- #
# Time to fix the card never runs past the cut-off (#638)
# --------------------------------------------------------------------------- #


async def test_a_card_refused_just_before_the_cut_off_has_until_the_cut_off(
    client, session_factory, clock, payments, mailbox, bonarka, four
):
    """Friday 16:50, ten minutes before the cut-off: her time to fix her card
    ends at it, not thirty minutes on."""

    club, _ = bonarka
    paula, *_ = four
    clock.move(SATURDAY_FIVE_S_CUT_OFF - MONDAY_MORNING - timedelta(minutes=10))

    proposal, answer = await a_game(client, session_factory, clock, club, four)

    assert answer["payment_awaited_until"] == "2026-10-09T15:00:00Z"
    [owed] = await to_confirm(client, paula)
    assert (owed["confirm_by"], owed["time_to"]) == (
        "2026-10-09T15:00:00Z",
        "FIX_THE_CARD",
    )
    assert (await told(client, mailbox, paula))[0][0] == (
        "Fix your card by 17:00 to keep your seat"
    )
    clock.move(timedelta(minutes=10))
    assert (await runs_out(session_factory, clock)).games == 1
    assert (await told(client, mailbox, paula))[0][0] == (
        "Your time to fix your card ran out · Sat 17:00"
    )


# --------------------------------------------------------------------------- #
# After the cut-off, money is taken at once: time to pay (#638)
# --------------------------------------------------------------------------- #


@pytest.fixture
def after_the_cut_off(clock) -> MovableClock:
    """Saturday 08:00 — Friday 17:00's cut-off has passed, the book-by not."""

    clock.move(SATURDAY_MORNING - MONDAY_MORNING)
    return clock


async def test_a_game_filling_after_its_cut_off_gives_a_refused_payment_time_to_pay(
    client, session_factory, after_the_cut_off, payments, mailbox, bonarka, four
):
    club, _ = bonarka
    paula, marta, *_ = four

    proposal, answer = await a_game(
        client, session_factory, after_the_cut_off, club, four
    )

    assert answer["payment_awaited_until"] == PAY_BY_ON_SATURDAY
    [hers, *_] = await notices_of(client, mailbox, paula)
    assert (hers["kind"], hers["title"], hers["body"]) == (
        "CONFIRM_PAYMENT",
        "Confirm your payment by 08:30 to keep your seat",
        "Padel · Sat 17:00 at Bonarka Arena — the others are waiting.",
    )
    [email] = await mailbox.to("paula@example.com")
    assert email.subject == "Confirm your payment by 08:30 to keep your seat"
    assert "Fix your card" not in email.text
    card = await the_card(client, paula, proposal)
    assert (card["your_payment_due_by"], card["time_to"]) == (
        PAY_BY_ON_SATURDAY,
        "PAY",
    )
    assert (await the_card(client, marta, proposal))["time_to"] == "PAY"
    booking = await client.get(f"/api/v1/bookings/{proposal}", headers=paula["headers"])
    assert booking.json()["time_to"] == "PAY"
    details = await client.get(
        f"/api/v1/proposals/{proposal}", headers=paula["headers"]
    )
    assert details.json()["time_to"] == "PAY"
    assert details.json()["your_payment"]["time_to"] == "PAY"
    [owed] = await to_confirm(client, paula)
    assert (owed["confirm_by"], owed["time_to"]) == (PAY_BY_ON_SATURDAY, "PAY")


async def test_paying_in_time_after_the_cut_off_takes_every_share_at_once(
    client, session_factory, after_the_cut_off, payments, mailbox, bonarka, four
):
    club, _ = bonarka
    paula, *_ = four
    proposal, _ = await a_game(client, session_factory, after_the_cut_off, club, four)
    [owed] = await to_confirm(client, paula)

    paid = await confirms(client, payments, paula, owed["seat_charge_id"])

    assert paid.json()["booked"]["booking_id"] == str(proposal), paid.text
    await mailbox.drain()
    assert (
        len({call.arguments["payment_id"] for call in payments.called("capture")}) == 4
    )


async def test_out_of_time_to_pay_after_the_cut_off_her_seat_reopens(
    client, session_factory, after_the_cut_off, payments, mailbox, bonarka, four
):
    club, _ = bonarka
    paula, marta, *_ = four
    proposal, _ = await a_game(client, session_factory, after_the_cut_off, club, four)
    await mailbox.drain()
    after_the_cut_off.move(timedelta(minutes=30))

    assert (await runs_out(session_factory, after_the_cut_off)).games == 1

    [hers, *_] = await notices_of(client, mailbox, paula)
    assert (hers["kind"], hers["title"]) == (
        "TIME_TO_PAY_RAN_OUT",
        "Your time to pay ran out · Sat 17:00",
    )
    assert (await told(client, mailbox, marta))[0] == (
        "Your Sat 17:00 at Bonarka Arena is filling again",
        "A seat opened — nobody paid.",
    )

