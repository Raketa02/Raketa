"""**Sending a friends game books the court at once, and friends answer with
their money** (#751; ``docs/adr/0202`` §5–§6; the friends mechanics §8–§10.3,
§11.2) — over HTTP, with the fake provider.

The friends card's own world (``test_friends_card.py``): **Ogrody 33** sells one
padel court on Saturdays at 10:00 at 100 zł — 25 zł each — its cut-off the
day before at 10:00. **Tomek** is in Ogrody 33 Club with **Ewa** and **Magda**,
and in Kazimierz crew with **Ania**, all three his friends. The clock stands on
**Monday 5 October 2026, 08:00 in Kraków**, and the card proposes **Saturday
10:00 at Ogrody 33** — the one hour all four are free.
"""

from __future__ import annotations

from datetime import timedelta
from uuid import UUID

from app.bootstrap.composition import (
    build_the_holding,
    build_booking_repository,
    build_domain_event_store,
    build_event_publisher,
    build_payment_method_repository,
    build_run_out_the_invitations,
    build_seat_charge_repository,
)
from app.core.config import get_settings
from app.kernel import instant
from app.modules.payments.domain.entered_cards import CardBehaviour
from tests.api.proposals_world import (
    a_member,
    makes,
    says_yes,
    the_cut_off_comes,
    warsaw,
)
from tests.api import test_friends_card as the_friends_card
from tests.api.club_courts_world import confirms_settings
from tests.api.test_friends_card import BOTH, World, card_of, ids, joins
from tests.api.test_friends_on_every_face import befriend

#: The friends card's own world and clock, as its module builds them.
clock = the_friends_card.clock
world = the_friends_card.world

HOME = "/api/v1/home"
NOTICES = "/api/v1/players/me/notices"
SATURDAY_TEN = warsaw(10, 10)
#: Ogrody 33's cut-off for it: the club's default 24 hours.
FRIDAY_TEN = SATURDAY_TEN - timedelta(hours=24)


# --------------------------------------------------------------------------- #
# The acts
# --------------------------------------------------------------------------- #


async def sends(client, world: World, *, pay_mode: str = "SPLIT_THE_COST", **more):
    """Tomek sends the card's court with Ewa, Magda and Ania, as the send
    sheet's button does."""

    card = await card_of(client, world.tomek, world.group, world.friends)
    assert card.status_code == 200, card.text
    court = card.json()["court"]
    return await client.post(
        f"/api/v1/pools/{world.group}/friends-games",
        json={
            "sport": "PADEL",
            "kind": "COMPETITIVE",
            "friend_ids": ids(*world.friends),
            "court_id": court["court_id"],
            "starts_at": court["starts_at"],
            "pay_mode": pay_mode,
            **more,
        },
        headers=world.tomek["headers"],
    )


async def a_friends_game(client, world: World, **more) -> str:
    sent = await sends(client, world, **more)
    assert sent.status_code == 200, sent.text
    assert sent.json()["booked"] is not None, sent.text
    return sent.json()["booking_id"]


async def accepts(client, player: dict, booking: str):
    return await client.post(
        f"/api/v1/bookings/{booking}/invitation/acceptance", headers=player["headers"]
    )


async def declines(client, player: dict, booking: str):
    return await client.post(
        f"/api/v1/bookings/{booking}/invitation/decline", headers=player["headers"]
    )


async def calls_off(client, player: dict, booking: str):
    return await client.post(
        f"/api/v1/bookings/{booking}/call-off", headers=player["headers"]
    )


async def runs_out_the_invitations(session_factory, clock):
    async with session_factory() as session:
        return await build_run_out_the_invitations(session, clock=clock).execute()


# --------------------------------------------------------------------------- #
# The reads
# --------------------------------------------------------------------------- #


async def charges_of(session_factory, booking: str) -> list:
    async with session_factory() as session:
        return list(
            await build_seat_charge_repository(
                session,
                event_store=build_domain_event_store(session),
                events=build_event_publisher(session),
            ).of_game(UUID(booking))
        )


def statuses(charges, *, of: dict, cover: bool | None = None) -> list[str]:
    return sorted(
        charge.status.value
        for charge in charges
        if charge.player_id == of["id"] and (cover is None or charge.cover is cover)
    )


async def the_booking(session_factory, booking: str):
    async with session_factory() as session:
        found = await build_booking_repository(
            session,
            event_store=build_domain_event_store(session),
            events=build_event_publisher(session),
        ).load(UUID(booking))
    assert found is not None
    return found


