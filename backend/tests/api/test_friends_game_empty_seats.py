"""**A friends game's empty seats get filled, its sender is warned before he
pays for them, and anyone can leave** (#752; the friends mechanics §10–§11) —
over HTTP, with the fake provider.

The friends card's own world (``test_friends_card.py``): **Ogrody 33** sells
one padel court on Saturdays at 10:00 at 100 zł — 25 zł each — its cut-off the
day before at 10:00. **Tomek** sends Ewa, Magda and Ania a *Split* game for
Saturday 10:00 on Monday morning. **Piotr** is Tomek's friend and **Kasia**
Ewa's, both in Ogrody 33 Club; **Kuba**, a member nobody is friends with, takes
a seat open to the group.
"""

from __future__ import annotations

from datetime import timedelta
from uuid import UUID

import pytest

from app.bootstrap.composition import build_warn_the_covers
from app.kernel import instant
from tests.api import test_friends_card as the_friends_card
from tests.api.club_courts_world import adds_a_court, sets_hours
from tests.api.test_friends import blocks
from tests.api.test_friends_card import THE_HOURS, World, joins
from tests.api.test_friends_games import (
    FRIDAY_TEN,
    a_friends_game,
    accepts,
    charges_of,
    declines,
    details_of,
    home_of,
    kinds,
    notices_of,
    runs_out_the_invitations,
    seat_states,
    statuses,
    the_booking,
)
from tests.api.test_friends_on_every_face import befriend
from tests.api.test_notifications import chooses
from tests.api.proposals_world import makes, says_yes, the_cut_off_comes
from tests.api.test_friends_card import SATURDAY_TEN

#: The friends card's own world and clock, as its module builds them.
clock = the_friends_card.clock
world = the_friends_card.world

#: Thursday 10:00 — a day before the cut-off: the cover warning.
THURSDAY_TEN = FRIDAY_TEN - timedelta(hours=24)
#: Wednesday morning, well before the cut-off.
WEDNESDAY = FRIDAY_TEN - timedelta(days=2)


@pytest.fixture
async def piotr_and_kasia(client, world: World) -> tuple[dict, dict]:
    """Piotr, Tomek's friend, and Kasia, Ewa's — both in Ogrody 33 Club."""

    kasia, piotr = world.first[0], world.first[1]
    await joins(client, world.group, kasia, piotr)
    await befriend(client, world.group, world.tomek, piotr)
    await befriend(client, world.group, world.ewa, kasia)
    return piotr, kasia


# --------------------------------------------------------------------------- #
# The acts
# --------------------------------------------------------------------------- #


async def invites(client, player: dict, booking: str, *, seat_of: dict, friend: dict):
    return await client.post(
        f"/api/v1/bookings/{booking}/seats/{seat_of['id']}/invitations",
        json={"friend_id": str(friend["id"])},
        headers=player["headers"],
    )


async def opens(client, player: dict, booking: str, *, seat_of: dict):
    return await client.post(
        f"/api/v1/bookings/{booking}/seats/{seat_of['id']}/opening",
        headers=player["headers"],
    )


async def leaves(client, player: dict, booking: str):
    return await client.post(
        f"/api/v1/bookings/{booking}/departure", headers=player["headers"]
    )


async def rescues(client, player: dict, booking: str):
    return await client.post(
        f"/api/v1/bookings/{booking}/seats", headers=player["headers"]
    )


async def fill_in_of(client, world: World, player: dict) -> list[str]:
    read = await client.get(
        f"/api/v1/pools/{world.group}/fill-in",
        params={"sport": "PADEL"},
        headers=player["headers"],
    )
    assert read.status_code == 200, read.text
    return [row["booking_id"] for row in read.json()["seats_to_fill"]]


async def warns(session_factory, clock):
    async with session_factory() as session:
        return await build_warn_the_covers(session, clock=clock).execute()


def moves_to(clock, moment) -> None:
    if clock.now() < moment:
        clock.move(instant(moment) - clock.now())


