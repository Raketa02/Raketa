"""**On request: the club confirms** (#543; the mechanics §13, §14.1, §16.3,
§16.8, §16.12, §16.16; the screens B2, B4).

At an On request club a full game waits for the club's answer: the court is
held, the club is emailed, and **nobody pays until it accepts**. Accept charges
everybody all together or not at all and books the held court; Refuse — or no
answer by the club's time to confirm — calls it off with nobody paid, and the
same players are dealt a new card first. A player leaving while it waits
withdraws their yes and the request with it, and the game is back in the decks.

Every act is taken over HTTP as the phone and the desk take it, against the
fake payment provider, and every claim is read where somebody would read it:
Home, the details, the club's list, the mailbox, the deck — and what the club
still sells, through the port the proposer reads.

The clock stands on **Monday 5 October 2026, 08:00 in Kraków**; the game is
**Saturday 10 October, 17:00** at Bonarka Arena — On request, one padel court
at 120 zł (30 zł a seat), thirty minutes to confirm.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy import select

from app.api.dependencies import get_clock
from app.bootstrap.composition import (
    build_court_hours,
    build_expire_unanswered_requests,
    build_propose_games,
)
from app.core.config import get_settings
from app.kernel import Sport
from app.modules.conversations.infrastructure.conversation_model import (
    ConversationORM,
)
from app.modules.proposals.application.propose_games import Proposed
from tests.api import players_world as players
from tests.api.proposals_world import (
    MONDAY_MORNING,
    SATURDAY_FIVE,
    a_club_and_its_desk,
    a_club_selling,
    a_group,
    a_member,
    a_player,
    live_ids,
    makes,
    says_yes,
    sweeps,
    the_cut_off_comes,
    warsaw,
    withdraws,
)
from tests.unit.fake_clock import MovableClock

HOME = "/api/v1/home"
WAITING = "/api/v1/club/bookings/waiting"
RECEIPTS = "/api/v1/players/me/receipts"
DESK_EMAIL = "desk@bonarka.pl"
#: The deadline: thirty minutes from the last yes on Monday morning.
ANSWER_BY = MONDAY_MORNING + timedelta(minutes=30)
#: The same moment as the players' reads carry it: 08:30 in Kraków, in UTC.
ANSWER_BY_ON_THE_WIRE = "2026-10-05T06:30:00Z"
#: Saturday evenings, 17:00–19:00.
SATURDAY_EVENINGS = [{"day": 6, "hour": hour} for hour in (17, 18)]


@pytest.fixture
def clock(app):
    """Monday 5 October 2026, 08:00 in Kraków."""

    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


@pytest.fixture
async def on_request(client) -> tuple[str, dict]:
    """Bonarka Arena, On request: the club and its desk's session."""

    return await a_club_and_its_desk(client, way="ON_REQUEST")


@pytest.fixture
async def four(client, payments) -> list[dict]:
    """Ola, Kuba, Ewa and Tomek: rated in padel, each with a card that pays."""

    return [
        await a_player(client, payments, name)
        for name in ("ola", "kuba", "ewa", "tomek")
    ]


async def a_full_game(
    client, session_factory, clock, *, club: str, four: list[dict]
) -> UUID:
    """The four's game at the club on Saturday at 17:00, every one of them In —
    the last yes answered *waiting for the club*."""

    group = await a_group(client, four[0], club, *four[1:])
    proposal = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    for player in four[:3]:
        said = await says_yes(client, player, proposal)
        assert said.status_code == 200, said.text
    last = await says_yes(client, four[3], proposal)
    assert last.status_code == 200, last.text
    assert last.json()["waiting_for_the_club"] is True, last.text
    return proposal


