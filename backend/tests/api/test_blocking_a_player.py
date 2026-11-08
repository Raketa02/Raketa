"""**A block keeps two people off one court** (``docs/adr/0193``; PRD #571).

Ola and Kuba play padel with the same group. Ola blocks Kuba. From that moment:

- **Ola's yeses where Kuba is In are taken back** (§4) — on a game still
  filling by the ordinary *Withdraw*, picks and posts alike, and on a full game
  waiting for one payment as if she left it, so the others In are told she
  left.
  Kuba's yes stands. A booked game is never touched.
- **No later yes puts them together** (§1), whichever of them says it.
- **Ola sees her block** — on *Blocked players* (§3) — **and Kuba sees
  nothing**: every read he can make is the bytes it was, but for a seat a
  withdrawal opened. **Neither opens the other's record** (``docs/adr/0203``
  §8, #773): the record answers the one refusal it answers anybody.
- **Unblocking is immediate and brings no yes back**, and a second block or a
  second unblock records nothing.

Every act is taken over HTTP as the phone takes it, and the withdrawal lands
when the outbox delivers the block — as a group leaver's does.

The clock stands on **Monday 5 October 2026, 08:00 in Kraków**; the game is
**Saturday 10 October, 17:00** at Bonarka Arena.
"""

from __future__ import annotations

from uuid import UUID

import pytest
from sqlalchemy import select

from app.api.dependencies import get_clock
from app.infrastructure.events.event_store_model import EventStoreORM
from app.modules.blocks.domain.ids import block_id
from app.modules.payments.domain.entered_cards import A_CARD_THE_BANK_ALWAYS_CHECKS
from tests.api import players_world as players
from tests.api.proposals_world import (
    MONDAY_MORNING,
    a_club_selling,
    a_group,
    a_member,
    a_player,
    live_ids,
    makes,
    says_yes,
    warsaw,
    withdraws,
)
from tests.unit.fake_clock import MovableClock

GROUPS = "/api/v1/groups"
HOME = "/api/v1/home"
NOTICES = "/api/v1/players/me/notices"
SATURDAY_SEVEN = warsaw(10, 19)


@pytest.fixture
def clock(app):
    """Monday 5 October 2026, 08:00 in Kraków."""

    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


@pytest.fixture
async def four(client, payments) -> list[dict]:
    """Ola, Kuba, Ewa and Tomek: rated in padel, each with a card."""

    return [
        await a_player(client, payments, name)
        for name in ("ola", "kuba", "ewa", "tomek")
    ]


@pytest.fixture
async def club(client) -> str:
    return await a_club_selling(client)


@pytest.fixture
async def group(client, club, four) -> UUID:
    return await a_group(client, four[0], club, *four[1:])


async def blocks(client, blocker: dict, blocked: dict) -> None:
    answered = await players.block_between(client, blocker["token"], blocked["id"])
    assert answered.status_code == 204, answered.text


async def unblocks(client, blocker: dict, blocked: dict) -> None:
    answered = await client.delete(
        f"/api/v1/blocks/{blocked['id']}", headers=blocker["headers"]
    )
    assert answered.status_code == 204, answered.text


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


async def details_of(client, player: dict, proposal: UUID) -> dict:
    read = await client.get(f"/api/v1/proposals/{proposal}", headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()


async def notices_of(client, mailbox, player: dict) -> list[dict]:
    await mailbox.drain()
    read = await client.get(NOTICES, headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()["notices"]


def every_key(payload) -> list[str]:
    if isinstance(payload, dict):
        return [
            name for key, value in payload.items() for name in (key, *every_key(value))
        ]
    if isinstance(payload, list):
        return [name for one in payload for name in every_key(one)]
    return []


# --------------------------------------------------------------------------- #
# A game still filling: the blocker's yes is taken back
# --------------------------------------------------------------------------- #


async def test_blocking_takes_back_my_yes_where_they_are_in_on_a_pick(
    client, session_factory, clock, mailbox, club, four, group
):
    """Only where Kuba is **In**: a pick he was merely dealt keeps Ola's yes,
    and Kuba's own yes stands."""

    ola, kuba, ewa = four[0], four[1], four[2]
    with_him = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    dealt_him = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=SATURDAY_SEVEN,
        versions=(tuple(four),),
    )
    for player in (ola, kuba, ewa):
        assert (await says_yes(client, player, with_him)).status_code == 200
    for player in (ola, ewa):
        assert (await says_yes(client, player, dealt_him)).status_code == 200

    await blocks(client, ola, kuba)
    await mailbox.drain()

    assert await live_ids(client, ola) == [str(dealt_him)]
    assert await live_ids(client, kuba) == [str(with_him)]
    assert (await details_of(client, ewa, with_him))["in_count"] == 2
    assert (await events_of(session_factory, with_him)).count(
        "proposals.yes_withdrawn"
    ) == 1
    # A withdrawal from a game still filling tells nobody anything.
    for player in four:
        assert await notices_of(client, mailbox, player) == []


async def test_blocking_takes_back_my_yes_on_a_post_i_made_and_one_i_joined(
    client, session_factory, clock, mailbox, club, four, group
):
    """Posts alike (§4). Kuba is In on both, so neither ends: the game carries
    on without Ola, as when a poster withdraws with others In."""

    ola, kuba, ewa, tomek = four
    mine = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        poster=ola,
        versions=((kuba, ewa, tomek),),
    )
    his = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=SATURDAY_SEVEN,
        poster=kuba,
        versions=((ola, ewa, tomek),),
    )
    assert (await says_yes(client, kuba, mine)).status_code == 200
    assert (await says_yes(client, ola, his)).status_code == 200

    await blocks(client, ola, kuba)
    await mailbox.drain()

    assert await live_ids(client, ola) == []
    assert sorted(await live_ids(client, kuba)) == sorted([str(mine), str(his)])
    for post in (mine, his):
        assert (await details_of(client, kuba, post))["status"] == "FILLING"
        assert "proposals.proposal_withdrawn" not in await events_of(
            session_factory, post
        )


