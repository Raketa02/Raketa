"""**The friends card and *Find a court***, read over HTTP as the Friends tab
reads them (#750; ``docs/adr/0202`` §5; the friends mechanics §7.4–§7.6).

**Ogrody 33 and Wisła Park**, 4 km apart, each sell padel on Tuesdays at 21:00
and Saturdays at 10:00, one court each, 100 zł a court — 25 zł each. **This
Tuesday at 21:00 Ogrody 33 is booked out** by four players who got there first,
so Ogrody 33 Club, its official group, is offered Wisła Park then and only
then.

**Tomek** (2,71) is in Ogrody 33 Club with **Ewa** (2,40) and **Magda** (2,90),
and in Kazimierz crew, a group players made, with **Ania** (2,20). All three are
his friends. Ewa, Magda and Tomek are free on Tuesday nights and Saturday
mornings; Ania on Saturday mornings only. On Ogrody 33 Club's Friends tab Tomek
seats Ewa, Magda and Ania — Ania as a **guest**, since she is not a member.

The clock stands on **Monday 5 October 2026, 08:00 in Kraków**.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy import func, select

from app.api.dependencies import get_clock
from app.infrastructure.events.event_store_model import EventStoreORM
from app.kernel import Sport
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
from tests.api.test_friends import blocks
from tests.api.test_friends_on_every_face import befriend
from tests.api.test_official_groups import an_official_group
from tests.unit.fake_clock import MovableClock

#: The two hours both clubs sell: Saturday 10:00 and Tuesday 21:00.
THE_HOURS = [(6, 10), (2, 21)]
TUESDAY_21 = warsaw(6, 21)
SATURDAY_TEN = warsaw(10, 10)
NEXT_TUESDAY_21 = warsaw(13, 21)
NEXT_SATURDAY_TEN = warsaw(17, 10)

SATURDAY_MORNINGS = [{"day": 6, "hour": 10}]
TUESDAY_NIGHTS = [{"day": 2, "hour": 21}]
BOTH = [*SATURDAY_MORNINGS, *TUESDAY_NIGHTS]


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
    #: *Kazimierz crew*, at a club far from both that is paused.
    crew: UUID
    tomek: dict
    ewa: dict
    magda: dict
    ania: dict
    #: A member of Ogrody 33 Club who is nobody's friend.
    kuba: dict
    #: The four who booked out Ogrody 33 on Tuesday at 21:00.
    first: list[dict]
    #: Ogrody 33's desk's session.
    desk: dict | None = None

    @property
    def friends(self) -> list[dict]:
        return [self.ewa, self.magda, self.ania]


async def joins(client, group: UUID, *people: dict) -> None:
    for player in people:
        joined = await client.post(
            f"{GROUPS}/{group}/membership", headers=player["headers"]
        )
        assert joined.status_code in (200, 201), joined.text


@pytest.fixture
async def world(client, session_factory, payments, clock, mailbox) -> World:
    ogrody, desk = await a_club_and_its_desk(
        client, name="Ogrody 33", hours=THE_HOURS, padel_grosze=100_00
    )
    wisla_park = await a_club_selling(
        client,
        name="Wisła Park",
        email="desk@wislapark.pl",
        point=(50.096, 19.95),
        hours=THE_HOURS,
        padel_grosze=100_00,
    )
    kazimierz = await a_club_selling(
        client,
        name="Kazimierz Club",
        email="desk@kazimierz.pl",
        point=(50.6, 20.6),
        hours=THE_HOURS,
        paused=True,
    )
    row = await invites(client, desk, name="Marta Wójcik", email=MARTA)
    marta_headers = await marta_sets_her_password(client, mailbox)
    marta = {
        "id": (await me(client, marta_headers))["id"],
        "headers": marta_headers,
        "administrator_id": row["id"],
    }
    group = UUID(
        (await an_official_group(client, marta, ogrody, join_policy="ANYONE"))["id"]
    )

    async def member(name: str, mu: float, week: list[dict], **more) -> dict:
        return await a_member(
            client, session_factory, payments, name, mu=mu, week=week, **more
        )

    tomek = await member("tomek", 2.71, BOTH, sports=(Sport.PADEL, Sport.TENNIS))
    ewa = await member("ewa", 2.40, BOTH, sports=(Sport.PADEL, Sport.TENNIS))
    magda = await member("magda", 2.90, BOTH)
    ania = await member("ania", 2.20, SATURDAY_MORNINGS)
    kuba = await member("kuba", 2.70, BOTH)
    await joins(client, group, tomek, ewa, magda, kuba)
    crew = await a_group(client, ania, kazimierz, tomek)
    await befriend(client, group, tomek, ewa)
    await befriend(client, group, magda, tomek)
    await befriend(client, crew, ania, tomek)

    # Four players who got there first book Ogrody 33's one court this Tuesday
    # at 21:00.
    first = [
        await member(name, 2.5, BOTH) for name in ("kasia", "piotr", "zofia", "marek")
    ]
    theirs = await a_group(client, first[0], ogrody, *first[1:])
    proposal = await makes(
        session_factory,
        clock,
        pool_id=theirs,
        club_id=ogrody,
        start=TUESDAY_21,
        versions=(tuple(first),),
    )
    for player in first:
        assert (await says_yes(client, player, proposal)).status_code == 200
    return World(
        ogrody=ogrody,
        wisla_park=wisla_park,
        group=group,
        crew=crew,
        tomek=tomek,
        ewa=ewa,
        magda=magda,
        ania=ania,
        kuba=kuba,
        first=first,
        desk=desk,
    )


def ids(*people: dict) -> list[str]:
    return [str(person["id"]) for person in people]


async def card_of(
    client,
    reader: dict,
    pool: UUID,
    friends: list[dict],
    *,
    sport: str = "PADEL",
    kind: str = "COMPETITIVE",
    **more,
):
    return await client.get(
        f"/api/v1/pools/{pool}/friends-card",
        params={"sport": sport, "kind": kind, "friend_ids": ids(*friends), **more},
        headers=reader["headers"],
    )


async def courts_of(
    client, reader: dict, pool: UUID, friends: list[dict], *, sport: str = "PADEL"
):
    return await client.get(
        f"/api/v1/pools/{pool}/friends-card/courts",
        params={"sport": sport, "friend_ids": ids(*friends)},
        headers=reader["headers"],
    )


async def the_card(client, reader, pool, friends, **params) -> dict:
    read = await card_of(client, reader, pool, friends, **params)
    assert read.status_code == 200, read.text
    return read.json()


def refusal(answer) -> tuple[int, str]:
    return answer.status_code, answer.json()["code"]


def where(court: dict) -> tuple[str, datetime, str]:
    return (
        court["club"]["id"],
        datetime.fromisoformat(court["starts_at"]),
        court["court_name"],
    )


# --------------------------------------------------------------------------- #
# The card
# --------------------------------------------------------------------------- #


async def test_the_card_is_the_evenest_sides_and_the_soonest_hour_all_four_are_free(
    client, world
):
    card = await the_card(client, world.tomek, world.group, world.friends)

    # *YOU + EWA VS MAGDA + ANIA*: 5,11 against 5,10.
    assert card["sides"] == {
        "yours": ids(world.tomek, world.ewa),
        "theirs": ids(world.magda, world.ania),
    }
    assert card["forecast"]["pct"] >= 80
    assert (card["sport"], card["kind"]) == ("PADEL", "COMPETITIVE")
    # Tuesday 21:00 at Wisła Park is sooner, but Ania is busy then: Saturday
    # 10:00 at Ogrody 33 is the soonest all four are free.
    court = card["court"]
    assert where(court) == (world.ogrody, SATURDAY_TEN, "Court 1")
    assert (court["share_grosze"], court["free_count"], court["busy"]) == (
        25_00,
        4,
        [],
    )
    assert court["home_club_full"] is False
    assert court["club"]["name"] == "Ogrody 33"
    assert card["home_club"] == {"id": world.ogrody, "name": "Ogrody 33"}
    # The overlap of their four weeks, Saturday morning ringed, and the club's
    # cut-off a day before.
    assert card["overlap"]["game"] == {"day": 6, "range": "MORNING"}
    assert len(card["overlap"]["cells"]) == 21
    assert datetime.fromisoformat(card["cut_off"]) == SATURDAY_TEN - timedelta(hours=24)


async def test_a_swap_draws_his_sides_and_the_percentage_follows_them(client, world):
    evenest = await the_card(client, world.tomek, world.group, world.friends)

    swapped = await the_card(
        client,
        world.tomek,
        world.group,
        world.friends,
        partner_id=str(world.magda["id"]),
    )

    assert swapped["sides"] == {
        "yours": ids(world.tomek, world.magda),
        "theirs": ids(world.ewa, world.ania),
    }
    assert swapped["forecast"]["pct"] < evenest["forecast"]["pct"]
    assert swapped["court"] == evenest["court"]


async def test_a_partner_who_is_not_seated_is_refused(client, world):
    answer = await card_of(
        client,
        world.tomek,
        world.group,
        world.friends,
        partner_id=str(world.kuba["id"]),
    )

    assert refusal(answer) == (400, "sides_not_of_the_line_up")


async def test_a_court_picked_in_find_a_court_is_the_cards(client, world):
    card = await the_card(
        client,
        world.tomek,
        world.group,
        world.friends,
        court_id=(await the_list(client, world))[0]["court_id"],
        starts_at=TUESDAY_21.isoformat(),
    )

    court = card["court"]
    assert where(court) == (world.wisla_park, TUESDAY_21, "Court 1")
    assert court["home_club_full"] is True
    assert (court["free_count"], court["busy"]) == (3, ids(world.ania))
    assert card["overlap"]["game"] == {"day": 2, "range": "EVENING"}
    # The card's sides never depend on the court.
    assert card["sides"]["yours"] == ids(world.tomek, world.ewa)


async def test_a_court_hour_the_list_does_not_offer_is_refused(client, world):
    # Ogrody 33's Tuesday court is booked out.
    ogrody_courts = await the_list(client, world)
    ogrody_court = next(
        row["court_id"] for row in ogrody_courts if row["club"]["id"] == world.ogrody
    )

    answer = await card_of(
        client,
        world.tomek,
        world.group,
        world.friends,
        court_id=ogrody_court,
        starts_at=TUESDAY_21.isoformat(),
    )

    assert refusal(answer) == (409, "court_hour_not_for_sale")


async def test_a_court_without_its_hour_is_refused(client, world):
    answer = await card_of(
        client,
        world.tomek,
        world.group,
        world.friends,
        court_id=str(world.tomek["id"]),
    )

    assert refusal(answer) == (400, "court_hour_incomplete")


async def test_a_friend_who_is_not_a_member_plays_as_a_guest(client, world):
    """Ania is in Kazimierz crew, not in Ogrody 33 Club — and on its card."""

    members = await client.get(
        f"{GROUPS}/{world.group}/members",
        params={"sport": "PADEL"},
        headers=world.tomek["headers"],
    )
    assert members.status_code == 200, members.text
    assert str(world.ewa["id"]) in members.text
    assert str(world.ania["id"]) not in members.text

    card = await the_card(client, world.tomek, world.group, world.friends)

    assert str(world.ania["id"]) in card["sides"]["theirs"]


async def test_singles_seats_one_friend(client, world):
    card = await the_card(
        client, world.tomek, world.group, [world.ewa], sport="TENNIS", kind="FOR_FUN"
    )

    assert card["sides"] == {"yours": ids(world.tomek), "theirs": ids(world.ewa)}
    assert card["kind"] == "FOR_FUN"
    # Tennis is Court 2 at both clubs, 80 zł — 40 zł each; Ogrody 33's is free
    # on Tuesday.
    assert where(card["court"]) == (world.ogrody, TUESDAY_21, "Court 2")
    assert card["court"]["share_grosze"] == 40_00


async def test_singles_has_no_partner_and_seats_no_more_than_one(client, world):
    partnered = await card_of(
        client,
        world.tomek,
        world.group,
        [world.ewa],
        sport="TENNIS",
        partner_id=str(world.ewa["id"]),
    )
    three = await card_of(
        client, world.tomek, world.group, world.friends, sport="TENNIS"
    )

    assert refusal(partnered) == (400, "sides_not_of_the_line_up")
    assert refusal(three) == (400, "wrong_line_up_size")
    assert three.json()["details"] == {"friends": 1}


async def test_doubles_seats_three(client, world):
    two = await card_of(client, world.tomek, world.group, [world.ewa, world.magda])

    assert refusal(two) == (400, "wrong_line_up_size")
    assert two.json()["details"] == {"friends": 3}


async def test_with_no_court_in_fourteen_days_the_card_says_so(client, world):
    """Kazimierz crew's club is paused, and no other club is within 10 km."""

    card = await the_card(client, world.tomek, world.crew, world.friends)
    listed = await courts_of(client, world.tomek, world.crew, world.friends)

    assert card["sides"]["yours"] == ids(world.tomek, world.ewa)
    assert (card["court"], card["overlap"], card["cut_off"]) == (None, None, None)
    assert listed.status_code == 200, listed.text
    assert listed.json()["courts"] == []