async def home_of(client, player: dict) -> list[dict]:
    read = await client.get(HOME, headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()["games"]


async def the_card(client, player: dict) -> dict:
    [card] = await home_of(client, player)
    return card


async def falls_back_on_the_home_of(client, player: dict, proposal: UUID) -> int:
    """The game, gone back to filling, on the player's Home as *Seat open* —
    nobody paid (#624, Q106). How many seats are open."""

    [card] = await home_of(client, player)
    assert card["booking_id"] == str(proposal)
    assert (card["status"], card["filling_again"]) == ("SEAT_OPEN", True)
    assert card["money"]["paid"] is False
    return card["open_seats"]


async def waiting_at(client, desk: dict) -> list[dict]:
    read = await client.get(WAITING, headers=desk)
    assert read.status_code == 200, read.text
    return read.json()["bookings"]


async def accepts(client, desk: dict, booking: UUID):
    return await client.post(
        f"/api/v1/club/bookings/{booking}/acceptance", headers=desk
    )


async def refuses(client, desk: dict, booking: UUID, reason: str | None = None):
    return await client.post(
        f"/api/v1/club/bookings/{booking}/refusal",
        json={"reason": reason},
        headers=desk,
    )


async def details_of(client, player: dict, proposal: UUID) -> dict:
    read = await client.get(f"/api/v1/proposals/{proposal}", headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()


async def booking_details_of(client, player: dict, booking: UUID) -> dict:
    read = await client.get(f"/api/v1/bookings/{booking}", headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()


async def answer_by_of(client, player: dict, proposal: UUID) -> dict[str, str | None]:
    """When each of the player's three reads of the game says the club must
    answer: Home's card, the booking's details and the proposal's."""

    [card] = [
        card
        for card in await home_of(client, player)
        if card["booking_id"] == str(proposal)
    ]
    booking = await booking_details_of(client, player, proposal)
    details = await details_of(client, player, proposal)
    return {
        "home card": card["answer_by"],
        "booking details": booking["answer_by"],
        "proposal details": details["answer_by"],
    }


def in_every_read(answer_by: str | None) -> dict[str, str | None]:
    return {
        "home card": answer_by,
        "booking details": answer_by,
        "proposal details": answer_by,
    }


async def the_court_is_on_sale(session_factory, clock, club: str) -> bool:
    """Whether a padel court at the club on Saturday at 17:00 is for sale."""

    async with session_factory() as session:
        offered = await build_court_hours(session).offered(
            UUID(club), sport=Sport.PADEL, start=SATURDAY_FIVE, now=clock.now()
        )
    return offered is not None


async def times_out(session_factory, clock):
    async with session_factory() as session:
        return await build_expire_unanswered_requests(
            session, clock=clock, settings=get_settings()
        ).execute()


async def receipts(client, player: dict) -> list[dict]:
    read = await client.get(RECEIPTS, headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()["receipts"]


# --------------------------------------------------------------------------- #
# Waiting for the club
# --------------------------------------------------------------------------- #


async def test_a_full_game_waits_for_the_club_and_nobody_is_charged(
    client, session_factory, clock, payments, on_request, four
):
    club, _ = on_request

    proposal = await a_full_game(client, session_factory, clock, club=club, four=four)

    assert payments.called("authorise") == []
    for player in four:
        card = await the_card(client, player)
        assert card["booking_id"] == str(proposal)
        assert card["status"] == "WAITING_FOR_THE_CLUB"
        assert (card["game_id"], card["court_name"]) == (None, None)
        assert card["called_off_reason"] is None
        assert card["money"] == {
            "share_grosze": 30_00,
            "paid": False,
            "free_to_leave_until": None,
            "share_state": None,
            "taken_at": None,
            "refunded_grosze": None,
        }
        assert not any(
            tile["paid"] for tile in (*card["sides"]["yours"], *card["sides"]["theirs"])
        )
        # Still a yes of theirs that has not filled: You're In's amber row.
        assert await live_ids(client, player) == [str(proposal)]
        assert await receipts(client, player) == []
    details = await details_of(client, four[0], proposal)
    assert details["status"] == "WAITING_FOR_THE_CLUB"
    assert details["actions"] == ["LEAVE"]


async def test_the_hour_stays_held_for_the_club_s_answer(
    client, session_factory, clock, on_request, four
):
    club, _ = on_request
    assert await the_court_is_on_sale(session_factory, clock, club)

    await a_full_game(client, session_factory, clock, club=club, four=four)

    # Nobody else is offered that court while the club decides.
    assert not await the_court_is_on_sale(session_factory, clock, club)


async def test_the_club_is_emailed_at_once_with_the_countdown(
    client, session_factory, clock, mailbox, on_request, four
):
    club, _ = on_request

    await a_full_game(client, session_factory, clock, club=club, four=four)

    [email] = await mailbox.to(DESK_EMAIL)
    assert email.subject == "A booking is waiting for your answer"
    assert "Padel at Bonarka Arena, Court 1 — Saturday 10 October, 17:00" in email.text
    assert "120 zł for the court" in email.text
    assert "Answer by Monday 5 October, 08:30" in email.text
    assert "/overview" in email.text
    # Nobody paid, so nobody is told they did.
    for name in ("ola", "kuba", "ewa", "tomek"):
        assert await mailbox.to(f"{name}@example.com") == []


async def test_the_players_read_when_the_club_must_answer(
    client, session_factory, clock, mailbox, on_request, four
):
    """*Bonarka Arena answers by 08:30* — the moment the desk's email names,
    on Home's card, the booking's details and the proposal's (Q98)."""

    club, _ = on_request

    proposal = await a_full_game(client, session_factory, clock, club=club, four=four)

    [email] = await mailbox.to(DESK_EMAIL)
    assert "Answer by Monday 5 October, 08:30" in email.text
    for player in four:
        assert await answer_by_of(client, player, proposal) == in_every_read(
            ANSWER_BY_ON_THE_WIRE
        )


async def test_a_game_still_filling_has_no_answer_to_wait_for(
    client, session_factory, clock, on_request, four
):
    club, _ = on_request
    group = await a_group(client, four[0], club, *four[1:])
    proposal = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    for player in four[:3]:
        await says_yes(client, player, proposal)

    details = await details_of(client, four[0], proposal)

    assert (details["status"], details["answer_by"]) == ("FILLING", None)


@pytest.mark.parametrize(("answers", "answered_with"), [(accepts, 200), (refuses, 204)])
async def test_once_the_club_answers_the_reads_no_longer_say_when(
    answers, answered_with, client, session_factory, clock, on_request, four
):
    """The booking keeps the moment; the players stop reading it."""

    club, desk = on_request
    proposal = await a_full_game(client, session_factory, clock, club=club, four=four)

    answered = await answers(client, desk, proposal)

    assert answered.status_code == answered_with, answered.text
    assert await answer_by_of(client, four[0], proposal) == in_every_read(None)


async def test_from_the_deadline_on_the_reads_no_longer_say_it(
    client, session_factory, clock, on_request, four
):
    """From 08:30 the club can no longer say yes: the game still waits for the
    timeout to call it off, and the line says only *nobody pays until Bonarka
    Arena confirms* (Q98) — as *free to leave until* leaves at the cut-off."""

    club, _ = on_request
    proposal = await a_full_game(client, session_factory, clock, club=club, four=four)
    clock.move(timedelta(minutes=29))
    assert await answer_by_of(client, four[0], proposal) == in_every_read(
        ANSWER_BY_ON_THE_WIRE
    )

    clock.move(timedelta(minutes=1))

    assert (await the_card(client, four[0]))["status"] == "WAITING_FOR_THE_CLUB"
    assert await answer_by_of(client, four[0], proposal) == in_every_read(None)
    assert (await times_out(session_factory, clock)).requests == 1
    assert await answer_by_of(client, four[0], proposal) == in_every_read(None)


async def test_an_instant_club_leaves_no_answer_to_wait_for(
    client, session_factory, clock, payments, four
):
    club = await a_club_selling(client)
    group = await a_group(client, four[0], club, *four[1:])
    proposal = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    for player in four:
        said = await says_yes(client, player, proposal)
        assert said.status_code == 200, said.text
    assert said.json()["booked"] is not None

    assert await answer_by_of(client, four[0], proposal) == in_every_read(None)


async def test_the_club_lists_what_waits_for_its_answer_and_no_other_club_does(
    client, session_factory, clock, on_request, four
):
    club, desk = on_request
    _, elsewhere = await a_club_and_its_desk(client, name="Ogrody 33")
    proposal = await a_full_game(client, session_factory, clock, club=club, four=four)

    [booking] = await waiting_at(client, desk)

    assert booking["booking_id"] == str(proposal)
    assert (booking["sport"], booking["kind"]) == ("PADEL", "COMPETITIVE")
    assert datetime.fromisoformat(booking["starts_at"]) == SATURDAY_FIVE
    assert booking["court_name"] == "Court 1"
    assert (booking["price_grosze"], booking["share_grosze"]) == (120_00, 30_00)
    assert datetime.fromisoformat(booking["answer_by"]) == ANSWER_BY
    assert sorted(player["name"] for player in booking["players"]) == [
        "ewa",
        "kuba",
        "ola",
        "tomek",
    ]
    assert await waiting_at(client, elsewhere) == []
    refused = await accepts(client, elsewhere, proposal)
    assert refused.status_code == 404
    assert refused.json()["code"] == "booking_not_found"


async def test_a_player_cannot_answer_for_the_club(
    client, session_factory, clock, on_request, four
):
    club, _ = on_request
    proposal = await a_full_game(client, session_factory, clock, club=club, four=four)

    refused = await accepts(client, four[0]["headers"], proposal)

    assert refused.status_code == 401


# --------------------------------------------------------------------------- #
# Accept
# --------------------------------------------------------------------------- #


async def test_accepting_holds_everybody_together_and_books_the_held_court(
    client, session_factory, clock, payments, mailbox, on_request, four
):
    club, desk = on_request
    proposal = await a_full_game(client, session_factory, clock, club=club, four=four)
    clock.move(timedelta(minutes=10))

    accepted = await accepts(client, desk, proposal)

    assert accepted.status_code == 200, accepted.text
    assert accepted.json() == {
        "outcome": "BOOKED",
        "court_name": "Court 1",
        "payment_due_by": None,
    }
    assert len(payments.called("authorise")) == 4
    await mailbox.drain()
    # Held until the cut-off, which takes them (#637).
    assert payments.called("capture") == []
    for player in four:
        card = await the_card(client, player)
        assert card["status"] == "BOOKED"
        assert card["game_id"] is not None
        assert card["court_name"] == "Court 1"
        assert card["money"]["share_state"] == "HELD"
    await the_cut_off_comes(session_factory, clock)
    await mailbox.drain()
    assert len(payments.called("capture")) == 4
    for player in four:
        assert (await the_card(client, player))["money"]["paid"] is True
        [receipt] = await receipts(client, player)
        assert receipt["amount_grosze"] == 30_00
        assert await live_ids(client, player) == []
    assert await waiting_at(client, desk) == []
    assert (await details_of(client, four[0], proposal))["status"] == "FILLED"
    assert not await the_court_is_on_sale(session_factory, clock, club)
    # *It's a game! · 30 zł held*, to each.
    [email] = await mailbox.to("ola@example.com")
    assert email.subject == "It's a game! · 30 zł held"


async def test_the_chat_opens_when_the_club_says_yes_and_not_before(
    client, session_factory, clock, mailbox, on_request, four
):
    club, desk = on_request
    proposal = await a_full_game(client, session_factory, clock, club=club, four=four)
    await mailbox.drain()

    async def the_room():
        async with session_factory() as session:
            return await session.scalar(
                select(ConversationORM.conversation_id).where(
                    ConversationORM.booking_id == proposal
                )
            )

    assert await the_room() is None
    await accepts(client, desk, proposal)
    await mailbox.drain()
    assert await the_room() is not None


# --------------------------------------------------------------------------- #
# Refuse, and no answer
# --------------------------------------------------------------------------- #


async def test_refusing_calls_it_off_nobody_paid_and_the_hour_is_the_club_s_again(
    client, session_factory, clock, payments, on_request, four
):
    club, desk = on_request
    proposal = await a_full_game(client, session_factory, clock, club=club, four=four)

    refused = await refuses(client, desk, proposal, reason="The desk sold it")

    assert refused.status_code == 204, refused.text
    assert payments.called("authorise") == []
    for player in four:
        card = await the_card(client, player)
        assert (card["status"], card["called_off_reason"]) == ("CALLED_OFF", "REFUSED")
        assert card["money"]["paid"] is False
        assert card["game_id"] is None
        assert await live_ids(client, player) == []
    details = await details_of(client, four[0], proposal)
    assert (details["status"], details["actions"]) == ("TURNED_DOWN", [])
    assert await waiting_at(client, desk) == []
    assert await the_court_is_on_sale(session_factory, clock, club)
    # The club's note is its own: no player reads it.
    home = await client.get(HOME, headers=four[0]["headers"])
    assert "The desk sold it" not in home.text


async def test_an_answered_request_is_answered_once(
    client, session_factory, clock, on_request, four
):
    club, desk = on_request
    proposal = await a_full_game(client, session_factory, clock, club=club, four=four)
    await refuses(client, desk, proposal)

    again = await refuses(client, desk, proposal)
    late_yes = await accepts(client, desk, proposal)

    for answer in (again, late_yes):
        assert answer.status_code == 409
        assert answer.json()["code"] == "request_not_waiting"


async def test_a_refusal_needs_no_reason(
    client, session_factory, clock, on_request, four
):
    club, desk = on_request
    proposal = await a_full_game(client, session_factory, clock, club=club, four=four)

    refused = await client.post(
        f"/api/v1/club/bookings/{proposal}/refusal", headers=desk
    )

    assert refused.status_code == 204, refused.text


async def test_no_answer_by_the_deadline_calls_it_off(
    client, session_factory, clock, payments, on_request, four
):
    club, desk = on_request
    proposal = await a_full_game(client, session_factory, clock, club=club, four=four)
    clock.move(timedelta(minutes=29))
    assert (await times_out(session_factory, clock)).requests == 0

    clock.move(timedelta(minutes=1))

    # Past the deadline the club can no longer answer, recorded or not …
    late = await accepts(client, desk, proposal)
    assert late.status_code == 409
    assert late.json()["code"] == "request_timed_out"
    assert await waiting_at(client, desk) == []
    # … and the job calls it off.
    done = await times_out(session_factory, clock)
    assert (done.requests, done.conflicts) == (1, 0)
    assert (await times_out(session_factory, clock)).requests == 0
    for player in four:
        card = await the_card(client, player)
        assert (card["status"], card["called_off_reason"]) == (
            "CALLED_OFF",
            "NO_ANSWER",
        )
    assert payments.called("authorise") == []
    assert await the_court_is_on_sale(session_factory, clock, club)
    assert (await details_of(client, four[0], proposal))["status"] == "TURNED_DOWN"


async def test_the_players_a_club_turned_down_are_dealt_a_new_card_first_elsewhere(
    client, session_factory, clock, payments
):
    club, desk = await a_club_and_its_desk(
        client, way="ON_REQUEST", hours=[(6, 17), (6, 18)]
    )
    crowd = [
        await a_member(client, session_factory, payments, name, week=SATURDAY_EVENINGS)
        for name in ("ola", "kuba", "ewa", "tomek")
    ]
    group = await a_group(client, crowd[0], club, *crowd[1:])
    await proposes(session_factory, clock, group)
    [card] = await deck_of(client, crowd[0], group)
    turned_down = UUID(card["proposal_id"])
    assert datetime.fromisoformat(card["starts_at"]) == warsaw(10, 17)
    for player in crowd:
        assert (await says_yes(client, player, turned_down)).status_code == 200
    assert (await refuses(client, desk, turned_down)).status_code == 204

    proposed = await proposes(session_factory, clock, group)

    assert (proposed.redealt, proposed.made) == (1, 1)
    [again] = await deck_of(client, crowd[0], group)
    # The four together, at the nearest hour they are all free — never the
    # club's 17:00, which it refused, though it sells it again.
    assert datetime.fromisoformat(again["starts_at"]) == warsaw(10, 18)
    assert {
        tile["name"] for tile in (*again["sides"]["yours"], *again["sides"]["theirs"])
    } == {"ola", "kuba", "ewa", "tomek"}
    assert again["in_count"] == 0
    assert (await proposes(session_factory, clock, group)).redealt == 0


# --------------------------------------------------------------------------- #
# Leaving while it waits
# --------------------------------------------------------------------------- #


async def test_leaving_while_it_waits_withdraws_the_yes_and_the_request(
    client, session_factory, clock, payments, on_request, four
):
    club, desk = on_request
    proposal = await a_full_game(client, session_factory, clock, club=club, four=four)
    kuba = four[1]

    left = await withdraws(client, kuba, proposal)

    assert left.status_code == 204, left.text
    assert payments.called("authorise") == []
    assert await home_of(client, kuba) == []
    assert await live_ids(client, kuba) == []
    for player in (four[0], *four[2:]):
        # The request is taken back; still In, they find the game back in the
        # decks with Kuba's seat open — and on their Home as *Seat open*.
        assert await falls_back_on_the_home_of(client, player, proposal) == 1
        assert await live_ids(client, player) == [str(proposal)]
    details = await details_of(client, four[0], proposal)
    assert (details["status"], details["in_count"]) == ("FILLING", 3)
    assert await waiting_at(client, desk) == []
    assert await the_court_is_on_sale(session_factory, clock, club)
    refused = await accepts(client, desk, proposal)
    assert refused.status_code == 409
    assert refused.json()["code"] == "request_not_waiting"


async def test_full_again_the_same_game_asks_the_club_again(
    client, session_factory, clock, mailbox, on_request, four
):
    club, desk = on_request
    proposal = await a_full_game(client, session_factory, clock, club=club, four=four)
    await withdraws(client, four[1], proposal)
    assert (await details_of(client, four[0], proposal))["answer_by"] is None
    clock.move(timedelta(minutes=5))

    again = await says_yes(client, four[1], proposal)

    assert again.json()["waiting_for_the_club"] is True
    [booking] = await waiting_at(client, desk)
    assert booking["booking_id"] == str(proposal)
    assert datetime.fromisoformat(booking["answer_by"]) == ANSWER_BY + timedelta(
        minutes=5
    )
    for player in four:
        assert (await the_card(client, player))["status"] == "WAITING_FOR_THE_CLUB"
        # The new deadline, 08:35 in Kraków — never the first one.
        assert await answer_by_of(client, player, proposal) == in_every_read(
            "2026-10-05T06:35:00Z"
        )
    assert len(await mailbox.to(DESK_EMAIL)) == 2
    accepted = await accepts(client, desk, proposal)
    assert accepted.json()["outcome"] == "BOOKED"


async def test_leaving_the_group_while_it_waits_takes_the_request_with_the_yes(
    client, session_factory, clock, on_request, four
):
    club, desk = on_request
    proposal = await a_full_game(client, session_factory, clock, club=club, four=four)
    group = (await details_of(client, four[0], proposal))["pool_id"]

    left = await client.delete(
        f"/api/v1/groups/{group}/membership", headers=four[2]["headers"]
    )
    assert left.status_code in (200, 204), left.text
    await players.deliver_the_outbox(session_factory)

    assert await waiting_at(client, desk) == []
    assert await home_of(client, four[2]) == []
    assert await falls_back_on_the_home_of(client, four[0], proposal) == 1


async def test_one_game_per_hour_takes_a_waiting_game_s_request_with_the_yes(
    client, session_factory, clock, payments, on_request, four
):
    """Ola is In on the On request game and on another at the same hour at an
    Instant club; the other books first, and her yes on the waiting one goes —
    with its request."""

    club, desk = on_request
    waiting = await a_full_game(client, session_factory, clock, club=club, four=four)
    instant_club = await a_club_selling(client, name="Ogrody 33")
    others = [
        await a_player(client, payments, name) for name in ("ania", "piotr", "marek")
    ]
    group = await a_group(client, four[0], instant_club, *others)
    elsewhere = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=instant_club,
        versions=((four[0], *others),),
    )
    for player in (*others, four[0]):
        said = await says_yes(client, player, elsewhere)
        assert said.status_code == 200, said.text
    assert said.json()["booked"] is not None

    assert await waiting_at(client, desk) == []
    assert await the_court_is_on_sale(session_factory, clock, club)
    assert await falls_back_on_the_home_of(client, four[1], waiting) == 1
    assert str(waiting) not in await live_ids(client, four[0])


# --------------------------------------------------------------------------- #
# The book-by
# --------------------------------------------------------------------------- #


async def test_a_game_that_filled_in_time_outlives_its_book_by_while_the_club_decides(
    client, session_factory, clock, on_request, four
):
    """Saturday's book-by is 15:00 (two hours' notice). The last yes lands at
    14:50, so the club's answer is due at 15:20 — and at 15:10 the game is still
    waiting, and the club may still say yes."""

    club, desk = on_request
    group = await a_group(client, four[0], club, *four[1:])
    proposal = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    for player in four[:3]:
        await says_yes(client, player, proposal)
    clock.move(warsaw(10, 14) + timedelta(minutes=50) - clock.now())
    last = await says_yes(client, four[3], proposal)
    assert last.json()["waiting_for_the_club"] is True, last.text
    clock.move(timedelta(minutes=20))

    swept = await sweeps(session_factory, clock)

    assert swept.proposals == 0
    assert (await the_card(client, four[0]))["status"] == "WAITING_FOR_THE_CLUB"
    assert await live_ids(client, four[0]) == [str(proposal)]
    accepted = await accepts(client, desk, proposal)
    assert accepted.json()["outcome"] == "BOOKED", accepted.text


# --------------------------------------------------------------------------- #
# Helpers the proposer's tests share
# --------------------------------------------------------------------------- #


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
