"""**Notifications: push, the recent list, and the three choices** (#549; the
mechanics §6.1–§6.4, §9.2, §10.1, §12–§13, §17.2; the screens A7.2, A9).

Seven notices are always on — *It's a game! · you paid*, *Confirm your payment*,
*Game called off · with the refund*, *Someone left your game*, *You've been
refunded*, *The club confirmed / couldn't take it*, *Your post didn't fill* —
and each is pushed to the player's phones and listed. Three are the player's:
*You complete it* (on, once a day, bundled), *Challenges for you* (on, three a
day, bundled), *Fill in alerts* (off, three a day). **No notice is ever sent for
a single swipe.**

Every act is taken over HTTP as the phone takes it, against the fake payment
provider; the outbox is drained the way the worker drains it, through the
recording push service, and every claim is read off what a phone was pushed and
off the list behind the bell.

The clock stands on **Monday 5 October 2026, 08:00 in Kraków**; the game is
**Saturday 10 October, 17:00** at Bonarka Arena, padel at 120 zł — 30 zł a
seat — with a 24-hour cut-off.
"""

from __future__ import annotations

from datetime import timedelta
from uuid import UUID

import pytest

from app.api.dependencies import get_clock
from app.bootstrap.composition import (
    build_call_off_short_games,
    build_expire_unanswered_requests,
)
from app.core.config import get_settings
from app.kernel import Sport
from app.modules.payments.domain.entered_cards import A_CARD_THAT_DECLINES_LATER
from tests.api import players_world as players
from tests.api.proposals_world import (
    MONDAY_MORNING,
    SATURDAY_FIVE,
    a_club_and_its_desk,
    a_group,
    a_member,
    deals,
    makes,
    saves_a_card,
    says_no,
    says_yes,
    sweeps,
    warsaw,
    withdraws,
)
from tests.unit.fake_clock import MovableClock

NOTIFICATIONS = "/api/v1/players/me/notifications"
DEVICES = "/api/v1/players/me/devices"
NOTICES = "/api/v1/players/me/notices"
CUT_OFF = SATURDAY_FIVE - timedelta(hours=24)
THE_GAME = "Padel at Bonarka Arena · Sat 10 Oct, 17:00"


@pytest.fixture
def clock(app):
    """Monday 5 October 2026, 08:00 in Kraków."""

    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


@pytest.fixture
async def bonarka(client) -> tuple[str, dict]:
    """Bonarka Arena, Instant: the club, and its desk's session."""

    return await a_club_and_its_desk(client, way="INSTANT")


@pytest.fixture
async def club(bonarka) -> str:
    return bonarka[0]


@pytest.fixture
async def crowd(client, session_factory, payments) -> list[dict]:
    """Ola, Kuba, Ewa and Tomek — who book Saturday's game — and Zosia and
    Marek, who could take a seat on it: padel 2,5, free every hour,
    competitive, each with a card that pays and a phone."""

    players = [
        await a_member(client, session_factory, payments, name)
        for name in ("ola", "kuba", "ewa", "tomek", "zosia", "marek")
    ]
    for player in players:
        await has_a_phone(client, player)
    return players


@pytest.fixture
async def group(client, club, crowd) -> UUID:
    return await a_group(client, crowd[0], club, *crowd[1:])


@pytest.fixture
async def booking(client, session_factory, clock, club, group, crowd, mailbox) -> str:
    """The four's game on Saturday at 17:00, booked by Tomek's yes — and
    delivered, so what a test does next is pushed after it. (The outbox orders
    the rows of one transaction among themselves by chance, so what is pushed
    in one drain may be pushed in any order.)"""

    booked = await a_booked_game(client, session_factory, clock, club, group, crowd[:4])
    await mailbox.drain()
    return booked


async def a_booked_game(
    client, session_factory, clock, club, group, four, *, start=SATURDAY_FIVE
) -> str:
    proposal = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=start,
        versions=(tuple(four),),
    )
    for player in four[:-1]:
        assert (await says_yes(client, player, proposal)).status_code == 200
    last = await says_yes(client, four[-1], proposal)
    assert last.status_code == 200, last.text
    assert last.json()["booked"] is not None, last.text
    return last.json()["booked"]["booking_id"]


