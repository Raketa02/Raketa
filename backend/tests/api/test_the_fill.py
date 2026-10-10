"""**The last yes books the game** (#541; the mechanics §11–§12.2; ADR-0189 §2,
§4–§5): every seat held together on the club's account until the cut-off
(#637), or nobody; a Booking on the first free court, opening an ordinary Game
and its chat; and what that does to everybody's other yeses and to the club's
hours.

Every act is taken over HTTP as the phone takes it, against the **fake payment
provider** the application holds, and every claim is read where somebody would
read it — the yes's answer, receipts, live yeses, the games list, the room, the
mailbox — except what only the provider sees: which calls were made, in which
order. The client gives its ten seconds of *Undo* before it sends the yes, so
the yes here is the one that arrives.

The clock stands on **Monday 5 October 2026, 08:00 in Kraków**; the game is
**Saturday 10 October, 17:00** at Bonarka Arena, padel at 120 zł — 30 zł a
seat — with a 24-hour cut-off.
"""

from __future__ import annotations

from datetime import timedelta
from uuid import UUID

import pytest
import stripe
from sqlalchemy import select

from app.api.dependencies import get_clock
from app.bootstrap.composition import build_court_hours
from app.core.config import get_settings
from app.infrastructure.events.event_store_model import EventStoreORM
from app.kernel import Sport
from app.modules.conversations.infrastructure.conversation_model import (
    ConversationORM,
)
from app.modules.payments.domain.entered_cards import (
    A_CARD_THAT_DECLINES_LATER,
    A_CARD_THE_BANK_ALWAYS_CHECKS,
)
from app.modules.proposals.domain.errors import CourtHourNotForSale
from tests.api import players_world as players
from app.modules.bookings.infrastructure.event_sourced_booking_repository import (
    SqlAlchemyBookingDirectory,
)
from tests.api.club_courts_world import adds_a_court, sets_hours
from tests.api.proposals_world import (
    MONDAY_MORNING,
    SATURDAY_FIVE,
    a_club_and_its_desk,
    a_club_selling,
    a_group,
    a_player,
    deals,
    every_hour_of_the_week,
    live_ids,
    makes,
    runs_out,
    saves_a_card,
    says_yes,
    sweeps,
    the_cut_off_comes,
    warsaw,
)
from tests.api.test_payment_notices import notice
from tests.unit.fake_clock import MovableClock

RECEIPTS = "/api/v1/players/me/receipts"
GAMES = "/api/v1/games"
CONNECT_WEBHOOK = "/api/v1/webhooks/stripe-connect"
CONNECT_SECRET = "whsec_the_fill_s_own"


def seat_charge_path(charge_id: str) -> str:
    return f"/api/v1/seat-charges/{charge_id}"


@pytest.fixture
def clock(app):
    """Monday 5 October 2026, 08:00 in Kraków."""

    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


@pytest.fixture
async def club(client) -> str:
    return await a_club_selling(client)


@pytest.fixture
async def four(client, payments) -> list[dict]:
    """Ola, Kuba, Ewa and Tomek: rated in padel, each with a card that pays."""

    return [
        await a_player(client, payments, name)
        for name in ("ola", "kuba", "ewa", "tomek")
    ]


@pytest.fixture
async def group(client, club, four) -> UUID:
    return await a_group(client, four[0], club, *four[1:])


async def a_full_card_but_one(
    client, session_factory, clock, *, club: str, group: UUID, four: list[dict]
) -> UUID:
    """The four's game at Bonarka on Saturday at 17:00, three of them In."""

    proposal = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    for player in four[:3]:
        said = await says_yes(client, player, proposal)
        assert said.status_code == 200, said.text
    return proposal


async def events_of(session_factory, aggregate_id: UUID) -> list[str]:
    async with session_factory() as session:
        return list(
            (
                await session.scalars(
                    select(EventStoreORM.event_type)
                    .where(EventStoreORM.aggregate_id == aggregate_id)
                    .order_by(EventStoreORM.version)
                )
            ).all()
        )


