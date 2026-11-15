"""Home's *Hottest groups*, and withdrawing a Join request — over HTTP, as the
player app calls them (#792; the Home rows mechanics §5, ``docs/adr/0204``
§3, §11).

Tomek's Home asks for the hottest groups and gets up to six, whether he is in
them or not: the busiest tagged **HOTTEST**, the fast-growing **GROWING**, the
rest untagged, each card carrying everything its group sheet shows and his own
relation to it. He asked to join a group by mistake, withdraws, and the request
leaves the Owner's, the Administrator's and the club's lists.

**Members join over HTTP and the clock moves** for *new this month*; **games
are booked through the Booking aggregate**, under the group's own id — which is
its pool's — the way the fill and a friends game's send file them, since a test
of a heat read is about the read. Every assertion reads what a player reads.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

import pytest

from app.bootstrap.composition import (
    build_booking_repository,
    build_domain_event_store,
    build_event_publisher,
)
from app.engines.matchfit.core import SearchMode
from app.infrastructure.events.sqlalchemy_domain_event_store import SqlAlchemyEventStore
from app.kernel import Sport, instant
from app.modules.bookings.domain.booking import (
    BookedCourt,
    Booking,
    CancelReason,
    PayMode,
)
from app.modules.rating.infrastructure.event_sourced_skill_rating_repository import (
    RATING_AGGREGATE,
)
from app.shared.ids import new_uuid
from tests.api.administration_world import (
    MARTA,
    club_signs_up,
    invites,
    marta_sets_her_password,
    me,
)
from tests.api.test_club_groups import requests_of, the_club_s_groups
from tests.api.test_group_members import a_padel_player
from tests.api.test_groups import GROUPS, a_club, a_group, a_player, join, read
from tests.api.test_official_groups import (
    an_administrator_who_plays,
    an_official_group,
    answer,
    page_of,
)

HOTTEST = "/api/v1/hottest-groups"
NOTICES = "/api/v1/players/me/notices"


async def hottest(client, player: dict) -> list[dict]:
    read_ = await client.get(HOTTEST, headers=player["headers"])
    assert read_.status_code == 200, read_.text
    return read_.json()["groups"]


def card(row: list[dict], group: dict) -> dict:
    return next(one for one in row if one["id"] == group["id"])


def named(row: list[dict]) -> list[str]:
    return [one["name"] for one in row]


async def people(client, *names: str) -> list[dict]:
    return [await a_player(client, name) for name in names]


async def a_group_of(
    client, owner: dict, club: dict, *members: dict, name: str, **overrides
) -> dict:
    """A group the Owner creates and every member joins — let in by the Owner
    where it needs approval."""

    group = await a_group(client, owner, club, name=name, **overrides)
    for member in members:
        await joins(client, member, group, owner=owner)
    return group


async def joins(client, member: dict, group: dict, *, owner: dict) -> None:
    tapped = await join(client, member, group)
    assert tapped.status_code == 200, tapped.text
    if tapped.json()["relation"] == "REQUESTED":
        approved = await client.post(
            f"{GROUPS}/{group['id']}/requests/{member['id']}/approve",
            headers=owner["headers"],
        )
        assert approved.status_code == 204, approved.text


async def leaves(client, member: dict, group: dict) -> None:
    left = await client.delete(
        f"{GROUPS}/{group['id']}/membership", headers=member["headers"]
    )
    assert left.status_code == 204, left.text


async def withdraws(client, player: dict, group: dict):
    return await client.delete(
        f"{GROUPS}/{group['id']}/join-request", headers=player["headers"]
    )


async def games_in(
    session_factory,
    group: dict,
    *starts: datetime,
    friends: bool = False,
    called_off: bool = False,
) -> None:
    """A padel game booked in the group at each hour — booked two days before
    it, filed under the group's id as its pool."""

    for start in starts:
        begins = instant(start)
        sides = ((new_uuid(), new_uuid()), (new_uuid(), new_uuid()))
        common = dict(
            booking_id=new_uuid(),
            pool_id=group["id"],
            club_id=new_uuid(),
            court=BookedCourt(court_id=new_uuid(), name="Court 1", indoor=True),
            sport=Sport.PADEL,
            kind=SearchMode.COMPETITIVE,
            start=begins,
            share_grosze=30_00,
            first_side=sides[0],
            second_side=sides[1],
            cut_off=instant(begins - timedelta(hours=24)),
            game_id=new_uuid(),
            at=instant(begins - timedelta(days=2)),
        )
        booking = (
            Booking.booked_by_a_friend(
                **common, sender=sides[0][0], pay_mode=PayMode.WHOLE_COURT
            )
            if friends
            else Booking.confirmed(**common)
        )
        if called_off:
            booking.cancel(
                CancelReason.WEATHER, at=instant(begins - timedelta(hours=1))
            )
        async with session_factory() as session:
            await build_booking_repository(
                session,
                event_store=build_domain_event_store(session),
                events=build_event_publisher(session),
            ).save(booking)
            await session.commit()


