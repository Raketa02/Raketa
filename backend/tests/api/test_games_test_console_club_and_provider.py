"""The games test console as the club and the payment provider (#591;
``docs/adr/0194`` §2–§5).

**The club row** answers a request, moves and cancels as the club whose court
it is — each press the club route's own use case, so it
answers what the desk's own button answers, refusals included. **The payment
provider** is the process's fake, given controls: a card set to succeed,
decline or ask for the bank's check; a payment the bank confirms on the phone a
laptop cannot reach the bank from; a refund delivered; and the notices it would
have sent, replayed twice or out of order through the webhook's own handling.
**Run it now** runs the club's answer window over what is due. And two
situations: *Needs her yes, On request club* (3) and *Card declines at the
fill* (4). *Check-in at the club* went with desk check-in (#651).

Every claim is read where somebody would read it: the protagonist's Home, deck,
receipts and booking details, and the desk's own lists.

The world: **Bonarka Arena**, Instant, two padel courts at 30 zł a seat, and
**Kazimierz Padel**, On request with thirty minutes to confirm, a kilometre
away — both desks addressed on the seed's reserved TLD — and four members the
seed could have made. The clock stands on **Monday 5 October 2026, 08:00 in
Kraków**.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID, uuid4

import pytest

from app.api.dependencies import get_clock
from app.modules.payments.presentation.dependencies import get_payment_provider
from tests.api import players_world as players
from tests.api.club_courts_world import adds_a_court, sets_hours
from tests.api.console_world import (
    CLUB,
    CONSOLE,
    PLAYER,
    SEED,
    at,
    board_of,
    code_of,
    deck_of,
    home_of,
    pane_of,
    presses,
    receipts_of,
    rows_of,
    says,
)
from tests.api.proposals_world import (
    MONDAY_MORNING,
    SATURDAY_FIVE,
    a_club_and_its_desk,
    a_group,
    a_member,
    a_player,
    every_hour_of_the_week,
    makes,
    the_cut_off_comes,
)
from tests.unit.fake_clock import MovableClock

#: Thirty minutes, Kazimierz's time to confirm.
TIME_TO_CONFIRM = timedelta(minutes=30)
#: Monday at 09:00 — the first hour Bonarka sells that has not begun.


@pytest.fixture
def clock(app):
    """Monday 5 October 2026, 08:00 in Kraków."""

    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


@dataclass(frozen=True)
class World:
    #: Instant, with Court 1 and Court 3 for padel.
    bonarka: str
    bonarka_desk: dict
    #: On request, thirty minutes to confirm.
    kazimierz: str
    kazimierz_desk: dict
    group: UUID
    #: The protagonist — the phone in the tester's hand.
    marta: dict
    kuba: dict
    zofia: dict
    marek: dict

    @property
    def three(self) -> tuple[dict, dict, dict]:
        return self.kuba, self.zofia, self.marek

    @property
    def four(self) -> tuple[dict, dict, dict, dict]:
        return self.marta, self.kuba, self.zofia, self.marek


@pytest.fixture
async def world(client, session_factory, payments, clock) -> World:
    bonarka, bonarka_desk = await a_club_and_its_desk(
        client, email=f"desk.bonarka@{SEED}"
    )
    second = await adds_a_court(client, bonarka_desk, name="Court 3", sport="PADEL")
    await sets_hours(client, bonarka_desk, [second["id"]], every_hour_of_the_week())
    kazimierz, kazimierz_desk = await a_club_and_its_desk(
        client,
        name="Kazimierz Padel",
        email=f"desk.kazimierz@{SEED}",
        way="ON_REQUEST",
        point=(50.05, 19.94),
    )
    marta, kuba, zofia, marek = [
        await a_member(client, session_factory, payments, name, domain=SEED)
        for name in ("marta", "kuba", "zofia", "marek")
    ]
    group = await a_group(client, marta, bonarka, kuba, zofia, marek)
    return World(
        bonarka,
        bonarka_desk,
        kazimierz,
        kazimierz_desk,
        group,
        marta,
        kuba,
        zofia,
        marek,
    )


# --------------------------------------------------------------------------- #
# Games, made as the platform makes them
# --------------------------------------------------------------------------- #


async def a_card(session_factory, clock, world: World, club: str, **kwargs) -> UUID:
    """A pick dealt to the four — Saturday 17:00 unless told otherwise."""

    return await makes(
        session_factory,
        clock,
        pool_id=world.group,
        club_id=club,
        versions=(world.four,),
        **kwargs,
    )


async def all_but_hers(client, game: UUID, world: World) -> None:
    """Kuba, Zofia and Marek say yes from the console's rows."""

    for member in world.three:
        said = await says(client, CONSOLE, "yes", member, game)
        assert said.status_code == 200, said.text


