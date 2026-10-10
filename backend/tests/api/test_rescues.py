"""**Rescues: seats to fill** (#545; the mechanics §8.1, §10.1, §12.3, §19; the
screens A2.3, A3.1, A4.3).

A booked game that lost a player offers the seat: on the group's **Fill in**
board to every member who fits and is free for the hour, and as a **Seat open**
card to the best fits' decks. **Taking it is the joiner's share held** until
the cut-off, like every seat's, or taken at once after it (#637) — the first
join wins and a second is told the seat was just taken — and **the leaver who
left after the cut-off is refunded, less the card fee, the moment the joiner's
payment succeeds**. Open seats stay until the cut-off whatever their number, then until
the start.

Every act is taken over HTTP as the phone takes it, against the fake payment
provider, and every claim is read where somebody would read it — the board, the
deck, Home, the details, the receipts, the mailbox, the chat, the record.

The clock stands on **Monday 5 October 2026, 08:00 in Kraków**; the game is
**Saturday 10 October, 17:00** at Bonarka Arena, padel at 120 zł — 30 zł a
seat — with a 24-hour cut-off, so it *fills by* **Friday 17:00**.
"""

from __future__ import annotations

from datetime import timedelta
from uuid import UUID

import pytest

from app.api.dependencies import get_clock
from app.bootstrap.composition import build_the_cut_off
from app.core.config import get_settings
from app.modules.payments.domain.entered_cards import A_CARD_THE_BANK_ALWAYS_CHECKS
from tests.api.proposals_world import (
    MONDAY_MORNING,
    SATURDAY_FIVE,
    a_club_and_its_desk,
    a_group,
    a_member,
    live_ids,
    makes,
    saves_a_card,
    says_yes,
    warsaw,
)
from tests.unit.fake_clock import MovableClock

SHARE = 30_00
#: The card fee the fake provider keeps on a 30 zł refund: 1.5 % and 1 zł.
FEE = 1_45
CUT_OFF = SATURDAY_FIVE - timedelta(hours=24)
AFTER_THE_CUT_OFF = CUT_OFF + timedelta(hours=1)
EVENINGS = [{"day": day, "hour": hour} for day in range(1, 8) for hour in (17, 18)]
MORNINGS = [{"day": day, "hour": hour} for day in range(1, 8) for hour in (8, 9)]


@pytest.fixture
def clock(app):
    """Monday 5 October 2026, 08:00 in Kraków."""

    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


@pytest.fixture
async def club(client) -> str:
    """Bonarka Arena, Instant: one padel court, a 24-hour cut-off."""

    club_id, _desk = await a_club_and_its_desk(client, way="INSTANT")
    return club_id


@pytest.fixture
async def crowd(client, session_factory, payments) -> list[dict]:
    """Ola, Kuba, Ewa and Tomek — who book Saturday's game — and Zosia and
    Marek, who could take a seat on it: all at padel 2,5, free every hour,
    competitive, each with a card that pays."""

    return [
        await a_member(client, session_factory, payments, name)
        for name in ("ola", "kuba", "ewa", "tomek", "zosia", "marek")
    ]


@pytest.fixture
async def group(client, club, crowd) -> UUID:
    return await a_group(client, crowd[0], club, *crowd[1:])


@pytest.fixture
async def booking(client, session_factory, clock, club, group, crowd) -> str:
    """The four's game on Saturday at 17:00, booked by Tomek's yes."""

    four = crowd[:4]
    proposal = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    for player in four[:3]:
        assert (await says_yes(client, player, proposal)).status_code == 200
    last = await says_yes(client, four[3], proposal)
    assert last.status_code == 200, last.text
    return last.json()["booked"]["booking_id"]


async def leaves(client, player: dict, booking_id: str):
    left = await client.post(
        f"/api/v1/bookings/{booking_id}/departure", headers=player["headers"]
    )
    assert left.status_code == 200, left.text
    return left.json()["left"]


async def joins(client, player: dict, booking_id: str):
    return await client.post(
        f"/api/v1/bookings/{booking_id}/seats", headers=player["headers"]
    )


async def fill_in(client, player: dict, group: UUID) -> dict:
    read = await client.get(
        f"/api/v1/pools/{group}/fill-in",
        params={"sport": "PADEL"},
        headers=player["headers"],
    )
    assert read.status_code == 200, read.text
    return read.json()


