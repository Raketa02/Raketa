"""**The owed card: closest to the cancelled game first, and first in its players'
deck** (#673; the mechanics §8.2, §16.9, §17.2, Q123; ``docs/adr/0196`` §3).

Bonarka Arena cancels the four's Saturday 17:00 game, *Padel po pracy*, and no
court absorbs it. **The card they are dealt first is the closest game they all
fit**: Bonarka's outdoor court at 17:00, when only the kind of court changed —
the court the club cancelled is closed for the hour — or else Kazimierz Padel
at 17:00 at 25 zł, or else the closest hour. **It is first in each one's deck**,
ahead of the deck's usual order, and in nobody else's. *Your new game* opens the
deck on it, and the cancel notice already said *We'll look for another game
for you first*.

Every act is taken over HTTP as the club website and the phone take it,
against the fake payment provider; the proposer is run by its builder, as its
jobs run it; every claim is read where somebody would read it.

The clock stands on **Monday 5 October 2026, 08:00 in Kraków**. Bonarka Arena
sells padel on Saturday at 16:00 and 17:00 on Court 1, indoor — and, in most of
these worlds, on Court 4, outdoor — at 160 zł, 40 zł a seat; Kazimierz Padel,
a kilometre away, at 17:00 at 100 zł, 25 zł a seat. The group's members are
free on Saturday at 17:00, and at no other hour.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

import pytest

from app.api.dependencies import get_clock
from app.bootstrap.composition import build_propose_games
from app.modules.proposals.application.propose_games import Proposed
from tests.api.club_courts_world import adds_a_court, sets_hours
from tests.api.proposals_world import (
    MONDAY_MORNING,
    SATURDAY_FIVE,
    a_club_and_its_desk,
    a_group,
    a_member,
    makes,
    says_yes,
    warsaw,
)
from tests.unit.fake_clock import MovableClock

NOTICES = "/api/v1/players/me/notices"
HOME = "/api/v1/home"
SATURDAY_FOUR = warsaw(10, 16)
#: The hours both clubs could sell on Saturday.
SELLS = [(6, 16), (6, 17)]
#: The one hour the group's members are free.
FREE = [{"day": 6, "hour": 17}]
PROMISE = "We'll look for another game for you first."


@pytest.fixture
def clock(app):
    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


async def a_world(client, session_factory, payments, *, outdoor_court: bool = True):
    """Bonarka Arena — Court 1, and Court 4 outdoor unless told otherwise —
    Kazimierz Padel close by, and the group: Ola, Kuba, Ewa and Tomek, who
    book Saturday's 17:00, and Zosia and Marek."""

    bonarka, desk = await a_club_and_its_desk(
        client, name="Bonarka Arena", hours=SELLS, padel_grosze=160_00
    )
    if outdoor_court:
        court_4 = await adds_a_court(
            client, desk, name="Court 4", sport="PADEL", indoor=False
        )
        await sets_hours(client, desk, [court_4["id"]], SELLS)
    kazimierz, _ = await a_club_and_its_desk(
        client,
        name="Kazimierz Padel",
        point=(50.05, 19.94),
        hours=[(6, 17)],
        padel_grosze=100_00,
    )
    people = {
        name: await a_member(client, session_factory, payments, name, week=FREE)
        for name in ("ola", "kuba", "ewa", "tomek", "zosia", "marek")
    }
    group = await a_group(
        client, people["ola"], bonarka, *(people[name] for name in list(people)[1:])
    )
    return {
        "bonarka": bonarka,
        "desk": desk,
        "kazimierz": kazimierz,
        "people": people,
        "group": group,
    }


def the_four(world) -> list[dict]:
    return [world["people"][name] for name in ("ola", "kuba", "ewa", "tomek")]


async def books_saturday(client, session_factory, clock, world) -> str:
    """The four's game at Bonarka on Saturday at 17:00, booked on Court 1."""

    four = the_four(world)
    game = await makes(
        session_factory,
        clock,
        pool_id=world["group"],
        club_id=world["bonarka"],
        versions=(tuple(four),),
    )
    for player in four:
        said = await says_yes(client, player, game)
        assert said.status_code == 200, said.text
    booked = said.json()["booked"]
    assert booked is not None, said.text
    return booked["booking_id"]


async def the_club_cancels(client, world, booking: str) -> None:
    cancelled = await client.post(
        f"/api/v1/club/bookings/{booking}/cancellation",
        json={"reason": "REPAIR"},
        headers=world["desk"],
    )
    assert cancelled.status_code == 200, cancelled.text
    # Court 1 is indoor, and Court 4 outdoor: no court absorbs it.
    assert cancelled.json()["outcome"] == "CALLED_OFF"