async def has_a_phone(client, player: dict) -> str:
    token = f"ExponentPushToken[{player['name']}-phone]"
    registered = await client.post(
        DEVICES, json={"token": token}, headers=player["headers"]
    )
    assert registered.status_code == 204, registered.text
    player["phone"] = token
    return token


async def pushed_to(mailbox, pushes, player: dict) -> list[tuple[str, str]]:
    """Every push the player's phone showed: its title and its body."""

    await mailbox.drain()
    return [(push.title, push.body) for push in pushes.to(player["phone"])]


async def titles_pushed_to(mailbox, pushes, player: dict) -> list[str]:
    return [title for title, _ in await pushed_to(mailbox, pushes, player)]


async def notices_of(client, mailbox, player: dict, **params) -> list[dict]:
    await mailbox.drain()
    read = await client.get(NOTICES, params=params, headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()["notices"]


async def chooses(client, player: dict, **choices) -> dict:
    current = await client.get(NOTIFICATIONS, headers=player["headers"])
    assert current.status_code == 200, current.text
    saved = await client.put(
        NOTIFICATIONS, json={**current.json(), **choices}, headers=player["headers"]
    )
    assert saved.status_code == 200, saved.text
    return saved.json()


async def leaves(client, player: dict, booking_id: str) -> None:
    left = await client.post(
        f"/api/v1/bookings/{booking_id}/departure", headers=player["headers"]
    )
    assert left.status_code == 200, left.text


async def joins(client, player: dict, booking_id: str) -> None:
    joined = await client.post(
        f"/api/v1/bookings/{booking_id}/seats", headers=player["headers"]
    )
    assert joined.status_code == 200, joined.text


async def cuts_off(session_factory, clock):
    async with session_factory() as session:
        return await build_call_off_short_games(
            session, clock=clock, settings=get_settings()
        ).execute()


# --------------------------------------------------------------------------- #
# The choices, and the phones
# --------------------------------------------------------------------------- #


async def test_a_player_starts_with_two_choices_on_and_fill_in_alerts_off(
    client, session_factory, payments
):
    ola = await a_member(client, session_factory, payments, "ola")

    read = await client.get(NOTIFICATIONS, headers=ola["headers"])

    assert read.status_code == 200, read.text
    assert read.json() == {
        "you_complete_it": True,
        "challenges_for_you": True,
        "fill_in_alerts": False,
    }


async def test_the_choices_are_saved_as_the_screen_taps_them(
    client, session_factory, payments
):
    ola = await a_member(client, session_factory, payments, "ola")

    saved = await chooses(client, ola, fill_in_alerts=True, you_complete_it=False)

    assert saved == {
        "you_complete_it": False,
        "challenges_for_you": True,
        "fill_in_alerts": True,
    }
    read = await client.get(NOTIFICATIONS, headers=ola["headers"])
    assert read.json() == saved


async def test_only_an_expo_push_token_is_a_phone(client, session_factory, payments):
    ola = await a_member(client, session_factory, payments, "ola")

    refused = await client.post(
        DEVICES, json={"token": "fcm:not-an-expo-token"}, headers=ola["headers"]
    )

    assert refused.status_code == 400, refused.text
    assert refused.json()["code"] == "push_token_invalid"


async def test_a_phone_signed_out_is_pushed_nothing_more(
    client, booking, crowd, mailbox, pushes
):
    ola, kuba, ewa = crowd[:3]
    assert await titles_pushed_to(mailbox, pushes, ola) == [
        "It's a game! · you paid 30 zł"
    ]

    signed_out = await client.post(
        f"{DEVICES}/removal", json={"token": ola["phone"]}, headers=ola["headers"]
    )
    await leaves(client, kuba, booking)

    assert signed_out.status_code == 204, signed_out.text
    assert await titles_pushed_to(mailbox, pushes, ola) == [
        "It's a game! · you paid 30 zł"
    ]
    assert "kuba left your game" in await titles_pushed_to(mailbox, pushes, ewa)
    # Still told — the list holds it, whatever became of the phone.
    assert [n["kind"] for n in await notices_of(client, mailbox, ola)] == [
        "SOMEONE_LEFT",
        "GAME_BOOKED",
    ]


async def test_a_phone_signed_in_as_somebody_else_is_theirs_alone(
    client, booking, crowd, mailbox, pushes
):
    ola, kuba, ewa = crowd[:3]
    await mailbox.drain()
    before = len(pushes.to(ola["phone"]))

    # Ewa signs in on Ola's phone.
    moved = await client.post(
        DEVICES, json={"token": ola["phone"]}, headers=ewa["headers"]
    )
    await leaves(client, kuba, booking)

    assert moved.status_code == 204, moved.text
    await mailbox.drain()
    after = [push.title for push in pushes.to(ola["phone"])[before:]]
    # One *kuba left* — Ewa's, on the phone that is hers now; never Ola's too.
    assert after == ["kuba left your game"]


async def test_a_phone_the_push_service_forgot_is_asked_about_no_more(
    client, booking, crowd, mailbox, pushes
):
    ola, kuba, ewa = crowd[:3]
    await mailbox.drain()
    pushes.forget(ola["phone"])

    await leaves(client, kuba, booking)
    await mailbox.drain()
    asked_once = [p for p in pushes.asked if p.token == ola["phone"]]
    await leaves(client, ewa, booking)
    await mailbox.drain()

    assert [p for p in pushes.asked if p.token == ola["phone"]] == asked_once
    assert [n["kind"] for n in await notices_of(client, mailbox, ola)] == [
        "SOMEONE_LEFT",
        "SOMEONE_LEFT",
        "GAME_BOOKED",
    ]


async def test_a_push_service_that_is_down_costs_the_push_and_never_the_notice(
    client, session_factory, clock, club, group, crowd, mailbox, pushes
):
    ola = crowd[0]
    pushes.unavailable = True

    booking = await a_booked_game(
        client, session_factory, clock, club, group, crowd[:4]
    )

    assert await titles_pushed_to(mailbox, pushes, ola) == []
    [notice] = await notices_of(client, mailbox, ola)
    assert (notice["kind"], notice["game_id"]) == ("GAME_BOOKED", booking)
    # And the outbox is not held behind it: the next notice is pushed.
    pushes.unavailable = False
    await leaves(client, crowd[1], booking)
    assert await titles_pushed_to(mailbox, pushes, ola) == ["kuba left your game"]


# --------------------------------------------------------------------------- #
# The seven that are always on
# --------------------------------------------------------------------------- #


async def test_a_game_that_fills_tells_every_player_they_paid(
    client, booking, crowd, mailbox, pushes
):
    for player in crowd[:4]:
        assert await pushed_to(mailbox, pushes, player) == [
            ("It's a game! · you paid 30 zł", f"{THE_GAME}.")
        ]
    [notice] = await notices_of(client, mailbox, crowd[0])
    assert {
        key: notice[key]
        for key in ("kind", "title", "body", "opens", "game_id", "sport", "gathered")
    } == {
        "kind": "GAME_BOOKED",
        "title": "It's a game! · you paid 30 zł",
        "body": f"{THE_GAME}.",
        "opens": "BOOKING",
        "game_id": booking,
        "sport": "PADEL",
        "gathered": 0,
    }
    # Nobody outside the game is told anything.
    assert await notices_of(client, mailbox, crowd[4]) == []


async def test_a_refused_payment_asks_its_player_and_nobody_else(
    client, session_factory, clock, payments, club, group, crowd, mailbox, pushes
):
    ola, kuba, ewa, tomek = crowd[:4]
    # Ewa's new card is saved, and every payment on it is declined.
    await saves_a_card(client, payments, ewa["headers"], A_CARD_THAT_DECLINES_LATER)
    proposal = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        versions=(tuple(crowd[:4]),),
    )
    for player in (ola, kuba, ewa, tomek):
        assert (await says_yes(client, player, proposal)).status_code == 200

    assert await pushed_to(mailbox, pushes, ewa) == [
        (
            "Confirm your payment to keep your seat",
            f"Your bank declined 30 zł — confirm it with another card. {THE_GAME}.",
        )
    ]
    [notice] = await notices_of(client, mailbox, ewa)
    assert (notice["kind"], notice["opens"], notice["game_id"]) == (
        "CONFIRM_PAYMENT",
        "PROPOSAL",
        str(proposal),
    )
    for player in (ola, kuba, tomek):
        assert await notices_of(client, mailbox, player) == []


