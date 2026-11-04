"""**Get your level — once per account, ever** (#727; ``docs/adr/0200`` §7; the
mechanics §17.2, Q126) — read from outside.

Ania signs up as ``ania.k``, joins Kuba's *Wednesday padel* rated in nothing,
and closes the app. A day later she is told, once and never again: *Get your
level so your groups can deal you games.* — a notice about no game at all,
always on, opening **Home**, pushed to her phone and never emailed. Kuba, who
is rated, is never told.

Every act is taken over HTTP as the phone sends it, the job is run by its
builder as the scheduler runs it each tick, and every claim is read off the
list behind the bell and the phone's pushes. The clock starts on Monday 5
October, 08:00 in Kraków, and moves.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from app.api.dependencies import get_clock
from app.bootstrap.composition import build_tell_get_your_level
from app.kernel import Sport
from app.modules.notifications.domain.notices import (
    GET_YOUR_LEVEL_AFTER,
    GET_YOUR_LEVEL_WITHIN,
)
from tests.api.administration_world import (
    MARTA,
    club_signs_up,
    invites,
    marta_sets_her_password,
    me,
)
from tests.api.proposals_world import MONDAY_MORNING
from tests.api.test_groups import a_club, a_group, a_player, a_rated_player, join
from tests.api.test_official_groups import an_official_group, answer
from tests.unit.fake_clock import MovableClock

NOTICES = "/api/v1/players/me/notices"
CHOICES = "/api/v1/players/me/notifications"
KIND = "GET_YOUR_LEVEL"
A_DAY = timedelta(hours=24)


@pytest.fixture
def clock(app):
    """Monday 5 October 2026, 08:00 in Kraków."""

    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


@pytest.fixture
async def club(client) -> dict:
    return await a_club(client)


@pytest.fixture
async def kuba(client) -> dict:
    """Rated in padel, and the Owner of *Wednesday padel*."""

    return await a_rated_player(client, "kuba", Sport.PADEL)


@pytest.fixture
async def wednesday_padel(client, clock, club, kuba) -> dict:
    return await a_group(client, kuba, club, name="Wednesday padel")


@pytest.fixture
async def ania(client) -> dict:
    """``ania.k``, rated in nothing, with a phone."""

    player = await a_player(client, "ania.k")
    await has_a_phone(client, player, "ania")
    return player


async def has_a_phone(client, player: dict, name: str) -> None:
    token = f"ExponentPushToken[{name}-phone]"
    registered = await client.post(
        "/api/v1/players/me/devices", json={"token": token}, headers=player["headers"]
    )
    assert registered.status_code == 204, registered.text
    player["phone"] = token


async def joins(client, player: dict, group: dict) -> None:
    joined = await join(client, player, group)
    assert joined.json()["relation"] == "MEMBER", joined.text


async def leaves(client, player: dict, group: dict) -> None:
    left = await client.delete(
        f"/api/v1/groups/{group['id']}/membership", headers=player["headers"]
    )
    assert left.status_code in (200, 204), left.text


async def a_day_passes(session_factory, clock, *, by: timedelta = A_DAY) -> None:
    """The clock moves on, and the job's own unit of work runs, as the
    scheduler runs it each tick."""

    clock.move(by)
    async with session_factory() as session:
        await build_tell_get_your_level(session, clock=clock).execute()


async def told(client, player: dict) -> list[dict]:
    """Every *Get your level* in the player's list, newest first."""

    read = await client.get(NOTICES, headers=player["headers"])
    assert read.status_code == 200, read.text
    return [notice for notice in read.json()["notices"] if notice["kind"] == KIND]


def pushed(pushes, player: dict) -> list:
    return [push for push in pushes.to(player["phone"]) if push.data["kind"] == KIND]


# --------------------------------------------------------------------------- #
# Told once
# --------------------------------------------------------------------------- #


async def test_a_day_after_joining_unrated_she_is_told_to_get_her_level(
    client, session_factory, clock, mailbox, pushes, ania, wednesday_padel
):
    await joins(client, ania, wednesday_padel)

    await a_day_passes(session_factory, clock)
    await mailbox.drain()

    [notice] = await told(client, ania)
    assert (notice["title"], notice["body"]) == (
        "Get your level so your groups can deal you games.",
        "Pick the sports you play — a few questions each.",
    )
    # About no game: it names no group and no sport, and opens Home.
    assert notice["opens"] == "HOME"
    assert (
        notice["game_id"],
        notice["pool_id"],
        notice["sport"],
        notice["game_kind"],
    ) == (None, None, None, None)
    assert notice["new"] is True and notice["your_own"] is False
    # Given a day after the join, whenever the job came to it.
    assert notice["given_at"].startswith("2026-10-06T06:00:00")
    [push] = pushed(pushes, ania)
    assert (push.title, push.body) == (notice["title"], notice["body"])
    assert dict(push.data) == {
        "notice_id": notice["notice_id"],
        "kind": KIND,
        "opens": "HOME",
    }
    # Never emailed.
    assert not [
        one for one in await mailbox.to("ania.k@example.com") if "level" in one.text
    ]


async def test_a_second_run_tells_nothing(
    client, session_factory, clock, mailbox, pushes, ania, wednesday_padel
):
    await joins(client, ania, wednesday_padel)
    await a_day_passes(session_factory, clock)

    await a_day_passes(session_factory, clock, by=timedelta(minutes=5))
    await a_day_passes(session_factory, clock)
    await mailbox.drain()

    assert len(await told(client, ania)) == 1
    assert len(pushed(pushes, ania)) == 1