@pytest.fixture
async def club(client):
    return await a_club(client, "Ogrody 33")


# --------------------------------------------------------------------------- #
# The row
# --------------------------------------------------------------------------- #


async def test_any_player_reads_the_row_tagged_in_order_with_each_bar(
    client, session_factory, clock, club
):
    """Ogrody (6 players, +1, 4 games) = 8 + 3 + 6 = 17; Kazimierz (4, +4, no
    game) = 12 + 4 = 16; Podgórze (5, nobody new, 2 games) = 4 + 5 = 9."""

    p1, p2, p3, p4, p5, p6, p7, p8, p9, tomek = await people(
        client, *(f"p{n}" for n in range(1, 10)), "tomek"
    )
    ogrody = await a_group_of(client, p1, club, p2, p3, p4, p5, name="Ogrody")
    podgorze = await a_group_of(client, p1, club, p2, p3, p4, p5, name="Podgórze")
    clock.move(timedelta(days=31))
    await joins(client, p6, ogrody, owner=p1)
    await a_group_of(client, p6, club, p7, p8, p9, name="Kazimierz")
    now = clock.now()
    await games_in(
        session_factory, ogrody, *(now - timedelta(days=d) for d in (1, 2, 3, 4))
    )
    await games_in(session_factory, podgorze, now - timedelta(days=1), now)

    row = await hottest(client, tomek)

    assert named(row) == ["Ogrody", "Kazimierz", "Podgórze"]
    assert [one["tag"] for one in row] == ["HOTTEST", "GROWING", None]
    assert [one["heat_share"] for one in row] == pytest.approx([1, 16 / 17, 9 / 17])
    assert [
        (one["games_this_week"], one["new_this_month"], one["member_count"])
        for one in row
    ] == [(4, 1, 6), (0, 4, 4), (2, 0, 5)]
    # Tomek is in none of them, and reads them all.
    assert {one["relation"] for one in row} == {"NONE"}


async def test_games_this_week_are_court_times_in_the_last_seven_days_not_called_off(
    client, session_factory, clock, club
):
    p1, p2, p3, tomek = await people(client, "p1", "p2", "p3", "tomek")
    group = await a_group_of(client, p1, club, p2, p3, name="Padel po pracy")
    now = clock.now()
    # Counted: six days ago, two hours ago with no score yet, and a friends
    # game booked in the group yesterday.
    await games_in(
        session_factory, group, now - timedelta(days=6), now - timedelta(hours=2)
    )
    await games_in(session_factory, group, now - timedelta(days=1), friends=True)
    # Not counted: eight days ago, the day after tomorrow, and one called off
    # three days ago.
    await games_in(
        session_factory, group, now - timedelta(days=8), now + timedelta(days=2)
    )
    await games_in(session_factory, group, now - timedelta(days=3), called_off=True)

    [only] = await hottest(client, tomek)

    assert only["games_this_week"] == 3
    # A rolling window, to the minute: a day on, the six-day-old game is out.
    clock.move(timedelta(days=1, minutes=1))
    assert (await hottest(client, tomek))[0]["games_this_week"] == 2