async def test_a_rescue_s_refused_payment_asks_to_take_the_seat(
    client, payments, booking, crowd, mailbox, pushes
):
    kuba, zosia = crowd[1], crowd[4]
    await saves_a_card(client, payments, zosia["headers"], A_CARD_THAT_DECLINES_LATER)
    await leaves(client, kuba, booking)

    refused = await client.post(
        f"/api/v1/bookings/{booking}/seats", headers=zosia["headers"]
    )

    assert refused.status_code == 200, refused.text
    assert refused.json()["booked"] is None
    assert await pushed_to(mailbox, pushes, zosia) == [
        (
            "Confirm your payment to take the seat",
            f"Your bank declined 30 zł — confirm it with another card. {THE_GAME}.",
        )
    ]
    [notice] = await notices_of(client, mailbox, zosia)
    assert (notice["kind"], notice["opens"]) == ("CONFIRM_PAYMENT", "BOOKING")


async def test_a_leaver_s_seat_tells_everybody_still_in_and_the_leaver_nothing(
    client, booking, crowd, mailbox, pushes
):
    ola, kuba, ewa, tomek = crowd[:4]

    await leaves(client, kuba, booking)

    for player in (ola, ewa, tomek):
        assert (await pushed_to(mailbox, pushes, player))[-1] == (
            "kuba left your game",
            f"{THE_GAME} — the seat is open.",
        )
    # Kuba left before the cut-off and was refunded less the card fee: his own
    # act, emailed and never pushed.
    assert await titles_pushed_to(mailbox, pushes, kuba) == [
        "It's a game! · you paid 30 zł"
    ]