# --------------------------------------------------------------------------- #
# The refusals, each naming nobody
# --------------------------------------------------------------------------- #


async def test_two_who_blocked_each_other_cannot_play_together(
    client, session_factory, world
):
    await blocks(client, session_factory, world.ewa, world.ania)

    card = await card_of(client, world.tomek, world.group, world.friends)
    listed = await courts_of(client, world.tomek, world.group, world.friends)

    for answer in (card, listed):
        assert refusal(answer) == (409, "cannot_play_together")
        # Never which two.
        for person in (world.ewa, world.ania):
            assert str(person["id"]) not in answer.text


async def test_somebody_who_is_not_his_friend_is_refused(client, world):
    answer = await card_of(
        client, world.tomek, world.group, [world.ewa, world.magda, world.kuba]
    )

    assert refusal(answer) == (409, "not_a_friend")
    assert str(world.kuba["id"]) not in answer.text


async def test_a_friend_with_no_level_in_the_sport_is_refused(client, world):
    """Magda plays no tennis."""

    answer = await card_of(
        client, world.tomek, world.group, [world.magda], sport="TENNIS"
    )

    assert refusal(answer) == (409, "no_level")
    assert str(world.magda["id"]) not in answer.text


async def test_a_reader_not_in_the_group_reads_nothing_of_it(client, world):
    """Ania reads Ogrody 33 Club's card as if it did not exist."""

    answer = await card_of(client, world.ania, world.group, [world.tomek])
    listed = await courts_of(client, world.ania, world.group, [world.tomek])

    assert refusal(answer) == (404, "pool_not_found")
    assert refusal(listed) == (404, "pool_not_found")


