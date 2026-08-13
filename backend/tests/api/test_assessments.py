"""HTTP flows for the assessment endpoints, plus event-stream assertions read
through the session factory (the same style as the event-delivery test)."""

from uuid import uuid4

import pytest
from sqlalchemy import select

from app.infrastructure.events.event_store_model import EventStoreORM

BOB = {
    "email": "bob@example.com",
    "password1": "hunter22!",
    "password2": "hunter22!",
    "nickname": "bob",
}


async def _auth_headers(client, payload) -> dict[str, str]:
    await client.post("/api/v1/users", json=payload)
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password1"]},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def _create(client, headers, sport="PADEL"):
    return await client.post(
        "/api/v1/assessments", json={"sport": sport}, headers=headers
    )


async def _answer(client, headers, assessment_id, question_id, option_id):
    return await client.post(
        f"/api/v1/assessments/{assessment_id}/answers",
        json={"question_id": question_id, "option_id": option_id},
        headers=headers,
    )


async def _get(client, headers, assessment_id):
    return await client.get(f"/api/v1/assessments/{assessment_id}", headers=headers)


async def _in_progress(client, headers, sport="PADEL"):
    return await client.get(
        "/api/v1/assessments/in-progress", params={"sport": sport}, headers=headers
    )


async def _abandon(client, headers, assessment_id):
    return await client.post(
        f"/api/v1/assessments/{assessment_id}/abandonment", headers=headers
    )


