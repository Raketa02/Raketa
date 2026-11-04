"""The club's desk reads ``ania.k``, not a name (#725).

``docs/adr/0199``: the **Name** is retired, and the club surface says what its
player fields hold. Bonarka Arena's desk reads Saturday's booking — Ania, who
picked ``ania.k``, Kuba, Ewa and Tomek — and every seat carries a
``nickname``; Ogrody 33's desk reads ``ania.k`` asking to join *Ogrody 33
Club*, with her Levels. **The Administrators keep the name their club typed**
(§4): Tomek plays as ``tomek.k`` and the desk still reads *Tomek Kowal* on its
table, on the invitation, as who runs a group and on the handover. And **the
club's emails carry no player at all** — *New bookings today* and *a game was
called off at the cut-off* name the hour, the court and the sport, and nobody.

Every act is taken over HTTP as the website and the phone take it; every claim
is read where the desk would read it.
"""

from __future__ import annotations

import pytest

from app.api.dependencies import get_clock
from app.bootstrap.composition import build_summarise_new_bookings
from app.core.config import get_settings
from app.kernel import Sport
from tests.api.administration_world import (
    MARTA,
    accept_path,
    club_signs_up,
    invites,
    listed,
    marta_sets_her_password,
    me,
)
from tests.api.proposals_world import (
    MONDAY_MORNING,
    a_club_and_its_desk,
    a_group,
    a_player,
    makes,
    says_yes,
    the_cut_off_comes,
    warsaw,
)
from tests.api.test_club_groups import (
    CLUB_GROUPS,
    hands_over,
    the_club_s_groups,
    the_club_s_queue,
)
from tests.api.test_groups import a_rated_player, join
from tests.api.test_official_groups import an_official_group
from tests.unit.fake_clock import MovableClock

ANIA = "ania.k"
BOOKINGS = "/api/v1/club/bookings"
DESK_EMAIL = "desk@bonarka.pl"
SATURDAY = "2026-10-10"


@pytest.fixture
def clock(app):
    """Monday 5 October 2026, 08:00 in Kraków."""

    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


@pytest.fixture
async def bonarka(client) -> tuple[str, dict]:
    return await a_club_and_its_desk(client)


@pytest.fixture
async def ogrody(client) -> dict:
    """Ogrody 33 — padel and tennis — and its desk's session."""

    club_id, desk = await club_signs_up(client, sports=("PADEL", "TENNIS"))
    return {"id": club_id, "desk": desk}


@pytest.fixture
async def marta(client, ogrody, mailbox) -> dict:
    """Marta, whom the desk made an administrator, signed in by her
    invitation's link."""

    await invites(client, ogrody["desk"], name="Marta Wójcik", email=MARTA)
    headers = await marta_sets_her_password(client, mailbox)
    return {"id": (await me(client, headers))["id"], "headers": headers}


@pytest.fixture
async def four(client, payments) -> list[dict]:
    """Kuba, Ewa, Tomek and Ania — who signed up as ``ania.k@example.com`` and
    named herself ``ania.k``."""

    return [
        await a_player(client, payments, name)
        for name in ("kuba", "ewa", "tomek", ANIA)
    ]


@pytest.fixture
async def booking(client, session_factory, clock, bonarka, four) -> str:
    """The four's game on Saturday at 17:00 at Bonarka, booked by Ania's yes."""

    club_id, _ = bonarka
    group = await a_group(client, four[0], club_id, *four[1:])
    proposal = await makes(
        session_factory, clock, pool_id=group, club_id=club_id, versions=(tuple(four),)
    )
    for player in four[:3]:
        assert (await says_yes(client, player, proposal)).status_code == 200
    last = await says_yes(client, four[3], proposal)
    assert last.status_code == 200, last.text
    return last.json()["booked"]["booking_id"]


# --------------------------------------------------------------------------- #
# A booking
# --------------------------------------------------------------------------- #