async def receipts(client, player: dict) -> list[dict]:
    read = await client.get(RECEIPTS, headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()["receipts"]


def payment_of(secret: str) -> str:
    """The fake's payment, by the secret it handed out (``fake_payments.py``)."""

    return secret.split("_secret_")[0]


# --------------------------------------------------------------------------- #
# All or nothing
# --------------------------------------------------------------------------- #


async def test_the_last_yes_books_the_game_and_holds_every_seat_together(
    client, session_factory, clock, payments, mailbox, club, four, group
):
    proposal = await a_full_card_but_one(
        client, session_factory, clock, club=club, group=group, four=four
    )
    assert payments.called("authorise") == []

    last = await says_yes(client, four[3], proposal)

    assert last.status_code == 200, last.text
    answer = last.json()
    assert answer["open_seats"] == 0
    assert answer["your_payment"] is None
    assert answer["booked"]["booking_id"] == str(proposal)
    # Every seat held on the club's account, off-session, for its share.
    held = payments.called("authorise")
    assert len(held) == 4
    assert {call.arguments["amount_grosze"] for call in held} == {30_00}
    assert {call.arguments["metadata"]["player_id"] for call in held} == {
        str(player["id"]) for player in four
    }
    await mailbox.drain()
    # Held until the club's cut-off, which takes them (#637).
    assert payments.called("capture") == []
    assert payments.called("cancel") == []
    assert await receipts(client, four[0]) == []
    await the_cut_off_comes(session_factory, clock)
    await mailbox.drain()
    assert len(payments.called("capture")) == 4
    for player in four:
        [receipt] = await receipts(client, player)
        assert receipt["kind"] == "CHARGE"
        assert receipt["amount_grosze"] == 30_00
        assert receipt["club"] == {"id": club, "name": "Bonarka Arena"}
        assert receipt["sport"] == "PADEL"
        assert receipt["starts_at"] == "2026-10-10T15:00:00Z"
        assert await live_ids(client, player) == []


async def test_every_seat_is_held_before_any_is_taken(
    client, session_factory, clock, payments, mailbox, club, four, group
):
    """The money moves only once every hold is in, and only at the club's
    cut-off (#637) — the captures follow the cut-off's commit."""

    proposal = await a_full_card_but_one(
        client, session_factory, clock, club=club, group=group, four=four
    )

    await says_yes(client, four[3], proposal)
    await mailbox.drain()
    at_the_fill = [call.name for call in payments.calls if call.name == "capture"]
    await the_cut_off_comes(session_factory, clock)
    await mailbox.drain()

    acts = [
        call.name for call in payments.calls if call.name in ("authorise", "capture")
    ]
    assert at_the_fill == []
    assert acts == ["authorise"] * 4 + ["capture"] * 4


async def test_a_declined_card_means_nobody_pays_and_its_seat_waits_for_him(
    client, session_factory, clock, payments, mailbox, club, four
):
    """Nobody pays, and **his seat is held for him alone** for his time to pay
    (#625, Q109): the three holds made wait on their cards, so paying in time
    books the game on them."""

    tomek = await a_player(
        client, payments, "tomek2", entered=A_CARD_THAT_DECLINES_LATER
    )
    players = [*four[:3], tomek]
    group = await a_group(client, four[0], club, *players[1:])
    proposal = await a_full_card_but_one(
        client, session_factory, clock, club=club, group=group, four=players
    )

    last = await says_yes(client, tomek, proposal)

    answer = last.json()
    assert last.status_code == 200, last.text
    assert answer["booked"] is None
    assert answer["open_seats"] == 0
    assert answer["your_payment"]["refusal"] == "DECLINED"
    assert answer["your_payment"]["confirm_by"] == "2026-10-05T06:30:00Z"
    await mailbox.drain()
    # Nothing is taken, and the three holds made are kept.
    assert payments.called("cancel") == []
    assert payments.called("capture") == []
    for player in players:
        assert await receipts(client, player) == []
    # Every one of them is still In: his seat is his until his time runs out.
    for player in players:
        assert await live_ids(client, player) == [str(proposal)]
    charge = await client.get(
        seat_charge_path(answer["your_payment"]["seat_charge_id"]),
        headers=tomek["headers"],
    )
    assert charge.json()["status"] == "FAILED"
    assert charge.json()["to_confirm"]["client_secret"]


async def test_somebody_else_s_decline_books_nothing_and_says_nothing_of_theirs(
    client, session_factory, clock, payments, club, four
):
    tomek = await a_player(
        client, payments, "tomek2", entered=A_CARD_THAT_DECLINES_LATER
    )
    players = [tomek, *four[:3]]
    group = await a_group(client, four[0], club, tomek, *four[1:3])
    proposal = await a_full_card_but_one(
        client, session_factory, clock, club=club, group=group, four=players
    )

    last = await says_yes(client, players[3], proposal)

    answer = last.json()
    assert answer["booked"] is None
    assert answer["open_seats"] == 0
    # Not this player's payment, so nothing about it is theirs to confirm —
    # only that the game waits for one, and until when (Q110).
    assert answer["your_payment"] is None
    assert answer["payment_awaited_until"] == "2026-10-05T06:30:00Z"


async def test_the_player_is_asked_by_email_to_confirm_and_the_others_are_not(
    client, session_factory, clock, payments, mailbox, club, four
):
    tomek = await a_player(
        client, payments, "tomek2", entered=A_CARD_THAT_DECLINES_LATER
    )
    players = [*four[:3], tomek]
    group = await a_group(client, four[0], club, *players[1:])
    proposal = await a_full_card_but_one(
        client, session_factory, clock, club=club, group=group, four=players
    )

    await says_yes(client, tomek, proposal)

    [email] = await mailbox.to("tomek2@example.com")
    # Before the cut-off nothing is taken: his card is to fix (#638).
    assert email.subject == "Fix your card by 08:30 to keep your seat"
    assert "Bonarka Arena" in email.text
    assert "30 zł" in email.text
    assert "another card" in email.text
    assert "held for you until 08:30" in email.text
    for player in ("ola", "kuba", "ewa"):
        assert await mailbox.to(f"{player}@example.com") == []


# --------------------------------------------------------------------------- #
# A bank that wants the player, and the payment confirmed
# --------------------------------------------------------------------------- #


async def a_checked_fourth(client, session_factory, clock, payments, club, four):
    tomek = await a_player(
        client, payments, "tomek2", entered=A_CARD_THE_BANK_ALWAYS_CHECKS
    )
    players = [*four[:3], tomek]
    group = await a_group(client, four[0], club, *players[1:])
    proposal = await a_full_card_but_one(
        client, session_factory, clock, club=club, group=group, four=players
    )
    refused = (await says_yes(client, tomek, proposal)).json()["your_payment"]
    return tomek, players, group, proposal, refused["seat_charge_id"]


async def test_a_bank_that_wants_the_player_asks_them_to_confirm_the_same_payment(
    client, session_factory, clock, payments, mailbox, club, four
):
    tomek, _, _, proposal, charge_id = await a_checked_fourth(
        client, session_factory, clock, payments, club, four
    )

    read = await client.get(seat_charge_path(charge_id), headers=tomek["headers"])

    assert read.status_code == 200, read.text
    body = read.json()
    assert body["status"] == "FAILED"
    assert body["refusal"] == "AUTHENTICATION_REQUIRED"
    assert body["proposal_id"] == str(proposal)
    assert body["amount_grosze"] == 30_00
    assert body["club"]["name"] == "Bonarka Arena"
    assert body["to_confirm"]["connected_account_id"].startswith("acct_")
    assert body["to_confirm"]["publishable_key"] == "pk_fake_raketa"
    [email] = await mailbox.to("tomek2@example.com")
    # Before the cut-off it is a hold, never a payment (#638).
    assert "confirm the 30 zł hold" in email.text


async def test_a_payment_not_yet_confirmed_is_refused_and_moves_nothing(
    client, session_factory, clock, payments, club, four
):
    tomek, _, _, proposal, charge_id = await a_checked_fourth(
        client, session_factory, clock, payments, club, four
    )

    early = await client.post(
        f"{seat_charge_path(charge_id)}/confirmation", headers=tomek["headers"]
    )

    assert early.status_code == 409
    assert early.json()["code"] == "payment_not_confirmed"
    assert early.json()["details"] == {"status": "AUTHENTICATION_REQUIRED"}
    # Still In: his seat is his alone while his time to pay runs.
    assert await live_ids(client, tomek) == [str(proposal)]


async def test_confirming_the_payment_is_the_yes_again_and_books_the_game(
    client, session_factory, clock, payments, mailbox, club, four
):
    tomek, players, _, proposal, charge_id = await a_checked_fourth(
        client, session_factory, clock, payments, club, four
    )
    secret = (
        await client.get(seat_charge_path(charge_id), headers=tomek["headers"])
    ).json()["to_confirm"]["client_secret"]
    payments.phone_confirms_payment(payment_of(secret))
    held_before = len(payments.called("authorise"))

    confirmed = await client.post(
        f"{seat_charge_path(charge_id)}/confirmation", headers=tomek["headers"]
    )

    assert confirmed.status_code == 200, confirmed.text
    answer = confirmed.json()
    assert answer["booked"]["booking_id"] == str(proposal)
    assert answer["open_seats"] == 0
    # Within his time to pay, everybody else's hold was kept: nobody's bank is
    # asked again, and Tomek's confirmed payment is the one taken (#625).
    assert len(payments.called("authorise")) == held_before
    await the_cut_off_comes(session_factory, clock)
    await mailbox.drain()
    taken = {call.arguments["payment_id"] for call in payments.called("capture")}
    assert payment_of(secret) in taken
    assert len(taken) == 4
    for player in players:
        assert len(await receipts(client, player)) == 1


async def test_a_seat_somebody_else_took_lets_the_confirmed_payment_go(
    client, session_factory, clock, payments, mailbox, club, four
):
    tomek, players, group, proposal, charge_id = await a_checked_fourth(
        client, session_factory, clock, payments, club, four
    )
    # His time to pay runs out: his seat is offered to others.
    clock.move(timedelta(minutes=30))
    await runs_out(session_factory, clock)
    eve = await a_player(client, payments, "eve")
    joined = await client.post(
        f"/api/v1/groups/{group}/membership", headers=eve["headers"]
    )
    assert joined.status_code in (200, 201), joined.text
    await deals(session_factory, clock, proposal, eve)
    took = await says_yes(client, eve, proposal)
    assert took.json()["booked"] is not None
    secret = (
        await client.get(seat_charge_path(charge_id), headers=tomek["headers"])
    ).json()["to_confirm"]
    # The game filled without him: his refused payment was let go with it.
    assert secret is None
    await mailbox.drain()

    too_late = await client.post(
        f"{seat_charge_path(charge_id)}/confirmation", headers=tomek["headers"]
    )

    assert too_late.status_code == 409
    assert too_late.json()["code"] == "payment_not_confirmed"
    read = await client.get(seat_charge_path(charge_id), headers=tomek["headers"])
    assert read.json()["status"] == "CANCELLED"
    assert await receipts(client, tomek) == []


async def test_a_payment_confirmed_after_somebody_took_the_seat_is_let_go(
    client, session_factory, clock, payments, mailbox, club, four
):
    """The phone confirmed it while the game was filling without them — the
    hold is let go, and nobody pays it."""

    tomek, players, group, proposal, charge_id = await a_checked_fourth(
        client, session_factory, clock, payments, club, four
    )
    secret = (
        await client.get(seat_charge_path(charge_id), headers=tomek["headers"])
    ).json()["to_confirm"]["client_secret"]
    payments.phone_confirms_payment(payment_of(secret))
    # His time to pay runs out before he says so: his seat is offered.
    clock.move(timedelta(minutes=30))
    await runs_out(session_factory, clock)
    eve = await a_player(client, payments, "eve")
    await client.post(f"/api/v1/groups/{group}/membership", headers=eve["headers"])
    await deals(session_factory, clock, proposal, eve)
    assert (await says_yes(client, eve, proposal)).json()["booked"] is not None

    too_late = await client.post(
        f"{seat_charge_path(charge_id)}/confirmation", headers=tomek["headers"]
    )

    assert too_late.status_code == 409
    await mailbox.drain()
    cancelled = {call.arguments["payment_id"] for call in payments.called("cancel")}
    assert payment_of(secret) in cancelled
    assert await receipts(client, tomek) == []


async def test_nobody_reads_another_player_s_charge(
    client, session_factory, clock, payments, club, four
):
    _, _, _, _, charge_id = await a_checked_fourth(
        client, session_factory, clock, payments, club, four
    )

    for path in (seat_charge_path(charge_id),):
        stranger = await client.get(path, headers=four[0]["headers"])
        assert stranger.status_code == 404
        assert stranger.json()["code"] == "seat_charge_not_found"
    confirm = await client.post(
        f"{seat_charge_path(charge_id)}/confirmation", headers=four[0]["headers"]
    )
    assert confirm.status_code == 404


async def test_a_plain_yes_after_a_refused_payment_points_to_the_payment(
    client, session_factory, clock, payments, club, four
):
    """Asking the bank the same question off-session meets the same answer, so
    the swipe sends the player to the payment instead — *confirming is your yes
    again*."""

    tomek, _, _, proposal, charge_id = await a_checked_fourth(
        client, session_factory, clock, payments, club, four
    )
    held_before = len(payments.called("authorise"))

    again = await says_yes(client, tomek, proposal)

    assert again.status_code == 409
    assert again.json()["code"] == "payment_to_confirm"
    assert again.json()["details"] == {"seat_charge_id": charge_id}
    assert len(payments.called("authorise")) == held_before


async def test_a_refused_player_who_was_not_the_last_yes_finds_the_payment(
    client, session_factory, clock, payments, club, four
):
    tomek = await a_player(
        client, payments, "tomek2", entered=A_CARD_THE_BANK_ALWAYS_CHECKS
    )
    players = [tomek, *four[:3]]
    group = await a_group(client, four[0], club, tomek, *four[1:3])
    proposal = await a_full_card_but_one(
        client, session_factory, clock, club=club, group=group, four=players
    )
    assert (await says_yes(client, players[3], proposal)).json()["your_payment"] is None

    owed = await client.get(
        "/api/v1/players/me/payments-to-confirm", headers=tomek["headers"]
    )

    assert owed.status_code == 200, owed.text
    [payment] = owed.json()["payments"]
    assert payment["refusal"] == "AUTHENTICATION_REQUIRED"
    assert payment["proposal_id"] == str(proposal)
    assert payment["club"]["name"] == "Bonarka Arena"
    assert payment["share_grosze"] == 30_00
    secret = (
        await client.get(
            seat_charge_path(payment["seat_charge_id"]), headers=tomek["headers"]
        )
    ).json()["to_confirm"]["client_secret"]
    payments.phone_confirms_payment(payment_of(secret))
    confirmed = await client.post(
        f"{seat_charge_path(payment['seat_charge_id'])}/confirmation",
        headers=tomek["headers"],
    )
    assert confirmed.json()["booked"] is not None
    after = await client.get(
        "/api/v1/players/me/payments-to-confirm", headers=tomek["headers"]
    )
    assert after.json()["payments"] == []


async def test_a_confirmed_payment_waits_with_the_others_when_another_is_refused(
    client, session_factory, clock, payments, mailbox, club, four
):
    """Out of his time, Tomek takes his seat back by confirming — and this time
    Ewa's card is refused. **Every hold is kept for her time to pay** (#625),
    his confirmed payment among them: nobody's money is let go while one
    payment is awaited."""

    tomek, players, _, proposal, charge_id = await a_checked_fourth(
        client, session_factory, clock, payments, club, four
    )
    clock.move(timedelta(minutes=30))
    await runs_out(session_factory, clock)
    ewa = players[2]
    await saves_a_card(client, payments, ewa["headers"], A_CARD_THAT_DECLINES_LATER)
    secret = (
        await client.get(seat_charge_path(charge_id), headers=tomek["headers"])
    ).json()["to_confirm"]["client_secret"]
    payments.phone_confirms_payment(payment_of(secret))
    await mailbox.drain()
    cancelled_before = len(payments.called("cancel"))

    confirmed = await client.post(
        f"{seat_charge_path(charge_id)}/confirmation", headers=tomek["headers"]
    )

    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["booked"] is None
    assert confirmed.json()["open_seats"] == 0
    assert confirmed.json()["your_payment"] is None
    assert confirmed.json()["payment_awaited_until"] == "2026-10-05T07:00:00Z"
    await mailbox.drain()
    assert len(payments.called("cancel")) == cancelled_before
    assert payments.called("capture") == []
    # Both are In; Ewa's seat is hers alone for her time to pay.
    assert await live_ids(client, tomek) == [str(proposal)]
    assert await live_ids(client, ewa) == [str(proposal)]


async def test_two_cards_that_read_one_court_free_book_two_courts(
    client, session_factory, clock, payments, mailbox, four, monkeypatch
):
    """Two full games at one club and hour, filling at once, both read Court 1
    free: the second's claim meets the court hour's unique index, and its yes is
    tried once more — on Court 3, with the same holds answered again."""

    club, desk = await a_club_and_its_desk(client)
    third = await adds_a_court(client, desk, name="Court 3", sport="PADEL")
    await sets_hours(client, desk, [third["id"]], every_hour_of_the_week())
    group = await a_group(client, four[0], club, *four[1:])
    first = await a_full_card_but_one(
        client, session_factory, clock, club=club, group=group, four=four
    )
    assert (await says_yes(client, four[3], first)).json()["booked"] is not None
    others = [
        await a_player(client, payments, name)
        for name in ("ania", "bart", "cela", "dawid")
    ]
    second_group = await a_group(client, others[0], club, *others[1:])
    second = await a_full_card_but_one(
        client, session_factory, clock, club=club, group=second_group, four=others
    )
    real = SqlAlchemyBookingDirectory.held_at
    blind = {"left": 1}

    async def blind_once(self, club_id, *, start, end):
        held = await real(self, club_id, start=start, end=end)
        if blind["left"] and end is not None and start <= SATURDAY_FIVE < end:
            # The other game's booking, not yet seen by this one's read.
            blind["left"] -= 1
            return []
        return held

    monkeypatch.setattr(SqlAlchemyBookingDirectory, "held_at", blind_once)
    authorised_before = len(payments.called("authorise"))

    last = await says_yes(client, others[3], second)

    assert last.status_code == 200, last.text
    assert last.json()["booked"]["booking_id"] == str(second)
    assert blind["left"] == 0
    # Eight asks, four holds: the second try was answered the first's.
    asked = payments.called("authorise")[authorised_before:]
    assert len(asked) == 8
    [email] = await mailbox.to("ania@example.com")
    assert "Bonarka Arena, Court 3" in email.text


# --------------------------------------------------------------------------- #
# The booking, its game and its chat
# --------------------------------------------------------------------------- #


async def test_the_booking_opens_an_ordinary_game_on_the_first_free_court(
    client, session_factory, clock, mailbox, club, four, group
):
    proposal = await a_full_card_but_one(
        client, session_factory, clock, club=club, group=group, four=four
    )

    booked = (await says_yes(client, four[3], proposal)).json()["booked"]

    games = await client.get(GAMES, headers=four[0]["headers"])
    [game] = games.json()["games"]
    assert game["game_id"] == booked["game_id"]
    assert game["kind"] == "COUNTED"
    assert game["standing"] == "AWAITING_ENTRY"
    sides: dict[str, set[str]] = {}
    for seat in game["seats"]:
        sides.setdefault(seat["side"], set()).add(seat["player_id"])
    assert sorted(len(side) for side in sides.values()) == [2, 2]
    assert set().union(*sides.values()) == {str(player["id"]) for player in four}
    # Its result can be told until a day after its hour — not a week after it
    # was booked.
    assert game["entry_closes_at"] == "2026-10-11T16:00:00Z"
    assert (await events_of(session_factory, proposal))[-1] == (
        "proposals.proposal_filled"
    )


async def test_the_chat_opens_with_the_players_as_members(
    client, session_factory, clock, payments, mailbox, club, four, group
):
    proposal = await a_full_card_but_one(
        client, session_factory, clock, club=club, group=group, four=four
    )
    await says_yes(client, four[3], proposal)
    await mailbox.drain()
    async with session_factory() as session:
        conversation_id = await session.scalar(
            select(ConversationORM.conversation_id).where(
                ConversationORM.booking_id == proposal
            )
        )
    assert conversation_id is not None

    for player in four:
        read = await client.get(
            f"/api/v1/conversations/{conversation_id}", headers=player["headers"]
        )
        assert read.status_code == 200, read.text
        assert {member["player_id"] for member in read.json()["members"]} == {
            str(member["id"]) for member in four
        }
    stranger = await a_player(client, payments, "stranger")
    refused = await client.get(
        f"/api/v1/conversations/{conversation_id}", headers=stranger["headers"]
    )
    assert refused.status_code == 404


async def test_every_version_disappears_and_a_late_yes_is_told_it_just_filled(
    client, session_factory, clock, payments, club, four, group
):
    eve = await a_player(client, payments, "eve")
    await client.post(f"/api/v1/groups/{group}/membership", headers=eve["headers"])
    proposal = await a_full_card_but_one(
        client, session_factory, clock, club=club, group=group, four=four
    )
    await deals(session_factory, clock, proposal, eve)
    await says_yes(client, four[3], proposal)

    late = await says_yes(client, eve, proposal)

    assert late.status_code == 409
    assert late.json()["code"] == "proposal_is_over"
    assert late.json()["details"] == {"standing": "FILLED"}


async def test_the_court_hour_leaves_what_the_club_sells(
    client, session_factory, clock, club, four, group
):
    proposal = await a_full_card_but_one(
        client, session_factory, clock, club=club, group=group, four=four
    )

    await says_yes(client, four[3], proposal)

    async with session_factory() as session:
        offered = await build_court_hours(session).offered(
            UUID(club), sport=Sport.PADEL, start=SATURDAY_FIVE, now=clock.now()
        )
    assert offered is None
    with pytest.raises(CourtHourNotForSale):
        await makes(
            session_factory,
            clock,
            pool_id=group,
            club_id=club,
            versions=(tuple(four),),
        )


async def test_the_last_yes_on_a_card_whose_court_went_books_nothing(
    client, session_factory, clock, payments, club, four, group
):
    """Bonarka sells one padel court: a second full game at the same hour has
    no court left to book, and nobody pays for it."""

    first = await a_full_card_but_one(
        client, session_factory, clock, club=club, group=group, four=four
    )
    others = [
        await a_player(client, payments, name)
        for name in ("ania", "bart", "cela", "dawid")
    ]
    second_group = await a_group(client, others[0], club, *others[1:])
    second = await a_full_card_but_one(
        client, session_factory, clock, club=club, group=second_group, four=others
    )
    await says_yes(client, four[3], first)
    held_before = len(payments.called("authorise"))

    lost = await says_yes(client, others[3], second)

    assert lost.status_code == 409
    assert lost.json()["code"] == "proposal_is_over"
    assert lost.json()["details"] == {"standing": "COURT_HOUR_LOST"}
    assert len(payments.called("authorise")) == held_before


async def test_a_pair_in_that_stopped_fitting_books_nothing_and_the_later_yes_goes(
    client, session_factory, clock, payments, club, four, group
):
    """Ola and Kuba were In, then Ola blocked Kuba: the game fills only with
    people who all fit each other (§7), so the later of their two yeses stops
    counting, his seat is open again, and nobody is asked for money."""

    ola, kuba, ewa, tomek = four
    proposal = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    await says_yes(client, ola, proposal)
    await says_yes(client, kuba, proposal)
    blocked = await players.block_between(client, ola["token"], kuba["id"])
    assert blocked.status_code in (200, 201, 204), blocked.text
    await says_yes(client, ewa, proposal)

    last = await says_yes(client, tomek, proposal)

    assert last.status_code == 200, last.text
    assert last.json()["booked"] is None
    assert last.json()["open_seats"] == 1
    assert payments.called("authorise") == []
    assert await live_ids(client, kuba) == []
    assert await live_ids(client, ola) == [str(proposal)]
    assert "proposals.seat_reopened" in await events_of(session_factory, proposal)


async def test_every_other_yes_of_the_players_at_that_hour_is_withdrawn(
    client, session_factory, clock, club, four, group
):
    ogrody = await a_club_selling(client, name="Ogrody 33", point=(50.07, 19.94))
    elsewhere_group = await a_group(client, four[0], ogrody, *four[1:])
    same_hour = await makes(
        session_factory,
        clock,
        pool_id=elsewhere_group,
        club_id=ogrody,
        versions=(tuple(four),),
    )
    await says_yes(client, four[0], same_hour)
    proposal = await a_full_card_but_one(
        client, session_factory, clock, club=club, group=group, four=four
    )

    await says_yes(client, four[3], proposal)

    assert str(same_hour) not in await live_ids(client, four[0])
    assert "proposals.yes_withdrawn" in await events_of(session_factory, same_hour)


async def test_a_player_whose_games_per_week_are_booked_has_that_week_paused(
    client, session_factory, clock, club, four, group
):
    ola = four[0]
    capped = await client.put(
        "/api/v1/players/me/games-and-money",
        json={"games_per_week": 1, "most_ill_pay_grosze": None},
        headers=ola["headers"],
    )
    assert capped.status_code == 200, capped.text
    sunday = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=warsaw(11, 10),
        versions=(tuple(four),),
    )
    next_week = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=warsaw(13, 18),
        versions=(tuple(four),),
    )
    for other in (sunday, next_week):
        await says_yes(client, ola, other)
    proposal = await a_full_card_but_one(
        client, session_factory, clock, club=club, group=group, four=four
    )

    await says_yes(client, four[3], proposal)

    assert await live_ids(client, ola) == [str(next_week)]
    assert "proposals.yes_paused" in await events_of(session_factory, sunday)
    # Kuba asked for the default two: his Sunday yes stands.
    await says_yes(client, four[1], sunday)
    assert str(sunday) in await live_ids(client, four[1])