async def a_request(client, session_factory, clock, world: World, **kwargs) -> UUID:
    """The four's game at Kazimierz, her yes last: waiting for the club."""

    game = await a_card(session_factory, clock, world, world.kazimierz, **kwargs)
    await all_but_hers(client, game, world)
    hers = await says(client, PLAYER, "yes", world.marta, game)
    assert hers.json()["waiting_for_the_club"] is True, hers.text
    return game


async def a_booked_game(
    client, session_factory, payments, clock, world: World, **kwargs
) -> UUID:
    """The four's game at Bonarka, her yes last — booked, every share held
    until the cut-off (#637)."""

    game = await a_card(session_factory, clock, world, world.bonarka, **kwargs)
    await all_but_hers(client, game, world)
    hers = await says(client, PLAYER, "yes", world.marta, game)
    assert hers.json()["booked"] is not None, hers.text
    await players.deliver_the_outbox(session_factory, payments=payments)
    return game


async def a_taken_game(
    client, session_factory, payments, clock, world: World, **kwargs
) -> UUID:
    """``a_booked_game``, and its cut-off come: every share taken and
    captured."""

    game = await a_booked_game(client, session_factory, payments, clock, world)
    await the_cut_off_comes(session_factory, clock)
    await players.deliver_the_outbox(session_factory, payments=payments)
    return game


def charge_of(board: dict, game: UUID, member: dict) -> dict:
    [charge] = [
        charge
        for charge in pane_of(board, game)["charges"]
        if charge["player"]["player_id"] == str(member["id"])
    ]
    return charge


async def her_home_game(client, world: World, game: UUID) -> dict:
    [found] = [
        g for g in await home_of(client, world.marta) if g["booking_id"] == str(game)
    ]
    return found


async def waiting_at(client, desk: dict) -> list[dict]:
    read = await client.get("/api/v1/club/bookings/waiting", headers=desk)
    assert read.status_code == 200, read.text
    return read.json()["bookings"]


async def the_desk_s_day(client, desk: dict) -> list[dict]:
    read = await client.get(
        "/api/v1/club/bookings", params={"date": "2026-10-05"}, headers=desk
    )
    assert read.status_code == 200, read.text
    return read.json()["bookings"]


# --------------------------------------------------------------------------- #
# The club row's presses are the desk's own
# --------------------------------------------------------------------------- #

_CLUB_ACTS = {
    "accept": ("POST", "acceptance"),
    "refuse": ("POST", "refusal"),
    "free courts": ("GET", "free-courts"),
    "move": ("POST", "move"),
    "cancel": ("POST", "cancellation"),
}


async def club_does(
    client, via: str, verb: str, club: str, desk: dict, booking: UUID, body=None
):
    """``verb`` on a booking, as the club: from its own desk, or from the
    console's club row, which holds no token."""

    method, tail = _CLUB_ACTS[verb]
    if via == CLUB:
        return await client.request(
            method, f"/api/v1/club/bookings/{booking}/{tail}", json=body, headers=desk
        )
    return await client.request(
        method, f"/dev/clubs/{club}/bookings/{booking}/{tail}", json=body
    )


@pytest.mark.parametrize("via", [CLUB, CONSOLE])
async def test_accepting_a_request_books_it_as_the_club_s_own(
    client, session_factory, clock, world, via
):
    game = await a_request(client, session_factory, clock, world)

    accepted = await club_does(
        client, via, "accept", world.kazimierz, world.kazimierz_desk, game
    )

    assert accepted.status_code == 200, accepted.text
    assert accepted.json() == {
        "outcome": "BOOKED",
        "court_name": "Court 1",
        "payment_due_by": None,
        "time_to": None,
    }
    assert (await her_home_game(client, world, game))["status"] == "BOOKED"
    assert await waiting_at(client, world.kazimierz_desk) == []


@pytest.mark.parametrize("via", [CLUB, CONSOLE])
async def test_accepting_an_answered_request_is_refused_alike(
    client, session_factory, clock, world, via
):
    game = await a_request(client, session_factory, clock, world)
    first = await club_does(
        client, CLUB, "accept", world.kazimierz, world.kazimierz_desk, game
    )
    assert first.status_code == 200, first.text

    again = await club_does(
        client, via, "accept", world.kazimierz, world.kazimierz_desk, game
    )

    assert again.status_code == 409, again.text
    assert code_of(again) == "request_not_waiting"


