"""An official group's courts, hour by hour, read as its players read them — the
Games deck and Post a game (``docs/adr/0202`` §7; the friends mechanics §6;
#746).

**Ogrody 33 gives Raketa two padel hours a week: Saturday 10:00 and Tuesday
21:00, one court each.** This Saturday at 10:00 is fully booked, by four players
who got there first. Wisła Park, 4 km north, sells the same two hours. Marta runs
*Ogrody 33 Club*, Ogrody 33's official group, and the club never touched its
switch — *Offer our groups other clubs' courts when ours are full*, on by
default.

- **At Saturday 10:00**, where Ogrody 33 is full, Tomek's four are dealt Wisła
  Park, and Post a game's sheet lists Wisła Park, marked as offered because
  Ogrody 33 is full. Next Saturday Ogrody 33 has its court again, and only it
  is listed.
- **At Tuesday 21:00**, where Ogrody 33 has a court, only Ogrody 33 is offered:
  a second four waits for next Tuesday rather than play at Wisła Park, and the
  sheet never lists it.
- **A club that turns the switch off** gets *only ours*: Tomek's four wait for
  next Saturday at Ogrody 33.

The proposer runs as the job runs it, and every claim is read over HTTP. The
clock stands on **Monday 5 October 2026, 08:00 in Kraków**.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

import pytest

from app.api.dependencies import get_clock
from app.bootstrap.composition import build_propose_games
from tests.api.administration_world import (
    MARTA,
    invites,
    marta_sets_her_password,
    me,
)
from tests.api.proposals_world import (
    GROUPS,
    MONDAY_MORNING,
    a_club_and_its_desk,
    a_club_selling,
    a_group,
    a_member,
    makes,
    says_yes,
    warsaw,
)
from tests.api.test_official_groups import an_official_group
from tests.unit.fake_clock import MovableClock

#: The two hours Ogrody 33 and Wisła Park sell: Saturday 10:00, Tuesday 21:00.
THE_HOURS = [(6, 10), (2, 21)]
#: This Saturday, 10:00 — booked out at Ogrody 33.
SATURDAY_TEN = warsaw(10, 10)
NEXT_SATURDAY_TEN = warsaw(17, 10)
TUESDAY_21 = warsaw(6, 21)
NEXT_TUESDAY_21 = warsaw(13, 21)
SATURDAY, NEXT_SATURDAY, TUESDAY = (
    date(2026, 10, 10),
    date(2026, 10, 17),
    date(2026, 10, 6),
)

SATURDAY_MORNINGS = [{"day": 6, "hour": 10}]
TUESDAY_NIGHTS = [{"day": 2, "hour": 21}]


@pytest.fixture
def clock(app):
    """Monday 5 October 2026, 08:00 in Kraków."""

    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


@dataclass(frozen=True)
class World:
    ogrody: str
    wisla_park: str
    #: *Ogrody 33 Club*, Ogrody 33's official group.
    group: UUID


async def the_world(client, session_factory, payments, clock, mailbox, **settings):
    """Ogrody 33 and Wisła Park, Marta's official group at Ogrody 33, and this
    Saturday 10:00 booked out at Ogrody 33. ``settings`` are what Ogrody 33's
    desk saves — its defaults unless told otherwise."""

    ogrody, desk = await a_club_and_its_desk(
        client, name="Ogrody 33", hours=THE_HOURS, **settings
    )
    wisla_park = await a_club_selling(
        client,
        name="Wisła Park",
        email="desk@wislapark.pl",
        point=(50.096, 19.95),
        hours=THE_HOURS,
    )
    row = await invites(client, desk, name="Marta Wójcik", email=MARTA)
    marta_headers = await marta_sets_her_password(client, mailbox)
    marta = {
        "id": (await me(client, marta_headers))["id"],
        "headers": marta_headers,
        "administrator_id": row["id"],
    }
    official = await an_official_group(client, marta, ogrody, join_policy="ANYONE")

    # Four players who got there first book Ogrody 33's one court this
    # Saturday at 10:00.
    first = [
        await a_member(client, session_factory, payments, name)
        for name in ("kasia", "piotr", "zofia", "marek")
    ]
    theirs = await a_group(client, first[0], ogrody, *first[1:])
    proposal = await makes(
        session_factory,
        clock,
        pool_id=theirs,
        club_id=ogrody,
        start=SATURDAY_TEN,
        versions=(tuple(first),),
    )
    for player in first:
        assert (await says_yes(client, player, proposal)).status_code == 200
    return World(ogrody=ogrody, wisla_park=wisla_park, group=UUID(official["id"]))


async def joined(client, session_factory, payments, world: World, *names, week):
    players = [
        await a_member(client, session_factory, payments, name, week=week)
        for name in names
    ]
    for player in players:
        answer = await client.post(
            f"{GROUPS}/{world.group}/membership", headers=player["headers"]
        )
        assert answer.status_code in (200, 201), answer.text
    return players


async def proposes(session_factory, clock, group: UUID) -> None:
    async with session_factory() as session:
        await build_propose_games(session, clock=clock).execute(group)


async def deck_of(client, player: dict, group: UUID) -> list[dict]:
    read = await client.get(
        f"/api/v1/pools/{group}/deck",
        params={"sport": "PADEL", "kind": "COMPETITIVE"},
        headers=player["headers"],
    )
    assert read.status_code == 200, read.text
    return read.json()["cards"]


def where_and_when(cards: list[dict]) -> list[tuple[str, datetime]]:
    return [
        (card["club"]["id"], datetime.fromisoformat(card["starts_at"]))
        for card in cards
    ]


def posting(**overrides) -> dict:
    return {"sport": "PADEL", "kind": "COMPETITIVE", "who": "ANYONE", **overrides}


async def sheet_of(client, player: dict, group: UUID, day: date, range_: str):
    read = await client.get(
        f"/api/v1/pools/{group}/posting-grid/slot",
        params={**posting(), "day": day.isoformat(), "range": range_},
        headers=player["headers"],
    )
    assert read.status_code == 200, read.text
    return read.json()


async def grid_cell(client, player: dict, group: UUID, day: date, range_: str):
    """One cell of the first week's grid, as the WHEN grid draws it."""

    read = await client.get(
        f"/api/v1/pools/{group}/posting-grid",
        params=posting(),
        headers=player["headers"],
    )
    assert read.status_code == 200, read.text
    [found] = [
        cell
        for row in read.json()["days"]
        if row["day"] == day.isoformat()
        for cell in row["cells"]
        if cell["range"] == range_
    ]
    return found


