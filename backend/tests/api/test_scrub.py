"""The clock a developer can move, and the two screens it makes reachable.

`tests/api/test_demo_week.py` proves the seeded week's *data* and says in its own
docstring what it cannot prove: the week is anchored to a fixed Monday in
September 2026, so the post-play conversation — a played match waiting for a
score, and a score waiting for an answer — is true only between Tuesday 21:00
and Wednesday 21:00 on that week, and no wall clock is ever there. Signing in
showed `full` before the week and `playedNoScore` after it. There was no day on
which a person could look at the screens ADR-0048 and ADR-0060 specify
(`Raketa02/Raketa#134`).

**This file is that gap closed, asserted the way the gap was described.** It
signs in over HTTP, moves the process's clock over HTTP, and reads the result
route over HTTP — no composition root, no clock handed in by a fixture. What it
proves is a *developer's experience*, which is the one thing the walkthrough
beside it could not.

Two more things are asserted here because nothing else can see them: that the
route is absent when the setting is off, and that it is on neither client's
contract. Both are one line away from being false in `create_app`, and a router
mounted one line higher would be a route both clients generate a type for.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.contract import SURFACES, build_surface_spec
from app.core.config import get_settings
from app.infrastructure.database.session import get_db
from app.kernel import Situation
from app.main import create_app
from app.seeds.catalog import ACCOUNTS, SEED_PASSWORD, SeedAccount
from app.seeds.matches import seed_moment
from app.seeds.runner import Seeded, seed

#: Tuesday 8 September 2026, 21:30 UTC — half an hour after the seeded squash
#: match ended and half an hour after a padel score went on the table. It is the
#: instant `match-played-and-unscored` and `match-with-a-score-on-the-table` are
#: **both** in the states they are named for, and it is the middle of the
#: twenty-four-hour window the issue says nothing could reach.
THE_EVENING = seed_moment(day_offset=1, hour=21, minute=30)

#: Who is sitting on those two matches. A scenario that names no seats is filled
#: from the head of the account catalog, skipping the account whose name promises
#: an empty screen — so this is the runner's own rule, read off the catalog
#: rather than copied as a slug that would rot silently the day the order moves.
FIRST_SEATED: SeedAccount = next(one for one in ACCOUNTS if not one.holds_nothing)

NEEDS_A_SCORE = "match-played-and-unscored"
AWAITING_AN_ANSWER = "match-with-a-score-on-the-table"


@pytest_asyncio.fixture
async def scrubbable(monkeypatch, session_factory):
    """An application whose clock can be moved, over the suite's own database.

    Configured through the process environment rather than by handing
    `create_app` a settings object, because the request dependencies read
    `get_settings()` — an application told one thing while its dependencies
    believed another would be a test proving nothing about a real process.

    `tests/conftest.py` puts the clock back after every test, so a scrub made
    here cannot reach the next one.
    """

    monkeypatch.setenv("CLOCK_SCRUBBABLE", "true")
    get_settings.cache_clear()
    app = create_app()

    async def _get_db_override():
        async with session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = _get_db_override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
    get_settings.cache_clear()


@pytest.fixture
async def week(session_factory) -> Seeded:
    """The whole seeded week, once, through the use cases a request runs."""

    async with session_factory() as session:
        return await seed(session)


def match_id(week: Seeded, slug: str) -> UUID:
    return next(one.match_id for one in week.matches if one.match.slug == slug)


async def token_for(client: AsyncClient, account: SeedAccount) -> str:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": account.email, "password": SEED_PASSWORD},
    )
    assert login.status_code == 200, login.text
    return login.json()["access_token"]


async def result_seen_by(client: AsyncClient, token: str, match: UUID) -> dict:
    response = await client.get(
        f"/api/v1/matches/{match}/result",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    return response.json()


# --- The two screens that had no day ----------------------------------------


async def test_the_post_play_conversation_is_reachable_by_signing_in(
    scrubbable, week
):
    """`Raketa02/Raketa#134`'s first problem, closed and asserted as such.

    Everything here is a request: the sign-in, the scrub and the two reads. On
    the wall clock these two matches read `full` — they have not been played yet
    — and this is the whole of what it takes for a developer to be standing in
    the hour where they are what they are named for.
    """

    token = await token_for(scrubbable, FIRST_SEATED)

    scrub = await scrubbable.post("/_clock", json={"at": THE_EVENING.isoformat()})
    assert scrub.status_code == 200, scrub.text

    unscored = await result_seen_by(scrubbable, token, match_id(week, NEEDS_A_SCORE))
    on_the_table = await result_seen_by(
        scrubbable, token, match_id(week, AWAITING_AN_ANSWER)
    )

    assert unscored["situation"]["situation"] == Situation.NEEDS_RESULT
    assert on_the_table["situation"]["situation"] == Situation.CONFIRM_RESULT


async def test_the_same_two_matches_say_something_else_on_the_wall_clock(
    scrubbable, week
):
    """The state of the world the issue describes, kept as the control.

    Without this, the test above would pass just as happily against a seeded
    week that had been quietly re-anchored to today — and the thing being
    asserted would no longer be the clock.
    """

    token = await token_for(scrubbable, FIRST_SEATED)

    unscored = await result_seen_by(scrubbable, token, match_id(week, NEEDS_A_SCORE))

    assert unscored["situation"]["situation"] != Situation.NEEDS_RESULT


async def test_the_screen_asks_for_a_score_and_not_only_for_a_name(scrubbable, week):
    """ADR-0074's three booleans, at the instant they mean something.

    A situation name is what a card prints; what a *screen* is for is the act
    beside it. Somebody seated on an unscored match may enter one, and that is
    the difference between the data being right and the screen being reachable.
    """

    token = await token_for(scrubbable, FIRST_SEATED)
    await scrubbable.post("/_clock", json={"at": THE_EVENING.isoformat()})

    unscored = await result_seen_by(scrubbable, token, match_id(week, NEEDS_A_SCORE))

    assert unscored["may_enter"] is True
    assert unscored["settlement_deadline"] is not None


# --- What the route itself does ---------------------------------------------


async def test_it_reports_the_host_clock_before_anybody_moves_it(scrubbable):
    reading = await scrubbable.get("/_clock")

    assert reading.status_code == 200, reading.text
    body = reading.json()
    assert body["scrubbed"] is False
    assert body["displaced_by_seconds"] == 0
    # Two reads of a running clock, so they are close rather than equal — the
    # displacement is what says they are the same clock.
    assert abs(
        (
            datetime.fromisoformat(body["now"])
            - datetime.fromisoformat(body["wall_clock"])
        ).total_seconds()
    ) < 1


async def test_a_scrub_outlives_the_request_that_made_it(scrubbable):
    """The reason the clock is the process's and not the request's.

    A clock built per request would answer 200 to the move and forget it on the
    way out, and the only symptom would be a screen that did not change.
    """

    await scrubbable.post("/_clock", json={"at": THE_EVENING.isoformat()})

    body = (await scrubbable.get("/_clock")).json()

    assert body["scrubbed"] is True
    assert abs(
        (datetime.fromisoformat(body["now"]) - THE_EVENING).total_seconds()
    ) < 60


async def test_the_host_clock_is_still_reported_underneath_a_scrub(scrubbable):
    """*Where you are* and *where you really are*, in one answer."""

    body = (
        await scrubbable.post("/_clock", json={"at": THE_EVENING.isoformat()})
    ).json()

    wall = datetime.fromisoformat(body["wall_clock"])
    assert abs((wall - datetime.now(timezone.utc)).total_seconds()) < 60


async def test_releasing_puts_the_host_clock_back(scrubbable):
    await scrubbable.post("/_clock", json={"at": THE_EVENING.isoformat()})

    released = await scrubbable.delete("/_clock")

    assert released.status_code == 200, released.text
    assert released.json()["scrubbed"] is False
    assert (await scrubbable.get("/_clock")).json()["displaced_by_seconds"] == 0


async def test_a_scrub_can_run_backwards_as_readily_as_forwards(scrubbable):
    """The seeded week is ahead of a laptop today and behind one next year."""

    last_year = datetime.now(timezone.utc) - timedelta(days=365)

    body = (await scrubbable.post("/_clock", json={"at": last_year.isoformat()})).json()

    assert body["displaced_by_seconds"] < 0


async def test_an_instant_with_no_offset_is_refused(scrubbable):
    """A 422 naming the field, rather than a 500 out of the kernel."""

    refused = await scrubbable.post("/_clock", json={"at": "2026-09-08T21:30:00"})

    assert refused.status_code == 422, refused.text


# --- Where the route is not -------------------------------------------------


async def test_there_is_no_clock_route_unless_somebody_asked_for_one(client):
    """The default application, which is the one every other suite builds.

    Off is the shipped state in all four environments, and the settings object
    refuses `CLOCK_SCRUBBABLE` anywhere but `local` — so this is what a
    deployment has, and it has no way to be told otherwise.
    """

    move = await client.post("/_clock", json={"at": "2026-09-08T21:30:00Z"})

    assert (await client.get("/_clock")).status_code == 404
    assert move.status_code == 404


@pytest.mark.parametrize("surface", sorted(SURFACES))
def test_neither_client_contract_mentions_the_clock(surface):
    """It is mounted on the application, never on a surface router.

    The two documents are emitted from those routers, so a route added there
    would be a type in both generated clients and a phone able to move the
    server's clock. This is that claim as an assertion rather than as a comment
    in `create_app`.
    """

    spec = build_surface_spec(f"Raketa {surface.capitalize()} API", SURFACES[surface])

    assert not [path for path in spec["paths"] if "clock" in path.lower()]