async def ania_says_no(client, world: World, **more) -> str:
    """Ewa and Magda In, Ania's seat empty — *can't make it*."""

    booking = await a_friends_game(client, world, **more)
    for friend in (world.ewa, world.magda):
        assert (await accepts(client, friend, booking)).status_code == 200
    assert (await declines(client, world.ania, booking)).status_code == 204
    return booking


def the_seat_of(friends_game: dict, player: dict) -> dict:
    [seat] = [
        seat for seat in friends_game["seats"] if seat["seat_of"] == str(player["id"])
    ]
    return seat


def refund_withheld(charges, *, of: dict, cover: bool | None = None) -> list:
    return sorted(
        str(charge.refund_withholds_fee)
        for charge in charges
        if charge.player_id == of["id"]
        and (cover is None or charge.cover is cover)
        and charge.refund_withholds_fee is not None
    )


# --------------------------------------------------------------------------- #
# Invite a friend
# --------------------------------------------------------------------------- #


async def test_anybody_in_invites_a_friend_and_the_first_accept_takes_the_seat(
    client, world, piotr_and_kasia, session_factory, mailbox
):
    piotr, kasia = piotr_and_kasia
    booking = await ania_says_no(client, world)
    seat = the_seat_of(
        (await details_of(client, world.tomek, booking))["friends_game"], world.ania
    )
    assert (seat["state"], seat["can_invite"], seat["can_open"]) == (
        "CANT_MAKE_IT",
        True,
        True,
    )

    tomeks = await invites(
        client, world.tomek, booking, seat_of=world.ania, friend=piotr
    )
    ewas = await invites(client, world.ewa, booking, seat_of=world.ania, friend=kasia)

    assert (tomeks.status_code, ewas.status_code) == (204, 204), ewas.text
    seat = the_seat_of(
        (await details_of(client, world.tomek, booking))["friends_game"], world.ania
    )
    assert sorted(one["nickname"] for one in seat["invitations"]) == ["kasia", "piotr"]
    # Each reads it on Home as the card's own invitation, in the seat.
    [card] = (await home_of(client, kasia))["friends_games"]
    assert card["booking_id"] == booking
    assert card["friends_game"]["your_invitation_until"] is not None
    faces = [t["player_id"] for side in card["sides"].values() for t in side]
    assert str(kasia["id"]) in faces and str(world.ania["id"]) not in faces
    [told] = [
        notice
        for notice in await notices_of(client, mailbox, kasia)
        if notice["kind"] == "FRIENDS_GAME_INVITATION"
    ]
    assert told["title"] == "ewa invited you to a game"

    # Kasia accepts and pays first: the seat is hers.
    accepted = await accepts(client, kasia, booking)

    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["whole"] is True
    assert statuses(await charges_of(session_factory, booking), of=kasia) == ["HELD"]
    late = await accepts(client, piotr, booking)
    assert late.json()["code"] == "invitation_not_waiting"
    assert "INVITED_SEAT_TAKEN" in kinds(await notices_of(client, mailbox, piotr))
    assert (await home_of(client, piotr))["friends_games"] == []
    game = (await details_of(client, world.tomek, booking))["friends_game"]
    assert game["friends_in"] == 3
    assert set(seat_states(game).values()) == {"IN"}


async def test_an_invitation_is_refused_naming_nobody(
    client, world, piotr_and_kasia, session_factory
):
    piotr, kasia = piotr_and_kasia
    booking = await ania_says_no(client, world)

    async def refused(player, friend, seat_of=world.ania) -> str:
        answer = await invites(client, player, booking, seat_of=seat_of, friend=friend)
        assert answer.status_code in (404, 409), answer.text
        return answer.json()["code"]

    # Not Tomek's friend; on the game already; an empty seat that isn't one.
    assert await refused(world.tomek, kasia) == "not_a_friend"
    assert await refused(world.tomek, world.magda) == "already_on_the_game"
    assert await refused(world.tomek, piotr, seat_of=world.ewa) == "seat_just_taken"
    # Only somebody In invites.
    assert await refused(world.ania, piotr) == "booking_not_found"
    # A block between the friend and somebody on the game.
    await blocks(client, session_factory, piotr, world.magda)
    assert await refused(world.tomek, piotr) == "cannot_play_together"