async def home_of(client, player: dict) -> dict:
    read = await client.get(HOME, headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()


async def details_of(client, player: dict, booking: str) -> dict:
    read = await client.get(f"/api/v1/bookings/{booking}", headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()


async def notices_of(client, mailbox, player: dict) -> list[dict]:
    await mailbox.drain()
    read = await client.get(NOTICES, headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()["notices"]


def kinds(notices: list[dict]) -> list[str]:
    return [notice["kind"] for notice in notices]


def seat_states(friends_game: dict) -> dict[str, str]:
    return {seat["player_id"]: seat["state"] for seat in friends_game["seats"]}


# --------------------------------------------------------------------------- #
# Sending: Split the cost
# --------------------------------------------------------------------------- #


async def test_sending_books_the_court_and_holds_the_whole_court_on_the_senders_card(
    client, world, session_factory, payments
):
    sent = await sends(client, world)

    assert sent.status_code == 200, sent.text
    body = sent.json()
    assert body["booked"]["booking_id"] == body["booking_id"]
    assert body["your_payments"] == []
    charges = await charges_of(session_factory, body["booking_id"])
    # His 25 zł, and a 25 zł cover for each of the three other seats.
    assert statuses(charges, of=world.tomek, cover=False) == ["HELD"]
    assert statuses(charges, of=world.tomek, cover=True) == ["HELD"] * 3
    assert {charge.amount_grosze for charge in charges} == {25_00}
    assert {charge.held_until for charge in charges} == {instant(FRIDAY_TEN)}
    booking = await the_booking(session_factory, body["booking_id"])
    assert booking.players == (world.tomek["id"],)
    assert booking.state.value == "BOOKED"
    assert {str(seat.player_id) for seat in booking.invited} == set(ids(*world.friends))


async def test_the_amount_agreed_is_recorded_with_the_terms(
    client, world, session_factory
):
    booking = await a_friends_game(client, world)

    async with session_factory() as session:
        method = await build_payment_method_repository(
            session,
            event_store=build_domain_event_store(session),
            events=build_event_publisher(session),
        ).load(world.tomek["id"])
    assert method.maximums_agreed == {UUID(booking): 100_00}


async def test_the_chat_opens_at_send_with_the_sender_in_it(client, world, mailbox):
    booking = await a_friends_game(client, world)
    await mailbox.drain()

    rooms = await client.get("/api/v1/conversations", headers=world.tomek["headers"])
    assert rooms.status_code == 200, rooms.text
    [room] = [
        room for room in rooms.json()["conversations"] if room["booking_id"] == booking
    ]
    assert [member["player_id"] for member in room["members"]] == [
        str(world.tomek["id"])
    ]


async def test_each_friend_is_invited_on_home_and_told(client, world, mailbox):
    booking = await a_friends_game(client, world)

    for friend in world.friends:
        home = await home_of(client, friend)
        [card] = home["friends_games"]
        assert card["booking_id"] == booking
        assert card["court_name"] == "Court 1"
        assert card["share_grosze"] == 25_00
        game = card["friends_game"]
        assert game["sender_id"] == str(world.tomek["id"])
        assert game["sender_nickname"] == "tomek"
        assert game["pay_mode"] == "SPLIT_THE_COST"
        assert game["your_invitation_until"] is not None
        assert seat_states(game)[str(world.tomek["id"])] == "IN"
        assert seat_states(game)[str(friend["id"])] == "WAITING"
        # Every seat the card drew, theirs among them.
        faces = [tile["player_id"] for side in card["sides"].values() for tile in side]
        assert sorted(faces) == sorted(ids(world.tomek, *world.friends))
        assert home["games"] == []
        assert "FRIENDS_GAME_INVITATION" in kinds(
            await notices_of(client, mailbox, friend)
        )


async def test_the_senders_game_is_in_your_games_with_each_seat_waiting(client, world):
    booking = await a_friends_game(client, world)

    home = await home_of(client, world.tomek)
    assert home["friends_games"] == []
    [card] = home["games"]
    assert card["booking_id"] == booking
    assert card["status"] == "BOOKED"
    game = card["friends_game"]
    assert game["you_are_the_sender"] is True
    assert game["can_call_off"] is True
    # *Leave · the others play on* beside *Call it off* (#752): free.
    assert (await details_of(client, world.tomek, booking))["leaving"] == {
        "kind": "BEFORE_THE_CUT_OFF",
        "refund_grosze": None,
        "card_fee_grosze": None,
    }
    assert (game["friends_in"], game["friends_seated"]) == (0, 3)
    assert set(seat_states(game).values()) == {"IN", "WAITING"}


async def test_sending_withdraws_the_senders_other_yeses_at_that_hour(
    client, world, session_factory, clock
):
    proposal = await makes(
        session_factory,
        clock,
        pool_id=world.group,
        club_id=world.wisla_park,
        start=SATURDAY_TEN,
        versions=((world.tomek, world.kuba),),
    )
    assert (await says_yes(client, world.tomek, proposal)).status_code == 200

    await a_friends_game(client, world)

    yeses = await client.get(
        "/api/v1/players/me/live-yeses", headers=world.tomek["headers"]
    )
    assert yeses.json()["yeses"] == []


# --------------------------------------------------------------------------- #
# Answering
# --------------------------------------------------------------------------- #


async def test_an_accept_with_split_holds_the_friends_own_share(
    client, world, session_factory, clock
):
    booking = await a_friends_game(client, world)
    clock.move(timedelta(hours=4))

    accepted = await accepts(client, world.ewa, booking)

    assert accepted.status_code == 200, accepted.text
    assert accepted.json() == {
        "booking_id": booking,
        "accepted": True,
        "whole": False,
        "your_payment": None,
    }
    charges = await charges_of(session_factory, booking)
    assert statuses(charges, of=world.ewa) == ["HELD"]
    home = await home_of(client, world.ewa)
    assert home["friends_games"] == []
    [card] = home["games"]
    assert seat_states(card["friends_game"])[str(world.ewa["id"])] == "IN"
    assert (await home_of(client, world.tomek))["games"][0]["friends_game"][
        "friends_in"
    ] == 1


async def test_a_second_accept_answers_the_same(client, world, session_factory):
    booking = await a_friends_game(client, world)
    assert (await accepts(client, world.ewa, booking)).status_code == 200

    again = await accepts(client, world.ewa, booking)

    assert again.status_code == 200, again.text
    assert again.json()["accepted"] is True
    assert statuses(await charges_of(session_factory, booking), of=world.ewa) == [
        "HELD"
    ]


async def test_the_last_seat_taken_is_its_a_game_to_all_four(client, world, mailbox):
    booking = await a_friends_game(client, world)
    for friend in (world.ewa, world.magda):
        assert (await accepts(client, friend, booking)).status_code == 200

    last = await accepts(client, world.ania, booking)

    assert last.json()["whole"] is True
    for player in (world.tomek, world.ewa, world.magda, world.ania):
        booked = [
            notice
            for notice in await notices_of(client, mailbox, player)
            if notice["kind"] == "GAME_BOOKED"
        ]
        assert [notice["title"] for notice in booked] == ["It's a game!"], player[
            "name"
        ]
        assert booked[0]["your_own"] is (player is world.ania)


async def test_a_friends_money_tells_no_its_a_game_on_its_own(client, world, mailbox):
    booking = await a_friends_game(client, world)
    assert (await accepts(client, world.ewa, booking)).status_code == 200

    for player in (world.tomek, world.ewa):
        assert "GAME_BOOKED" not in kinds(await notices_of(client, mailbox, player))


async def test_a_decline_empties_the_seat_and_tells_the_sender(client, world, mailbox):
    booking = await a_friends_game(client, world)

    declined = await declines(client, world.ania, booking)

    assert declined.status_code == 204, declined.text
    assert (await home_of(client, world.ania))["friends_games"] == []
    game = (await home_of(client, world.tomek))["games"][0]["friends_game"]
    assert seat_states(game)[str(world.ania["id"])] == "CANT_MAKE_IT"
    [told] = [
        notice
        for notice in await notices_of(client, mailbox, world.tomek)
        if notice["kind"] == "CANT_MAKE_IT"
    ]
    assert told["title"] == "ania can't make it"
    assert told["body"] == (
        "Saturday 10:00 · Invite a friend, or open the seat to "
        f"{told['body'].split('open the seat to ')[1]}"
    )
    # Declined is final: accepting after is refused, a second decline is quiet.
    assert (await accepts(client, world.ania, booking)).json()["code"] == (
        "invitation_not_waiting"
    )
    assert (await declines(client, world.ania, booking)).status_code == 204


async def test_silence_runs_out_by_the_job_and_tells_the_sender(
    client, world, session_factory, clock, mailbox
):
    booking = await a_friends_game(client, world)
    assert (await accepts(client, world.ewa, booking)).status_code == 200
    clock.move(timedelta(hours=23))
    assert (await accepts(client, world.magda, booking)).status_code == 200
    clock.move(timedelta(hours=1))

    # Read off the clock before the job records it.
    game = (await home_of(client, world.tomek))["games"][0]["friends_game"]
    assert seat_states(game)[str(world.ania["id"])] == "DIDNT_ANSWER"
    assert (await home_of(client, world.ania))["friends_games"] == []
    late = await accepts(client, world.ania, booking)
    assert late.json()["code"] == "invitation_not_waiting"

    ran = await runs_out_the_invitations(session_factory, clock)

    assert ran.ran_out == 1
    assert "DIDNT_ANSWER" in kinds(await notices_of(client, mailbox, world.tomek))
    assert (await runs_out_the_invitations(session_factory, clock)).ran_out == 0


async def test_a_stranger_reads_nothing_of_a_friends_game(client, world):
    booking = await a_friends_game(client, world)

    assert (await accepts(client, world.kuba, booking)).json()["code"] == (
        "booking_not_found"
    )
    read = await client.get(
        f"/api/v1/bookings/{booking}", headers=world.kuba["headers"]
    )
    assert read.status_code == 404


async def test_an_invitee_reads_the_details_from_outside(client, world):
    booking = await a_friends_game(client, world)

    details = await details_of(client, world.ania, booking)

    assert details["friends_game"]["your_invitation_until"] is not None
    assert details["friends_game"]["you_are_the_sender"] is False
    assert details["friends_game"]["pay_mode"] == "SPLIT_THE_COST"
    assert details["leaving"] is None
    faces = [tile["player_id"] for side in details["sides"].values() for tile in side]
    assert str(world.ania["id"]) in faces


# --------------------------------------------------------------------------- #
# The cut-off: covers taken or let go
# --------------------------------------------------------------------------- #


async def test_at_the_cut_off_a_cover_is_taken_only_for_the_unpaid_seat(
    client, world, session_factory, clock, mailbox
):
    booking = await a_friends_game(client, world)
    for friend in (world.ewa, world.magda):
        assert (await accepts(client, friend, booking)).status_code == 200

    ran = await the_cut_off_comes(session_factory, clock, at=FRIDAY_TEN)
    await mailbox.drain()

    assert ran.games == 0
    charges = await charges_of(session_factory, booking)
    assert statuses(charges, of=world.tomek, cover=False) == ["CAPTURED"]
    # Ania's empty seat's cover is taken; Ewa's and Magda's are let go.
    assert statuses(charges, of=world.tomek, cover=True) == [
        "CANCELLED",
        "CANCELLED",
        "CAPTURED",
    ]
    assert statuses(charges, of=world.ewa) == ["CAPTURED"]
    assert statuses(charges, of=world.magda) == ["CAPTURED"]
    booking_now = await the_booking(session_factory, booking)
    assert booking_now.is_booked


async def test_whole_court_keeps_every_hold_and_friends_accept_free(
    client, world, session_factory, clock, mailbox
):
    booking = await a_friends_game(client, world, pay_mode="WHOLE_COURT")
    for friend in world.friends:
        accepted = await accepts(client, friend, booking)
        assert accepted.status_code == 200, accepted.text
    card = (await home_of(client, world.ewa))["games"][0]
    assert card["friends_game"]["pay_mode"] == "WHOLE_COURT"
    charges = await charges_of(session_factory, booking)
    assert all(charge.player_id == world.tomek["id"] for charge in charges)

    await the_cut_off_comes(session_factory, clock, at=FRIDAY_TEN)
    await mailbox.drain()

    charges = await charges_of(session_factory, booking)
    assert statuses(charges, of=world.tomek) == ["CAPTURED"] * 4


async def test_the_cut_off_decides_no_cover_before_it_comes(
    client, world, session_factory, clock
):
    booking = await a_friends_game(client, world)
    assert (await accepts(client, world.ewa, booking)).status_code == 200

    await the_cut_off_comes(session_factory, clock, at=FRIDAY_TEN - timedelta(hours=1))

    charges = await charges_of(session_factory, booking)
    assert statuses(charges, of=world.tomek) == ["HELD"] * 4


# --------------------------------------------------------------------------- #
# Calling it off
# --------------------------------------------------------------------------- #


async def test_the_sender_calls_it_off_every_hold_let_go_and_everybody_told(
    client, world, session_factory, clock, mailbox
):
    booking = await a_friends_game(client, world)
    assert (await accepts(client, world.ewa, booking)).status_code == 200
    # Wednesday.
    clock.move(timedelta(days=2))

    called = await calls_off(client, world.tomek, booking)
    await mailbox.drain()

    assert called.status_code == 204, called.text
    charges = await charges_of(session_factory, booking)
    assert statuses(charges, of=world.tomek) == ["CANCELLED"] * 4
    assert statuses(charges, of=world.ewa) == ["CANCELLED"]
    booking_now = await the_booking(session_factory, booking)
    assert booking_now.called_off.value == "BY_THE_SENDER"
    # Magda's and Ania's 24 hours ran out on Tuesday: only those In are told.
    for player in (world.ewa, world.tomek):
        [told] = [
            notice
            for notice in await notices_of(client, mailbox, player)
            if notice["kind"] == "GAME_CALLED_OFF"
        ]
        assert told["title"].startswith("tomek called off ")
        assert told["body"] == "Nobody paid."
        # His own act: born seen.
        assert told["your_own"] is (player is world.tomek)
    card = (await home_of(client, world.tomek))["games"][0]
    assert (card["status"], card["called_off_reason"]) == (
        "CALLED_OFF",
        "BY_THE_SENDER",
    )
    # The court is the club's again: another game may book it.
    assert (await a_friends_game(client, world)) != booking


async def test_the_club_reads_a_game_its_sender_called_off_as_called_off(client, world):
    booking = await a_friends_game(client, world)
    # An ordinary booking to the club while it waits on its friends.
    assert (await _the_club_row(client, world, booking))["status"] == "BOOKED"
    assert (await calls_off(client, world.tomek, booking)).status_code == 204

    row = await _the_club_row(client, world, booking)

    assert (row["status"], row["called_off_reason"]) == ("CALLED_OFF", "BY_THE_SENDER")


async def _the_club_row(client, world: World, booking: str) -> dict:
    day = await client.get(
        "/api/v1/club/bookings", params={"date": "2026-10-10"}, headers=world.desk
    )
    assert day.status_code == 200, day.text
    [row] = [row for row in day.json()["bookings"] if row["booking_id"] == booking]
    return row


async def test_a_clubs_cancel_calls_a_friends_game_off_and_lets_every_hold_go(
    client, world, session_factory, mailbox
):
    """The club sees an ordinary booking, and its cancel — no court absorbs
    it, Ogrody 33 has one — calls it off as any booked game's: every hold and
    cover let go before the cut-off."""

    booking = await a_friends_game(client, world)
    assert (await accepts(client, world.ewa, booking)).status_code == 200

    cancelled = await client.post(
        f"/api/v1/club/bookings/{booking}/cancellation",
        json={"reason": "REPAIR", "anyway": False},
        headers=world.desk,
    )
    await mailbox.drain()

    assert cancelled.status_code == 200, cancelled.text
    charges = await charges_of(session_factory, booking)
    assert statuses(charges, of=world.tomek) == ["CANCELLED"] * 4
    assert statuses(charges, of=world.ewa) == ["CANCELLED"]
    assert (await _the_club_row(client, world, booking))["called_off_reason"] == (
        "CANCELLED_BY_THE_CLUB"
    )


async def test_only_the_sender_calls_it_off_and_only_before_the_cut_off(
    client, world, clock
):
    booking = await a_friends_game(client, world)

    assert (await calls_off(client, world.ewa, booking)).json()["code"] == (
        "booking_not_found"
    )
    clock.move(instant(FRIDAY_TEN) - clock.now())
    late = await calls_off(client, world.tomek, booking)
    assert late.json()["code"] == "cut_off_has_passed"


# --------------------------------------------------------------------------- #
# Refusals
# --------------------------------------------------------------------------- #


async def test_a_third_waiting_friends_game_is_refused(client, world):
    await a_friends_game(client, world)
    # The card's next court for the four: another hour, another club.
    second = await client.post(
        f"/api/v1/pools/{world.group}/friends-games",
        json=await _another_court(client, world),
        headers=world.tomek["headers"],
    )
    assert second.status_code == 200, second.text
    assert second.json()["booked"] is not None

    third = await sends(client, world)

    assert third.status_code == 409
    assert third.json()["code"] == "friends_games_waiting"
    assert third.json()["details"] == {"cap": 2}


async def _another_court(client, world: World) -> dict:
    """The next row of *Find a court* for the four after the first one sent."""

    found = await client.get(
        f"/api/v1/pools/{world.group}/friends-card/courts",
        params={"sport": "PADEL", "friend_ids": ids(*world.friends)},
        headers=world.tomek["headers"],
    )
    assert found.status_code == 200, found.text
    row = found.json()["courts"][0]
    return {
        "sport": "PADEL",
        "kind": "FOR_FUN",
        "friend_ids": ids(*world.friends),
        "court_id": row["court_id"],
        "starts_at": row["starts_at"],
        "pay_mode": "SPLIT_THE_COST",
    }


async def test_a_court_somebody_took_a_second_earlier_is_court_just_taken(
    client, world, session_factory, payments
):
    card = await card_of(client, world.tomek, world.group, world.friends)
    court = card.json()["court"]
    # Magda sends the same court first, with three friends of her own.
    for friend in (world.ewa, world.kuba):
        await befriend(client, world.group, world.magda, friend)
    first = await client.post(
        f"/api/v1/pools/{world.group}/friends-games",
        json=_the_send(court, ids(world.tomek, world.ewa, world.kuba)),
        headers=world.magda["headers"],
    )
    assert first.status_code == 200, first.text
    asked = len(payments.called("authorise"))

    taken = await client.post(
        f"/api/v1/pools/{world.group}/friends-games",
        json=_the_send(court, ids(*world.friends)),
        headers=world.tomek["headers"],
    )

    assert taken.status_code == 409
    assert taken.json()["code"] == "court_just_taken"
    # Nothing was asked of his bank, and nothing is held.
    assert len(payments.called("authorise")) == asked
    assert (await home_of(client, world.tomek))["games"] == []


async def test_a_send_books_where_the_store_enforces_its_foreign_keys(
    client, world, db_engine
):
    """Postgres enforces ``booking_invitations.booking_id → bookings.id`` at
    every statement; this suite's SQLite does not unless asked. The flush
    orders mappers that share no ``relationship()`` by class name, which put
    the invitations before their booking, and the repository read the
    violation as a court taken — every send answered ``court_just_taken``.
    ``db_engine`` turns the check on; this fails if it ever stops."""

    async with db_engine.connect() as conn:
        assert (await conn.exec_driver_sql("PRAGMA foreign_keys")).scalar() == 1

    sent = await sends(client, world)

    assert sent.status_code == 200, sent.text
    assert sent.json()["booked"] is not None, sent.text


def _the_send(court: dict, friend_ids: list[str], **more) -> dict:
    return {
        "sport": "PADEL",
        "kind": "COMPETITIVE",
        "friend_ids": friend_ids,
        "court_id": court["court_id"],
        "starts_at": court["starts_at"],
        "pay_mode": "SPLIT_THE_COST",
        **more,
    }


async def saved_method_of(session_factory, player: dict) -> str:
    async with session_factory() as session:
        method = await build_payment_method_repository(
            session,
            event_store=build_domain_event_store(session),
            events=build_event_publisher(session),
        ).load(player["id"])
    assert method.method is not None
    return method.method.method_id


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


async def test_a_card_whose_bank_wants_him_present_books_nothing_until_confirmed(
    client, world, session_factory, payments
):
    payments.card_behaves(
        await saved_method_of(session_factory, world.tomek),
        CardBehaviour.CHECKED_EVERY_TIME,
    )

    sent = await sends(client, world)

    assert sent.status_code == 200, sent.text
    body = sent.json()
    assert body["booked"] is None
    assert [payment["refusal"] for payment in body["your_payments"]] == [
        "AUTHENTICATION_REQUIRED"
    ] * 4
    async with session_factory() as session:
        assert (
            await build_booking_repository(
                session,
                event_store=build_domain_event_store(session),
                events=build_event_publisher(session),
            ).load(UUID(body["booking_id"]))
        ) is None

    # Nobody else sends under his id.
    for friend in (world.ewa, world.kuba):
        await befriend(client, world.group, world.magda, friend)
    card = await card_of(client, world.tomek, world.group, world.friends)
    theirs = await client.post(
        f"/api/v1/pools/{world.group}/friends-games",
        json=_the_send(
            card.json()["court"],
            ids(world.tomek, world.ewa, world.kuba),
            booking_id=body["booking_id"],
        ),
        headers=world.magda["headers"],
    )
    assert theirs.status_code == 404, theirs.text
    assert theirs.json()["code"] == "booking_not_found"

    # He confirms each in the app, and sends again under the same id.
    for payment in body["your_payments"]:
        confirmed = await confirms(
            client, payments, world.tomek, payment["seat_charge_id"]
        )
        assert confirmed.status_code == 200, confirmed.text
    asked = len(payments.called("authorise"))
    again = await sends(client, world, booking_id=body["booking_id"])

    assert again.status_code == 200, again.text
    assert again.json()["booked"]["booking_id"] == body["booking_id"]
    # Nothing asked of his bank again: the holds he confirmed are taken.
    assert len(payments.called("authorise")) == asked
    charges = await charges_of(session_factory, body["booking_id"])
    assert statuses(charges, of=world.tomek, cover=False) == ["HELD"]
    assert statuses(charges, of=world.tomek, cover=True) == ["HELD"] * 3


async def test_a_retried_send_answers_what_it_booked(client, world):
    booking = await a_friends_game(client, world)

    again = await sends(client, world, booking_id=booking)

    assert again.status_code == 200, again.text
    assert again.json()["booked"]["booking_id"] == booking


async def test_a_refused_share_on_accept_keeps_the_seat_theirs_to_confirm(
    client, world, session_factory, payments
):
    booking = await a_friends_game(client, world)
    payments.card_behaves(
        await saved_method_of(session_factory, world.ewa),
        CardBehaviour.CHECKED_EVERY_TIME,
    )

    refused = await accepts(client, world.ewa, booking)

    assert refused.status_code == 200, refused.text
    body = refused.json()
    assert body["accepted"] is False
    assert body["your_payment"]["refusal"] == "AUTHENTICATION_REQUIRED"
    assert body["your_payment"]["confirm_by"] is not None
    # Still hers to answer.
    assert [
        card["booking_id"]
        for card in (await home_of(client, world.ewa))["friends_games"]
    ] == [booking]

    confirmed = await confirms(
        client, payments, world.ewa, body["your_payment"]["seat_charge_id"]
    )

    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["booked"]["booking_id"] == booking
    charges = await charges_of(session_factory, booking)
    assert statuses(charges, of=world.ewa) == ["HELD"]
    assert (
        seat_states((await home_of(client, world.ewa))["games"][0]["friends_game"])[
            str(world.ewa["id"])
        ]
        == "IN"
    )


async def test_accepting_is_refused_for_a_game_at_that_hour(
    client, world, session_factory, clock
):
    booking = await a_friends_game(client, world)
    others = [world.kuba, world.first[0], world.first[1]]
    await joins(client, world.group, *others[1:])
    proposal = await makes(
        session_factory,
        clock,
        pool_id=world.group,
        club_id=world.wisla_park,
        start=SATURDAY_TEN,
        versions=((world.ewa, *others),),
    )
    for player in (world.ewa, *others):
        assert (await says_yes(client, player, proposal)).status_code == 200

    refused = await accepts(client, world.ewa, booking)

    assert refused.status_code == 409
    assert refused.json()["code"] == "you_play_then"


async def test_a_full_week_refuses_the_accept(client, world):
    week = await client.put(
        "/api/v1/players/me/games-and-money",
        json={"games_per_week": 1, "most_ill_pay_grosze": None},
        headers=world.ewa["headers"],
    )
    assert week.status_code == 200, week.text
    booking = await a_friends_game(client, world)
    second = await client.post(
        f"/api/v1/pools/{world.group}/friends-games",
        json=await _another_court(client, world),
        headers=world.tomek["headers"],
    )
    assert second.status_code == 200, second.text
    assert (await accepts(client, world.ewa, booking)).status_code == 200

    refused = await accepts(client, world.ewa, second.json()["booking_id"])

    assert refused.status_code == 409
    assert refused.json()["code"] == "games_per_week_booked"


async def test_a_sender_with_no_payment_method_is_refused(
    client, world, session_factory, payments
):
    lena = await a_member(
        client, session_factory, payments, "lena", mu=2.5, week=BOTH, card=False
    )
    await joins(client, world.group, lena)
    for friend in (world.ewa, world.magda, world.kuba):
        await befriend(client, world.group, lena, friend)
    card = await card_of(
        client, lena, world.group, [world.ewa, world.magda, world.kuba]
    )
    assert card.status_code == 200, card.text

    refused = await client.post(
        f"/api/v1/pools/{world.group}/friends-games",
        json=_the_send(card.json()["court"], ids(world.ewa, world.magda, world.kuba)),
        headers=lena["headers"],
    )

    assert refused.status_code == 409
    assert refused.json()["code"] == "payment_method_required"


# --------------------------------------------------------------------------- #
# Far ahead, and after the cut-off
# --------------------------------------------------------------------------- #

NEXT_SATURDAY_TEN = warsaw(17, 10)
#: Its cut-off, and four days before it, the Holding time.
NEXT_FRIDAY_TEN = NEXT_SATURDAY_TEN - timedelta(hours=24)
THE_HOLDING = NEXT_FRIDAY_TEN - timedelta(days=4)


async def holds(session_factory, clock, payments):
    """The clock moved to the Holding time and the holding job run then."""

    clock.move(instant(THE_HOLDING) - clock.now())
    async with session_factory() as session:
        return await build_the_holding(
            session, clock=clock, provider=payments, settings=get_settings()
        ).execute()


async def test_a_game_sent_far_ahead_checks_the_court_and_holds_it_at_the_holding(
    client, world, session_factory, clock, payments, mailbox
):
    """A Visa held without its player lasts 4 days 18 hours: eleven days before
    the cut-off, every hold is only checked, and held again four days before
    it — then settled at the cut-off like any covered game."""

    payments.clock = clock
    card = await card_of(client, world.tomek, world.group, world.friends)
    court = {
        **card.json()["court"],
        "starts_at": instant(NEXT_SATURDAY_TEN).isoformat(),
    }
    sent = await client.post(
        f"/api/v1/pools/{world.group}/friends-games",
        json=_the_send(court, ids(*world.friends)),
        headers=world.tomek["headers"],
    )
    assert sent.status_code == 200, sent.text
    booking = sent.json()["booking_id"]
    await mailbox.drain()
    assert (
        statuses(await charges_of(session_factory, booking), of=world.tomek)
        == ["CHECKED"] * 4
    )
    assert (await accepts(client, world.ewa, booking)).status_code == 200

    held = await holds(session_factory, clock, payments)

    # Tomek's and Ewa's.
    assert held.held == 2
    charges = await charges_of(session_factory, booking)
    assert statuses(charges, of=world.tomek) == ["HELD"] * 4
    await the_cut_off_comes(session_factory, clock, at=NEXT_FRIDAY_TEN)
    await mailbox.drain()
    charges = await charges_of(session_factory, booking)
    assert statuses(charges, of=world.tomek, cover=True) == [
        "CANCELLED",
        "CAPTURED",
        "CAPTURED",
    ]
    assert statuses(charges, of=world.ewa) == ["CAPTURED"]


async def test_a_game_sent_after_its_cut_off_takes_the_share_and_decides_covers_later(
    client, world, session_factory, clock, mailbox
):
    """A call: sent after the cut-off, the sender's own share is taken at once,
    each invitation runs its 24 hours — never past the start — and the covers
    are held until they end, then decided as at a cut-off."""

    await confirms_settings(client, world.desk, release_lead_days=1, cut_off_hours=48)
    # Thursday 12:00: Saturday 10:00's cut-off, Thursday 10:00, has passed.
    clock.move(instant(warsaw(8, 12)) - clock.now())
    booking = await a_friends_game(client, world)
    charges = await charges_of(session_factory, booking)
    assert statuses(charges, of=world.tomek, cover=False) == ["TAKING"]
    assert statuses(charges, of=world.tomek, cover=True) == ["HELD"] * 3
    # Thursday 12:00 and a day: Friday 12:00.
    invitations_end = instant(warsaw(9, 12))
    assert {charge.held_until for charge in charges if charge.cover} == {
        invitations_end
    }
    assert (await accepts(client, world.ewa, booking)).status_code == 200
    assert statuses(await charges_of(session_factory, booking), of=world.ewa) == [
        "TAKING"
    ]

    await the_cut_off_comes(session_factory, clock, at=invitations_end)
    await mailbox.drain()

    charges = await charges_of(session_factory, booking)
    assert statuses(charges, of=world.tomek, cover=True) == [
        "CANCELLED",
        "CAPTURED",
        "CAPTURED",
    ]