@pytest.mark.parametrize("via", [CLUB, CONSOLE])
async def test_refusing_a_request_calls_it_off_as_the_club_s_own(
    client, session_factory, clock, world, via
):
    game = await a_request(client, session_factory, clock, world)

    refused = await club_does(
        client,
        via,
        "refuse",
        world.kazimierz,
        world.kazimierz_desk,
        game,
        body={"reason": "Court booked by a league"},
    )

    assert refused.status_code == 204, refused.text
    home = await her_home_game(client, world, game)
    assert (home["status"], home["called_off_reason"]) == ("CALLED_OFF", "REFUSED")
    assert await waiting_at(client, world.kazimierz_desk) == []


@pytest.mark.parametrize("via", [CLUB, CONSOLE])
async def test_moving_a_game_as_the_club_s_own(
    client, session_factory, payments, clock, world, via
):
    game = await a_booked_game(client, session_factory, payments, clock, world)

    free = await club_does(
        client, via, "free courts", world.bonarka, world.bonarka_desk, game
    )
    assert free.status_code == 200, free.text
    [court] = free.json()["courts"]
    assert court["name"] == "Court 3"
    moved = await club_does(
        client,
        via,
        "move",
        world.bonarka,
        world.bonarka_desk,
        game,
        body={"court_id": court["court_id"]},
    )

    assert moved.status_code == 200, moved.text
    assert moved.json() == court
    assert (await her_home_game(client, world, game))["court_name"] == "Court 3"


@pytest.mark.parametrize("via", [CLUB, CONSOLE])
async def test_moving_onto_a_court_that_is_not_free_is_refused_alike(
    client, session_factory, payments, clock, world, via
):
    game = await a_booked_game(client, session_factory, payments, clock, world)

    moved = await club_does(
        client,
        via,
        "move",
        world.bonarka,
        world.bonarka_desk,
        game,
        body={"court_id": str(uuid4())},
    )

    assert moved.status_code == 409, moved.text
    assert code_of(moved) == "court_not_free"


@pytest.mark.parametrize("via", [CLUB, CONSOLE])
async def test_cancelling_a_game_as_the_club_s_own(
    client, session_factory, payments, clock, world, via
):
    game = await a_booked_game(client, session_factory, payments, clock, world)

    cancelled = await club_does(
        client,
        via,
        "cancel",
        world.bonarka,
        world.bonarka_desk,
        game,
        body={"reason": "WEATHER"},
    )

    assert cancelled.status_code == 204, cancelled.text
    home = await her_home_game(client, world, game)
    assert (home["status"], home["called_off_reason"], home["club_cancel_reason"]) == (
        "CALLED_OFF",
        "CANCELLED_BY_THE_CLUB",
        "WEATHER",
    )


@pytest.mark.parametrize("via", [CLUB, CONSOLE])
async def test_cancelling_a_game_called_off_already_is_refused_alike(
    client, session_factory, payments, clock, world, via
):
    game = await a_booked_game(client, session_factory, payments, clock, world)
    first = await club_does(
        client,
        CLUB,
        "cancel",
        world.bonarka,
        world.bonarka_desk,
        game,
        body={"reason": "REPAIR"},
    )
    assert first.status_code == 204, first.text

    again = await club_does(
        client,
        via,
        "cancel",
        world.bonarka,
        world.bonarka_desk,
        game,
        body={"reason": "REPAIR"},
    )

    assert again.status_code == 409, again.text
    assert code_of(again) == "booking_is_called_off"


@pytest.mark.parametrize(
    ("method", "tail"),
    [
        ("POST", "bookings/{booking}/acceptance"),
        ("POST", "bookings/{booking}/refusal"),
        ("GET", "bookings/{booking}/free-courts"),
        ("POST", "bookings/{booking}/move"),
        ("POST", "bookings/{booking}/cancellation"),
    ],
)
async def test_the_club_row_refuses_a_club_the_seed_did_not_create(
    client, world, method, tail
):
    """A club whose desk signs in at a real address is somebody's — and an id
    that is no club's is not one the seed made either."""

    real, _ = await a_club_and_its_desk(client, name="Wisła Park")
    bodies = {
        "move": {"court_id": str(uuid4())},
        "cancellation": {"reason": "OTHER"},
    }
    body = bodies.get(tail.rsplit("/", 1)[-1])

    for club in (real, uuid4()):
        pressed = await client.request(
            method,
            f"/dev/clubs/{club}/" + tail.format(booking=uuid4()),
            json=body,
        )

        assert pressed.status_code == 403, pressed.text
        assert code_of(pressed) == "not_a_seed_account"


# --------------------------------------------------------------------------- #
# The payment provider: a card steered
# --------------------------------------------------------------------------- #


async def card_does(client, member: dict, outcome: str):
    return await client.put(
        f"/dev/payments/cards/{member['id']}", json={"outcome": outcome}
    )