async def test_a_friend_with_a_game_then_or_a_full_week_is_refused_naming_nobody(
    client, world, piotr_and_kasia, session_factory, clock
):
    """Piotr plays this Tuesday at 21:00 (``world.first``); with one game a
    week his week is full. Kasia plays at Wisła Park at Saturday 10:00."""

    piotr, kasia = piotr_and_kasia
    booking = await ania_says_no(client, world)
    week = await client.put(
        "/api/v1/players/me/games-and-money",
        json={"games_per_week": 1, "most_ill_pay_grosze": None},
        headers=piotr["headers"],
    )
    assert week.status_code == 200, week.text
    others = [world.kuba, world.first[2], world.first[3]]
    await joins(client, world.group, *others[1:])
    proposal = await makes(
        session_factory,
        clock,
        pool_id=world.group,
        club_id=world.wisla_park,
        start=SATURDAY_TEN,
        versions=((kasia, *others),),
    )
    for player in (kasia, *others):
        assert (await says_yes(client, player, proposal)).status_code == 200

    full = await invites(client, world.tomek, booking, seat_of=world.ania, friend=piotr)
    then = await invites(client, world.ewa, booking, seat_of=world.ania, friend=kasia)

    assert full.json()["code"] == "friends_week_is_full"
    assert then.json()["code"] == "friend_plays_then"
    # Naming nobody.
    assert str(piotr["id"]) not in full.text and str(kasia["id"]) not in then.text


async def test_an_invitation_into_an_empty_seat_runs_out_like_the_card_s(
    client, world, piotr_and_kasia, session_factory, clock, mailbox
):
    piotr, _ = piotr_and_kasia
    booking = await ania_says_no(client, world)
    assert (
        await invites(client, world.tomek, booking, seat_of=world.ania, friend=piotr)
    ).status_code == 204
    clock.move(timedelta(hours=24))

    ran = await runs_out_the_invitations(session_factory, clock)

    assert ran.ran_out == 1
    told = [
        notice
        for notice in await notices_of(client, mailbox, world.tomek)
        if notice["kind"] == "DIDNT_ANSWER"
    ]
    assert [notice["title"] for notice in told] == ["piotr didn't answer"]
    # The seat is as empty as it was, still Ania's to name.
    seat = the_seat_of(
        (await details_of(client, world.tomek, booking))["friends_game"], world.ania
    )
    assert (seat["state"], seat["invitations"]) == ("CANT_MAKE_IT", [])


# --------------------------------------------------------------------------- #
# Open to Ogrody
# --------------------------------------------------------------------------- #


async def test_the_sender_opens_the_seat_and_a_member_takes_it_as_a_rescue(
    client, world, session_factory, clock, mailbox
):
    booking = await ania_says_no(client, world)
    # Nothing is offered before the sender opens it.
    assert await fill_in_of(client, world, world.kuba) == []

    opened = await opens(client, world.tomek, booking, seat_of=world.ania)

    assert opened.status_code == 204, opened.text
    seat = the_seat_of(
        (await details_of(client, world.tomek, booking))["friends_game"], world.ania
    )
    assert (seat["state"], seat["can_open"], seat["can_invite"]) == (
        "SEAT_OPEN",
        False,
        True,
    )
    assert await fill_in_of(client, world, world.kuba) == [booking]
    # Opened already: a second press records nothing.
    assert (
        await opens(client, world.tomek, booking, seat_of=world.ania)
    ).status_code == 204
    # Only the sender opens a seat.
    assert (await opens(client, world.ewa, booking, seat_of=world.ania)).json()[
        "code"
    ] == "booking_not_found"

    joined = await rescues(client, world.kuba, booking)

    assert joined.status_code == 200, joined.text
    assert joined.json()["money"]["share_state"] == "HELD"
    assert await fill_in_of(client, world, world.kuba) == []
    # At the cut-off his held share lets the seat's cover go.
    await the_cut_off_comes(session_factory, clock, at=FRIDAY_TEN)
    await mailbox.drain()
    charges = await charges_of(session_factory, booking)
    assert statuses(charges, of=world.tomek, cover=True) == ["CANCELLED"] * 3
    assert statuses(charges, of=world.tomek, cover=False) == ["CAPTURED"]
    assert statuses(charges, of=world.kuba) == ["CAPTURED"]