async def test_a_game_still_short_at_the_cut_off_is_called_off_with_the_refund(
    client, session_factory, clock, booking, crowd, mailbox, pushes
):
    ola, kuba, ewa, tomek = crowd[:4]
    await leaves(client, kuba, booking)
    await mailbox.drain()

    clock.move(CUT_OFF - MONDAY_MORNING)
    await cuts_off(session_factory, clock)

    for player in (ola, ewa, tomek):
        assert (await pushed_to(mailbox, pushes, player))[-1] == (
            "Game called off · you're refunded 30 zł",
            f"{THE_GAME} was still short at the club's cut-off.",
        )
    assert "GAME_CALLED_OFF" not in [
        n["kind"] for n in await notices_of(client, mailbox, kuba)
    ]


async def test_a_game_the_club_cancels_is_called_off_with_its_reason(
    client, bonarka, booking, crowd, mailbox, pushes
):
    _, desk = bonarka

    cancelled = await client.post(
        f"/api/v1/club/bookings/{booking}/cancellation",
        json={"reason": "WEATHER"},
        headers=desk,
    )

    assert cancelled.status_code == 204, cancelled.text
    for player in crowd[:4]:
        assert (await pushed_to(mailbox, pushes, player))[-1] == (
            "Game called off · you're refunded 30 zł",
            "Bonarka Arena cancelled padel · Sat 10 Oct, 17:00 because of the weather.",
        )


