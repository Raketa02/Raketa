"""Seed, sign in, and see the state the account is named for.

This is the acceptance criterion the whole ticket is for: a developer runs one
command and a screen has something predictable to be developed against. So it is
asserted the way a developer would meet it — over HTTP, signed in, with nothing
about the seed system visible except its address and its password.

**The replay is the second claim, and it is made through the API on purpose.**
Reading the event store back would prove the rows exist; it would not prove they
*are* the aggregate. `GET /assessments/{id}` rebuilds the run from its stream and
serves the question the seed left outstanding — and answering it then appends to
that same stream, which a fabricated row could not survive: the version the
append expects comes from the replay.

The seed runs against the suite's own fixtures rather than a database of its own,
which is why `seed` takes a session. The `client` fixture overrides `get_db` with
the same factory, so the data seeded here is the data the requests see.
"""

from __future__ import annotations

import pytest

from app.seeds.catalog import ASSESSMENT_IN_PROGRESS, SEED_PASSWORD
from app.seeds.runner import seed


@pytest.fixture
async def seeded(session_factory):
    async with session_factory() as session:
        return await seed(session)


async def _sign_in(client, email: str, password: str = SEED_PASSWORD) -> dict:
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def test_signing_in_as_the_seeded_address_works(client, seeded):
    headers = await _sign_in(client, ASSESSMENT_IN_PROGRESS.email)

    me = await client.get("/api/v1/users/me", headers=headers)

    assert me.status_code == 200, me.text
    assert me.json()["email"] == ASSESSMENT_IN_PROGRESS.email
    assert me.json()["nickname"] == ASSESSMENT_IN_PROGRESS.nickname


async def test_the_account_is_in_the_state_its_name_promises(client, seeded):
    """`assessment-in-progress`: one open run, at its first question, no rating."""

    headers = await _sign_in(client, ASSESSMENT_IN_PROGRESS.email)

    open_runs = await client.get("/api/v1/assessments/in-progress", headers=headers)
    assert open_runs.status_code == 200, open_runs.text
    assessments = open_runs.json()["assessments"]
    assert len(assessments) == 1
    assert assessments[0]["sport"] == ASSESSMENT_IN_PROGRESS.sport.value

    ratings = await client.get("/api/v1/ratings", headers=headers)
    assert ratings.status_code == 200, ratings.text
    assert ratings.json()["ratings"] == []


async def test_the_seeded_assessment_replays_and_accepts_the_next_answer(
    client, seeded
):
    """The claim direct table writes would break, made where it can be seen.

    A row inserted into the event store by hand reads back fine. What it cannot
    do is be *replayed into an aggregate* that then accepts an append at the
    version the replay reports — so answering the seeded question, and receiving
    the next one, is the strongest statement available here that the seed used
    the real write path.
    """

    headers = await _sign_in(client, ASSESSMENT_IN_PROGRESS.email)
    assessment_id = seeded[0].assessment_id

    replayed = await client.get(
        f"/api/v1/assessments/{assessment_id}", headers=headers
    )
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
    # Which option was offered first is the engine's business and may change, so
    # nothing here asserts what the run does next — only that it went on.
    assert step_after["status"] == "in_progress"


async def test_seeding_twice_leaves_one_account_and_one_run(
    client, session_factory, seeded
):
    """Idempotency as a developer meets it: run it again, nothing doubles."""

    async with session_factory() as session:
        again = await seed(session)

    assert [entry.player_id for entry in again] == [
        entry.player_id for entry in seeded
    ]

    headers = await _sign_in(client, ASSESSMENT_IN_PROGRESS.email)
    open_runs = await client.get("/api/v1/assessments/in-progress", headers=headers)

    assert len(open_runs.json()["assessments"]) == 1
    assert open_runs.json()["assessments"][0]["assessment_id"] == str(
        seeded[0].assessment_id
    )