async def test_a_method_with_a_booked_game_ahead_cannot_be_removed(
    client, session_factory, clock, club, four, group
):
    proposal = await a_full_card_but_one(
        client, session_factory, clock, club=club, group=group, four=four
    )
    await says_yes(client, four[3], proposal)

    removed = await client.delete(
        "/api/v1/players/me/payment-methods/current", headers=four[3]["headers"]
    )

    assert removed.status_code == 409
    assert removed.json()["details"] == {"live_yeses": 0, "upcoming_games": 1}


# --------------------------------------------------------------------------- #
# The emails
# --------------------------------------------------------------------------- #


async def test_everybody_is_emailed_it_s_a_game_with_their_share_held(
    client, session_factory, clock, mailbox, club, four, group
):
    proposal = await a_full_card_but_one(
        client, session_factory, clock, club=club, group=group, four=four
    )

    await says_yes(client, four[3], proposal)

    for name in ("ola", "kuba", "ewa", "tomek"):
        [email] = await mailbox.to(f"{name}@example.com")
        assert email.subject == "It's a game! · 30 zł held"
        assert "Bonarka Arena, Court 1" in email.text
        assert "Saturday 10 October, 17:00 until 18:00" in email.text
        # Held until the cut-off, and leaving before it takes nothing (#637).
        assert (
            "30 zł is held on your card and taken on Fri 17:00, the club's "
            "cut-off. Leave before then and nothing is taken."
        ) in email.text
        assert "card fee" not in email.text


