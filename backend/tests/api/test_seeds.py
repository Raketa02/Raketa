"""Seed, sign in, and see the state the account is named for.

This is the acceptance criterion the whole ticket is for: a developer runs one
command and a screen has something predictable to be developed against. So it is
asserted the way a developer would meet it — over HTTP, signed in, with nothing
about the seed system visible except its address and its password.

**The replay is the second claim, and it is made through the API on purpose.**
Reading the event store back would prove the rows exist; it would not prove they
*are* the aggregate. `GET /assessments/{id}` rebuilds a run from its stream and
serves the question the seed left outstanding — and answering it then appends to
that same stream, which a fabricated row could not survive: the version the
append expects comes from the replay.

**The edges are what is asserted, because they are what breaks a screen.** An
account with nothing in it, an account whose run ended without a rating, the two
that share a band and differ inside it, and the one that fills a list. The middle
of the distribution needs no fixture; a hundred average players are one scenario
a hundred times.

The seed runs against the suite's own fixtures rather than a database of its own,
which is why `seed` takes a session. The `client` fixture overrides `get_db` with
the same factory, so the data seeded here is the data the requests see.
"""

from __future__ import annotations

import pytest

from app.kernel import Sport
from app.seeds.catalog import (
    ASSESSMENT_ABANDONED,
    ASSESSMENT_COMPLETED,
    ASSESSMENT_IN_PROGRESS,
    BRAND_NEW_PLAYER,
    RATED_IN_EVERY_SPORT,
    RATING_BARELY_ESTABLISHED,
    RATING_WELL_ESTABLISHED,
    SEED_PASSWORD,
    TESTERS,
    SeedAccount,
)
from app.seeds.runner import seed


@pytest.fixture
async def seeded(session_factory):
    """Every account, keyed by the slug that names its state."""

    async with session_factory() as session:
        return {entry.account.slug: entry for entry in await seed(session)}