async def test_a_block_of_somebody_in_withdraws_nothing_of_theirs(
    client, session_factory, clock, mailbox, club, four, group
):
    """**Only the blocker's yeses** (§4): Kuba's yes on a game Ola is not In on
    is his, and her block takes nothing of his."""

    ola, kuba, ewa = four[0], four[1], four[2]
    pick = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    for player in (kuba, ewa):
        assert (await says_yes(client, player, pick)).status_code == 200

    await blocks(client, ola, kuba)
    await mailbox.drain()

    assert await live_ids(client, kuba) == [str(pick)]
    assert "proposals.yes_withdrawn" not in await events_of(session_factory, pick)


async def test_a_paused_yes_where_they_are_in_is_taken_back_too_and_never_resumes(
    client, session_factory, clock, mailbox, club, four, group
):
    """Ola plays one game a week, and Saturday's booking paused her Sunday yes.
    A paused yes is still hers: the block takes it back like a live one, so
    when her week frees after she unblocks, nothing comes back on her behalf
    (§4: *nothing reappears on the blocker's behalf*)."""

    ola, kuba = four[0], four[1]
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
    for player in (ola, kuba):
        assert (await says_yes(client, player, sunday)).status_code == 200
    saturday = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    for player in four:
        said = await says_yes(client, player, saturday)
        assert said.status_code == 200, said.text
    booking = said.json()["booked"]["booking_id"]
    await mailbox.drain()
    assert str(sunday) not in await live_ids(client, ola), "paused by the booking"

    await blocks(client, ola, kuba)
    await mailbox.drain()
    await unblocks(client, ola, kuba)
    left = await client.post(
        f"/api/v1/bookings/{booking}/departure", headers=ola["headers"]
    )
    assert left.status_code == 200, left.text
    await mailbox.drain()

    assert str(sunday) not in await live_ids(client, ola)
    assert await live_ids(client, kuba) == [str(sunday)]
    assert (await events_of(session_factory, sunday)).count(
        "proposals.yes_withdrawn"
    ) == 1


# --------------------------------------------------------------------------- #
# A booking: confirmed is never touched, waiting is left as if by hand
# --------------------------------------------------------------------------- #


async def test_a_booked_game_is_never_touched(
    client, session_factory, clock, mailbox, payments, club, four, group
):
    ola, kuba = four[0], four[1]
    pick = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    for player in four[:-1]:
        assert (await says_yes(client, player, pick)).status_code == 200
    last = await says_yes(client, four[-1], pick)
    assert last.json()["booked"] is not None, last.text
    await mailbox.drain()
    homes = {
        player["id"]: (await client.get(HOME, headers=player["headers"])).text
        for player in (ola, kuba)
    }
    written = await events_of(session_factory, pick)
    charged = len(payments.called("authorise"))

    await blocks(client, ola, kuba)
    await mailbox.drain()

    assert await events_of(session_factory, pick) == written
    for player in (ola, kuba):
        home = await client.get(HOME, headers=player["headers"])
        assert home.text == homes[player["id"]]
    assert len(payments.called("authorise")) == charged