async def test_a_game_that_fills_after_its_cut_off_says_so(
    client, session_factory, clock, mailbox, club, four, group
):
    """Tuesday 6 October at 07:00 is inside the 24-hour cut-off from Monday
    08:00: the game was never free to leave."""

    proposal = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=warsaw(6, 7),
        versions=(tuple(four),),
    )
    for player in four:
        await says_yes(client, player, proposal)

    [email] = await mailbox.to("ola@example.com")
    assert (
        "This game has no free cancellation: if you leave, you're refunded "
        "only when someone takes your seat."
    ) in email.text
    assert "You can leave until" not in email.text


# --------------------------------------------------------------------------- #
# On request, and singles
# --------------------------------------------------------------------------- #


async def test_a_full_game_at_an_on_request_club_waits_and_nobody_pays(
    client, session_factory, clock, payments, four
):
    club, _ = await a_club_and_its_desk(client, way="ON_REQUEST")
    group = await a_group(client, four[0], club, *four[1:])
    proposal = await a_full_card_but_one(
        client, session_factory, clock, club=club, group=group, four=four
    )

    last = await says_yes(client, four[3], proposal)

    assert last.status_code == 200, last.text
    assert last.json()["open_seats"] == 0
    assert last.json()["booked"] is None
    assert payments.called("authorise") == []