async def test_joining_a_second_group_tells_nothing_more(
    client, session_factory, clock, mailbox, pushes, club, kuba, ania, wednesday_padel
):
    await joins(client, ania, wednesday_padel)
    await a_day_passes(session_factory, clock)
    friday_tennis = await a_group(client, kuba, club, name="Friday tennis")

    await joins(client, ania, friday_tennis)
    await a_day_passes(session_factory, clock)
    await mailbox.drain()

    assert len(await told(client, ania)) == 1
    assert len(pushed(pushes, ania)) == 1


async def test_leaving_the_first_group_for_a_later_one_tells_nothing_more(
    client, session_factory, clock, mailbox, club, kuba, ania, wednesday_padel
):
    """Once per account, ever — not once per first join: told a day after
    *Wednesday padel*, she joins *Friday tennis* and leaves the first, and a
    day after the second join she is still told once."""

    await joins(client, ania, wednesday_padel)
    await a_day_passes(session_factory, clock)
    friday_tennis = await a_group(client, kuba, club, name="Friday tennis")
    await joins(client, ania, friday_tennis)
    await leaves(client, ania, wednesday_padel)

    await a_day_passes(session_factory, clock)
    await mailbox.drain()

    assert len(await told(client, ania)) == 1


async def test_it_is_always_on_whatever_she_chose(
    client, session_factory, clock, mailbox, ania, wednesday_padel
):
    """Not one of the three a player chooses: switching all three off leaves
    it on."""

    off = await client.put(
        CHOICES,
        json={
            "you_complete_it": False,
            "challenges_for_you": False,
            "fill_in_alerts": False,
        },
        headers=ania["headers"],
    )
    assert off.status_code == 200, off.text
    await joins(client, ania, wednesday_padel)

    await a_day_passes(session_factory, clock)
    await mailbox.drain()

    assert len(await told(client, ania)) == 1


async def test_an_official_group_counts_from_the_moment_she_is_let_in(
    client, session_factory, clock, mailbox, ania
):
    """*Ogrody 33 Club* approves joins: Ania asks at 08:00 and Marta lets her
    in at 10:00, so her day runs from 10:00 — and Marta, who runs the group
    and never joined it, is no member and is told nothing."""

    club_id, desk = await club_signs_up(client)
    await invites(client, desk, name="Marta Wójcik", email=MARTA)
    marta_headers = await marta_sets_her_password(client, mailbox)
    marta = {"id": (await me(client, marta_headers))["id"], "headers": marta_headers}
    ogrody_33_club = await an_official_group(client, marta, club_id)
    asked = await join(client, ania, ogrody_33_club)
    assert asked.json()["relation"] == "REQUESTED", asked.text
    clock.move(timedelta(hours=2))
    let_in = await answer(client, marta, club_id, ogrody_33_club, ania, "approve")
    assert let_in.status_code == 204, let_in.text

    await a_day_passes(session_factory, clock, by=timedelta(hours=23))
    await mailbox.drain()
    assert await told(client, ania) == []

    await a_day_passes(session_factory, clock, by=timedelta(hours=1))
    await mailbox.drain()

    [notice] = await told(client, ania)
    assert notice["given_at"].startswith("2026-10-06T08:00:00")
    assert await told(client, marta) == []


# --------------------------------------------------------------------------- #
# Never told
# --------------------------------------------------------------------------- #


async def test_a_run_more_than_a_week_past_her_day_tells_nothing(
    client, session_factory, clock, mailbox, ania, wednesday_padel
):
    """A run that reaches an account later than ``GET_YOUR_LEVEL_WITHIN`` past
    its day — the process down that long — tells nothing; Home's card still
    asks."""

    await joins(client, ania, wednesday_padel)

    await a_day_passes(
        session_factory,
        clock,
        by=GET_YOUR_LEVEL_AFTER + GET_YOUR_LEVEL_WITHIN + timedelta(minutes=1),
    )
    await mailbox.drain()

    assert await told(client, ania) == []


async def test_at_twenty_three_hours_she_is_not_told_yet(
    client, session_factory, clock, mailbox, pushes, ania, wednesday_padel
):
    await joins(client, ania, wednesday_padel)

    await a_day_passes(session_factory, clock, by=timedelta(hours=23))
    await mailbox.drain()

    assert await told(client, ania) == []
    assert pushed(pushes, ania) == []


async def test_a_player_with_any_rating_is_never_told(
    client, session_factory, clock, mailbox, wednesday_padel
):
    """Rated in tennis, joining a padel group: any rating is enough — the
    group's door asks her for padel, and the notice is for the rated-in-nothing
    alone."""

    ola = await a_rated_player(client, "ola", Sport.TENNIS)
    await joins(client, ola, wednesday_padel)

    await a_day_passes(session_factory, clock)
    await mailbox.drain()

    assert await told(client, ola) == []


async def test_the_owner_who_is_rated_is_never_told(
    client, session_factory, clock, mailbox, kuba, wednesday_padel
):
    await a_day_passes(session_factory, clock)
    await mailbox.drain()

    assert await told(client, kuba) == []


async def test_a_player_who_left_every_group_is_never_told(
    client, session_factory, clock, mailbox, pushes, ania, wednesday_padel
):
    await joins(client, ania, wednesday_padel)
    await leaves(client, ania, wednesday_padel)

    await a_day_passes(session_factory, clock)
    await mailbox.drain()

    assert await told(client, ania) == []
    assert pushed(pushes, ania) == []


async def test_a_player_in_no_group_is_never_told(
    client, session_factory, clock, mailbox, ania, wednesday_padel
):
    await a_day_passes(session_factory, clock)
    await mailbox.drain()

    assert await told(client, ania) == []