async def test_a_seat_open_to_the_group_is_offered_to_members_never_to_a_guest(
    client, world, mailbox
):
    """Zofia plays nowhere in Ogrody 33 Club: a seat opened to it is no rescue
    of hers. Kuba, a member who fits, reads it from outside — and is alerted,
    once he switched Fill in alerts on."""

    await chooses(client, world.kuba, fill_in_alerts=True)
    booking = await a_friends_game(client, world)
    for friend in (world.ewa, world.ania):
        assert (await accepts(client, friend, booking)).status_code == 200
    assert (await declines(client, world.magda, booking)).status_code == 204
    assert (
        await opens(client, world.tomek, booking, seat_of=world.magda)
    ).status_code == 204

    read = await client.get(
        f"/api/v1/bookings/{booking}", headers=world.kuba["headers"]
    )

    assert read.status_code == 200
    assert read.json()["rescue"] is not None
    assert "FILL_IN_ALERT" in kinds(await notices_of(client, mailbox, world.kuba))
    guest = world.first[2]
    assert (await rescues(client, guest, booking)).json()["code"] == (
        "booking_not_found"
    )
    # Magda said no to the seat: it is never offered back to her.
    assert await fill_in_of(client, world, world.magda) == []


async def test_opening_after_the_cut_off_is_refused_it_opened_on_its_own(
    client, world, clock
):
    booking = await ania_says_no(client, world)
    moves_to(clock, FRIDAY_TEN)

    late = await opens(client, world.tomek, booking, seat_of=world.ania)

    assert late.json()["code"] == "cut_off_has_passed"


# --------------------------------------------------------------------------- #
# The cover warning
# --------------------------------------------------------------------------- #


async def test_the_sender_is_warned_once_a_day_before_the_cut_off(
    client, world, session_factory, clock, mailbox
):
    booking = await a_friends_game(client, world)
    for friend in (world.ewa, world.magda):
        assert (await accepts(client, friend, booking)).status_code == 200
    moves_to(clock, THURSDAY_TEN - timedelta(minutes=1))
    assert (await warns(session_factory, clock)).warned == 0

    moves_to(clock, THURSDAY_TEN)
    ran = await warns(session_factory, clock)

    assert ran.warned == 1
    [warned] = [
        notice
        for notice in await notices_of(client, mailbox, world.tomek)
        if notice["kind"] == "COVER_WARNING"
    ]
    assert warned["title"] == "Saturday 10:00 · 1 seat still empty"
    assert warned["body"] == "At Fri 10:00 you pay 50 zł: your 25 zł and ania's seat."
    assert warned["opens"] == "BOOKING"
    # Once.
    clock.move(timedelta(hours=1))
    assert (await warns(session_factory, clock)).warned == 0
    assert booking


async def test_no_cover_warning_with_whole_court_he_pays_every_seat_already(
    client, world, session_factory, clock, mailbox
):
    whole = await a_friends_game(client, world, pay_mode="WHOLE_COURT")
    moves_to(clock, THURSDAY_TEN)

    assert (await warns(session_factory, clock)).warned == 0
    assert "COVER_WARNING" not in kinds(await notices_of(client, mailbox, world.tomek))
    assert whole