async def test_new_this_month_is_who_joined_in_thirty_days_and_is_still_in(
    client, clock, club
):
    owner, ania, bartek, celina, darek, ewa, tomek = await people(
        client, "owner", "ania", "bartek", "celina", "darek", "ewa", "tomek"
    )
    group = await a_group_of(client, owner, club, ania, bartek, name="Bonarka")
    clock.move(timedelta(days=31))
    for member in (celina, darek, ewa):
        await joins(client, member, group, owner=owner)
    # Ewa joined and left; Bartek left and came back, counted by the join that
    # stands.
    await leaves(client, ewa, group)
    await leaves(client, bartek, group)
    await joins(client, bartek, group, owner=owner)

    [only] = await hottest(client, tomek)

    assert (only["new_this_month"], only["member_count"]) == (3, 5)


async def test_players_count_up_to_twenty_in_the_heat(client, clock, club):
    """A 21-player group heats as 20 once nobody in it is new: a 3-player
    group's bar is 3 / 20 of it, and the card still says 21."""

    crowd = await people(client, *(f"p{n}" for n in range(1, 22)))
    tomek = await a_player(client, "tomek")
    await a_group_of(client, crowd[0], club, *crowd[1:], name="Big")
    await a_group_of(client, crowd[0], club, *crowd[1:3], name="Small")
    clock.move(timedelta(days=31))

    big_card, small_card = await hottest(client, tomek)

    assert (big_card["member_count"], big_card["heat_share"]) == (21, 1)
    assert small_card["heat_share"] == pytest.approx(3 / 20)


async def test_only_a_top_group_that_played_is_hottest_and_bars_take_the_highest(
    client, session_factory, clock, club
):
    """The busiest group by heat had no game this week, so nobody is HOTTEST —
    not even the lower group that played — and the bars measure against the
    highest heat in the row."""

    p1, p2, p3, p4, p5, p6, p7, tomek = await people(
        client, "p1", "p2", "p3", "p4", "p5", "p6", "p7", "tomek"
    )
    played = await a_group_of(client, p1, club, p2, p3, name="Played")
    clock.move(timedelta(days=31))
    crowded = await a_group_of(client, p4, club, p5, p6, p7, name="Crowded")
    now = clock.now()
    await games_in(session_factory, played, now - timedelta(days=1))

    row = await hottest(client, tomek)

    # Crowded: 3 × 4 + 4 = 16, GROWING; Played: 2 + 3 = 5.
    assert [(one["id"], one["tag"]) for one in row] == [
        (crowded["id"], "GROWING"),
        (played["id"], None),
    ]
    assert [one["heat_share"] for one in row] == pytest.approx([1, 5 / 16])

    # One game in the crowded group, and it is HOTTEST.
    await games_in(session_factory, crowded, now - timedelta(hours=3))
    assert [one["tag"] for one in await hottest(client, tomek)] == ["HOTTEST", None]


async def test_growing_needs_four_new_and_a_quarter_of_today_s_players(
    client, clock, club
):
    crowd = await people(client, *(f"p{n}" for n in range(1, 18)))
    tomek = await a_player(client, "tomek")
    big = await a_group_of(client, crowd[0], club, *crowd[1:13], name="Big")
    clock.move(timedelta(days=31))
    # +4 of 17: four new, but under a quarter of today's players.
    for member in crowd[13:17]:
        await joins(client, member, big, owner=crowd[0])
    # +4 of 4, and +3 of 3.
    four = await a_group_of(client, crowd[0], club, *crowd[1:4], name="Four")
    three = await a_group_of(client, crowd[0], club, *crowd[1:3], name="Three")

    row = await hottest(client, tomek)

    tags = {one["id"]: one["tag"] for one in row}
    assert tags == {big["id"]: None, four["id"]: "GROWING", three["id"]: None}
    assert card(row, big)["new_this_month"] == 4