async def deck_cards(client, player: dict, group: UUID) -> list[dict]:
    read = await client.get(
        f"/api/v1/pools/{group}/deck",
        params={"sport": "PADEL", "kind": "COMPETITIVE"},
        headers=player["headers"],
    )
    assert read.status_code == 200, read.text
    return read.json()["cards"]


async def home_of(client, player: dict) -> list[dict]:
    read = await client.get("/api/v1/home", headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()["games"]


async def receipts_of(client, mailbox, player: dict) -> list[dict]:
    # The money follows the commit: the outbox takes and gives back first.
    await mailbox.drain()
    read = await client.get("/api/v1/players/me/receipts", headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()["receipts"]


async def rooms_of(client, mailbox, player: dict) -> list[str]:
    await mailbox.drain()
    read = await client.get("/api/v1/conversations", headers=player["headers"])
    assert read.status_code == 200, read.text
    return [room["booking_id"] for room in read.json()["conversations"]]


async def cuts_off(session_factory, clock):
    async with session_factory() as session:
        return await build_the_cut_off(
            session, clock=clock, settings=get_settings()
        ).execute()


async def own_record(client, player: dict) -> dict:
    read = await client.get("/api/v1/players/me/record", headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()


# --------------------------------------------------------------------------- #
# The board
# --------------------------------------------------------------------------- #


async def test_a_seat_left_is_on_the_board_of_a_member_who_fits_and_is_free(
    client, group, booking, crowd
):
    ola, kuba, ewa, tomek, zosia, _ = crowd
    await leaves(client, kuba, booking)

    board = await fill_in(client, zosia, group)

    assert board["badge"] == 1
    [row] = board["seats_to_fill"]
    assert row["booking_id"] == booking
    assert (row["sport"], row["kind"], row["court_name"]) == (
        "PADEL",
        "COMPETITIVE",
        "Court 1",
    )
    assert row["club"]["name"] == "Bonarka Arena"
    assert (row["share_grosze"], row["open_seats"]) == (SHARE, 1)
    assert row["fills_by_the_cut_off"] is True
    assert row["deadline"].startswith("2026-10-09T15:00:00")
    assert {tile["player_id"] for tile in row["players"]} == {
        str(ola["id"]),
        str(ewa["id"]),
        str(tomek["id"]),
    }
    # Held until the cut-off, which takes them: not paid yet (#637).
    assert not any(tile["paid"] for tile in row["players"])
    # Nobody on the game, nor the leaver, is offered a seat on it.
    assert (await fill_in(client, ola, group))["seats_to_fill"] == []
    assert (await fill_in(client, kuba, group))["seats_to_fill"] == []


async def test_the_board_offers_nothing_to_a_member_who_is_not_free_or_wants_fun(
    client, session_factory, payments, group, booking, crowd
):
    kuba = crowd[1]
    mornings = await a_member(client, session_factory, payments, "ania", week=MORNINGS)
    for_fun = await a_member(
        client, session_factory, payments, "piotr", intent="FOR_FUN"
    )
    for player in (mornings, for_fun):
        joined = await client.post(
            f"/api/v1/groups/{group}/membership", headers=player["headers"]
        )
        assert joined.status_code in (200, 201), joined.text
    await leaves(client, kuba, booking)

    assert (await fill_in(client, mornings, group))["badge"] == 0
    assert (await fill_in(client, for_fun, group))["badge"] == 0


async def test_a_stranger_reads_no_group_s_board(client, payments, group, crowd):
    from tests.api.proposals_world import a_player

    stranger = await a_player(client, payments, "zbyszek")

    read = await client.get(
        f"/api/v1/pools/{group}/fill-in",
        params={"sport": "PADEL"},
        headers=stranger["headers"],
    )

    assert (read.status_code, read.json()["code"]) == (404, "pool_not_found")


# --------------------------------------------------------------------------- #
# How long a seat stays
# --------------------------------------------------------------------------- #


async def test_a_seat_left_after_the_cut_off_is_offered_until_the_start(
    client, clock, group, booking, crowd
):
    kuba, zosia = crowd[1], crowd[4]
    clock.move(AFTER_THE_CUT_OFF - MONDAY_MORNING)
    await leaves(client, kuba, booking)

    [row] = (await fill_in(client, zosia, group))["seats_to_fill"]
    assert row["fills_by_the_cut_off"] is False
    assert row["deadline"].startswith("2026-10-10T15:00:00")

    clock.move(SATURDAY_FIVE - AFTER_THE_CUT_OFF)
    assert (await fill_in(client, zosia, group))["seats_to_fill"] == []


async def test_a_seat_still_open_at_the_cut_off_leaves_the_board_with_the_game(
    client, clock, group, booking, crowd
):
    kuba, zosia = crowd[1], crowd[4]
    await leaves(client, kuba, booking)
    clock.move(CUT_OFF - MONDAY_MORNING)

    assert (await fill_in(client, zosia, group))["seats_to_fill"] == []
    joined = await joins(client, zosia, booking)
    assert (joined.status_code, joined.json()["code"]) == (409, "booking_is_called_off")


async def test_open_seats_stay_until_the_cut_off_whatever_their_number(
    client, session_factory, clock, group, booking, crowd, mailbox
):
    ola, kuba, ewa, tomek, zosia, marek = crowd
    for leaver in (kuba, ewa, tomek):
        await leaves(client, leaver, booking)

    [row] = (await fill_in(client, zosia, group))["seats_to_fill"]
    assert row["open_seats"] == 3
    taken = await joins(client, zosia, booking)
    assert (taken.status_code, taken.json()["open_seats"]) == (200, 2)
    [row] = (await fill_in(client, marek, group))["seats_to_fill"]
    assert row["open_seats"] == 2

    clock.move(CUT_OFF - MONDAY_MORNING)
    assert (await cuts_off(session_factory, clock)).games == 1

    # Still short at the cut-off: everybody still in, the rescue too, has
    # their hold let go — nothing was taken (#637).
    assert await receipts_of(client, mailbox, zosia) == []
    assert await receipts_of(client, mailbox, ola) == []


# --------------------------------------------------------------------------- #
# Taking a seat
# --------------------------------------------------------------------------- #


async def test_taking_a_seat_holds_the_share_and_the_game_is_whole_again(
    client, session_factory, clock, payments, group, booking, crowd, mailbox
):
    """Before the cut-off a rescue follows the seats it joins (#637): its share
    is held, and the cut-off takes it with everybody's."""

    ola, kuba, *_ = crowd
    zosia = crowd[4]
    await leaves(client, kuba, booking)

    taken = await joins(client, zosia, booking)

    assert taken.status_code == 200, taken.text
    answer = taken.json()
    assert answer["booked"]["booking_id"] == booking
    assert answer["open_seats"] == 0
    assert answer["your_payment"] is None
    [card] = await home_of(client, zosia)
    assert (card["booking_id"], card["status"], card["open_seats"]) == (
        booking,
        "BOOKED",
        0,
    )
    assert (card["money"]["paid"], card["money"]["share_state"]) == (False, "HELD")
    [olas] = await home_of(client, ola)
    assert (olas["status"], olas["needs_you"]) == ("BOOKED", False)
    assert await receipts_of(client, mailbox, zosia) == []
    [email] = [
        sent
        for sent in await mailbox.to("zosia@example.com")
        if sent.subject.startswith("It's a game!")
    ]
    assert email.subject == "It's a game! · 30 zł held"
    clock.move(CUT_OFF - MONDAY_MORNING)
    await cuts_off(session_factory, clock)
    [charge] = await receipts_of(client, mailbox, zosia)
    assert (charge["kind"], charge["amount_grosze"]) == ("CHARGE", SHARE)
    assert len(payments.called("capture")) == 4
    assert booking in await rooms_of(client, mailbox, zosia)
    assert (await fill_in(client, crowd[5], group))["seats_to_fill"] == []


async def test_the_first_join_wins_and_the_second_is_told_the_seat_was_just_taken(
    client, payments, group, booking, crowd, mailbox
):
    kuba, zosia, marek = crowd[1], crowd[4], crowd[5]
    await leaves(client, kuba, booking)
    held_before = len(payments.called("authorise"))

    first = await joins(client, zosia, booking)
    second = await joins(client, marek, booking)

    assert first.status_code == 200, first.text
    assert (second.status_code, second.json()["code"]) == (409, "seat_just_taken")
    # Marek's bank was never asked.
    assert len(payments.called("authorise")) == held_before + 1
    assert await receipts_of(client, mailbox, marek) == []


async def test_a_second_tap_of_the_joiner_charges_nothing_more(
    client, payments, booking, crowd, mailbox
):
    kuba, zosia = crowd[1], crowd[4]
    await leaves(client, kuba, booking)
    first = await joins(client, zosia, booking)
    held = len(payments.called("authorise"))

    again = await joins(client, zosia, booking)

    assert again.status_code == 200, again.text
    assert again.json()["booked"] == first.json()["booked"]
    assert len(payments.called("authorise")) == held
    # Held, not taken, until the cut-off (#637): nothing charged twice.
    await receipts_of(client, mailbox, zosia)
    assert len(payments.called("authorise")) == held


async def test_nobody_takes_a_seat_on_a_game_they_left_or_are_in(
    client, booking, crowd
):
    ola, kuba = crowd[0], crowd[1]
    await leaves(client, kuba, booking)

    back = await joins(client, kuba, booking)
    already = await joins(client, ola, booking)

    assert (back.status_code, back.json()["code"]) == (409, "rescue_not_offered")
    assert already.status_code == 200
    assert already.json()["open_seats"] == 1


async def test_no_seat_is_taken_once_the_game_has_begun(client, clock, booking, crowd):
    kuba, zosia = crowd[1], crowd[4]
    clock.move(AFTER_THE_CUT_OFF - MONDAY_MORNING)
    await leaves(client, kuba, booking)
    clock.move(SATURDAY_FIVE - AFTER_THE_CUT_OFF)

    joined = await joins(client, zosia, booking)

    assert (joined.status_code, joined.json()["code"]) == (409, "game_has_started")


async def test_a_whole_game_has_no_seat_to_take(client, booking, crowd):
    joined = await joins(client, crowd[4], booking)

    assert (joined.status_code, joined.json()["code"]) == (409, "seat_just_taken")


# --------------------------------------------------------------------------- #
# The leaver's money, and their record
# --------------------------------------------------------------------------- #


async def test_a_leaver_after_the_cut_off_is_refunded_less_the_fee_once_it_is_taken(
    client, session_factory, clock, booking, crowd, mailbox
):
    kuba, zosia = crowd[1], crowd[4]
    clock.move(AFTER_THE_CUT_OFF - MONDAY_MORNING)
    await cuts_off(session_factory, clock)
    await leaves(client, kuba, booking)
    [charge] = await receipts_of(client, mailbox, kuba)
    assert charge["kind"] == "CHARGE"

    assert (await joins(client, zosia, booking)).status_code == 200

    refund, charge = await receipts_of(client, mailbox, kuba)
    assert (refund["kind"], refund["amount_grosze"], refund["card_fee_grosze"]) == (
        "REFUND",
        SHARE - FEE,
        FEE,
    )
    [email] = [
        sent
        for sent in await mailbox.to("kuba@example.com")
        if sent.subject.startswith("You've been refunded")
    ]
    assert email.subject == "You've been refunded · your seat was taken"
    assert "30 zł share is being refunded" in email.text


async def test_a_leaver_before_the_cut_off_had_nothing_taken_and_gets_nothing_back(
    client, payments, booking, crowd, mailbox
):
    """His hold was let go when he left (#637): his seat taken gives him
    nothing back, since nothing was taken."""

    kuba, zosia = crowd[1], crowd[4]
    await leaves(client, kuba, booking)

    assert (await joins(client, zosia, booking)).status_code == 200

    assert await receipts_of(client, mailbox, kuba) == []
    assert payments.called("refund") == []
    assert not [
        sent
        for sent in await mailbox.to("kuba@example.com")
        if sent.subject.startswith("You've been refunded")
    ]


async def test_a_leaver_whose_seat_was_taken_kept_the_game_off_their_record(
    client, clock, booking, crowd
):
    kuba, zosia = crowd[1], crowd[4]
    clock.move(AFTER_THE_CUT_OFF - MONDAY_MORNING)
    await leaves(client, kuba, booking)
    assert (await joins(client, zosia, booking)).status_code == 200

    clock.move(SATURDAY_FIVE - AFTER_THE_CUT_OFF + timedelta(hours=2))

    assert "reliability" not in await own_record(client, kuba)


# --------------------------------------------------------------------------- #
# The deck, and a no
# --------------------------------------------------------------------------- #


async def test_a_seat_open_card_is_dealt_to_the_best_fits(
    client, group, booking, crowd
):
    ola, kuba, ewa, tomek, zosia, _ = crowd
    await leaves(client, kuba, booking)

    [card] = await deck_cards(client, zosia, group)

    assert card["type"] == "SEAT_OPEN"
    assert card["proposal_id"] == booking
    assert (card["court"], card["court_name"]) == ("BOOKED", "Court 1")
    assert (card["share_grosze"], card["open_seats_after_your_yes"]) == (SHARE, 0)
    assert card["in_count"] == 0
    assert card["no_free_cancellation"] is False
    assert card["deadline"].startswith("2026-10-09T15:00:00")
    # Zosia stands in Kuba's seat, on his side, beside his partner.
    yours = [tile["player_id"] for tile in card["sides"]["yours"]]
    assert yours[0] == str(zosia["id"])
    paid = {
        tile["player_id"]
        for tile in [*card["sides"]["yours"], *card["sides"]["theirs"]]
        if tile["paid"]
    }
    # Held until the cut-off, which takes them: not paid yet (#637).
    assert paid == set()
    assert (await deck_cards(client, ola, group)) == []


async def test_a_no_to_a_seat_open_card_keeps_it_out_of_the_deck_and_on_the_board(
    client, group, booking, crowd
):
    kuba, zosia = crowd[1], crowd[4]
    await leaves(client, kuba, booking)

    said = await client.post(f"/api/v1/bookings/{booking}/no", headers=zosia["headers"])
    again = await client.post(
        f"/api/v1/bookings/{booking}/no", headers=zosia["headers"]
    )

    assert (said.status_code, again.status_code) == (204, 204)
    assert await deck_cards(client, zosia, group) == []
    assert (await fill_in(client, zosia, group))["badge"] == 1
    assert (await joins(client, zosia, booking)).status_code == 200


# --------------------------------------------------------------------------- #
# The rescue seen from outside
# --------------------------------------------------------------------------- #


async def test_a_member_offered_the_seat_reads_the_game_from_outside(
    client, payments, booking, crowd
):
    from tests.api.proposals_world import a_player

    kuba, zosia = crowd[1], crowd[4]
    await leaves(client, kuba, booking)
    stranger = await a_player(client, payments, "zbyszek")

    read = await client.get(f"/api/v1/bookings/{booking}", headers=zosia["headers"])
    outside = await client.get(
        f"/api/v1/bookings/{booking}", headers=stranger["headers"]
    )

    assert read.status_code == 200, read.text
    details = read.json()
    assert details["status"] == "SEAT_OPEN"
    assert details["court_name"] == "Court 1"
    assert details["rescue"]["fills_by_the_cut_off"] is True
    assert details["rescue"]["deadline"].startswith("2026-10-09T15:00:00")
    assert (details["leaving"], details["check_in"]) == (None, None)
    assert details["needs_you"] is False
    # Zosia has paid nothing and has nothing to leave: *I'm in · 30 zł*.
    assert details["money"] == {
        "share_grosze": SHARE,
        "paid": False,
        "share_state": None,
        "taken_at": None,
        "free_to_leave_until": None,
        "refunded_grosze": None,
    }
    [you, *partner] = details["sides"]["yours"]
    assert (you["player_id"], you["is_you"], you["paid"]) == (
        str(zosia["id"]),
        True,
        False,
    )
    # The others' shares are held until the cut-off, not paid yet (#637).
    assert not any(tile["paid"] for tile in [*partner, *details["sides"]["theirs"]])
    assert (outside.status_code, outside.json()["code"]) == (404, "booking_not_found")


# --------------------------------------------------------------------------- #
# A bank that wants the joiner
# --------------------------------------------------------------------------- #


def payment_of(secret: str) -> str:
    """The fake's payment, by the secret it handed out (``fake_payments.py``)."""

    return secret.split("_secret_")[0]


async def test_a_refused_payment_takes_no_seat_and_confirming_it_is_the_join_again(
    client, payments, booking, crowd, mailbox
):
    kuba, zosia = crowd[1], crowd[4]
    await saves_a_card(
        client, payments, zosia["headers"], A_CARD_THE_BANK_ALWAYS_CHECKS
    )
    await leaves(client, kuba, booking)

    refused = await joins(client, zosia, booking)

    assert refused.status_code == 200, refused.text
    assert refused.json()["booked"] is None
    assert refused.json()["open_seats"] == 1
    payment = refused.json()["your_payment"]
    assert payment["refusal"] == "AUTHENTICATION_REQUIRED"
    again = await joins(client, zosia, booking)
    assert (again.status_code, again.json()["code"]) == (409, "payment_to_confirm")
    assert again.json()["details"]["seat_charge_id"] == payment["seat_charge_id"]
    [email] = await mailbox.to("zosia@example.com")
    assert email.subject == "Confirm your payment to take the seat"

    charge = f"/api/v1/seat-charges/{payment['seat_charge_id']}"
    secret = (await client.get(charge, headers=zosia["headers"])).json()["to_confirm"][
        "client_secret"
    ]
    payments.phone_confirms_payment(payment_of(secret))
    confirmed = await client.post(f"{charge}/confirmation", headers=zosia["headers"])

    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["booked"]["booking_id"] == booking
    assert confirmed.json()["open_seats"] == 0
    [card] = await home_of(client, zosia)
    assert card["status"] == "BOOKED"


async def test_a_payment_confirmed_after_somebody_else_took_the_seat_is_let_go(
    client, payments, booking, crowd, mailbox
):
    kuba, zosia, marek = crowd[1], crowd[4], crowd[5]
    await saves_a_card(
        client, payments, zosia["headers"], A_CARD_THE_BANK_ALWAYS_CHECKS
    )
    await leaves(client, kuba, booking)
    payment = (await joins(client, zosia, booking)).json()["your_payment"]
    assert (await joins(client, marek, booking)).status_code == 200

    charge = f"/api/v1/seat-charges/{payment['seat_charge_id']}"
    secret = (await client.get(charge, headers=zosia["headers"])).json()["to_confirm"]
    assert secret is None
    late = await client.post(f"{charge}/confirmation", headers=zosia["headers"])

    # The last seat went to Marek, and Zosia's payment was let go with the board.
    assert (late.status_code, late.json()["code"]) == (409, "payment_not_confirmed")
    assert await receipts_of(client, mailbox, zosia) == []


# --------------------------------------------------------------------------- #
# The joiner's other yeses
# --------------------------------------------------------------------------- #


async def test_a_seat_taken_pauses_the_joiner_s_other_yeses_in_a_full_week(
    client, session_factory, clock, club, group, booking, crowd
):
    kuba, zosia, marek = crowd[1], crowd[4], crowd[5]
    capped = await client.put(
        "/api/v1/players/me/games-and-money",
        json={"games_per_week": 1, "most_ill_pay_grosze": None},
        headers=zosia["headers"],
    )
    assert capped.status_code == 200, capped.text
    sunday = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=warsaw(11, 10),
        versions=((zosia, marek, crowd[0], crowd[2]),),
    )
    assert (await says_yes(client, zosia, sunday)).status_code == 200
    await leaves(client, kuba, booking)

    assert (await joins(client, zosia, booking)).status_code == 200

    assert str(sunday) not in await live_ids(client, zosia)


async def test_the_deck_deals_a_seat_to_three_best_fits_and_the_board_to_every_fit(
    client, session_factory, payments, group, booking, crowd
):
    """Everybody here forecasts alike, so the pool's own order — who joined
    first — breaks the tie: Zosia, Marek and Ania are dealt the card."""

    kuba, zosia, marek = crowd[1], crowd[4], crowd[5]
    later = [
        await a_member(client, session_factory, payments, name)
        for name in ("ania", "piotr", "basia")
    ]
    for player in later:
        joined = await client.post(
            f"/api/v1/groups/{group}/membership", headers=player["headers"]
        )
        assert joined.status_code in (200, 201), joined.text
    ania, piotr, basia = later
    await leaves(client, kuba, booking)

    dealt = {
        player["name"]: [
            card["type"] for card in await deck_cards(client, player, group)
        ]
        for player in (zosia, marek, ania, piotr, basia)
    }

    assert dealt == {
        "zosia": ["SEAT_OPEN"],
        "marek": ["SEAT_OPEN"],
        "ania": ["SEAT_OPEN"],
        "piotr": [],
        "basia": [],
    }
    for player in (piotr, basia):
        assert (await fill_in(client, player, group))["badge"] == 1


async def test_a_no_hands_the_seat_open_card_to_the_next_best_fit(
    client, session_factory, payments, group, booking, crowd
):
    """The mechanics §6.2: a no deals the seat to the next best fit — so a
    member who said no holds none of the three places."""

    kuba, zosia = crowd[1], crowd[4]
    later = [
        await a_member(client, session_factory, payments, name)
        for name in ("ania", "piotr")
    ]
    for player in later:
        joined = await client.post(
            f"/api/v1/groups/{group}/membership", headers=player["headers"]
        )
        assert joined.status_code in (200, 201), joined.text
    piotr = later[1]
    await leaves(client, kuba, booking)
    assert await deck_cards(client, piotr, group) == []

    said = await client.post(f"/api/v1/bookings/{booking}/no", headers=zosia["headers"])

    assert said.status_code == 204
    [card] = await deck_cards(client, piotr, group)
    assert card["type"] == "SEAT_OPEN"