async def test_each_row_shows_their_saved_card_and_what_it_will_do(
    client, clock, world
):
    rows = rows_of(await board_of(client, world.group))
    assert rows["marta"]["card"] == {
        "brand": "visa",
        "last_four": "4242",
        "outcome": "SUCCEEDS",
        "kind": "PERSONAL_EU",
        "network": "visa",
    }

    steered = await card_does(client, world.marta, "DECLINES")

    assert steered.status_code == 200, steered.text
    assert steered.json()["outcome"] == "DECLINES"
    rows = rows_of(await board_of(client, world.group))
    assert rows["marta"]["card"]["outcome"] == "DECLINES"
    assert rows["kuba"]["card"]["outcome"] == "SUCCEEDS"
    assert (await board_of(client, world.group))["payments"] == {
        "steerable": True,
        "refunds_wait": False,
    }


async def test_a_card_is_set_to_a_kind_and_a_network_each_on_its_own(
    client, payments, clock, world
):
    """**The fee kept and how long a hold lasts** (ADR-0190's 2026-10-10
    amendment): a business card keeps 1,9 % + 1 zł, and a Mastercard holds a
    share 7 days. Each press moves one thing and leaves the rest."""

    as_business = await client.put(
        f"/dev/payments/cards/{world.marta['id']}", json={"kind": "BUSINESS"}
    )
    on_mastercard = await client.put(
        f"/dev/payments/cards/{world.marta['id']}", json={"network": "mastercard"}
    )

    assert as_business.status_code == 200, as_business.text
    assert (as_business.json()["kind"], as_business.json()["network"]) == (
        "BUSINESS",
        "visa",
    )
    assert on_mastercard.status_code == 200, on_mastercard.text
    assert on_mastercard.json()["outcome"] == "SUCCEEDS"
    assert "business card" in on_mastercard.json()["says"]
    assert "7 days" in on_mastercard.json()["says"]
    card = rows_of(await board_of(client, world.group))["marta"]["card"]
    assert (card["brand"], card["kind"], card["network"]) == (
        "visa",
        "BUSINESS",
        "mastercard",
    )
    assert rows_of(await board_of(client, world.group))["kuba"]["card"]["kind"] == (
        "PERSONAL_EU"
    )


async def test_a_card_kind_the_provider_does_not_know_is_refused(client, world):
    pressed = await client.put(
        f"/dev/payments/cards/{world.marta['id']}", json={"kind": "PLATINUM"}
    )

    assert pressed.status_code == 422, pressed.text


@pytest.mark.parametrize(
    ("outcome", "refusal"),
    [("DECLINES", "DECLINED"), ("ASKS_FOR_VERIFICATION", "AUTHENTICATION_REQUIRED")],
)
async def test_a_card_steered_away_from_paying_refuses_her_share_at_the_fill(
    client, session_factory, clock, world, outcome, refusal
):
    steered = await card_does(client, world.marta, outcome)
    assert steered.status_code == 200, steered.text
    game = await a_card(session_factory, clock, world, world.bonarka)
    await all_but_hers(client, game, world)

    hers = await says(client, PLAYER, "yes", world.marta, game)

    assert hers.status_code == 200, hers.text
    assert hers.json()["booked"] is None
    assert hers.json()["your_payment"]["refusal"] == refusal
    to_confirm = await client.get(
        "/api/v1/players/me/payments-to-confirm", headers=world.marta["headers"]
    )
    assert to_confirm.status_code == 200, to_confirm.text
    assert [p["proposal_id"] for p in to_confirm.json()["payments"]] == [str(game)]
    assert await receipts_of(client, world.marta) == []


async def test_a_card_steered_back_to_succeed_pays_again(
    client, session_factory, payments, clock, world
):
    await card_does(client, world.marta, "DECLINES")

    steered = await card_does(client, world.marta, "SUCCEEDS")

    assert steered.status_code == 200, steered.text
    await a_taken_game(client, session_factory, payments, clock, world)
    [receipt] = await receipts_of(client, world.marta)
    assert (receipt["kind"], receipt["starts_at"]) == ("CHARGE", at(SATURDAY_FIVE))