async def test_six_cards_hottest_then_growing_then_untagged_which_drop_out_first(
    client, session_factory, clock, club
):
    old = await people(client, *(f"old{n}" for n in range(1, 7)))
    new = await people(client, *(f"new{n}" for n in range(1, 5)))
    tomek = await a_player(client, "tomek")
    # Untagged, by heat: 6, 5, 4 and 3 old players.
    untagged = [
        await a_group_of(client, old[0], club, *old[1:size], name=f"Old {size}")
        for size in (3, 4, 5, 6)
    ]
    clock.move(timedelta(days=31))
    # GROWING: four new each, 16. HOTTEST: four new and two games, 20.
    growing = [
        await a_group_of(client, new[0], club, *new[1:], name=f"Growing {n}")
        for n in (1, 2)
    ]
    hot = await a_group_of(client, new[0], club, *new[1:], name="Hot")
    now = clock.now()
    await games_in(
        session_factory, hot, now - timedelta(days=1), now - timedelta(days=2)
    )

    row = await hottest(client, tomek)

    assert [one["tag"] for one in row] == [
        "HOTTEST",
        "GROWING",
        "GROWING",
        None,
        None,
        None,
    ]
    assert row[0]["id"] == hot["id"]
    assert {one["id"] for one in row[1:3]} == {group["id"] for group in growing}
    # The untagged by heat, and the coolest of four cut.
    assert [one["name"] for one in row[3:]] == ["Old 6", "Old 5", "Old 4"]
    assert untagged[0]["id"] not in {one["id"] for one in row}


async def test_a_group_under_three_players_is_left_out(client, club):
    owner, ania, bartek, tomek = await people(
        client, "owner", "ania", "bartek", "tomek"
    )
    group = await a_group_of(client, owner, club, ania, name="Two of us")

    assert await hottest(client, tomek) == []

    await joins(client, bartek, group, owner=owner)
    assert named(await hottest(client, tomek)) == ["Two of us"]

    # One leaving takes it off the row on the next read.
    await leaves(client, bartek, group)
    assert await hottest(client, tomek) == []


# --------------------------------------------------------------------------- #
# The card: everything the sheet shows
# --------------------------------------------------------------------------- #


async def befriends(client, asker: dict, answerer: dict) -> None:
    asked = await client.post(
        "/api/v1/friends/requests",
        json={"player_id": str(answerer["id"]), "made_from": "RECORD"},
        headers=asker["headers"],
    )
    assert asked.status_code == 200, asked.text
    accepted = await client.post(
        f"/api/v1/friends/requests/{asker['id']}/acceptance",
        headers=answerer["headers"],
    )
    assert accepted.status_code == 200, accepted.text


async def test_faces_are_friends_first_then_the_longest_standing_never_the_reader(
    client, club
):
    owner, ania, bartek, celina, darek, ewa, filip, gosia = await people(
        client, "owner", "ania", "bartek", "celina", "darek", "ewa", "filip", "gosia"
    )
    tomek = await a_player(client, "tomek")
    await a_group_of(
        client,
        owner,
        club,
        ania,
        tomek,
        bartek,
        celina,
        darek,
        ewa,
        filip,
        gosia,
        name="Kazimierz crew",
    )
    await befriends(client, tomek, gosia)
    await befriends(client, filip, tomek)

    [only] = await hottest(client, tomek)

    assert [face["nickname"] for face in only["faces"]] == [
        "filip",
        "gosia",
        "owner",
        "ania",
        "bartek",
        "celina",
    ]
    assert only["friends_count"] == 2
    # A face is a nickname and a photograph, and nothing else.
    assert set(only["faces"][0]) == {"player_id", "nickname"}
    # Another reader sees the same group in joining order, Tomek among them.
    [theirs] = await hottest(client, owner)
    assert [face["nickname"] for face in theirs["faces"]] == [
        "ania",
        "tomek",
        "bartek",
        "celina",
        "darek",
        "ewa",
    ]
    assert theirs["friends_count"] == 0