def free_courts(sheet: dict) -> list[tuple[str, datetime, bool, bool]]:
    """Each *Free courts* row: its club, its hour, whether it is the home club
    and whether it is offered because the home club is full then."""

    return [
        (
            court["club"]["id"],
            datetime.fromisoformat(court["starts_at"]),
            court["home_club"],
            court["home_club_full"],
        )
        for court in sheet["free_courts"]
    ]


# --------------------------------------------------------------------------- #
# The Games deck
# --------------------------------------------------------------------------- #


async def test_at_the_hour_ogrody_33_is_full_its_group_is_dealt_wisla_park(
    client, session_factory, payments, clock, mailbox
):
    world = await the_world(client, session_factory, payments, clock, mailbox)
    tomek, *_ = await joined(
        client,
        session_factory,
        payments,
        world,
        "tomek",
        "ewa",
        "magda",
        "ola",
        week=SATURDAY_MORNINGS,
    )

    await proposes(session_factory, clock, world.group)

    # This Saturday, at Wisła Park — not next Saturday at Ogrody 33, which an
    # hour they share at home kept them to until #746.
    assert where_and_when(await deck_of(client, tomek, world.group)) == [
        (world.wisla_park, SATURDAY_TEN)
    ]


async def test_at_an_hour_ogrody_33_has_a_court_only_ogrody_33_is_dealt(
    client, session_factory, payments, clock, mailbox
):
    world = await the_world(client, session_factory, payments, clock, mailbox)
    eight = await joined(
        client,
        session_factory,
        payments,
        world,
        "tomek",
        "ewa",
        "magda",
        "ola",
        "kuba",
        "ania",
        "jan",
        "iga",
        week=TUESDAY_NIGHTS,
    )

    await proposes(session_factory, clock, world.group)

    # Ogrody 33's one court on Tuesday takes one four; the other four wait for
    # next Tuesday there, though Wisła Park has a court free at 21:00.
    dealt = {
        place
        for player in eight
        for place in where_and_when(await deck_of(client, player, world.group))
    }
    assert dealt == {(world.ogrody, TUESDAY_21), (world.ogrody, NEXT_TUESDAY_21)}