# --------------------------------------------------------------------------- #
# Find a court
# --------------------------------------------------------------------------- #


async def the_list(client, world: World) -> list[dict]:
    listed = await courts_of(client, world.tomek, world.group, world.friends)
    assert listed.status_code == 200, listed.text
    return listed.json()["courts"]


async def test_find_a_court_lists_every_court_with_who_is_free_and_the_full_home_club(
    client, world
):
    courts = await the_list(client, world)

    assert [
        (*where(row), row["home_club_full"], row["free_count"], row["busy"])
        for row in courts
    ] == [
        # Ogrody 33 is full this Tuesday: Wisła Park, marked.
        (world.wisla_park, TUESDAY_21, "Court 1", True, 3, ids(world.ania)),
        (world.ogrody, SATURDAY_TEN, "Court 1", False, 4, []),
        # Next Tuesday Ogrody 33 has its court again, and only it is listed.
        (world.ogrody, NEXT_TUESDAY_21, "Court 1", False, 3, ids(world.ania)),
        (world.ogrody, NEXT_SATURDAY_TEN, "Court 1", False, 4, []),
    ]
    assert [row["club"]["name"] for row in courts] == [
        "Wisła Park",
        "Ogrody 33",
        "Ogrody 33",
        "Ogrody 33",
    ]
    assert {row["share_grosze"] for row in courts} == {25_00}