async def proposes(session_factory, clock, group: UUID) -> Proposed:
    async with session_factory() as session:
        return await build_propose_games(session, clock=clock).execute(group)


async def deck_of(client, player: dict, group: UUID) -> list[dict]:
    read = await client.get(
        f"/api/v1/pools/{group}/deck",
        params={"sport": "PADEL", "kind": "COMPETITIVE"},
        headers=player["headers"],
    )
    assert read.status_code == 200, read.text
    return read.json()["cards"]


async def this_saturday(client, player: dict, group: UUID) -> list[str]:
    """The cards the player's deck deals for this Saturday, in its order — the
    proposer deals next Saturday's 17:00 too, the same way it always has."""

    return [
        card["proposal_id"]
        for card in await deck_of(client, player, group)
        if datetime.fromisoformat(card["starts_at"]) in (SATURDAY_FOUR, SATURDAY_FIVE)
    ]


def on(card: dict) -> set[UUID]:
    return {
        UUID(tile["player_id"])
        for side in ("yours", "theirs")
        for tile in card["sides"][side]
        if tile["player_id"] is not None
    }


def where(card: dict) -> tuple[str, datetime, int, bool | None]:
    return (
        card["club"]["name"],
        datetime.fromisoformat(card["starts_at"]),
        card["share_grosze"],
        card["indoor"],
    )