async def test_a_seat_that_empties_inside_the_last_day_carries_the_cover_line(
    client, world, clock, mailbox
):
    booking = await a_friends_game(client, world)
    for friend in world.friends:
        assert (await accepts(client, friend, booking)).status_code == 200
    moves_to(clock, THURSDAY_TEN + timedelta(hours=2))

    assert (await leaves(client, world.ewa, booking)).status_code == 200

    notices = await notices_of(client, mailbox, world.tomek)
    [left] = [notice for notice in notices if notice["kind"] == "SOMEONE_LEFT"]
    assert left["title"] == "ewa left your game"
    assert left["body"].endswith(
        "the seat is empty. At Fri 10:00 you pay 50 zł: your 25 zł and ewa's seat."
    )
    # Magda is told too, without the sender's line.
    [hers] = [
        notice
        for notice in await notices_of(client, mailbox, world.magda)
        if notice["kind"] == "SOMEONE_LEFT"
    ]
    assert "you pay" not in hers["body"]


# --------------------------------------------------------------------------- #
# At the cut-off
# --------------------------------------------------------------------------- #


async def test_at_the_cut_off_the_empty_seat_opens_and_a_late_taker_refunds_the_cover(
    client, world, session_factory, clock, mailbox
):
    booking = await a_friends_game(client, world)
    for friend in (world.ewa, world.magda):
        assert (await accepts(client, friend, booking)).status_code == 200

    ran = await the_cut_off_comes(session_factory, clock, at=FRIDAY_TEN)
    await mailbox.drain()

    assert ran.games == 0
    charges = await charges_of(session_factory, booking)
    assert statuses(charges, of=world.tomek, cover=True) == [
        "CANCELLED",
        "CANCELLED",
        "CAPTURED",
    ]
    game = (await details_of(client, world.tomek, booking))["friends_game"]
    assert the_seat_of(game, world.ania)["state"] == "SEAT_OPEN"
    assert await fill_in_of(client, world, world.kuba) == [booking]

    # Kuba takes it on Friday afternoon: he pays at once, and Tomek's cover is
    # refunded, less the fee.
    clock.move(timedelta(hours=5))
    joined = await rescues(client, world.kuba, booking)
    await mailbox.drain()

    assert joined.status_code == 200, joined.text
    assert joined.json()["money"]["share_state"] == "TAKEN"
    charges = await charges_of(session_factory, booking)
    assert refund_withheld(charges, of=world.tomek, cover=True) == ["True"]
    assert refund_withheld(charges, of=world.tomek, cover=False) == []
    assert statuses(charges, of=world.kuba) == ["CAPTURED"]


async def test_after_the_cut_off_a_friend_s_friend_takes_the_seat_and_pays_at_once(
    client, world, piotr_and_kasia, session_factory, clock, mailbox
):
    _, kasia = piotr_and_kasia
    booking = await a_friends_game(client, world)
    for friend in (world.ewa, world.magda):
        assert (await accepts(client, friend, booking)).status_code == 200
    await the_cut_off_comes(session_factory, clock, at=FRIDAY_TEN)
    await mailbox.drain()

    invited = await invites(
        client, world.ewa, booking, seat_of=world.ania, friend=kasia
    )
    assert invited.status_code == 204, invited.text
    accepted = await accepts(client, kasia, booking)
    await mailbox.drain()

    assert accepted.status_code == 200, accepted.text
    charges = await charges_of(session_factory, booking)
    assert statuses(charges, of=kasia) == ["CAPTURED"]
    assert refund_withheld(charges, of=world.tomek, cover=True) == ["True"]
    assert await fill_in_of(client, world, world.kuba) == []


# --------------------------------------------------------------------------- #
# Leaving
# --------------------------------------------------------------------------- #