async def test_a_leaver_whose_seat_was_taken_is_told_they_were_refunded(
    client, clock, booking, crowd, mailbox, pushes
):
    kuba, zosia = crowd[1], crowd[4]
    clock.move(CUT_OFF + timedelta(hours=1) - MONDAY_MORNING)
    await leaves(client, kuba, booking)

    await joins(client, zosia, booking)

    # 30 zł less the 1,45 zł card fee the bank keeps.
    assert (await pushed_to(mailbox, pushes, kuba))[-1] == (
        "You've been refunded 28,55 zł",
        f"Somebody took your seat — {THE_GAME}.",
    )
    assert await titles_pushed_to(mailbox, pushes, zosia) == [
        "It's a game! · you paid 30 zł"
    ]


async def test_a_post_not_full_by_its_book_by_tells_its_poster(
    client, session_factory, clock, club, group, crowd, mailbox, pushes
):
    ola, kuba = crowd[:2]
    await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        poster=ola,
        versions=((kuba,),),
        start=SATURDAY_FIVE,
        sport=Sport.PADEL,
    )

    # Its book-by: the club's two hours' notice before the hour.
    clock.move(SATURDAY_FIVE - timedelta(hours=2) - MONDAY_MORNING)
    await sweeps(session_factory, clock)

    assert await pushed_to(mailbox, pushes, ola) == [
        (
            "Your Sat 17:00 didn't fill",
            "Padel at Bonarka Arena — nobody paid. Post it again?",
        )
    ]
    [notice] = await notices_of(client, mailbox, ola)
    assert (notice["kind"], notice["opens"]) == ("POST_DID_NOT_FILL", "PROPOSAL")


# --------------------------------------------------------------------------- #
# On request: the club's answer
# --------------------------------------------------------------------------- #


@pytest.fixture
async def on_request(client) -> tuple[str, dict]:
    """Kazimierz Padel, On request: the club and its desk's session."""

    return await a_club_and_its_desk(client, name="Kazimierz Padel", way="ON_REQUEST")


async def a_game_waiting_for(client, session_factory, clock, on_request, crowd) -> UUID:
    club, _ = on_request
    four = crowd[:4]
    group = await a_group(client, four[0], club, *four[1:])
    proposal = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    for player in four:
        assert (await says_yes(client, player, proposal)).status_code == 200
    return proposal


async def test_the_club_s_yes_is_one_notice_that_it_confirmed_and_they_paid(
    client, session_factory, clock, on_request, crowd, mailbox, pushes
):
    _, desk = on_request
    proposal = await a_game_waiting_for(
        client, session_factory, clock, on_request, crowd
    )

    accepted = await client.post(
        f"/api/v1/club/bookings/{proposal}/acceptance", headers=desk
    )

    assert accepted.status_code == 200, accepted.text
    for player in crowd[:4]:
        assert await pushed_to(mailbox, pushes, player) == [
            (
                "Kazimierz Padel confirmed your game",
                "Padel · Sat 10 Oct, 17:00 — it's a game, and you paid 30 zł.",
            )
        ]


async def test_the_club_s_no_tells_everybody_waiting_on_it(
    client, session_factory, clock, on_request, crowd, mailbox, pushes
):
    _, desk = on_request
    proposal = await a_game_waiting_for(
        client, session_factory, clock, on_request, crowd
    )

    refused = await client.post(
        f"/api/v1/club/bookings/{proposal}/refusal",
        json={"reason": "a tournament"},
        headers=desk,
    )

    assert refused.status_code == 204, refused.text
    for player in crowd[:4]:
        assert await pushed_to(mailbox, pushes, player) == [
            (
                "Kazimierz Padel couldn't take your game",
                "Padel · Sat 10 Oct, 17:00. Nobody paid — you'll get a new card first.",
            )
        ]


async def test_the_club_s_silence_tells_everybody_waiting_on_it_too(
    client, session_factory, clock, on_request, crowd, mailbox, pushes
):
    await a_game_waiting_for(client, session_factory, clock, on_request, crowd)

    # Its time to confirm is thirty minutes; the job calls it off past them.
    clock.move(timedelta(minutes=30))
    async with session_factory() as session:
        done = await build_expire_unanswered_requests(
            session, clock=clock, settings=get_settings()
        ).execute()

    assert done.requests == 1
    for player in crowd[:4]:
        assert await titles_pushed_to(mailbox, pushes, player) == [
            "Kazimierz Padel couldn't take your game"
        ]