async def _sign_in(client, account: SeedAccount, password: str = SEED_PASSWORD) -> dict:
    login = await client.post(
        "/api/v1/auth/login", json={"email": account.email, "password": password}
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def _ratings(client, headers) -> dict[str, dict]:
    response = await client.get("/api/v1/ratings", headers=headers)
    assert response.status_code == 200, response.text
    return {rating["sport"]: rating for rating in response.json()["ratings"]}


async def _open_runs(client, headers) -> list[dict]:
    response = await client.get("/api/v1/assessments/in-progress", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()["assessments"]


async def test_every_seeded_address_signs_in_and_is_who_it_says(client, seeded):
    """One password, every address, and the name and nickname the catalog dealt.

    ``First Last`` and a lowercase handle without a dot (``docs/adr/0171`` §5):
    a seeded court reads *Diego Fabregat left* and never *Diego.Fabregat left*.

    **And a Tester exactly when the catalog says so** (``docs/adr/0180`` §9):
    ``/me`` is where the player app reads the mark it hands to flag evaluation,
    so a seeded tester is one the app would really treat as one.
    """

    testers_seen = 0
    for entry in seeded.values():
        headers = await _sign_in(client, entry.account)

        me = await client.get("/api/v1/users/me", headers=headers)

        assert me.status_code == 200, me.text
        assert me.json()["email"] == entry.account.email
        assert me.json()["name"] == entry.account.name
        assert me.json()["nickname"] == entry.account.nickname
        assert " " in entry.account.name and "." not in entry.account.name
        assert entry.account.nickname == entry.account.nickname.lower()
        assert "." not in entry.account.nickname
        assert me.json()["is_tester"] is (entry.account in TESTERS), entry.account.slug
        testers_seen += entry.account in TESTERS

    assert testers_seen == len(TESTERS)


async def test_the_brand_new_player_has_every_empty_state_at_once(client, seeded):
    """The account an empty screen is drawn from: registered and nothing else.

    Empty is a state, and it is the one a client is least likely to have a
    fixture for — every other seeded account has *something*, so without this one
    the empty list is only ever seen on a database nobody has seeded.
    """

    headers = await _sign_in(client, BRAND_NEW_PLAYER)

    assert await _open_runs(client, headers) == []
    assert await _ratings(client, headers) == {}


async def test_the_open_run_is_at_its_first_question_and_replays(client, seeded):
    """`assessment-in-progress`: one open run, at its first question, no rating.

    The replay is the claim direct table writes would break, made where it can
    be seen. A row inserted into the event store by hand reads back fine. What it
    cannot do is be *replayed into an aggregate* that then accepts an append at
    the version the replay reports — so answering the seeded question, and
    receiving the next one, is the strongest statement available here that the
    seed used the real write path.
    """

    headers = await _sign_in(client, ASSESSMENT_IN_PROGRESS)
    assessment_id = seeded[ASSESSMENT_IN_PROGRESS.slug].scenarios[0].assessment_id

    open_runs = await _open_runs(client, headers)
    assert len(open_runs) == 1
    assert open_runs[0]["sport"] == Sport.PADEL.value
    assert await _ratings(client, headers) == {}

    replayed = await client.get(f"/api/v1/assessments/{assessment_id}", headers=headers)
    assert replayed.status_code == 200, replayed.text
    step = replayed.json()
    assert step["status"] == "in_progress"
    assert step["questions_asked"] == 0
    assert step["transcript"] == []
    assert step["result"] is None
    assert step["question"] is not None

    question = step["question"]
    answered = await client.post(
        f"/api/v1/assessments/{assessment_id}/answers",
        json={
            "question_id": question["id"],
            "option_id": question["options"][0]["id"],
        },
        headers=headers,
    )

    assert answered.status_code == 200, answered.text
    step_after = answered.json()
    assert step_after["questions_asked"] == 1
    # The answer is on the stream the seed opened, not on one of its own: the
    # transcript served back is that stream replayed, and it now starts with the
    # question the seed left outstanding.
    assert step_after["transcript"][0]["question"]["id"] == question["id"]


async def test_the_abandoned_run_is_a_run_that_ended_without_a_rating(client, seeded):
    """The failed case, and the one every finder is silent about.

    An abandoned run is not open, so nothing offers it for resume and nothing
    lists it as a rating — which is exactly why the sport is free to be started
    again, and why an account in this state is worth having: the state is
    invisible to every read, and the only thing that shows it is the run itself.
    """

    headers = await _sign_in(client, ASSESSMENT_ABANDONED)
    assessment_id = seeded[ASSESSMENT_ABANDONED.slug].scenarios[0].assessment_id

    assert await _open_runs(client, headers) == []
    assert await _ratings(client, headers) == {}

    run = await client.get(f"/api/v1/assessments/{assessment_id}", headers=headers)
    assert run.status_code == 200, run.text
    assert run.json()["status"] == "abandoned"
    assert run.json()["result"] is None


async def test_the_completed_assessment_has_a_rating_and_the_run_behind_it(
    client, seeded
):
    """A finished run and the rating it produced, both readable.

    The transcript is asserted beside the rating because a rating written
    directly would have none — and a review screen renders the transcript, not
    the number.
    """

    headers = await _sign_in(client, ASSESSMENT_COMPLETED)
    assessment_id = seeded[ASSESSMENT_COMPLETED.slug].scenarios[0].assessment_id

    assert await _open_runs(client, headers) == []

    ratings = await _ratings(client, headers)
    assert set(ratings) == {Sport.PADEL.value}
    assert ratings[Sport.PADEL.value]["band"]["name"] == "New"
    # Every onboarding rating is a hypothesis, not a verdict.
    assert ratings[Sport.PADEL.value]["status"] == "Initial Estimate"

    run = await client.get(f"/api/v1/assessments/{assessment_id}", headers=headers)
    assert run.status_code == 200, run.text
    assert run.json()["status"] == "completed"
    assert run.json()["result"] is not None
    assert len(run.json()["transcript"]) == run.json()["questions_asked"] >= 1


async def test_the_two_established_accounts_differ_where_their_names_say(
    client, seeded
):
    """One band, two players — which is the whole point of having both.

    `barely` is named for a Level just inside the band's lower edge, with a
    likely range that still reaches down into Developing; `well` is clear of it.
    Asserted against the band's *own* edges, which travel on the rating, so a
    re-cut band moves the assertion with it rather than invalidating it.
    """

    barely = await _ratings(client, await _sign_in(client, RATING_BARELY_ESTABLISHED))
    well = await _ratings(client, await _sign_in(client, RATING_WELL_ESTABLISHED))

    one = barely[Sport.PADEL.value]
    other = well[Sport.PADEL.value]

    assert one["band"]["name"] == other["band"]["name"] == "Established"
    assert one["band"] == other["band"]
    assert one["mu"] < other["mu"]

    lower = one["band"]["lower"]
    width = one["band"]["upper"] - lower
    assert (one["mu"] - lower) / width <= 0.25
    assert (other["mu"] - lower) / width >= 0.6

    # The card that has to draw a band its own range does not stay inside.
    assert one["range"]["low"] < lower


async def test_every_sport_is_rated_and_no_two_share_a_band(client, seeded):
    """The maximum a ratings screen is asked for: one row per sport, four bands.

    The list is the read model with the most ways to be wrong — ordering, the
    band pill, a missing sport — and it is the one no other account exercises
    past a single row.
    """

    headers = await _sign_in(client, RATED_IN_EVERY_SPORT)

    ratings = await _ratings(client, headers)

    assert set(ratings) == {sport.value for sport in Sport}
    bands = [rating["band"]["name"] for rating in ratings.values()]
    assert sorted(bands) == sorted({"New", "Developing", "Established", "Advanced"})
    for rating in ratings.values():
        assert rating["range"]["low"] <= rating["mu"] <= rating["range"]["high"]

    # Every sport rated means no sport left to assess.
    assert await _open_runs(client, headers) == []


async def test_seeding_twice_leaves_one_account_and_one_run(
    client, session_factory, seeded
):
    """Idempotency as a developer meets it: run it again, nothing doubles."""

    async with session_factory() as session:
        again = {entry.account.slug: entry for entry in await seed(session)}

    assert {slug: entry.player_id for slug, entry in again.items()} == {
        slug: entry.player_id for slug, entry in seeded.items()
    }

    headers = await _sign_in(client, ASSESSMENT_IN_PROGRESS)
    open_runs = await _open_runs(client, headers)

    assert len(open_runs) == 1
    assert open_runs[0]["assessment_id"] == str(
        seeded[ASSESSMENT_IN_PROGRESS.slug].scenarios[0].assessment_id
    )

    every_sport = await _sign_in(client, RATED_IN_EVERY_SPORT)
    assert len(await _ratings(client, every_sport)) == len(Sport)