async def test_a_friend_who_accepted_leaves_free_and_the_sender_is_told(
    client, world, session_factory, clock, mailbox
):
    booking = await a_friends_game(client, world)
    assert (await accepts(client, world.ewa, booking)).status_code == 200
    moves_to(clock, WEDNESDAY)

    left = await leaves(client, world.ewa, booking)
    await mailbox.drain()

    assert left.status_code == 200, left.text
    assert left.json()["left"] == "BEFORE_THE_CUT_OFF"
    assert statuses(await charges_of(session_factory, booking), of=world.ewa) == [
        "CANCELLED"
    ]
    game = (await details_of(client, world.tomek, booking))["friends_game"]
    assert the_seat_of(game, world.ewa)["state"] == "EMPTY"
    # Empty, no rescue: the sender's to fill.
    assert await fill_in_of(client, world, world.kuba) == []
    [told] = [
        notice
        for notice in await notices_of(client, mailbox, world.tomek)
        if notice["kind"] == "SOMEONE_LEFT"
    ]
    assert told["title"] == "ewa left your game"
    assert told["body"].endswith("the seat is empty.")


async def test_the_split_sender_leaving_lets_everything_go_and_the_game_turns_ordinary(
    client, world, session_factory, clock, mailbox
):
    booking = await ania_says_no(client, world)
    moves_to(clock, WEDNESDAY)

    left = await leaves(client, world.tomek, booking)
    await mailbox.drain()

    assert left.status_code == 200, left.text
    charges = await charges_of(session_factory, booking)
    assert statuses(charges, of=world.tomek) == ["CANCELLED"] * 4
    # His seat and Ania's are rescues at once.
    booking_now = await the_booking(session_factory, booking)
    assert booking_now.ordinary and booking_now.open_seats == 2
    assert await fill_in_of(client, world, world.kuba) == [booking]
    # A seat still open at the cut-off calls it off, nobody paying.
    ran = await the_cut_off_comes(session_factory, clock, at=FRIDAY_TEN)
    await mailbox.drain()
    assert ran.games == 1
    charges = await charges_of(session_factory, booking)
    for friend in (world.ewa, world.magda):
        assert statuses(charges, of=friend) == ["CANCELLED"]
    card = (await home_of(client, world.ewa))["games"][0]
    assert (card["status"], card["called_off_reason"]) == (
        "CALLED_OFF",
        "SHORT_AT_THE_CUT_OFF",
    )


async def test_the_whole_court_sender_leaving_still_pays_and_a_taker_pays_him_back(
    client, world, session_factory, clock, mailbox
):
    booking = await a_friends_game(client, world, pay_mode="WHOLE_COURT")
    for friend in world.friends:
        assert (await accepts(client, friend, booking)).status_code == 200
    moves_to(clock, WEDNESDAY)

    left = await leaves(client, world.tomek, booking)
    await mailbox.drain()

    assert left.status_code == 200, left.text
    assert (
        statuses(await charges_of(session_factory, booking), of=world.tomek)
        == ["HELD"] * 4
    )
    assert await fill_in_of(client, world, world.kuba) == [booking]
    assert (await rescues(client, world.kuba, booking)).status_code == 200

    await the_cut_off_comes(session_factory, clock, at=FRIDAY_TEN)
    await mailbox.drain()

    charges = await charges_of(session_factory, booking)
    # Kuba's 25 zł pays the sender back: one cover let go.
    assert statuses(charges, of=world.tomek) == [
        "CANCELLED",
        "CAPTURED",
        "CAPTURED",
        "CAPTURED",
    ]
    assert statuses(charges, of=world.kuba) == ["CAPTURED"]


async def test_the_sender_who_left_calls_nothing_off(client, world, clock):
    booking = await a_friends_game(client, world, pay_mode="WHOLE_COURT")
    assert (await leaves(client, world.tomek, booking)).status_code == 200

    refused = await client.post(
        f"/api/v1/bookings/{booking}/call-off", headers=world.tomek["headers"]
    )

    assert refused.json()["code"] == "booking_not_found"