async def test_a_singles_game_books_one_against_one(
    client, session_factory, clock, payments, mailbox, club
):
    ola, kuba = [
        await a_player(client, payments, name, sports=(Sport.TENNIS,))
        for name in ("ola", "kuba")
    ]
    group = await a_group(client, ola, club, kuba)
    proposal = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        sport=Sport.TENNIS,
        versions=((ola, kuba),),
    )
    await says_yes(client, ola, proposal)

    last = await says_yes(client, kuba, proposal)

    assert last.json()["booked"] is not None
    [game] = (await client.get(GAMES, headers=ola["headers"])).json()["games"]
    assert sorted(seat["side"] for seat in game["seats"]) == ["A", "B"]
    await the_cut_off_comes(session_factory, clock)
    await mailbox.drain()
    [receipt] = await receipts(client, kuba)
    # Tennis at 80 zł, between two.
    assert receipt["amount_grosze"] == 40_00


# --------------------------------------------------------------------------- #
# The provider's notices, and the sweep
# --------------------------------------------------------------------------- #


@pytest.fixture
def the_connect_secret(monkeypatch):
    monkeypatch.setenv("STRIPE_CONNECT_WEBHOOK_SECRET", CONNECT_SECRET)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def a_payment_notice(kind: str, payment_id: str, account: str, notice_id: str) -> str:
    body = notice(
        kind, {"id": payment_id, "object": "payment_intent"}, notice_id=notice_id
    )
    # A direct charge's notice names the club's account at its top level.
    return body[:-1] + f', "account": "{account}"}}'