async def test_a_player_group_card_says_who_runs_it_and_where_it_plays(client, club):
    karol, ania, bartek, tomek = await people(
        client, "karol.n", "ania", "bartek", "tomek"
    )
    group = await a_group_of(
        client,
        karol,
        club,
        ania,
        bartek,
        name="Ogrody wieczorem",
        join_policy="PEOPLE_I_APPROVE",
    )

    [only] = await hottest(client, tomek)

    assert only == {
        "id": group["id"],
        "kind": "PLAYER",
        "name": "Ogrody wieczorem",
        "monogram": group["monogram"],
        "sports": [],
        "member_count": 3,
        "join_policy": "PEOPLE_I_APPROVE",
        "run_by": "karol.n",
        "club": {"id": club["id"], "name": "Ogrody 33"},
        "games_this_week": 0,
        "new_this_month": 3,
        "heat_share": 1.0,
        "tag": None,
        "faces": [
            {"player_id": str(karol["id"]), "nickname": "karol.n"},
            {"player_id": str(ania["id"]), "nickname": "ania"},
            {"player_id": str(bartek["id"]), "nickname": "bartek"},
        ],
        "friends_count": 0,
        "relation": "NONE",
        "is_administrator": False,
    }


async def test_the_dots_are_the_group_s_own(client, club):
    owner = await a_padel_player(client, "owner")
    ania = await a_padel_player(client, "ania")
    bartek, tomek = await people(client, "bartek", "tomek")
    await a_group_of(client, owner, club, ania, bartek, name="Padel")

    [only] = await hottest(client, tomek)

    assert only["sports"] == ["PADEL"]


@pytest.fixture
def rating_loads(monkeypatch: pytest.MonkeyPatch) -> list[UUID]:
    """Every rating stream the store loads, in the order it loads them."""

    loads: list[UUID] = []
    original = SqlAlchemyEventStore.load_stream

    async def counting(self, *, aggregate_type: str, aggregate_id: UUID):
        if aggregate_type == RATING_AGGREGATE:
            loads.append(aggregate_id)
        return await original(
            self, aggregate_type=aggregate_type, aggregate_id=aggregate_id
        )

    monkeypatch.setattr(SqlAlchemyEventStore, "load_stream", counting)
    return loads


async def test_the_dots_replay_no_rating_and_ask_whether_once(
    client, club, rating_loads
):
    """**A dot needs whether, never a figure**: the row asks which of its
    members' rating streams exist, about every member and every sport at once,
    and replays none of them — where it once loaded a stream per member per
    sport, most of them streams that do not exist."""

    owner = await a_padel_player(client, "owner", Sport.TENNIS)
    ania = await a_padel_player(client, "ania", Sport.TENNIS)
    bartek, tomek = await people(client, "bartek", "tomek")
    await a_group_of(client, owner, club, ania, bartek, name="Padel")
    rating_loads.clear()

    [only] = await hottest(client, tomek)

    assert only["sports"] == ["PADEL", "TENNIS"]
    assert rating_loads == []


async def test_the_reader_s_relation_to_each_group(client, club):
    owner, ania, bartek, tomek = await people(
        client, "owner", "ania", "bartek", "tomek"
    )
    mine = await a_group_of(client, owner, club, ania, tomek, name="Mine")
    asked = await a_group_of(
        client, owner, club, ania, bartek, name="Asked", join_policy="PEOPLE_I_APPROVE"
    )
    other = await a_group_of(client, owner, club, ania, bartek, name="Other")
    assert (await join(client, tomek, asked)).json()["relation"] == "REQUESTED"

    row = await hottest(client, tomek)

    assert {one["id"]: one["relation"] for one in row} == {
        mine["id"]: "MEMBER",
        asked["id"]: "REQUESTED",
        other["id"]: "NONE",
    }