@pytest.mark.parametrize("outcome", ["DECLINES", "ASKS_FOR_VERIFICATION"])
async def test_the_bank_confirms_a_refused_payment_and_her_confirmation_books_it(
    client, session_factory, clock, world, outcome
):
    """A laptop's phone cannot reach a bank: the console is the bank saying yes
    — another card typed, or the check passed — and the phone's own *Confirm*
    is then the yes again."""

    await card_does(client, world.marta, outcome)
    game = await a_card(session_factory, clock, world, world.bonarka)
    await all_but_hers(client, game, world)
    refused = (await says(client, PLAYER, "yes", world.marta, game)).json()
    charge = refused["your_payment"]["seat_charge_id"]

    bank = await client.post(f"/dev/payments/charges/{charge}/bank-confirms")

    assert bank.status_code == 200, bank.text
    confirmed = await client.post(
        f"/api/v1/seat-charges/{charge}/confirmation", headers=world.marta["headers"]
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["booked"]["booking_id"] == str(game)
    assert (await her_home_game(client, world, game))["status"] == "BOOKED"


async def test_the_bank_confirms_only_a_payment_waiting_for_its_player(
    client, session_factory, payments, clock, world
):
    game = await a_booked_game(client, session_factory, payments, clock, world)
    taken = charge_of(await board_of(client, world.group), game, world.marta)

    bank = await client.post(
        f"/dev/payments/charges/{taken['charge_id']}/bank-confirms"
    )

    assert bank.status_code == 409, bank.text
    assert code_of(bank) == "payment_not_waiting_for_its_player"


async def test_a_card_is_steered_only_for_a_seed_account_with_one_saved(
    client, session_factory, payments, clock, world
):
    piotr = await a_player(client, payments, "piotr")
    ewa = await a_member(
        client, session_factory, payments, "ewa", domain=SEED, card=False
    )

    real = await card_does(client, piotr, "DECLINES")
    nobody = await card_does(client, {"id": uuid4()}, "DECLINES")
    no_card = await card_does(client, ewa, "DECLINES")

    assert (real.status_code, code_of(real)) == (403, "not_a_seed_account")
    assert (nobody.status_code, code_of(nobody)) == (403, "not_a_seed_account")
    assert (no_card.status_code, code_of(no_card)) == (409, "no_saved_card")


async def test_the_controls_refuse_a_provider_that_is_not_the_process_s_fake(
    app, client, world
):
    class Stripe:
        """Any provider but the fake: the console has nothing to steer."""

    app.dependency_overrides[get_payment_provider] = lambda: Stripe()

    steered = await card_does(client, world.marta, "DECLINES")
    waits = await client.put("/dev/payments/refunds", json={"wait": True})

    assert (steered.status_code, code_of(steered)) == (409, "provider_not_the_fake")
    assert (waits.status_code, code_of(waits)) == (409, "provider_not_the_fake")
    assert (await board_of(client, world.group))["payments"] == {
        "steerable": False,
        "refunds_wait": None,
    }


# --------------------------------------------------------------------------- #
# The payment provider: a refund delivered
# --------------------------------------------------------------------------- #


async def the_club_cancels(client, game: UUID, world: World) -> None:
    """From its desk, after the cut-off took the shares: everybody refunded in
    full (#637) — a refund decided, and made from the outbox."""

    cancelled = await client.post(
        f"/api/v1/club/bookings/{game}/cancellation",
        json={"reason": "WEATHER"},
        headers=world.bonarka_desk,
    )
    assert cancelled.status_code == 204, cancelled.text


def kinds(receipts: list[dict]) -> list[str]:
    return sorted(receipt["kind"] for receipt in receipts)


async def test_a_refund_decided_is_delivered_from_the_console(
    client, session_factory, payments, clock, world
):
    game = await a_taken_game(client, session_factory, payments, clock, world)
    await the_club_cancels(client, game, world)
    assert kinds(await receipts_of(client, world.kuba)) == ["CHARGE"]
    charge = charge_of(await board_of(client, world.group), game, world.kuba)

    delivered = await client.post(f"/dev/payments/charges/{charge['charge_id']}/refund")

    assert delivered.status_code == 200, delivered.text
    assert delivered.json()["given_at"] == at(clock.now())
    assert delivered.json()["given_back_grosze"] == 30_00
    assert kinds(await receipts_of(client, world.kuba)) == ["CHARGE", "REFUND"]


async def test_refunds_that_wait_land_only_when_one_is_delivered(
    client, session_factory, payments, clock, world
):
    game = await a_taken_game(client, session_factory, payments, clock, world)
    waits = await client.put("/dev/payments/refunds", json={"wait": True})
    assert waits.status_code == 200, waits.text
    await the_club_cancels(client, game, world)

    # The outbox asks the provider, which has not given it.
    await players.deliver_the_outbox(session_factory, payments=payments)
    assert kinds(await receipts_of(client, world.kuba)) == ["CHARGE"]
    charge = charge_of(await board_of(client, world.group), game, world.kuba)
    assert charge["refund"]["given_at"] is None

    delivered = await client.post(f"/dev/payments/charges/{charge['charge_id']}/refund")

    assert delivered.status_code == 200, delivered.text
    assert kinds(await receipts_of(client, world.kuba)) == ["CHARGE", "REFUND"]
    # The outbox's next try finds it given, and asks nothing twice.
    await players.deliver_the_outbox(session_factory, payments=payments)
    assert kinds(await receipts_of(client, world.kuba)) == ["CHARGE", "REFUND"]


async def test_delivering_a_refund_nobody_decided_is_refused(
    client, session_factory, payments, clock, world
):
    game = await a_booked_game(client, session_factory, payments, clock, world)
    charge = charge_of(await board_of(client, world.group), game, world.kuba)

    delivered = await client.post(f"/dev/payments/charges/{charge['charge_id']}/refund")
    nobody_s = await client.post(f"/dev/payments/charges/{uuid4()}/refund")

    assert (delivered.status_code, code_of(delivered)) == (409, "no_refund_decided")
    assert (nobody_s.status_code, code_of(nobody_s)) == (404, "seat_charge_not_found")


# --------------------------------------------------------------------------- #
# The payment provider: its notices, replayed
# --------------------------------------------------------------------------- #


async def notices_of(client, game: UUID) -> list[dict]:
    read = await client.get("/dev/payments/notices", params={"game_id": str(game)})
    assert read.status_code == 200, read.text
    return read.json()["notices"]


async def delivers(client, *notice_ids: str):
    return await client.post(
        "/dev/payments/notices/delivery", json={"notice_ids": list(notice_ids)}
    )


async def test_a_game_s_notices_are_listed_in_the_order_its_payments_moved(
    client, session_factory, payments, clock, world
):
    game = await a_taken_game(client, session_factory, payments, clock, world)

    notices = await notices_of(client, game)

    kuba = [n for n in notices if n["player"]["player_id"] == str(world.kuba["id"])]
    assert [(n["kind"], n["status"], n["read"]) for n in kuba] == [
        ("payment_intent.amount_capturable_updated", "AUTHORISED", False),
        ("payment_intent.succeeded", "CAPTURED", False),
    ]
    assert len(notices) == 8


async def test_a_confirmation_replayed_twice_is_read_once(
    client, session_factory, payments, clock, world
):
    game = await a_taken_game(client, session_factory, payments, clock, world)
    [taken] = [
        n
        for n in await notices_of(client, game)
        if n["player"]["player_id"] == str(world.kuba["id"])
        and n["kind"] == "payment_intent.succeeded"
    ]

    delivered = await delivers(client, taken["notice_id"], taken["notice_id"])

    assert delivered.status_code == 200, delivered.text
    assert [d["read"] for d in delivered.json()["deliveries"]] == [True, False]
    assert kinds(await receipts_of(client, world.kuba)) == ["CHARGE"]
    [listed] = [
        n
        for n in await notices_of(client, game)
        if n["notice_id"] == taken["notice_id"]
    ]
    assert listed["read"] is True


async def test_confirmations_out_of_order_move_nothing_the_provider_does_not_say(
    client, session_factory, payments, clock, world
):
    game = await a_taken_game(client, session_factory, payments, clock, world)
    newest_first = [n["notice_id"] for n in reversed(await notices_of(client, game))]

    delivered = await delivers(client, *newest_first)

    assert delivered.status_code == 200, delivered.text
    assert all(d["read"] for d in delivered.json()["deliveries"])
    for member in world.four:
        assert kinds(await receipts_of(client, member)) == ["CHARGE"]
    [booking] = await the_desk_s_day_of(client, world, SATURDAY_FIVE)
    assert booking["money"]["collected_grosze"] == 120_00
    assert all(p["paid"] for p in booking["players"])


async def the_desk_s_day_of(client, world: World, day) -> list[dict]:
    read = await client.get(
        "/api/v1/club/bookings",
        params={"date": day.date().isoformat()},
        headers=world.bonarka_desk,
    )
    assert read.status_code == 200, read.text
    return read.json()["bookings"]


async def test_her_confirmation_arriving_before_her_phone_s_still_fills_the_game(
    client, session_factory, clock, world
):
    """The notice that the bank said yes reaches the server before her phone
    does — out of order with the refusal before it."""

    await card_does(client, world.marta, "DECLINES")
    game = await a_card(session_factory, clock, world, world.bonarka)
    await all_but_hers(client, game, world)
    refused = (await says(client, PLAYER, "yes", world.marta, game)).json()
    charge = refused["your_payment"]["seat_charge_id"]
    await client.post(f"/dev/payments/charges/{charge}/bank-confirms")
    hers = [
        n
        for n in await notices_of(client, game)
        if n["player"]["player_id"] == str(world.marta["id"])
    ]
    assert [n["kind"] for n in hers] == [
        "payment_intent.payment_failed",
        "payment_intent.amount_capturable_updated",
    ]

    delivered = await delivers(client, *(n["notice_id"] for n in reversed(hers)))

    assert delivered.status_code == 200, delivered.text
    confirmed = await client.post(
        f"/api/v1/seat-charges/{charge}/confirmation", headers=world.marta["headers"]
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["booked"]["booking_id"] == str(game)


async def test_a_notice_about_a_share_the_seed_did_not_make_is_refused(
    client, session_factory, payments, clock, world
):
    """Piotr signed up himself: his payment's notice is his money's, and the
    console moves nobody's but the seed's."""

    piotr = await a_member(client, session_factory, payments, "piotr")
    joined = await client.post(
        f"/api/v1/groups/{world.group}/membership", headers=piotr["headers"]
    )
    assert joined.status_code in (200, 201), joined.text
    game = await makes(
        session_factory,
        clock,
        pool_id=world.group,
        club_id=world.bonarka,
        versions=((world.marta, world.kuba, world.zofia, piotr),),
    )
    for member in (world.kuba, world.zofia, world.marta):
        await says(client, CONSOLE, "yes", member, game)
    booked = await says(client, PLAYER, "yes", piotr, game)
    assert booked.json()["booked"] is not None, booked.text
    [his] = [
        n
        for n in await notices_of(client, game)
        if n["player"]["player_id"] == str(piotr["id"])
    ]

    delivered = await delivers(client, his["notice_id"])

    assert (delivered.status_code, code_of(delivered)) == (403, "not_a_seed_account")


async def test_a_notice_the_provider_never_sent_is_refused_before_any_is_read(
    client, session_factory, payments, clock, world
):
    game = await a_booked_game(client, session_factory, payments, clock, world)
    first = (await notices_of(client, game))[0]

    delivered = await delivers(client, first["notice_id"], "evt_fake_nobody")

    assert delivered.status_code == 404, delivered.text
    assert code_of(delivered) == "notice_not_found"
    assert (await notices_of(client, game))[0]["read"] is False


# --------------------------------------------------------------------------- #
# Run it now: the club's answer window
# --------------------------------------------------------------------------- #


async def runs_the_answer_window(client):
    ran = await client.post("/dev/jobs/request-timeout")
    assert ran.status_code == 200, ran.text
    return ran.json()


async def test_run_it_now_leaves_a_request_that_is_not_due_waiting(
    client, session_factory, clock, world
):
    game = await a_request(client, session_factory, clock, world)

    ran = await runs_the_answer_window(client)

    assert ran["done"] == 0
    assert (await her_home_game(client, world, game))[
        "status"
    ] == "WAITING_FOR_THE_CLUB"
    assert len(await waiting_at(client, world.kazimierz_desk)) == 1


async def test_run_it_now_calls_off_a_request_once_its_answer_is_due(
    client, session_factory, clock, world
):
    game = await a_request(client, session_factory, clock, world)
    clock.move(TIME_TO_CONFIRM + timedelta(minutes=1))

    ran = await runs_the_answer_window(client)

    assert ran["done"] == 1
    home = await her_home_game(client, world, game)
    assert (home["status"], home["called_off_reason"]) == ("CALLED_OFF", "NO_ANSWER")
    assert (await runs_the_answer_window(client))["done"] == 0


# --------------------------------------------------------------------------- #
# Situation 3 · Needs her yes, On request club
# --------------------------------------------------------------------------- #


async def test_needs_her_yes_on_request_leaves_her_yes_to_ask_the_club(
    client, session_factory, clock, world
):
    game = await a_card(session_factory, clock, world, world.kazimierz)

    pressed = await presses(
        client,
        "needs-her-yes-on-request-club",
        group_id=world.group,
        sport="PADEL",
        protagonist_id=world.marta["id"],
    )

    assert pressed.status_code == 200, pressed.text
    assert pressed.json()["game_id"] == str(game)
    assert pressed.json()["answer_by"] is None
    [card] = [
        c
        for c in await deck_of(client, world.marta, world.group)
        if c["proposal_id"] == str(game)
    ]
    assert (card["in_count"], card["open_seats_after_your_yes"]) == (3, 0)
    assert card["club_confirms"] is True
    # Her yes, from her phone, asks the club — and the club row answers it.
    hers = await says(client, PLAYER, "yes", world.marta, game)
    assert hers.json()["waiting_for_the_club"] is True, hers.text
    [waiting] = await waiting_at(client, world.kazimierz_desk)
    assert waiting["booking_id"] == str(game)
    accepted = await club_does(
        client, CONSOLE, "accept", world.kazimierz, world.kazimierz_desk, game
    )
    assert accepted.json()["outcome"] == "BOOKED", accepted.text


async def test_needs_her_yes_on_request_says_so_when_no_game_can_be_set_up(
    client, clock, world
):
    """Nobody in the group is rated in tennis, so no tennis card can be left
    needing her — and the situation says so rather than inventing one."""

    pressed = await presses(
        client,
        "needs-her-yes-on-request-club",
        group_id=world.group,
        sport="TENNIS",
        protagonist_id=world.marta["id"],
    )

    assert pressed.status_code == 409, pressed.text
    assert code_of(pressed) == "situation_unavailable"


async def test_needs_her_yes_on_request_can_have_asked_the_club_minutes_ago(
    client, clock, world
):
    """The request written as if it had been asked twenty-five minutes ago, so
    the club's half hour runs out in five — and *Run it now* then calls it
    off, and not a moment before."""

    pressed = await presses(
        client,
        "needs-her-yes-on-request-club",
        group_id=world.group,
        sport="PADEL",
        protagonist_id=world.marta["id"],
        answer_due_in_minutes=5,
    )

    assert pressed.status_code == 200, pressed.text
    answer_by = MONDAY_MORNING + timedelta(minutes=5)
    assert pressed.json()["answer_by"] == at(answer_by)
    assert "5 min" in pressed.json()["says"]
    game = UUID(pressed.json()["game_id"])
    assert (await her_home_game(client, world, game))[
        "status"
    ] == "WAITING_FOR_THE_CLUB"
    [waiting] = await waiting_at(client, world.kazimierz_desk)
    assert (waiting["booking_id"], waiting["answer_by"]) == (str(game), at(answer_by))
    assert {p["player_id"] for p in waiting["players"]} == {
        str(m["id"]) for m in world.four
    }

    assert (await runs_the_answer_window(client))["done"] == 0
    clock.move(timedelta(minutes=6))
    assert (await runs_the_answer_window(client))["done"] == 1

    home = await her_home_game(client, world, game)
    assert (home["status"], home["called_off_reason"]) == ("CALLED_OFF", "NO_ANSWER")
    assert await waiting_at(client, world.kazimierz_desk) == []


async def test_needs_her_yes_on_request_asks_now_when_the_club_gives_less_time(
    client, clock, world
):
    """Kazimierz gives thirty minutes: asked for forty-five, the club is asked
    now and its answer is due when its own half hour runs out."""

    pressed = await presses(
        client,
        "needs-her-yes-on-request-club",
        group_id=world.group,
        sport="PADEL",
        protagonist_id=world.marta["id"],
        answer_due_in_minutes=45,
    )

    assert pressed.status_code == 200, pressed.text
    assert pressed.json()["answer_by"] == at(MONDAY_MORNING + TIME_TO_CONFIRM)


# --------------------------------------------------------------------------- #
# Situation 4 · Card declines at the fill
# --------------------------------------------------------------------------- #


async def test_card_declines_at_the_fill_leaves_her_yes_to_be_refused_and_recovered(
    client, session_factory, clock, world
):
    game = await a_card(session_factory, clock, world, world.bonarka)

    pressed = await presses(
        client,
        "card-declines-at-the-fill",
        group_id=world.group,
        sport="PADEL",
        protagonist_id=world.marta["id"],
    )

    assert pressed.status_code == 200, pressed.text
    assert pressed.json()["game_id"] == str(game)
    assert (
        rows_of(await board_of(client, world.group))["marta"]["card"]["outcome"]
        == "DECLINES"
    )
    [card] = [
        c
        for c in await deck_of(client, world.marta, world.group)
        if c["proposal_id"] == str(game)
    ]
    assert card["open_seats_after_your_yes"] == 0
    # Her yes, from her phone: the fill refuses her share and books nothing.
    hers = await says(client, PLAYER, "yes", world.marta, game)
    assert hers.json()["booked"] is None
    assert hers.json()["your_payment"]["refusal"] == "DECLINED"
    # The recovery: her bank says yes, and her confirmation books it.
    charge = hers.json()["your_payment"]["seat_charge_id"]
    await client.post(f"/dev/payments/charges/{charge}/bank-confirms")
    confirmed = await client.post(
        f"/api/v1/seat-charges/{charge}/confirmation", headers=world.marta["headers"]
    )
    assert confirmed.json()["booked"]["booking_id"] == str(game), confirmed.text


async def test_a_situation_makes_its_game_only_at_a_club_the_seed_signed_up(
    client, payments, clock, world
):
    """The same four in a group homed at a club whose desk is somebody's: the
    game is made at Bonarka, a seed club the group also plays at, and never at
    the real club."""

    real, _ = await a_club_and_its_desk(client, name="Wisła Park")
    homed_elsewhere = await a_group(
        client, world.marta, real, world.kuba, world.zofia, world.marek
    )

    pressed = await presses(
        client,
        "just-played",
        group_id=homed_elsewhere,
        sport="PADEL",
        protagonist_id=world.marta["id"],
    )

    assert pressed.status_code == 200, pressed.text
    assert pressed.json()["club_id"] == world.bonarka


@pytest.mark.parametrize(
    "situation",
    [
        "needs-her-yes-on-request-club",
        "card-declines-at-the-fill",
    ],
)
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