async def sends(client, body: str):
    return await client.post(
        CONNECT_WEBHOOK,
        content=body.encode(),
        headers={
            "Stripe-Signature": stripe.WebhookSignature.generate_signature_header(
                body, CONNECT_SECRET
            ),
            "Content-Type": "application/json",
        },
    )


async def test_a_payment_confirmed_in_the_app_is_heard_from_the_provider_once(
    client, session_factory, clock, payments, club, four, the_connect_secret
):
    tomek, _, _, _, charge_id = await a_checked_fourth(
        client, session_factory, clock, payments, club, four
    )
    read = (
        await client.get(seat_charge_path(charge_id), headers=tomek["headers"])
    ).json()
    secret, account = (
        read["to_confirm"]["client_secret"],
        read["to_confirm"]["connected_account_id"],
    )
    payments.phone_confirms_payment(payment_of(secret))
    body = a_payment_notice(
        "payment_intent.amount_capturable_updated",
        payment_of(secret),
        account,
        notice_id="evt_held",
    )

    first = await sends(client, body)
    again = await sends(client, body)

    assert first.status_code == 204, first.text
    assert again.status_code == 204
    held = await client.get(seat_charge_path(charge_id), headers=tomek["headers"])
    assert held.json()["status"] == "AUTHORISED"
    assert held.json()["to_confirm"] is None
    assert await events_of(session_factory, UUID(charge_id)) == [
        "payments.seat_charge_failed",
        "payments.seat_charge_confirmed",
    ]