async def test_leaving_a_game_waiting_for_the_club_tells_the_others_it_fills_again(
    client, session_factory, clock, on_request, crowd, mailbox, pushes
):
    ola, kuba, ewa, tomek = crowd[:4]
    proposal = await a_game_waiting_for(
        client, session_factory, clock, on_request, crowd
    )

    assert (await withdraws(client, kuba, proposal)).status_code == 204

    for player in (ola, ewa, tomek):
        assert await pushed_to(mailbox, pushes, player) == [
            (
                "kuba left your game",
                "Padel at Kazimierz Padel · Sat 10 Oct, 17:00 — it's filling again.",
            )
        ]
    assert await notices_of(client, mailbox, kuba) == []


# --------------------------------------------------------------------------- #
# The three that are the player's — and no notice for a single swipe
# --------------------------------------------------------------------------- #


async def test_no_notice_is_ever_sent_for_a_single_swipe(
    client, session_factory, clock, club, group, crowd, mailbox, pushes
):
    ola, kuba, ewa, tomek = crowd[:4]
    proposal = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        versions=(tuple(crowd[:4]),),
    )

    assert (await says_yes(client, ola, proposal)).status_code == 200
    assert (await says_no(client, kuba, proposal)).status_code == 204
    assert (await says_yes(client, ewa, proposal)).status_code == 200
    assert (await withdraws(client, ewa, proposal)).status_code == 204

    await mailbox.drain()
    assert pushes.asked == []
    for player in crowd:
        assert await notices_of(client, mailbox, player) == []


async def test_a_card_that_needs_only_you_says_so(
    client, session_factory, clock, club, group, crowd, mailbox, pushes
):
    ola, kuba, ewa, tomek = crowd[:4]
    proposal = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        versions=(tuple(crowd[:4]),),
    )
    for player in (ola, kuba, ewa):
        assert (await says_yes(client, player, proposal)).status_code == 200

    assert await pushed_to(mailbox, pushes, tomek) == [
        ("A game needs only you", f"{THE_GAME} — say yes and it's booked.")
    ]
    [notice] = await notices_of(client, mailbox, tomek)
    assert (notice["kind"], notice["opens"], notice["game_id"]) == (
        "YOU_COMPLETE_IT",
        "DECK",
        str(proposal),
    )
    for player in (ola, kuba, ewa):
        assert await notices_of(client, mailbox, player) == []


async def test_a_second_card_that_needs_only_you_the_same_day_is_bundled(
    client, session_factory, clock, club, group, crowd, mailbox, pushes
):
    ola, kuba, ewa, tomek = crowd[:4]
    for start in (SATURDAY_FIVE, warsaw(10, 18), warsaw(10, 19)):
        proposal = await makes(
            session_factory,
            clock,
            pool_id=group,
            club_id=club,
            start=start,
            versions=(tuple(crowd[:4]),),
        )
        for player in (ola, kuba, ewa):
            assert (await says_yes(client, player, proposal)).status_code == 200
        await mailbox.drain()

    assert await titles_pushed_to(mailbox, pushes, tomek) == ["A game needs only you"]
    [notice] = await notices_of(client, mailbox, tomek)
    assert (notice["title"], notice["gathered"]) == ("3 games need only you", 2)

    # Gathering one more moved it up, above what was told in between.
    await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        poster=ola,
        versions=((tomek,),),
    )
    clock.move(timedelta(minutes=5))
    proposal = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=warsaw(10, 21),
        versions=(tuple(crowd[:4]),),
    )
    for player in (ola, kuba, ewa):
        assert (await says_yes(client, player, proposal)).status_code == 200
    newest, challenged = await notices_of(client, mailbox, tomek)
    assert (newest["title"], newest["gathered"]) == ("4 games need only you", 3)
    assert challenged["kind"] == "CHALLENGE"

    # The next day is a day of its own.
    clock.move(timedelta(days=1))
    proposal = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=warsaw(10, 20),
        versions=(tuple(crowd[:4]),),
    )
    for player in (ola, kuba, ewa):
        assert (await says_yes(client, player, proposal)).status_code == 200
    assert await titles_pushed_to(mailbox, pushes, tomek) == [
        "A game needs only you",
        "ola challenged you",
        "A game needs only you",
    ]


