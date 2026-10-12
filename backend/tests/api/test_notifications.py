"""**Notifications: push, the recent list, and the three choices** (#549; the
mechanics §6.1–§6.4, §9.2, §10.1, §12–§13, §17.2; the screens A7.2, A9).

Seven notices are always on — *It's a game! · you paid*, *Confirm your
payment*, *Game called off · with the refund*, *Someone left your game*,
*You've been refunded*, *Your new game* (#622), *Your post didn't fill* — and
each is pushed to the player's phones and listed. Three are the player's:
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

from datetime import datetime, timedelta
from uuid import UUID

import pytest

from app.api.dependencies import get_clock
from app.bootstrap.composition import (
    build_the_cut_off,
    build_notice_day_repository,
    build_propose_games,
)
from app.core.config import get_settings
from app.kernel import Sport, instant
from app.modules.clubs.domain.court_hours import local_day
from app.modules.notifications.domain.notices import (
    Notice,
    NoticeKind,
    NoticeReason,
    Opens,
)
from app.modules.payments.domain.entered_cards import A_CARD_THAT_DECLINES_LATER
from app.modules.proposals.application.propose_games import Proposed
from app.shared.ids import new_uuid
from tests.api import players_world as players
from tests.api.club_courts_world import EXCEPTIONS, adds_a_court, sets_hours
from tests.api.proposals_world import (
    MONDAY_MORNING,
    SATURDAY_FIVE,
    a_club_and_its_desk,
    a_group,
    a_member,
    deals,
    every_hour_of_the_week,
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
    """Bonarka Arena: the club, and its desk's session."""

    return await a_club_and_its_desk(client)


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
        return await build_the_cut_off(
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
        "It's a game! · 30 zł held"
    ]

    signed_out = await client.post(
        f"{DEVICES}/removal", json={"token": ola["phone"]}, headers=ola["headers"]
    )
    await leaves(client, kuba, booking)

    assert signed_out.status_code == 204, signed_out.text
    assert await titles_pushed_to(mailbox, pushes, ola) == [
        "It's a game! · 30 zł held"
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
    # Tomek's yes filled it: his own copy is pushed to nobody (Q102).
    for player in crowd[:3]:
        assert await pushed_to(mailbox, pushes, player) == [
            ("It's a game! · 30 zł held", f"{THE_GAME}.")
        ]
    assert await pushed_to(mailbox, pushes, crowd[3]) == []
    [notice] = await notices_of(client, mailbox, crowd[0])
    assert {
        key: notice[key]
        for key in ("kind", "title", "body", "opens", "game_id", "sport", "gathered")
    } == {
        "kind": "GAME_BOOKED",
        "title": "It's a game! · 30 zł held",
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

    # Her time to fix her card: thirty minutes from 08:00, before the cut-off
    # (#625, #638; Q109, Q113).
    assert await pushed_to(mailbox, pushes, ewa) == [
        (
            "Fix your card by 08:30 to keep your seat",
            "Nothing is paid now. Padel · Sat 17:00 at Bonarka Arena — the "
            "others are waiting.",
        )
    ]
    [notice] = await notices_of(client, mailbox, ewa)
    assert (notice["kind"], notice["opens"], notice["game_id"]) == (
        "FIX_YOUR_CARD",
        "PROPOSAL",
        str(proposal),
    )
    # The others are told the game waits for one payment — never whose — and
    # Tomek's yes filled it, so his copy is his own (Q110).
    for player in (ola, kuba, tomek):
        [waiting] = await notices_of(client, mailbox, player)
        assert waiting["kind"] == "WAITING_FOR_A_PAYMENT"
        assert "ewa" not in (waiting["title"] + waiting["body"]).lower()
        assert waiting["your_own"] is (player is tomek)
    assert await pushed_to(mailbox, pushes, tomek) == []


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
    # Before the cut-off the seat is kept for her to fix the card (#640).
    assert await pushed_to(mailbox, pushes, zosia) == [
        (
            "Fix your card by 08:30 to take the seat",
            "Your bank declined the 30 zł hold — fix it with another card. "
            "Nothing is paid now. Padel · Sat 17:00 at Bonarka Arena — the seat "
            "is kept for you until then.",
        )
    ]
    [notice] = await notices_of(client, mailbox, zosia)
    assert (notice["kind"], notice["opens"]) == ("FIX_YOUR_CARD", "BOOKING")


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
    # Kuba left before the cut-off and his hold was let go: his own act,
    # emailed and never pushed.
    assert await titles_pushed_to(mailbox, pushes, kuba) == [
        "It's a game! · 30 zł held"
    ]


async def test_a_game_still_short_at_the_cut_off_is_called_off_and_nothing_taken(
    client, session_factory, clock, booking, crowd, mailbox, pushes
):
    ola, kuba, ewa, tomek = crowd[:4]
    await leaves(client, kuba, booking)
    await mailbox.drain()

    clock.move(CUT_OFF - MONDAY_MORNING)
    await cuts_off(session_factory, clock)

    for player in (ola, ewa, tomek):
        assert (await pushed_to(mailbox, pushes, player))[-1] == (
            "Game called off · nothing was taken",
            f"{THE_GAME} was still short at the club's cut-off.",
        )
    # Kuba's empty seat called it off: he is told so, as a leaver, and that
    # it counts on his record (Q108).
    [notice, *_] = await notices_of(client, mailbox, kuba)
    assert (notice["kind"], notice["title"], notice["body"]) == (
        "GAME_CALLED_OFF",
        "Saturday's 17:00 at Bonarka Arena, which you left, was called off",
        "Your seat stayed empty, so it counts on your record. Nothing was "
        "taken from you.",
    )
    # He has no seat on it: it opens the game he left.
    assert notice["opens"] == "PROPOSAL"


async def test_a_game_the_club_cancels_is_called_off_with_its_reason(
    client, bonarka, booking, crowd, mailbox, pushes
):
    _, desk = bonarka

    cancelled = await client.post(
        f"/api/v1/club/bookings/{booking}/cancellation",
        json={"reason": "WEATHER"},
        headers=desk,
    )

    assert cancelled.status_code == 200, cancelled.text
    # No other court takes it: called off (#672).
    assert cancelled.json()["outcome"] == "CALLED_OFF"
    for player in crowd[:4]:
        assert (await pushed_to(mailbox, pushes, player))[-1] == (
            "Game called off · nothing was taken",
            "Bonarka Arena cancelled padel · Sat 10 Oct, 17:00 because of the weather.",
        )


async def test_a_game_the_club_moves_tells_everybody_the_court_and_its_kind(
    client, bonarka, booking, crowd, mailbox, pushes
):
    """*Game moved* (#671; the mechanics §17.2, Q122): always on, to every
    player on the booking, opening the booked game, and never emailed."""

    _, desk = bonarka
    court_3 = await adds_a_court(client, desk, name="Court 3", sport="PADEL")
    await sets_hours(client, desk, [court_3["id"]], every_hour_of_the_week())
    told_before = {player["name"]: len(pushes.to(player["phone"])) for player in crowd}

    moved = await client.post(
        f"/api/v1/club/bookings/{booking}/move",
        json={"court_id": court_3["id"]},
        headers=desk,
    )

    assert moved.status_code == 200, moved.text
    for player in crowd[:4]:
        assert (await pushed_to(mailbox, pushes, player))[
            told_before[player["name"]] :
        ] == [
            (
                "Bonarka Arena moved your game to Court 3 · Sat 17:00",
                "Padel · indoor · nothing else changes",
            )
        ]
        [notice, *_] = await notices_of(client, mailbox, player)
        assert (notice["kind"], notice["opens"], notice["game_id"]) == (
            "GAME_MOVED",
            "BOOKING",
            booking,
        )
        assert notice["your_own"] is False
        emails = await mailbox.to(f"{player['name']}@example.com")
        assert all("moved" not in email.subject.lower() for email in emails)
    for player in crowd[4:]:
        assert len(pushes.to(player["phone"])) == told_before[player["name"]]


async def test_a_leaver_whose_seat_was_taken_is_told_they_were_refunded(
    client, session_factory, clock, booking, crowd, mailbox, pushes
):
    kuba, zosia = crowd[1], crowd[4]
    clock.move(CUT_OFF + timedelta(hours=1) - MONDAY_MORNING)
    await cuts_off(session_factory, clock)
    await leaves(client, kuba, booking)

    await joins(client, zosia, booking)

    # 30 zł less exactly the 1,45 zł kept on his payment, told once the
    # refund is made (#641).
    assert (await pushed_to(mailbox, pushes, kuba))[-1] == (
        "You've been refunded 28,55 zł · your seat was taken",
        f"30 zł less the 1,45 zł kept on your payment — {THE_GAME}.",
    )
    # Zosia took the seat herself and saw *It's a game!*: her notice is her
    # own, listed and pushed to nobody (Q102).
    assert await titles_pushed_to(mailbox, pushes, zosia) == []
    [joined] = await notices_of(client, mailbox, zosia)
    # After the cut-off her share was taken at once.
    assert (joined["title"], joined["your_own"]) == (
        "It's a game! · you paid 30 zł",
        True,
    )


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

    # Its book-by: the club's release time, a day before the hour.
    clock.move(SATURDAY_FIVE - timedelta(days=1) - MONDAY_MORNING)
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
# Your new game — the card a club's cancel owed
# --------------------------------------------------------------------------- #

#: Saturday evenings, 17:00–19:00 — the only hours the four are free.
SATURDAY_EVENINGS = [{"day": 6, "hour": hour} for hour in (17, 18)]


async def proposes(session_factory, clock, *pools: UUID) -> Proposed:
    done = Proposed()
    async with session_factory() as session:
        proposer = build_propose_games(session, clock=clock)
        for pool_id in pools:
            done += await proposer.execute(pool_id)
    return done


async def deck_of(client, player: dict, group: UUID) -> list[dict]:
    read = await client.get(
        f"/api/v1/pools/{group}/deck",
        params={"sport": "PADEL", "kind": "COMPETITIVE"},
        headers=player["headers"],
    )
    assert read.status_code == 200, read.text
    return read.json()["cards"]


async def a_game_the_club_cancels(
    client, session_factory, clock, mailbox, payments
) -> tuple[list[dict], UUID]:
    """Kazimierz Padel sells padel on Saturday at 17:00 and 18:00. The proposer
    deals the four Saturday's 17:00; all four say yes, the last books it, and
    the club cancels it. The four, each with a phone, and their group."""

    club, desk = await a_club_and_its_desk(
        client, name="Kazimierz Padel", hours=[(6, 17), (6, 18)]
    )
    four = [
        await a_member(client, session_factory, payments, name, week=SATURDAY_EVENINGS)
        for name in ("ola", "kuba", "ewa", "tomek")
    ]
    for player in four:
        await has_a_phone(client, player)
    group = await a_group(client, four[0], club, *four[1:])
    assert (await proposes(session_factory, clock, group)).made == 1
    [card] = await deck_of(client, four[0], group)
    game = UUID(card["proposal_id"])
    assert datetime.fromisoformat(card["starts_at"]) == SATURDAY_FIVE
    for player in four:
        said = await says_yes(client, player, game)
        assert said.status_code == 200, said.text
    assert said.json()["booked"] is not None, said.text
    cancelled = await client.post(
        f"/api/v1/club/bookings/{game}/cancellation",
        json={"reason": "REPAIR"},
        headers=desk,
    )
    assert cancelled.status_code == 200, cancelled.text
    # No other court takes it: called off (#672).
    assert cancelled.json()["outcome"] == "CALLED_OFF"
    await mailbox.drain()
    return four, group


async def test_the_new_card_a_club_s_cancel_owed_is_told_to_each_player_once(
    client, session_factory, clock, mailbox, payments, pushes
):
    four, group = await a_game_the_club_cancels(
        client, session_factory, clock, mailbox, payments
    )
    told_before = {player["name"]: len(pushes.to(player["phone"])) for player in four}

    proposed = await proposes(session_factory, clock, group)
    await proposes(session_factory, clock, group)

    assert (proposed.redealt, proposed.made) == (1, 1)
    [card] = await deck_of(client, four[0], group)
    # The four together at the nearest hour they are all free — never the
    # 17:00 the club cancelled.
    assert datetime.fromisoformat(card["starts_at"]) == warsaw(10, 18)
    for player in four:
        assert (await pushed_to(mailbox, pushes, player))[
            told_before[player["name"]] :
        ] == [
            (
                "Your new game · Sat 18:00 at Kazimierz Padel",
                "The same players · 30 zł a share — say yes to book it.",
            )
        ]
        [notice, *_] = await notices_of(client, mailbox, player)
        assert (notice["kind"], notice["opens"], notice["your_own"]) == (
            "NEW_GAME",
            "DECK",
            False,
        )
        # The deck opens on the card: its group, sport and kind.
        assert (
            notice["game_id"],
            notice["pool_id"],
            notice["sport"],
            notice["game_kind"],
        ) == (card["proposal_id"], str(group), "PADEL", "COMPETITIVE")
        emails = await mailbox.to(f"{player['name']}@example.com")
        assert all("new game" not in email.subject.lower() for email in emails)


async def test_a_card_the_proposer_deals_for_any_other_reason_tells_nobody(
    client, session_factory, clock, mailbox, payments, pushes
):
    """The four's first card at Kazimierz Padel is the proposer's ordinary
    pick. When its court goes, the three In are dealt a new card first — but
    no notice promised them one. Both cards are in their decks, and nobody is
    told of either."""

    club, desk = await a_club_and_its_desk(
        client, name="Kazimierz Padel", hours=[(6, 17), (6, 18)]
    )
    four = [
        await a_member(client, session_factory, payments, name, week=SATURDAY_EVENINGS)
        for name in ("ola", "kuba", "ewa", "tomek")
    ]
    for player in four:
        await has_a_phone(client, player)
    group = await a_group(client, four[0], club, *four[1:])

    assert (await proposes(session_factory, clock, group)).made == 1
    await mailbox.drain()
    assert pushes.asked == []
    [card] = await deck_of(client, four[0], group)
    for player in four[:3]:
        assert (
            await says_yes(client, player, UUID(card["proposal_id"]))
        ).status_code == 200
    await mailbox.drain()
    # Tomek is the one seat left: *A game needs only you*, and nothing else.
    told = [(push.token, push.title) for push in pushes.sent]
    assert told == [(four[3]["phone"], "A game needs only you")]
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

    proposed = await proposes(session_factory, clock, group)

    assert (proposed.lost, proposed.made) == (1, 1)
    await mailbox.drain()
    assert [(push.token, push.title) for push in pushes.sent] == told


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
        "It's a game! · 30 zł held",
    ]
    assert [n["title"] for n in await notices_of(client, mailbox, ola, limit=1)] == [
        "ewa left your game"
    ]


# --------------------------------------------------------------------------- #
# The bell's number (#621; the mechanics Q101, Q102)
# --------------------------------------------------------------------------- #

VISIT = f"{NOTICES}/visit"


async def the_list(client, mailbox, player: dict, **params) -> dict:
    """The notices read whole: the rows, the bell's number and the last visit."""

    await mailbox.drain()
    read = await client.get(NOTICES, params=params, headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()


async def opens_the_list(client, player: dict) -> None:
    opened = await client.post(VISIT, headers=player["headers"])
    assert opened.status_code == 204, opened.text


async def another_phone(client, player: dict) -> dict:
    """The same player, signed in a second time — another phone."""

    signed_in = await client.post(
        "/api/v1/auth/login",
        json={"email": f"{player['name']}@example.com", "password": "hunter22!"},
    )
    assert signed_in.status_code == 200, signed_in.text
    tokens = signed_in.json()
    return {
        **player,
        "headers": players.auth(tokens["access_token"]),
        "refresh_token": tokens["refresh_token"],
    }


async def test_every_notice_is_new_until_the_list_is_opened_and_then_only_later_ones(
    client, clock, booking, crowd, mailbox
):
    ola, kuba = crowd[:2]

    never_opened = await the_list(client, mailbox, ola)
    assert (never_opened["new_count"], never_opened["last_opened_at"]) == (1, None)
    assert [n["new"] for n in never_opened["notices"]] == [True]

    await opens_the_list(client, ola)
    opened = await the_list(client, mailbox, ola)
    assert opened["new_count"] == 0
    assert opened["last_opened_at"] == clock.now().isoformat().replace("+00:00", "Z")
    assert [n["new"] for n in opened["notices"]] == [False]

    clock.move(timedelta(minutes=5))
    await leaves(client, kuba, booking)
    later = await the_list(client, mailbox, ola)
    assert later["new_count"] == 1
    assert [(n["title"], n["new"]) for n in later["notices"]] == [
        ("kuba left your game", True),
        ("It's a game! · 30 zł held", False),
    ]


async def test_a_notice_listed_after_the_visit_is_new_though_it_happened_before(
    client, booking, crowd, mailbox
):
    """Counted by when it reached the list, never by the instant of what it
    tells: the outbox delivers after the act, and a notice delivered after the
    visit was not on the list that was opened."""

    ola, kuba = crowd[:2]
    await the_list(client, mailbox, ola)

    await leaves(client, kuba, booking)  # not delivered yet
    await opens_the_list(client, ola)
    after = await the_list(client, mailbox, ola)

    assert after["new_count"] == 1
    assert after["notices"][0]["title"] == "kuba left your game"
    assert after["notices"][0]["new"] is True


async def test_two_phones_signed_in_as_one_player_read_one_number(
    client, booking, crowd, mailbox
):
    ola = crowd[0]
    other = await another_phone(client, ola)

    assert (await the_list(client, mailbox, ola))["new_count"] == 1
    assert (await the_list(client, mailbox, other))["new_count"] == 1

    await opens_the_list(client, other)

    assert (await the_list(client, mailbox, ola))["new_count"] == 0
    visit = (await the_list(client, mailbox, other))["last_opened_at"]

    # The phone that opened it signs out; a new one reads the same visit.
    signed_out = await client.post(
        "/api/v1/auth/logout", json={"refresh_token": other["refresh_token"]}
    )
    assert signed_out.status_code == 200, signed_out.text
    new_phone = await the_list(client, mailbox, await another_phone(client, ola))
    assert (new_phone["new_count"], new_phone["last_opened_at"]) == (0, visit)


async def test_the_number_is_exact_past_the_thirty_rows_sent(
    client, session_factory, clock, club, group, crowd, mailbox
):
    zosia = crowd[4]
    at = clock.now()
    async with session_factory() as session:
        days = build_notice_day_repository(session)
        day = await days.load(zosia["id"], local_day(at))
        for n in range(105):
            day.give(
                Notice(
                    kind=NoticeKind.SOMEONE_LEFT,
                    key=f"{NoticeKind.SOMEONE_LEFT}:{n}",
                    game_id=new_uuid(),
                    pool_id=group,
                    sport=Sport.PADEL,
                    game_kind="COMPETITIVE",
                    club_id=UUID(club),
                    starts_at=instant(SATURDAY_FIVE),
                    opens=Opens.BOOKING,
                    people=(crowd[1]["id"],),
                    reason=NoticeReason.SEAT_OPEN,
                ),
                at=at,
            )
        await days.save(day)
        await session.commit()

    read = await the_list(client, mailbox, zosia)

    # The phone writes 99+; the server says how many.
    assert (len(read["notices"]), read["new_count"]) == (30, 105)


async def test_the_filler_s_own_notice_is_theirs_and_never_counted_or_pushed(
    client, booking, crowd, mailbox, pushes
):
    """Tomek's yes filled the game, and his phone said *It's a game!*: his
    notice is in his list, marked his own, and the bell does not count it. The
    other three's copies are news to them."""

    tomek = crowd[3]

    filler = await the_list(client, mailbox, tomek)
    [own] = filler["notices"]
    assert (own["kind"], own["your_own"], own["new"]) == ("GAME_BOOKED", True, False)
    assert filler["new_count"] == 0
    assert await pushed_to(mailbox, pushes, tomek) == []

    for player in crowd[:3]:
        others = await the_list(client, mailbox, player)
        [theirs] = others["notices"]
        assert (theirs["your_own"], theirs["new"], others["new_count"]) == (
            False,
            True,
            1,
        )


async def test_opening_the_list_again_or_with_a_clock_behind_never_moves_back(
    client, clock, booking, crowd, mailbox
):
    ola = crowd[0]
    await opens_the_list(client, ola)
    first = (await the_list(client, mailbox, ola))["last_opened_at"]

    await opens_the_list(client, ola)
    clock.move(timedelta(hours=-1))
    await opens_the_list(client, ola)

    assert (await the_list(client, mailbox, ola))["last_opened_at"] == first
    clock.move(timedelta(hours=2))
    await opens_the_list(client, ola)
    assert (await the_list(client, mailbox, ola))["last_opened_at"] > first


async def test_a_notice_a_later_one_was_bundled_into_is_new_again(
    client, session_factory, clock, club, group, crowd, mailbox
):
    """It moved up the list because it says more than it did."""

    ola, kuba, ewa, tomek = crowd[:4]
    for start in (SATURDAY_FIVE, warsaw(10, 18)):
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
        if start == SATURDAY_FIVE:
            assert (await the_list(client, mailbox, tomek))["new_count"] == 1
            await opens_the_list(client, tomek)
            assert (await the_list(client, mailbox, tomek))["new_count"] == 0
            clock.move(timedelta(minutes=5))

    read = await the_list(client, mailbox, tomek)
    [bundled] = read["notices"]
    assert (bundled["title"], bundled["gathered"], bundled["new"]) == (
        "2 games need only you",
        1,
        True,
    )
    assert read["new_count"] == 1