async def test_a_capture_heard_after_it_was_recorded_records_nothing(
    client,
    session_factory,
    clock,
    payments,
    mailbox,
    club,
    four,
    group,
    the_connect_secret,
):
    proposal = await a_full_card_but_one(
        client, session_factory, clock, club=club, group=group, four=four
    )
    await says_yes(client, four[3], proposal)
    await the_cut_off_comes(session_factory, clock)
    await mailbox.drain()
    capture = payments.called("capture")[0]
    [receipt] = await receipts(client, four[0])
    charge_id = UUID(receipt["seat_charge_id"])
    before = await events_of(session_factory, charge_id)

    heard = await sends(
        client,
        a_payment_notice(
            "payment_intent.succeeded",
            capture.arguments["payment_id"],
            capture.arguments["account_id"],
            notice_id="evt_taken",
        ),
    )

    assert heard.status_code == 204
    assert await events_of(session_factory, charge_id) == before


async def test_a_confirmed_payment_on_a_game_that_never_filled_is_let_go(
    client, session_factory, clock, payments, mailbox, club, four, the_connect_secret
):
    """The phone confirmed it, the provider said so, and nobody else's yes came
    before the book-by: the sweep lets the hold go with the game."""

    tomek, _, _, _, charge_id = await a_checked_fourth(
        client, session_factory, clock, payments, club, four
    )
    read = (
        await client.get(seat_charge_path(charge_id), headers=tomek["headers"])
    ).json()["to_confirm"]
    payments.phone_confirms_payment(payment_of(read["client_secret"]))
    await sends(
        client,
        a_payment_notice(
            "payment_intent.amount_capturable_updated",
            payment_of(read["client_secret"]),
            read["connected_account_id"],
            notice_id="evt_held",
        ),
    )
    clock.move(timedelta(days=6))
    # His time to pay ran out long before; the job ends it, then the sweep.
    await runs_out(session_factory, clock)

    await sweeps(session_factory, clock)
    await mailbox.drain()

    cancelled = {call.arguments["payment_id"] for call in payments.called("cancel")}
    assert payment_of(read["client_secret"]) in cancelled
    gone = await client.get(seat_charge_path(charge_id), headers=tomek["headers"])
    assert gone.json()["status"] == "CANCELLED"