async def _run_to_result(client, headers, sport="PADEL", option=-1):
    """Answer whatever the server asks until it returns a result.

    The client cannot know which question is the last one — the engine decides it
    has enough only after an answer arrives — so the loop is exactly what a client
    must do: keep answering until ``question`` comes back null.
    """

    body = (await _create(client, headers, sport)).json()
    while body["question"] is not None:
        question = body["question"]
        resp = await _answer(
            client,
            headers,
            body["assessment_id"],
            question["id"],
            question["options"][option]["id"],
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
    return body


@pytest.mark.asyncio
async def test_create_returns_opening_question(client, valid_signup_payload):
    headers = await _auth_headers(client, valid_signup_payload)
    resp = await _create(client, headers)

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["assessment_id"]
    assert body["status"] == "in_progress"
    assert body["result"] is None
    question = body["question"]
    assert question["id"] == "opening.regularity"
    assert question["category"] and question["situation"] and question["text"]
    assert question["qualifier"]
    assert len(question["options"]) == 5


@pytest.mark.asyncio
async def test_create_requires_authentication(client):
    resp = await client.post("/api/v1/assessments", json={"sport": "PADEL"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_beginner_answer_returns_the_exact_result(client, valid_signup_payload):
    headers = await _auth_headers(client, valid_signup_payload)
    created = (await _create(client, headers)).json()

    resp = await _answer(
        client,
        headers,
        created["assessment_id"],
        created["question"]["id"],
        "never-played",
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["question"] is None
    assert body["status"] == "completed"
    result = body["result"]
    assert result["mu"] == 1.40
    assert result["sigma"] == 0.9821
    assert result["confidence"] == 18
    assert result["range"] == {"low": 1.0, "high": 2.38}
    assert result["band"] == {"name": "New", "lower": 1.0, "upper": 2.0}
    assert result["status"] == "Initial Estimate"
    assert result["questions_asked"] == 1
    assert result["engine_version"] == "racketskill-fusion-v3"


@pytest.mark.asyncio
async def test_completion_writes_both_streams_in_one_transaction(
    client, session_factory, valid_signup_payload
):
    headers = await _auth_headers(client, valid_signup_payload)
    created = (await _create(client, headers)).json()
    await _answer(
        client,
        headers,
        created["assessment_id"],
        created["question"]["id"],
        "never-played",
    )

    async with session_factory() as session:
        rows = (
            (
                await session.execute(
                    select(EventStoreORM).order_by(
                        EventStoreORM.aggregate_type, EventStoreORM.version
                    )
                )
            )
            .scalars()
            .all()
        )

    by_type = [(row.aggregate_type, row.event_type) for row in rows]
    # The assessment stream: started, asked, answered, completed.
    assert ("assessment", "rating.assessment_started") in by_type
    assert ("assessment", "rating.question_asked") in by_type
    assert ("assessment", "rating.answer_submitted") in by_type
    assert ("assessment", "rating.assessment_completed") in by_type
    # Completion and rating-initialisation land together, in the same store.
    assert ("skill_rating", "rating.rating_initialised") in by_type

    asked = [r for r in rows if r.event_type == "rating.question_asked"]
    assert asked and asked[0].payload["reason"] == "opening"


@pytest.mark.asyncio
async def test_resubmitting_the_answered_question_is_idempotent(
    client, session_factory, valid_signup_payload
):
    headers = await _auth_headers(client, valid_signup_payload)
    created = (await _create(client, headers)).json()
    aid, qid = created["assessment_id"], created["question"]["id"]

    first = (await _answer(client, headers, aid, qid, "never-played")).json()
    resp = await _answer(client, headers, aid, qid, "never-played")

    assert resp.status_code == 200, resp.text
    assert resp.json()["result"] == first["result"]

    # Records nothing on replay: exactly one answer and one rating-init survive.
    async with session_factory() as session:
        rows = (await session.execute(select(EventStoreORM))).scalars().all()
    event_types = [r.event_type for r in rows]
    assert event_types.count("rating.answer_submitted") == 1
    assert event_types.count("rating.assessment_completed") == 1
    assert event_types.count("rating.rating_initialised") == 1


@pytest.mark.asyncio
async def test_finished_assessment_conflicts_on_a_different_question(
    client, valid_signup_payload
):
    headers = await _auth_headers(client, valid_signup_payload)
    created = (await _create(client, headers)).json()
    aid, qid = created["assessment_id"], created["question"]["id"]
    await _answer(client, headers, aid, qid, "never-played")

    resp = await _answer(client, headers, aid, "some.other.question", "x")
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_invalid_option_is_rejected(client, valid_signup_payload):
    headers = await _auth_headers(client, valid_signup_payload)
    created = (await _create(client, headers)).json()
    resp = await _answer(
        client,
        headers,
        created["assessment_id"],
        created["question"]["id"],
        "not-an-option",
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_unknown_assessment_is_not_found(client, valid_signup_payload):
    headers = await _auth_headers(client, valid_signup_payload)
    resp = await _answer(client, headers, uuid4(), "opening.regularity", "never-played")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_a_player_cannot_touch_another_players_assessment(
    client, valid_signup_payload
):
    alice = await _auth_headers(client, valid_signup_payload)
    created = (await _create(client, alice)).json()
    aid, qid = created["assessment_id"], created["question"]["id"]

    bob = await _auth_headers(client, BOB)
    resp = await _answer(client, bob, aid, qid, "never-played")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_fetch_returns_the_outstanding_question(client, valid_signup_payload):
    headers = await _auth_headers(client, valid_signup_payload)
    created = (await _create(client, headers)).json()

    resp = await _get(client, headers, created["assessment_id"])

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "in_progress"
    assert body["result"] is None
    assert body["question"]["id"] == created["question"]["id"]


@pytest.mark.asyncio
async def test_fetch_a_finished_assessment_returns_its_result(
    client, valid_signup_payload
):
    headers = await _auth_headers(client, valid_signup_payload)
    created = (await _create(client, headers)).json()
    await _answer(
        client,
        headers,
        created["assessment_id"],
        created["question"]["id"],
        "never-played",
    )

    resp = await _get(client, headers, created["assessment_id"])

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "completed"
    assert body["question"] is None
    assert body["result"]["mu"] == 1.40


@pytest.mark.asyncio
async def test_fetch_another_players_assessment_is_not_found(
    client, valid_signup_payload
):
    alice = await _auth_headers(client, valid_signup_payload)
    created = (await _create(client, alice)).json()

    bob = await _auth_headers(client, BOB)
    resp = await _get(client, bob, created["assessment_id"])
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_in_progress_offers_the_run_to_resume(client, valid_signup_payload):
    headers = await _auth_headers(client, valid_signup_payload)
    created = (await _create(client, headers)).json()

    resp = await _in_progress(client, headers, "PADEL")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["assessment_id"] == created["assessment_id"]
    assert body["question"]["id"] == created["question"]["id"]


@pytest.mark.asyncio
async def test_in_progress_is_nothing_when_none_open(client, valid_signup_payload):
    headers = await _auth_headers(client, valid_signup_payload)
    resp = await _in_progress(client, headers, "PADEL")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_in_progress_is_scoped_to_the_sport(client, valid_signup_payload):
    headers = await _auth_headers(client, valid_signup_payload)
    await _create(client, headers, "PADEL")

    assert (await _in_progress(client, headers, "PADEL")).status_code == 200
    assert (await _in_progress(client, headers, "TENNIS")).status_code == 204


@pytest.mark.asyncio
async def test_resuming_continues_the_same_stream(
    client, session_factory, valid_signup_payload
):
    headers = await _auth_headers(client, valid_signup_payload)
    created = (await _create(client, headers)).json()

    resumed = (await _in_progress(client, headers, "PADEL")).json()
    done = (
        await _answer(
            client,
            headers,
            resumed["assessment_id"],
            resumed["question"]["id"],
            "never-played",
        )
    ).json()

    assert resumed["assessment_id"] == created["assessment_id"]
    assert done["status"] == "completed"

    # Resuming answered the existing run rather than starting a new one: exactly
    # one assessment stream exists.
    async with session_factory() as session:
        rows = (
            (
                await session.execute(
                    select(EventStoreORM).where(
                        EventStoreORM.aggregate_type == "assessment"
                    )
                )
            )
            .scalars()
            .all()
        )
    assert len({row.aggregate_id for row in rows}) == 1


@pytest.mark.asyncio
async def test_abandoning_ends_the_run_and_frees_the_sport(
    client, session_factory, valid_signup_payload
):
    headers = await _auth_headers(client, valid_signup_payload)
    first = (await _create(client, headers, "PADEL")).json()

    assert (await _abandon(client, headers, first["assessment_id"])).status_code == 204

    # The abandoned run is no longer offered for resume.
    assert (await _in_progress(client, headers, "PADEL")).status_code == 204
    # Its own state reads as abandoned, not as a question or a result.
    fetched = (await _get(client, headers, first["assessment_id"])).json()
    assert fetched["status"] == "abandoned"
    assert fetched["question"] is None and fetched["result"] is None

    # A new PADEL run can be started, and it is the one now offered.
    second = (await _create(client, headers, "PADEL")).json()
    assert second["assessment_id"] != first["assessment_id"]
    resumed = (await _in_progress(client, headers, "PADEL")).json()
    assert resumed["assessment_id"] == second["assessment_id"]

    async with session_factory() as session:
        abandoned = (
            (
                await session.execute(
                    select(EventStoreORM).where(
                        EventStoreORM.event_type == "rating.assessment_abandoned"
                    )
                )
            )
            .scalars()
            .all()
        )
    assert len(abandoned) == 1


@pytest.mark.asyncio
async def test_abandoning_one_sport_leaves_another_untouched(
    client, valid_signup_payload
):
    headers = await _auth_headers(client, valid_signup_payload)
    padel = (await _create(client, headers, "PADEL")).json()
    await _create(client, headers, "BADMINTON")

    await _abandon(client, headers, padel["assessment_id"])

    assert (await _in_progress(client, headers, "PADEL")).status_code == 204
    assert (await _in_progress(client, headers, "BADMINTON")).status_code == 200


@pytest.mark.asyncio
async def test_abandoning_a_finished_assessment_conflicts(client, valid_signup_payload):
    headers = await _auth_headers(client, valid_signup_payload)
    created = (await _create(client, headers)).json()
    await _answer(
        client,
        headers,
        created["assessment_id"],
        created["question"]["id"],
        "never-played",
    )

    resp = await _abandon(client, headers, created["assessment_id"])
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_abandoning_another_players_assessment_is_not_found(
    client, valid_signup_payload
):
    alice = await _auth_headers(client, valid_signup_payload)
    created = (await _create(client, alice)).json()

    bob = await _auth_headers(client, BOB)
    resp = await _abandon(client, bob, created["assessment_id"])
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_two_sports_are_independent(
    client, session_factory, valid_signup_payload
):
    headers = await _auth_headers(client, valid_signup_payload)

    padel = (await _create(client, headers, "PADEL")).json()
    badminton = (await _create(client, headers, "BADMINTON")).json()
    assert padel["assessment_id"] != badminton["assessment_id"]

    for assessment in (padel, badminton):
        done = (
            await _answer(
                client,
                headers,
                assessment["assessment_id"],
                assessment["question"]["id"],
                "never-played",
            )
        ).json()
        assert done["status"] == "completed"

    async with session_factory() as session:
        ratings = (
            (
                await session.execute(
                    select(EventStoreORM).where(
                        EventStoreORM.aggregate_type == "skill_rating"
                    )
                )
            )
            .scalars()
            .all()
        )
    assert len({row.aggregate_id for row in ratings}) == 2


# --- The explained result -------------------------------------------------------

RESULT_KEYS = {
    "mu",
    "sigma",
    "confidence",
    "range",
    "band",
    "status",
    "questions_asked",
    "engine_version",
    "calibration_priority",
    "confidence_reason",
    "factors",
    "uncertainty_factors",
}


@pytest.mark.asyncio
async def test_the_result_explains_itself(client, valid_signup_payload):
    headers = await _auth_headers(client, valid_signup_payload)
    result = (await _run_to_result(client, headers))["result"]

    assert set(result) == RESULT_KEYS
    assert result["calibration_priority"] in {"standard", "elevated"}

    # Every factor row carries a direction the server computed, and the client
    # is given the level it was computed from rather than being asked to trust it.
    assert result["factors"]
    for factor in result["factors"]:
        assert set(factor) == {"key", "label", "direction", "level"}
        assert factor["direction"] in {"up", "down", "neutral"}
        assert factor["key"] and factor["label"]

    for widened in result["uncertainty_factors"]:
        assert set(widened) == {"key", "label", "detail", "sigma_added"}
        assert widened["sigma_added"] > 0

    # The confidence sentence travels with the number it explains, so a wording
    # change never needs a mobile release.
    reason = result["confidence_reason"]
    assert set(reason) == {"key", "sentence"}
    assert reason["key"] and reason["sentence"].endswith(".")


@pytest.mark.asyncio
async def test_the_beginner_result_explains_itself_too(client, valid_signup_payload):
    headers = await _auth_headers(client, valid_signup_payload)
    created = (await _create(client, headers)).json()
    result = (
        await _answer(
            client,
            headers,
            created["assessment_id"],
            created["question"]["id"],
            "never-played",
        )
    ).json()["result"]

    # One answer, so one row — and the base confidence branch, because nothing
    # widened the range beyond the floor every onboarding rating sits at.
    assert [factor["key"] for factor in result["factors"]] == ["recent-activity"]
    assert result["uncertainty_factors"] == []
    assert result["confidence_reason"]["key"] == "limited-match-evidence"
    assert result["calibration_priority"] == "standard"


@pytest.mark.asyncio
async def test_the_payload_carries_no_presentation_values(client, valid_signup_payload):
    # Colours, glyphs and ordering are the client's, and the two clients do not
    # share a shape — a hex code here is a decision one of them would have to undo.
    headers = await _auth_headers(client, valid_signup_payload)
    result = (await _run_to_result(client, headers))["result"]

    def keys(node):
        if isinstance(node, dict):
            for key, value in node.items():
                yield key
                yield from keys(value)
        elif isinstance(node, list):
            for item in node:
                yield from keys(item)

    for key in keys(result):
        assert not any(
            word in key.lower()
            for word in ("colour", "color", "icon", "glyph", "emoji", "order", "sort")
        ), f"{key} looks like presentation"


@pytest.mark.asyncio
async def test_refetching_a_finished_assessment_returns_the_same_explanation(
    client, valid_signup_payload
):
    # The explanation is reproduced from the transcript rather than stored, so
    # this is the test that the reproduction is exact — a refetched result that
    # differed from the one the player was shown would be the worst kind of bug.
    headers = await _auth_headers(client, valid_signup_payload)
    finished = await _run_to_result(client, headers)

    fetched = (await _get(client, headers, finished["assessment_id"])).json()
    assert fetched["status"] == "completed"
    assert fetched["result"] == finished["result"]


@pytest.mark.asyncio
async def test_the_explanation_survives_a_retried_submission(
    client, valid_signup_payload
):
    headers = await _auth_headers(client, valid_signup_payload)
    created = (await _create(client, headers)).json()
    question_id = created["question"]["id"]
    first = (
        await _answer(
            client, headers, created["assessment_id"], question_id, "never-played"
        )
    ).json()

    # The same answer again: a lost response, retried. It records nothing and
    # returns the identical explained result.
    retried = (
        await _answer(
            client, headers, created["assessment_id"], question_id, "never-played"
        )
    ).json()
    assert retried["result"] == first["result"]


@pytest.mark.asyncio
async def test_completion_records_why_confidence_landed_where_it_did(
    client, session_factory, valid_signup_payload
):
    # The stable key is a fact and is recorded; the sentence it selects is copy
    # and is not, so a wording change is never a migration.
    headers = await _auth_headers(client, valid_signup_payload)
    finished = await _run_to_result(client, headers)
    expected = finished["result"]["confidence_reason"]["key"]

    async with session_factory() as session:
        rows = (
            (
                await session.execute(
                    select(EventStoreORM).where(
                        EventStoreORM.event_type.in_(
                            ("rating.assessment_completed", "rating.rating_initialised")
                        )
                    )
                )
            )
            .scalars()
            .all()
        )

    assert len(rows) == 2
    for row in rows:
        assert row.payload["confidence_reason_key"] == expected
        assert (
            row.payload["calibration_priority"]
            == finished["result"]["calibration_priority"]
        )
        assert "sentence" not in str(row.payload)