async def test_you_complete_it_switched_off_is_not_told(
    client, session_factory, clock, club, group, crowd, mailbox, pushes
):
    ola, kuba, ewa, tomek = crowd[:4]
    await chooses(client, tomek, you_complete_it=False)
    proposal = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        versions=(tuple(crowd[:4]),),
    )
    for player in (ola, kuba, ewa):
        assert (await says_yes(client, player, proposal)).status_code == 200

    assert await notices_of(client, mailbox, tomek) == []
    assert pushes.asked == []


async def test_you_complete_it_is_the_named_player_s_and_never_a_next_best_fit_s(
    client, session_factory, clock, club, group, crowd, mailbox, pushes
):
    """The mechanics §6.3: *the named player keeps two advantages … they get
    the You complete it alert*. A next best fit dealt the seat a no left is
    dealt a card, not told about it."""

    ola, kuba, ewa, tomek, zosia = crowd[:5]
    proposal = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        versions=(tuple(crowd[:4]),),
    )
    assert (await says_no(client, tomek, proposal)).status_code == 204
    await deals(session_factory, clock, proposal, zosia, into=1)
    for player in (ola, kuba, ewa):
        assert (await says_yes(client, player, proposal)).status_code == 200

    await mailbox.drain()
    assert pushes.asked == []
    assert await notices_of(client, mailbox, zosia) == []


async def test_a_card_the_reader_s_deck_does_not_show_is_not_told(
    client, session_factory, clock, club, group, crowd, mailbox, pushes
):
    ola, kuba, ewa, tomek = crowd[:4]
    # Tomek wants padel for fun now: the deck shows him no competitive card.
    await players.declare_intent(client, tomek["token"], intent="FOR_FUN")
    proposal = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        versions=(tuple(crowd[:4]),),
    )
    for player in (ola, kuba, ewa):
        assert (await says_yes(client, player, proposal)).status_code == 200

    assert await notices_of(client, mailbox, tomek) == []


async def test_a_paused_yes_that_comes_back_one_seat_short_tells_the_named(
    client, session_factory, clock, club, group, crowd, mailbox, pushes
):
    ola, kuba, ewa, tomek, zosia, marek = crowd
    # One game a week for Ola: Saturday's booking pauses her Sunday yes.
    saved = await client.put(
        "/api/v1/players/me/games-and-money",
        json={"games_per_week": 1, "most_ill_pay_grosze": None},
        headers=ola["headers"],
    )
    assert saved.status_code == 200, saved.text
    sunday = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=warsaw(11, 17),
        versions=((ola, kuba, ewa, zosia),),
    )
    assert (await says_yes(client, ola, sunday)).status_code == 200
    saturday = await a_booked_game(
        client, session_factory, clock, club, group, (ola, tomek, marek, kuba)
    )
    for player in (kuba, ewa):
        assert (await says_yes(client, player, sunday)).status_code == 200
    await mailbox.drain()
    assert await notices_of(client, mailbox, zosia) == []

    # Ola leaves Saturday: her week has room, and her Sunday yes comes back.
    await leaves(client, ola, saturday)

    assert await pushed_to(mailbox, pushes, zosia) == [
        (
            "A game needs only you",
            "Padel at Bonarka Arena · Sun 11 Oct, 17:00 — say yes and it's booked.",
        )
    ]