async def test_an_hour_one_of_them_has_a_game_at_is_left_out(
    client, session_factory, payments, clock, world
):
    """Magda books Saturday 10:00 at Wisła Park with three others: Saturday is
    gone from her line-up's list, and so the card proposes next Saturday."""

    others = [
        await a_member(client, session_factory, payments, name)
        for name in ("ola", "iga", "jan")
    ]
    hers = await a_group(client, world.magda, world.wisla_park, *others)
    proposal = await makes(
        session_factory,
        clock,
        pool_id=hers,
        club_id=world.wisla_park,
        start=SATURDAY_TEN,
        versions=((world.magda, *others),),
    )
    for player in (world.magda, *others):
        assert (await says_yes(client, player, proposal)).status_code == 200

    starts = [
        datetime.fromisoformat(row["starts_at"])
        for row in await the_list(client, world)
    ]
    card = await the_card(client, world.tomek, world.group, world.friends)

    assert starts == [TUESDAY_21, NEXT_TUESDAY_21, NEXT_SATURDAY_TEN]
    assert datetime.fromisoformat(card["court"]["starts_at"]) == NEXT_SATURDAY_TEN


async def test_the_card_records_nothing(client, session_factory, world):
    async def events() -> int:
        async with session_factory() as session:
            return (
                await session.execute(select(func.count()).select_from(EventStoreORM))
            ).scalar_one()

    before = await events()
    await the_card(client, world.tomek, world.group, world.friends)
    await the_list(client, world)

    assert await events() == before