async def test_a_game_waiting_for_a_payment_loses_my_place_as_if_i_left(
    client, session_factory, clock, mailbox, payments, club
):
    """Ruled 2026-10-06 (§4): Ewa's share was refused as the game filled, so it
    waits for her payment. Ola's yes is withdrawn, the game fills again with her
    seat open, nobody has paid, and the others In are told she left — the one
    notice a block causes, and it reads exactly like leaving."""

    ola, kuba, ewa, tomek = [
        await a_player(client, payments, "ola"),
        await a_player(client, payments, "kuba"),
        await a_player(client, payments, "ewa", entered=A_CARD_THE_BANK_ALWAYS_CHECKS),
        await a_player(client, payments, "tomek"),
    ]
    group = await a_group(client, ola, club, kuba, ewa, tomek)
    game = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        versions=((ola, kuba, ewa, tomek),),
    )
    for player in (ola, kuba, ewa, tomek):
        said = await says_yes(client, player, game)
        assert said.status_code == 200, said.text
    assert said.json()["payment_awaited_until"] is not None, said.text
    await mailbox.drain()

    await blocks(client, ola, kuba)
    await mailbox.drain()

    assert await live_ids(client, ola) == []
    assert await live_ids(client, kuba) == [str(game)]
    details = await details_of(client, kuba, game)
    assert (details["status"], details["in_count"]) == ("FILLING", 3)
    assert payments.called("capture") == []
    # Kuba and Tomek were told it was a game waiting for one payment; the
    # block adds one notice to them, and to Ewa, and Ola none.
    for player in (kuba, tomek):
        [notice, waiting] = await notices_of(client, mailbox, player)
        assert waiting["kind"] == "WAITING_FOR_A_PAYMENT"
        assert notice["kind"] == "SOMEONE_LEFT"
        assert notice["title"] == "ola left your game"
        assert "block" not in notice["title"].lower() + notice["body"].lower()
    [notice, *_] = await notices_of(client, mailbox, ewa)
    assert notice["title"] == "ola left your game"
    assert [n["kind"] for n in await notices_of(client, mailbox, ola)] == [
        "WAITING_FOR_A_PAYMENT"
    ]


# --------------------------------------------------------------------------- #
# No later yes puts them together
# --------------------------------------------------------------------------- #


async def test_a_later_yes_that_would_pair_them_is_refused_whoever_says_it(
    client, session_factory, clock, club, four, group
):
    """Both were dealt before the block, and nobody was In; a version naming
    them both is never dealt after it."""

    ola, kuba, ewa = four[0], four[1], four[2]
    hers = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    his = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=SATURDAY_SEVEN,
        versions=(tuple(four),),
    )
    await blocks(client, ola, kuba)
    assert (await says_yes(client, ola, hers)).status_code == 200
    assert (await says_yes(client, kuba, his)).status_code == 200

    refused = (
        await says_yes(client, kuba, hers),
        await says_yes(client, ola, his),
    )

    for answer in refused:
        assert answer.status_code == 409, answer.text
        assert answer.json()["code"] == "no_longer_fits"
        assert "details" not in answer.json()
    # Everybody else still gets in.
    assert (await says_yes(client, ewa, hers)).status_code == 200


async def test_neither_joins_the_other_s_post(
    client, session_factory, clock, payments, club
):
    """Joining a post from the sheet is a yes on a post never dealt to you, and
    the pair rule refuses it exactly as it refuses a dealt yes (§1) — while
    anybody else the post is open to still joins."""

    ola, kuba, ewa = [
        await a_member(client, session_factory, payments, name)
        for name in ("ola", "kuba", "ewa")
    ]
    group = await a_group(client, ola, club, kuba, ewa)
    hers = await makes(
        session_factory, clock, pool_id=group, club_id=club, poster=ola
    )
    his = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=SATURDAY_SEVEN,
        poster=kuba,
    )
    await blocks(client, ola, kuba)

    refused = (
        await says_yes(client, kuba, hers),
        await says_yes(client, ola, his),
    )

    for answer in refused:
        assert answer.status_code == 409, answer.text
        assert answer.json()["code"] == "no_longer_fits"
    assert (await says_yes(client, ewa, hers)).status_code == 200


# --------------------------------------------------------------------------- #
# Nothing the blocked player reads moves
# --------------------------------------------------------------------------- #