async def notices_of(client, mailbox, player: dict) -> list[dict]:
    await mailbox.drain()
    read = await client.get(NOTICES, headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()["notices"]


async def the_owed_card(
    client, session_factory, clock, mailbox, world, *, leaver: dict | None = None
) -> str:
    """Saturday's game booked, ``leaver`` gone from it, cancelled by the club,
    and the proposer run: the owed card's id."""

    booking = await books_saturday(client, session_factory, clock, world)
    if leaver is not None:
        left = await client.post(
            f"/api/v1/bookings/{booking}/departure", headers=leaver["headers"]
        )
        assert left.status_code == 200, left.text
    await the_club_cancels(client, world, booking)
    await mailbox.drain()
    proposed = await proposes(session_factory, clock, world["group"])
    assert proposed.redealt == 1, proposed
    [card] = [
        card
        for card in await deck_of(client, world["people"]["ola"], world["group"])
        if datetime.fromisoformat(card["starts_at"]) == SATURDAY_FIVE
    ]
    return card["proposal_id"]


async def an_earlier_card(session_factory, clock, world) -> str:
    """A card at Bonarka on Saturday at 16:00 for everybody in the group — its
    deadline sooner than the owed card's, so the deck's usual order would deal
    it first."""

    people = world["people"]
    game = await makes(
        session_factory,
        clock,
        pool_id=world["group"],
        club_id=world["bonarka"],
        start=SATURDAY_FOUR,
        versions=(
            tuple(people[name] for name in ("ola", "kuba", "ewa", "zosia")),
            tuple(people[name] for name in ("tomek", "marek")),
        ),
    )
    return str(game)


# --------------------------------------------------------------------------- #
# Closest to the cancelled game first
# --------------------------------------------------------------------------- #


async def test_the_owed_card_is_the_same_club_and_hour_on_the_court_left(
    client, session_factory, clock, mailbox, payments
):
    """The court the club cancelled is closed for the hour; Court 4, outdoor,
    is free. The four are dealt Bonarka at 17:00 again — not Kazimierz Padel —
    and their yeses book Court 4."""

    world = await a_world(client, session_factory, payments)
    four = the_four(world)

    owed = await the_owed_card(client, session_factory, clock, mailbox, world)

    [card, *_] = await deck_of(client, four[0], world["group"])
    assert card["proposal_id"] == owed
    assert where(card) == ("Bonarka Arena", SATURDAY_FIVE, 40_00, False)
    assert on(card) == {player["id"] for player in four}
    for player in four:
        said = await says_yes(client, player, UUID(owed))
        assert said.status_code == 200, said.text
    assert said.json()["booked"] is not None, said.text
    home = (await client.get(HOME, headers=four[0]["headers"])).json()["games"]
    [booked] = [game for game in home if game["status"] == "BOOKED"]
    assert (booked["court_name"], booked["indoor"]) == ("Court 4", False)


async def test_a_player_group_is_dealt_another_club_at_the_same_hour_next(
    client, session_factory, clock, mailbox, payments
):
    """Bonarka has no other padel court at 17:00: Kazimierz Padel at 17:00, at
    its own 25 zł."""

    world = await a_world(client, session_factory, payments, outdoor_court=False)
    four = the_four(world)

    owed = await the_owed_card(client, session_factory, clock, mailbox, world)

    [card, *_] = await deck_of(client, four[0], world["group"])
    assert card["proposal_id"] == owed
    assert where(card) == ("Kazimierz Padel", SATURDAY_FIVE, 25_00, True)
    assert on(card) == {player["id"] for player in four}


# --------------------------------------------------------------------------- #
# First in its players' deck — and nobody else's
# --------------------------------------------------------------------------- #


async def test_the_owed_card_is_first_in_each_of_the_four_s_deck(
    client, session_factory, clock, mailbox, payments
):
    world = await a_world(client, session_factory, payments)
    owed = await the_owed_card(client, session_factory, clock, mailbox, world)
    earlier = await an_earlier_card(session_factory, clock, world)

    for player in the_four(world):
        assert await this_saturday(client, player, world["group"]) == [
            owed,
            earlier,
        ], player["name"]
    # Zosia and Marek were owed nothing: their decks deal as ever.
    for name in ("zosia", "marek"):
        assert await this_saturday(client, world["people"][name], world["group"]) == [
            earlier
        ], name


async def test_the_best_fit_beside_them_is_dealt_it_in_the_usual_order(
    client, session_factory, clock, mailbox, payments
):
    """Tomek left before the club cancelled: the card is owed to the three still
    in, and completed by their best fit — who was promised nothing, and whose
    deck deals it after the sooner card."""

    world = await a_world(client, session_factory, payments)
    people = world["people"]
    three = [people[name] for name in ("ola", "kuba", "ewa")]

    owed = await the_owed_card(
        client, session_factory, clock, mailbox, world, leaver=people["tomek"]
    )
    earlier = await an_earlier_card(session_factory, clock, world)

    [card, *_] = await deck_of(client, three[0], world["group"])
    assert card["proposal_id"] == owed
    [fit] = on(card) - {player["id"] for player in three}
    for player in three:
        assert await this_saturday(client, player, world["group"]) == [
            owed,
            earlier,
        ], player["name"]
    [best_fit] = [player for player in people.values() if player["id"] == fit]
    assert await this_saturday(client, best_fit, world["group"]) == [earlier, owed]


async def test_once_answered_the_deck_deals_in_its_usual_order(
    client, session_factory, clock, mailbox, payments
):
    world = await a_world(client, session_factory, payments)
    ola = world["people"]["ola"]
    owed = await the_owed_card(client, session_factory, clock, mailbox, world)
    earlier = await an_earlier_card(session_factory, clock, world)

    said = await says_yes(client, ola, UUID(owed))

    assert said.status_code == 200, said.text
    assert await this_saturday(client, ola, world["group"]) == [earlier]


# --------------------------------------------------------------------------- #
# What the players are told
# --------------------------------------------------------------------------- #


async def test_the_cancel_promises_the_new_game_and_your_new_game_names_the_kind(
    client, session_factory, clock, mailbox, payments
):
    world = await a_world(client, session_factory, payments)
    four = the_four(world)

    owed = await the_owed_card(client, session_factory, clock, mailbox, world)

    for player in four:
        told = await notices_of(client, mailbox, player)
        [new_game] = [notice for notice in told if notice["kind"] == "NEW_GAME"]
        assert (new_game["title"], new_game["body"]) == (
            "Your new game · Sat 17:00 at Bonarka Arena",
            "The same players · outdoor · 40 zł a share — say yes to book it.",
        )
        # It opens the deck on the card: its group, sport and kind.
        assert (
            new_game["opens"],
            new_game["game_id"],
            new_game["pool_id"],
            new_game["sport"],
            new_game["game_kind"],
        ) == ("DECK", owed, str(world["group"]), "PADEL", "COMPETITIVE")
        [called_off] = [
            notice for notice in told if notice["kind"] == "GAME_CALLED_OFF"
        ]
        assert (called_off["title"], called_off["body"]) == (
            "Game called off · nothing was taken",
            "Bonarka Arena cancelled padel · Sat 10 Oct, 17:00 because a court "
            f"needs repair. {PROMISE}",
        )


async def test_your_new_game_at_another_club_names_no_kind(
    client, session_factory, clock, mailbox, payments
):
    world = await a_world(client, session_factory, payments, outdoor_court=False)
    ola = world["people"]["ola"]

    await the_owed_card(client, session_factory, clock, mailbox, world)

    told = await notices_of(client, mailbox, ola)
    [new_game] = [notice for notice in told if notice["kind"] == "NEW_GAME"]
    assert (new_game["title"], new_game["body"]) == (
        "Your new game · Sat 17:00 at Kazimierz Padel",
        "The same players · 25 zł a share — say yes to book it.",
    )