@pytest.fixture
async def ogrody(client):
    """Ogrody 33 — padel and tennis — and its desk's session."""

    club_id, desk = await club_signs_up(client, sports=("PADEL", "TENNIS"))
    return {"id": club_id, "desk": desk}


@pytest.fixture
async def marta(client, ogrody, mailbox):
    """Marta, whom the desk made an administrator; she set her password by the
    invitation's link and is signed in."""

    row = await invites(client, ogrody["desk"], name="Marta Wójcik", email=MARTA)
    headers = await marta_sets_her_password(client, mailbox)
    return {
        "id": (await me(client, headers))["id"],
        "headers": headers,
        "administrator_id": row["id"],
    }


async def test_an_official_group_is_run_by_its_club_and_its_runner_reads_join(
    client, ogrody
):
    tomek = await an_administrator_who_plays(client, ogrody, "tomek")
    ania, bartek, celina, kuba = await people(
        client, "ania", "bartek", "celina", "kuba"
    )
    club_group = await an_official_group(client, tomek, ogrody["id"])
    for player in (ania, bartek, celina):
        await join(client, player, club_group)
        approved = await answer(
            client, tomek, ogrody["id"], club_group, player, "approve"
        )
        assert approved.status_code == 204, approved.text

    [as_tomek] = await hottest(client, tomek)
    [as_kuba] = await hottest(client, kuba)

    assert (as_tomek["kind"], as_tomek["run_by"]) == ("OFFICIAL", "Ogrody 33")
    assert as_tomek["sports"] == ["PADEL"]
    # Tomek runs it and is not in it: his chip is Join, which admits him.
    assert (as_tomek["is_administrator"], as_tomek["relation"]) == (True, "NONE")
    assert (as_kuba["is_administrator"], as_kuba["relation"]) == (False, "NONE")
    assert as_kuba["run_by"] == "Ogrody 33"


async def test_a_non_member_reads_the_card_but_the_group_page_stays_members_only(
    client, club
):
    owner, ania, bartek, tomek = await people(
        client, "owner", "ania", "bartek", "tomek"
    )
    group = await a_group_of(client, owner, club, ania, bartek, name="Kazimierz")

    assert named(await hottest(client, tomek)) == ["Kazimierz"]
    page = await read(client, tomek, group)
    assert page.status_code == 404
    assert page.json()["code"] == "group_not_found"


async def test_the_row_needs_a_player(client):
    assert (await client.get(HOTTEST)).status_code == 401


# --------------------------------------------------------------------------- #
# Withdrawing a Join request
# --------------------------------------------------------------------------- #


async def owners_requests(client, owner: dict, group: dict) -> list[str]:
    read_ = await client.get(
        f"{GROUPS}/{group['id']}/requests", headers=owner["headers"]
    )
    assert read_.status_code == 200, read_.text
    return [request["nickname"] for request in read_.json()["requests"]]


async def test_withdrawing_takes_the_request_off_the_owner_s_list(client, club):
    owner, ania, bartek, tomek, kasia = await people(
        client, "owner", "ania", "bartek", "tomek", "kasia"
    )
    group = await a_group_of(
        client,
        owner,
        club,
        ania,
        bartek,
        name="Ogrody wieczorem",
        join_policy="PEOPLE_I_APPROVE",
    )
    await join(client, tomek, group)
    await join(client, kasia, group)
    assert await owners_requests(client, owner, group) == ["tomek", "kasia"]

    withdrawn = await withdraws(client, tomek, group)

    assert withdrawn.status_code == 204, withdrawn.text
    assert await owners_requests(client, owner, group) == ["kasia"]
    assert card(await hottest(client, tomek), group)["relation"] == "NONE"
    # He may ask again, as after a decline.
    assert (await join(client, tomek, group)).json()["relation"] == "REQUESTED"
    assert await owners_requests(client, owner, group) == ["kasia", "tomek"]