async def test_nothing_kuba_reads_names_the_block_or_moves_for_it(
    client, session_factory, clock, mailbox, club, four, group
):
    """Every read Kuba can make about Ola and their group is the bytes it was
    (§3). The one thing that moves is a seat on a game Ola was In on — and it
    moves as it would for a withdrawal by hand, naming nothing. **Ola's record
    closes to him**, as it does to her: the one refusal, which names no block
    (``docs/adr/0203`` §8)."""

    ola, kuba = four[0], four[1]
    pick = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    for player in (ola, kuba):
        assert (await says_yes(client, player, pick)).status_code == 200
    reads = (
        "/api/v1/users/me",
        "/api/v1/blocks",
        f"{GROUPS}/{group}",
        f"{GROUPS}/{group}/members?sport=PADEL",
        f"/api/v1/pools/{group}/fill-in?sport=PADEL",
        HOME,
        NOTICES,
    )

    async def what_kuba_reads() -> dict[str, str]:
        await mailbox.drain()
        answers = {}
        for path in reads:
            answer = await client.get(path, headers=kuba["headers"])
            assert answer.status_code == 200, (path, answer.text)
            answers[path] = answer.text
        return answers

    before = await what_kuba_reads()

    await blocks(client, ola, kuba)

    assert await what_kuba_reads() == before
    record = await client.get(
        f"/api/v1/players/{ola['id']}/record", headers=kuba["headers"]
    )
    assert record.status_code == 404, record.text
    assert record.json()["code"] == "record_unavailable"
    seen = await details_of(client, kuba, pick)
    assert seen["in_count"] == 1
    deck = await client.get(
        f"/api/v1/pools/{group}/deck",
        params={"sport": "PADEL", "kind": "COMPETITIVE"},
        headers=kuba["headers"],
    )
    assert deck.status_code == 200, deck.text
    for answer in (seen, deck.json()):
        assert not [key for key in every_key(answer) if "block" in key.lower()]


# --------------------------------------------------------------------------- #
# Unblocking, and doing either twice
# --------------------------------------------------------------------------- #


async def test_unblocking_is_immediate_and_brings_no_yes_back(
    client, session_factory, clock, mailbox, club, four, group
):
    ola, kuba = four[0], four[1]
    pick = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    for player in (ola, kuba):
        assert (await says_yes(client, player, pick)).status_code == 200
    await blocks(client, ola, kuba)
    await mailbox.drain()

    await unblocks(client, ola, kuba)
    await mailbox.drain()

    assert await live_ids(client, ola) == []
    record = await client.get(
        f"/api/v1/players/{kuba['id']}/record", headers=ola["headers"]
    )
    # The record opens again, the moment the block is lifted (#773).
    assert record.status_code == 200, record.text
    # Immediate: the same yes may be said again at once.
    again = await says_yes(client, ola, pick)
    assert again.status_code == 200, again.text
    assert await live_ids(client, ola) == [str(pick)]


async def test_a_block_lifted_before_it_was_delivered_still_took_the_yes_back(
    client, session_factory, clock, mailbox, club, four, group
):
    """The block was recorded, so its withdrawal is owed however soon it was
    lifted: what a block takes back never depends on how fast the outbox ran.
    Unblocking brings nothing back, whenever it came."""

    ola, kuba = four[0], four[1]
    pick = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    for player in (ola, kuba):
        assert (await says_yes(client, player, pick)).status_code == 200

    await blocks(client, ola, kuba)
    await unblocks(client, ola, kuba)
    await mailbox.drain()

    assert await live_ids(client, ola) == []


async def test_blocking_and_unblocking_twice_record_nothing_more(
    client, session_factory, clock, mailbox, club, four, group
):
    ola, kuba = four[0], four[1]
    pick = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    for player in (ola, kuba):
        assert (await says_yes(client, player, pick)).status_code == 200

    await blocks(client, ola, kuba)
    await mailbox.drain()
    listed = (await client.get("/api/v1/blocks", headers=ola["headers"])).text
    await blocks(client, ola, kuba)
    await mailbox.drain()

    stream = block_id(UUID(str(ola["id"])), UUID(str(kuba["id"])))
    assert await events_of(session_factory, stream) == ["blocks.player_blocked"]
    assert (await client.get("/api/v1/blocks", headers=ola["headers"])).text == listed
    assert (await events_of(session_factory, pick)).count(
        "proposals.yes_withdrawn"
    ) == 1

    await unblocks(client, ola, kuba)
    await unblocks(client, ola, kuba)

    assert await events_of(session_factory, stream) == [
        "blocks.player_blocked",
        "blocks.player_unblocked",
    ]


async def test_a_yes_withdrawn_by_hand_first_is_not_withdrawn_twice(
    client, session_factory, clock, mailbox, club, four, group
):
    ola, kuba = four[0], four[1]
    pick = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    for player in (ola, kuba):
        assert (await says_yes(client, player, pick)).status_code == 200
    assert (await withdraws(client, ola, pick)).status_code == 204

    await blocks(client, ola, kuba)
    await mailbox.drain()

    assert (await events_of(session_factory, pick)).count(
        "proposals.yes_withdrawn"
    ) == 1