async def test_a_post_challenges_everybody_it_names_three_times_a_day_then_bundles(
    client, session_factory, clock, club, group, crowd, mailbox, pushes
):
    ola, kuba, ewa, tomek, zosia, marek = crowd
    posters = (ola, kuba, ewa, tomek)
    for hour, poster in zip((17, 18, 19, 20), posters, strict=True):
        await makes(
            session_factory,
            clock,
            pool_id=group,
            club_id=club,
            start=warsaw(10, hour),
            poster=poster,
            versions=((zosia, marek),) if poster is not tomek else ((zosia,),),
        )
        await mailbox.drain()

    assert await pushed_to(mailbox, pushes, zosia) == [
        ("ola challenged you", f"{THE_GAME}."),
        ("kuba challenged you", "Padel at Bonarka Arena · Sat 10 Oct, 18:00."),
        ("ewa challenged you", "Padel at Bonarka Arena · Sat 10 Oct, 19:00."),
    ]
    newest, *_ = await notices_of(client, mailbox, zosia)
    assert (newest["kind"], newest["opens"], newest["gathered"]) == (
        "CHALLENGE",
        "DECK",
        1,
    )
    assert newest["title"] == "2 challenges for you"
    assert len(await titles_pushed_to(mailbox, pushes, marek)) == 3


async def test_challenges_switched_off_are_not_told(
    client, session_factory, clock, club, group, crowd, mailbox, pushes
):
    ola, zosia = crowd[0], crowd[4]
    await chooses(client, zosia, challenges_for_you=False)

    await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        poster=ola,
        versions=((zosia,),),
    )

    assert await notices_of(client, mailbox, zosia) == []


async def test_fill_in_alerts_are_off_until_switched_on(
    client, booking, crowd, mailbox, pushes
):
    kuba, zosia, marek = crowd[1], crowd[4], crowd[5]
    await chooses(client, zosia, fill_in_alerts=True)

    await leaves(client, kuba, booking)

    assert await pushed_to(mailbox, pushes, zosia) == [
        ("A game you fit needs one more", f"{THE_GAME} · 30 zł a seat.")
    ]
    [notice] = await notices_of(client, mailbox, zosia)
    assert (notice["kind"], notice["opens"], notice["game_id"]) == (
        "FILL_IN_ALERT",
        "BOOKING",
        booking,
    )
    assert await notices_of(client, mailbox, marek) == []


async def test_fill_in_alerts_past_three_a_day_are_not_given(
    client, session_factory, clock, club, group, crowd, mailbox, pushes
):
    ola, kuba, *_, zosia, marek = crowd
    await chooses(client, zosia, fill_in_alerts=True)
    for player in (ola, kuba, marek):
        saved = await client.put(
            "/api/v1/players/me/games-and-money",
            json={"games_per_week": 7, "most_ill_pay_grosze": None},
            headers=player["headers"],
        )
        assert saved.status_code == 200, saved.text
    # Four games of three — Ola, Kuba and Marek — each one short of four from
    # the start, so Zosia's seat is open the moment Kuba leaves.
    for hour in (17, 18, 19, 20):
        booking = await a_booked_game(
            client,
            session_factory,
            clock,
            club,
            group,
            (ola, kuba, marek, crowd[3]),
            start=warsaw(10, hour),
        )
        await leaves(client, kuba, booking)
        await mailbox.drain()

    assert (
        await titles_pushed_to(mailbox, pushes, zosia)
        == ["A game you fit needs one more"] * 3
    )
    assert len(await notices_of(client, mailbox, zosia)) == 3


# --------------------------------------------------------------------------- #
# The list behind the bell
# --------------------------------------------------------------------------- #


async def test_the_recent_list_is_the_newest_first_and_as_long_as_asked(
    client, booking, crowd, mailbox
):
    ola, kuba, ewa = crowd[:3]
    await leaves(client, kuba, booking)
    await mailbox.drain()
    await leaves(client, ewa, booking)

    notices = await notices_of(client, mailbox, ola)
    assert [n["title"] for n in notices] == [
        "ewa left your game",
        "kuba left your game",
        "It's a game! · you paid 30 zł",
    ]
    assert [n["title"] for n in await notices_of(client, mailbox, ola, limit=1)] == [
        "ewa left your game"
    ]