async def test_after_the_cut_off_a_leaver_is_refunded_when_somebody_takes_the_seat(
    client, world, session_factory, clock, mailbox
):
    booking = await a_friends_game(client, world)
    for friend in world.friends:
        assert (await accepts(client, friend, booking)).status_code == 200
    await the_cut_off_comes(session_factory, clock, at=FRIDAY_TEN)
    await mailbox.drain()
    clock.move(timedelta(hours=2))

    left = await leaves(client, world.magda, booking)

    assert left.json()["left"] == "AFTER_THE_CUT_OFF"
    assert await fill_in_of(client, world, world.kuba) == [booking]
    assert (await rescues(client, world.kuba, booking)).status_code == 200
    await mailbox.drain()
    charges = await charges_of(session_factory, booking)
    assert refund_withheld(charges, of=world.magda) == ["True"]
    assert refund_withheld(charges, of=world.tomek) == []


async def test_the_sender_leaving_after_the_cut_off_is_a_late_leaver(
    client, world, session_factory, clock, mailbox
):
    booking = await a_friends_game(client, world)
    for friend in world.friends:
        assert (await accepts(client, friend, booking)).status_code == 200
    await the_cut_off_comes(session_factory, clock, at=FRIDAY_TEN)
    await mailbox.drain()

    left = await leaves(client, world.tomek, booking)
    assert left.json()["left"] == "AFTER_THE_CUT_OFF"
    assert (await rescues(client, world.kuba, booking)).status_code == 200
    await mailbox.drain()

    # His own share comes back, never a cover.
    charges = await charges_of(session_factory, booking)
    assert refund_withheld(charges, of=world.tomek, cover=False) == ["True"]
    assert refund_withheld(charges, of=world.tomek, cover=True) == []


# --------------------------------------------------------------------------- #
# A club's cancel
# --------------------------------------------------------------------------- #


async def test_a_clubs_cancel_moves_a_friends_game_as_any_booked_game(
    client, world, session_factory, mailbox
):
    """Ogrody 33 opens a second padel court after the send: the cancel moves
    the game onto it and nothing else happens — every hold and cover stays,
    and a friend still invited still is."""

    booking = await a_friends_game(client, world)
    assert (await accepts(client, world.ewa, booking)).status_code == 200
    court = await adds_a_court(client, world.desk, name="Court 3")
    await sets_hours(client, world.desk, [court["id"]], THE_HOURS)

    cancelled = await client.post(
        f"/api/v1/club/bookings/{booking}/cancellation",
        json={"reason": "REPAIR", "anyway": False},
        headers=world.desk,
    )
    await mailbox.drain()

    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["outcome"] == "MOVED"
    booking_now = await the_booking(session_factory, booking)
    assert booking_now.is_booked and booking_now.court.name == "Court 3"
    charges = await charges_of(session_factory, booking)
    assert statuses(charges, of=world.tomek) == ["HELD"] * 4
    assert statuses(charges, of=world.ewa) == ["HELD"]
    assert (await home_of(client, world.ania))["friends_games"] != []
    assert "GAME_MOVED" in kinds(await notices_of(client, mailbox, world.ewa))


async def test_a_clubs_cancel_after_the_cut_off_refunds_every_cover_in_full(
    client, world, session_factory, clock, mailbox
):
    booking = await a_friends_game(client, world)
    assert (await accepts(client, world.ewa, booking)).status_code == 200
    await the_cut_off_comes(session_factory, clock, at=FRIDAY_TEN)
    await mailbox.drain()

    cancelled = await client.post(
        f"/api/v1/club/bookings/{booking}/cancellation",
        json={"reason": "WEATHER", "anyway": True},
        headers=world.desk,
    )
    await mailbox.drain()

    assert cancelled.status_code == 200, cancelled.text
    charges = await charges_of(session_factory, booking)
    # Everything taken from him comes back whole: his share and both covers
    # the cut-off took.
    assert refund_withheld(charges, of=world.tomek) == ["False"] * 3
    assert refund_withheld(charges, of=world.ewa) == ["False"]
    assert UUID(booking)