async def test_the_desk_reads_ania_k_on_saturday_s_booking(client, bonarka, booking):
    _, desk = bonarka

    read = await client.get(
        BOOKINGS, params={"date": SATURDAY, "filter": "ALL"}, headers=desk
    )

    assert read.status_code == 200, read.text
    [row] = read.json()["bookings"]
    assert row["booking_id"] == booking
    assert sorted(player["nickname"] for player in row["players"]) == [
        ANIA,
        "ewa",
        "kuba",
        "tomek",
    ]
    # The nickname, whether they paid and whether it is held — and nothing
    # called ``name``.
    assert all(
        set(player) == {"player_id", "nickname", "paid", "held"}
        for player in row["players"]
    )


async def test_the_desk_s_emails_never_say_ania_k(
    client, session_factory, clock, mailbox, booking, four
):
    """Monday's *New bookings today*, and Saturday's game called off at the
    cut-off once Ania left it and nobody took her seat: the hour, the court
    and the sport, and no player."""

    clock.move(warsaw(5, 23) - clock.now())
    async with session_factory() as session:
        await build_summarise_new_bookings(
            session, clock=clock, settings=get_settings()
        ).execute()
    ania = four[3]
    left = await client.post(
        f"/api/v1/bookings/{booking}/departure", headers=ania["headers"]
    )
    assert left.status_code == 200, left.text
    await mailbox.drain()
    await the_cut_off_comes(session_factory, clock)

    told = await mailbox.to(DESK_EMAIL)

    assert sorted(one.subject for one in told) == [
        "A game was called off at the cut-off — the hour is free again",
        "New bookings today",
    ]
    for one in told:
        assert "Court 1" in one.text
        for player in (ANIA, "kuba", "ewa", "tomek"):
            assert player not in one.text, (one.subject, player)


# --------------------------------------------------------------------------- #
# A Join request, and the Administrators
# --------------------------------------------------------------------------- #


async def test_the_desk_reads_ania_k_asking_to_join_with_her_levels(
    client, ogrody, marta
):
    group = await an_official_group(client, marta, ogrody["id"])
    ania = await a_rated_player(client, ANIA, Sport.TENNIS, Sport.PADEL)
    asked = await join(client, ania, group)
    assert asked.json()["relation"] == "REQUESTED"

    [request] = await the_club_s_queue(client, ogrody, group)

    assert set(request) == {"player_id", "nickname", "levels"}
    assert (request["player_id"], request["nickname"]) == (str(ania["id"]), ANIA)
    assert [row["sport"] for row in request["levels"]] == ["PADEL", "TENNIS"]


async def test_an_administrator_who_plays_as_tomek_k_is_tomek_kowal_to_the_desk(
    client, ogrody, marta
):
    """The table, the invitation, *run by* and the handover all read the name
    the club typed — never the nickname he plays under."""

    group = await an_official_group(client, marta, ogrody["id"])
    tomek = await a_rated_player(client, "tomek.k", Sport.PADEL)
    invited = await invites(
        client, ogrody["desk"], name="Tomek Kowal", email="tomek.k@example.com"
    )
    accepted = await client.post(accept_path(invited["id"]), headers=tomek["headers"])
    assert accepted.status_code == 200, accepted.text

    handed = await hands_over(client, ogrody["desk"], group, invited["id"])

    assert invited["name"] == "Tomek Kowal"
    assert handed.status_code == 200, handed.text
    assert handed.json()["administrator"] == {
        "id": invited["id"],
        "name": "Tomek Kowal",
    }
    (row,) = await the_club_s_groups(client, ogrody)
    assert row["administrator"]["name"] == "Tomek Kowal"
    table = {one["id"]: one["name"] for one in await listed(client, ogrody["desk"])}
    assert table[invited["id"]] == "Tomek Kowal"
    groups = await client.get(CLUB_GROUPS, headers=ogrody["desk"])
    assert "tomek.k" not in groups.text