async def test_a_club_that_switches_other_clubs_off_keeps_its_group_at_home(
    client, session_factory, payments, clock, mailbox
):
    world = await the_world(
        client,
        session_factory,
        payments,
        clock,
        mailbox,
        other_clubs_courts={"offered": False, "within_km": 10},
    )
    tomek, *_ = await joined(
        client,
        session_factory,
        payments,
        world,
        "tomek",
        "ewa",
        "magda",
        "ola",
        week=SATURDAY_MORNINGS,
    )

    await proposes(session_factory, clock, world.group)

    assert where_and_when(await deck_of(client, tomek, world.group)) == [
        (world.ogrody, NEXT_SATURDAY_TEN)
    ]


# --------------------------------------------------------------------------- #
# Post a game
# --------------------------------------------------------------------------- #


async def test_post_a_game_offers_wisla_park_only_at_the_hour_ogrody_33_is_full(
    client, session_factory, payments, clock, mailbox
):
    world = await the_world(client, session_factory, payments, clock, mailbox)
    tomek, *_ = await joined(
        client,
        session_factory,
        payments,
        world,
        "tomek",
        "ewa",
        "magda",
        "ola",
        week=[*SATURDAY_MORNINGS, *TUESDAY_NIGHTS],
    )

    grid_saturday = await grid_cell(client, tomek, world.group, SATURDAY, "MORNING")
    grid_tuesday = await grid_cell(client, tomek, world.group, TUESDAY, "EVENING")
    this_saturday = await sheet_of(client, tomek, world.group, SATURDAY, "MORNING")
    next_saturday = await sheet_of(client, tomek, world.group, NEXT_SATURDAY, "MORNING")
    tuesday = await sheet_of(client, tomek, world.group, TUESDAY, "EVENING")

    # The grid counts the three of them at 10:00 on a court either way: Wisła
    # Park's this Saturday, Ogrody 33's on Tuesday.
    for drawn, start in ((grid_saturday, SATURDAY_TEN), (grid_tuesday, TUESDAY_21)):
        assert drawn["court_free"] is True
        assert datetime.fromisoformat(drawn["best_starts_at"]) == start
        assert drawn["fits_free"] == 3
    # Full at home: Wisła Park, marked — *Ogrody 33 is full at 10:00*.
    assert free_courts(this_saturday) == [(world.wisla_park, SATURDAY_TEN, False, True)]
    assert this_saturday["cell"]["court_free"] is True
    # A court at home: only home, and never marked.
    assert free_courts(next_saturday) == [
        (world.ogrody, NEXT_SATURDAY_TEN, True, False)
    ]
    assert free_courts(tuesday) == [(world.ogrody, TUESDAY_21, True, False)]


async def test_a_post_is_made_at_wisla_park_only_at_the_hour_ogrody_33_is_full(
    client, session_factory, payments, clock, mailbox
):
    world = await the_world(client, session_factory, payments, clock, mailbox)
    tomek, *_ = await joined(
        client,
        session_factory,
        payments,
        world,
        "tomek",
        "ewa",
        "magda",
        "ola",
        week=[*SATURDAY_MORNINGS, *TUESDAY_NIGHTS],
    )

    async def posts_at(start: datetime):
        return await client.post(
            f"/api/v1/pools/{world.group}/posts",
            json={
                **posting(),
                "club_id": world.wisla_park,
                "starts_at": start.isoformat(),
            },
            headers=tomek["headers"],
        )

    elsewhere_at_a_free_hour = await posts_at(TUESDAY_21)
    elsewhere_at_the_full_hour = await posts_at(SATURDAY_TEN)

    assert (
        elsewhere_at_a_free_hour.status_code,
        elsewhere_at_a_free_hour.json()["code"],
    ) == (409, "court_hour_not_for_sale")
    assert elsewhere_at_the_full_hour.status_code == 201, (
        elsewhere_at_the_full_hour.text
    )