async def test_withdrawing_takes_it_off_the_administrator_s_and_the_club_s_lists(
    client, ogrody, marta
):
    club_group = await an_official_group(client, marta, ogrody["id"])
    tomek, kasia = await people(client, "tomek", "kasia")
    await join(client, tomek, club_group)
    await join(client, kasia, club_group)

    withdrawn = await withdraws(client, tomek, club_group)

    assert withdrawn.status_code == 204, withdrawn.text
    page = await page_of(client, marta, ogrody["id"], club_group)
    assert [request["player_id"] for request in page["requests"]] == [str(kasia["id"])]
    queue = await client.get(requests_of(club_group), headers=ogrody["desk"])
    assert [request["nickname"] for request in queue.json()["requests"]] == ["kasia"]
    (row,) = await the_club_s_groups(client, ogrody)
    assert row["waiting_count"] == 1


async def test_withdrawing_what_is_not_waiting_changes_nothing_and_succeeds(
    client, club
):
    owner, ania, tomek, kasia = await people(client, "owner", "ania", "tomek", "kasia")
    group = await a_group_of(
        client, owner, club, ania, name="Closed", join_policy="PEOPLE_I_APPROVE"
    )
    await join(client, tomek, group)
    await join(client, kasia, group)
    # Kasia's was approved a moment before she withdrew it.
    approved = await client.post(
        f"{GROUPS}/{group['id']}/requests/{kasia['id']}/approve",
        headers=owner["headers"],
    )
    assert approved.status_code == 204, approved.text

    first = await withdraws(client, tomek, group)
    again = await withdraws(client, tomek, group)
    after_approval = await withdraws(client, kasia, group)
    never_asked = await withdraws(client, ania, group)

    assert [
        answer_.status_code for answer_ in (first, again, after_approval, never_asked)
    ] == [204, 204, 204, 204]
    assert (await read(client, kasia, group)).status_code == 200
    assert await owners_requests(client, owner, group) == []


async def test_withdrawing_from_a_group_deleted_meanwhile_still_succeeds(client, club):
    """The Owner alone deletes the group while Tomek's *Asked* sheet is open:
    the requests went with it, and his tap is not an error."""

    owner, tomek = await people(client, "owner", "tomek")
    group = await a_group(client, owner, club, join_policy="PEOPLE_I_APPROVE")
    await join(client, tomek, group)
    deleted = await client.delete(f"{GROUPS}/{group['id']}", headers=owner["headers"])
    assert deleted.status_code == 204, deleted.text

    late = await withdraws(client, tomek, group)
    nowhere = await client.delete(
        f"{GROUPS}/{new_uuid()}/join-request", headers=tomek["headers"]
    )

    assert (late.status_code, nowhere.status_code) == (204, 204)


async def test_withdrawing_tells_nobody(client, club, mailbox):
    owner, ania, bartek, tomek = await people(
        client, "owner", "ania", "bartek", "tomek"
    )
    group = await a_group_of(
        client, owner, club, ania, bartek, name="Closed", join_policy="PEOPLE_I_APPROVE"
    )
    await join(client, tomek, group)
    await mailbox.drain()
    told_before = await notices(client, owner)
    emails_before = len(mailbox.mailer.sent)

    withdrawn = await withdraws(client, tomek, group)
    await mailbox.drain()

    assert withdrawn.status_code == 204, withdrawn.text
    assert await notices(client, owner) == told_before
    assert await notices(client, tomek) == []
    assert len(mailbox.mailer.sent) == emails_before


async def notices(client, player: dict) -> list:
    read_ = await client.get(NOTICES, headers=player["headers"])
    assert read_.status_code == 200, read_.text
    return read_.json()["notices"]
