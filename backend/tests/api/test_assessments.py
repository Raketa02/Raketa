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
    "adult_attested": True,
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


async def _all_in_progress(client, headers):
    """The same route with the sport left off — every unfinished run at once."""

    return await client.get("/api/v1/assessments/in-progress", headers=headers)


async def _abandon(client, headers, assessment_id):
    return await client.post(
        f"/api/v1/assessments/{assessment_id}/abandonment", headers=headers
    )


async def _complete(client, headers, assessment_id):
    return await client.post(
        f"/api/v1/assessments/{assessment_id}/completion", headers=headers
    )


async def _run_to_stop(client, headers, sport="PADEL", option=-1):
    """Answer whatever the server asks until it stops asking.

    The client cannot know which question is the last one — the engine decides it
    has enough only after an answer arrives — so the loop is exactly what a client
    must do: keep answering until ``question`` comes back null. The step it ends
    on carries neither a question nor a result, and no rating exists yet.
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


async def _run_to_result(client, headers, sport="PADEL", option=-1):
    """Answer to the stop, then ask for the rating — the whole client flow.

    Two moments, not one: the rating is created by ``POST /completion``, which is
    the only irreversible call a player makes (``docs/adr/0020``).
    """

    stopped = await _run_to_stop(client, headers, sport, option)
    resp = await _complete(client, headers, stopped["assessment_id"])
    assert resp.status_code == 200, resp.text
    return resp.json()


async def _beginner_to_result(client, headers, sport="PADEL"):
    """The shortest run there is: *I have never played*, then the rating."""

    created = (await _create(client, headers, sport)).json()
    stopped = (
        await _answer(
            client,
            headers,
            created["assessment_id"],
            created["question"]["id"],
            "never-played",
        )
    ).json()
    resp = await _complete(client, headers, stopped["assessment_id"])
    assert resp.status_code == 200, resp.text
    return resp.json()


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


# --- Starting is idempotent per player and sport --------------------------------


async def _assessment_stream_ids(session_factory) -> set:
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
    return {row.aggregate_id for row in rows}


@pytest.mark.asyncio
async def test_starting_twice_for_one_sport_returns_the_open_run(
    client, session_factory, valid_signup_payload
):
    # A double-tapped confirm, or a retry after a response lost in flight. Before
    # the guard this opened a second stream and stranded one of them: the
    # in-progress lookup answers with a single run, so the other was neither
    # resumable nor abandonable through any client path.
    headers = await _auth_headers(client, valid_signup_payload)
    first = (await _create(client, headers, "PADEL")).json()

    resp = await _create(client, headers, "PADEL")

    assert resp.status_code == 200, resp.text
    second = resp.json()
    assert second["assessment_id"] == first["assessment_id"]
    assert second["question"]["id"] == first["question"]["id"]
    assert second["status"] == "in_progress"

    assert len(await _assessment_stream_ids(session_factory)) == 1


@pytest.mark.asyncio
async def test_the_second_start_returns_the_outstanding_question_not_the_opening_one(
    client, valid_signup_payload
):
    # Idempotent means *resumed*, not "replayed from the top". A start that
    # handed back the opening question of a run already several answers deep
    # would re-ask something answered and be rejected by the aggregate.
    headers = await _auth_headers(client, valid_signup_payload)
    created = (await _create(client, headers, "PADEL")).json()
    mid_run = (
        await _answer(
            client,
            headers,
            created["assessment_id"],
            created["question"]["id"],
            "regular",
        )
    ).json()
    assert mid_run["question"] is not None
    assert mid_run["question"]["id"] != created["question"]["id"]

    resp = await _create(client, headers, "PADEL")

    assert resp.status_code == 200, resp.text
    assert resp.json()["question"]["id"] == mid_run["question"]["id"]


@pytest.mark.asyncio
async def test_starting_after_a_completed_run_is_refused(
    client, session_factory, valid_signup_payload
):
    # This test used to assert the opposite — that a rated sport can always be
    # rated again — and the assertion held only because it stopped at the start.
    # Answering that second run to the end appended a second opening event to a
    # rating stream keyed by (player, sport), which the store rejects, so the
    # player got a 500 on the last answer of a questionnaire they had just
    # finished (#53).
    #
    # The run is refused where refusing is free instead. Whether re-rating
    # should *replace* the rating is a live question; the transition that would
    # answer it belongs to the match-update engine.
    headers = await _auth_headers(client, valid_signup_payload)
    finished = await _run_to_result(client, headers, "PADEL")
    assert finished["status"] == "completed"

    resp = await _create(client, headers, "PADEL")

    assert resp.status_code == 409, resp.text
    assert resp.json()["code"] == "sport_already_rated"
    # Nothing was opened: the one stream is the run that produced the rating.
    assert len(await _assessment_stream_ids(session_factory)) == 1


@pytest.mark.asyncio
async def test_a_rated_sport_does_not_block_an_unrated_one(
    client, valid_signup_payload
):
    # The refusal is per sport, like every other guard on this endpoint. A
    # player rated at padel is still a player who has never played tennis.
    headers = await _auth_headers(client, valid_signup_payload)
    await _run_to_result(client, headers, "PADEL")

    resp = await _create(client, headers, "TENNIS")

    assert resp.status_code == 201, resp.text
    assert resp.json()["question"]["id"] == "opening.regularity"


@pytest.mark.asyncio
async def test_starting_after_an_abandoned_run_opens_a_new_one(
    client, session_factory, valid_signup_payload
):
    headers = await _auth_headers(client, valid_signup_payload)
    abandoned = (await _create(client, headers, "PADEL")).json()
    await _abandon(client, headers, abandoned["assessment_id"])

    resp = await _create(client, headers, "PADEL")

    assert resp.status_code == 201, resp.text
    assert resp.json()["assessment_id"] != abandoned["assessment_id"]
    assert len(await _assessment_stream_ids(session_factory)) == 2


@pytest.mark.asyncio
async def test_the_guard_is_scoped_to_one_sport(client, valid_signup_payload):
    # A player may hold in-progress runs for several sports at once, and that is
    # correct — the guard must not read one sport's open run as another's.
    headers = await _auth_headers(client, valid_signup_payload)
    padel = (await _create(client, headers, "PADEL")).json()

    resp = await _create(client, headers, "BADMINTON")

    assert resp.status_code == 201, resp.text
    assert resp.json()["assessment_id"] != padel["assessment_id"]


@pytest.mark.asyncio
async def test_the_guard_is_scoped_to_one_player(client, valid_signup_payload):
    # Alice's open PADEL run must not be handed to Bob, nor stop him starting his
    # own — the lookup is keyed by player as well as sport.
    alice = await _auth_headers(client, valid_signup_payload)
    hers = (await _create(client, alice, "PADEL")).json()

    bob = await _auth_headers(client, BOB)
    resp = await _create(client, bob, "PADEL")

    assert resp.status_code == 201, resp.text
    assert resp.json()["assessment_id"] != hers["assessment_id"]


@pytest.mark.asyncio
async def test_the_resumed_start_and_the_in_progress_read_agree(
    client, valid_signup_payload
):
    # Two routes answering the same question must not disagree about which run is
    # open, or the entry gate and the sports picker would route to different runs.
    headers = await _auth_headers(client, valid_signup_payload)
    first = (await _create(client, headers, "PADEL")).json()

    restarted = (await _create(client, headers, "PADEL")).json()
    resumed = (await _in_progress(client, headers, "PADEL")).json()

    # All three name the run the *first* call opened. Asserting only that the
    # last two agree would pass without the guard at all, because both would
    # then name the second run the restart had just created.
    assert restarted["assessment_id"] == first["assessment_id"]
    assert resumed["assessment_id"] == first["assessment_id"]
    assert restarted["question"]["id"] == resumed["question"]["id"]


@pytest.mark.asyncio
async def test_both_start_outcomes_are_stated_on_the_operation():
    # A client can only rely on the idempotence if the contract says so — this is
    # what the generated types and a reader of the document both see.
    from app.api.contract import build_surface_spec
    from app.api.v1.player import player_api_router

    operation = build_surface_spec("player", player_api_router)["paths"][
        "/api/v1/assessments"
    ]["post"]

    assert "Idempotent per player and sport" in operation["description"]
    for code in ("200", "201"):
        schema = operation["responses"][code]["content"]["application/json"]["schema"]
        assert schema["$ref"].endswith("/AssessmentStepResponse")
        assert operation["responses"][code]["description"]


@pytest.mark.asyncio
async def test_beginner_answer_returns_the_exact_result(client, valid_signup_payload):
    headers = await _auth_headers(client, valid_signup_payload)
    body = await _beginner_to_result(client, headers)

    assert body["question"] is None
    assert body["status"] == "completed"
    result = body["result"]
    assert result["mu"] == 1.40
    assert result["sigma"] == 0.9821
    assert result["confidence"] == 18
    assert result["range"] == {"low": 1.0, "high": 2.38}
    assert result["band"] == {"name": "New", "lower": 1.0, "upper": 1.5}
    assert result["status"] == "Initial Estimate"
    assert result["questions_asked"] == 1
    assert result["engine_version"] == "racketskill-fusion-v3"


@pytest.mark.asyncio
async def test_completion_writes_both_streams_in_one_transaction(
    client, session_factory, valid_signup_payload
):
    headers = await _auth_headers(client, valid_signup_payload)
    await _beginner_to_result(client, headers)

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
    # Both are the **stopped** step — no question left to ask, and nothing rated
    # — and the replay describes the run exactly as the answer that reached it
    # did, down to the transcript.
    assert first["question"] is None and first["result"] is None
    assert resp.json() == first

    # Records nothing on replay, and the answer that stopped the run recorded no
    # rating either: only completion does that.
    async with session_factory() as session:
        rows = (await session.execute(select(EventStoreORM))).scalars().all()
    event_types = [r.event_type for r in rows]
    assert event_types.count("rating.answer_submitted") == 1
    assert event_types.count("rating.assessment_completed") == 0
    assert event_types.count("rating.rating_initialised") == 0


@pytest.mark.asyncio
async def test_finished_assessment_conflicts_on_a_different_question(
    client, valid_signup_payload
):
    headers = await _auth_headers(client, valid_signup_payload)
    created = (await _create(client, headers)).json()
    aid, qid = created["assessment_id"], created["question"]["id"]
    await _answer(client, headers, aid, qid, "never-played")
    assert (await _complete(client, headers, aid)).status_code == 200

    resp = await _answer(client, headers, aid, "some.other.question", "x")
    assert resp.status_code == 409
    # Refetch the current step and re-render — the *other* 409 this endpoint
    # family can return means jump to the result, so the code is what separates
    # a double-tapped confirm from a second device on a finished assessment.
    assert resp.json()["code"] == "question_not_outstanding"


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
    assert resp.json()["code"] == "invalid_answer_option"


@pytest.mark.asyncio
async def test_unknown_assessment_is_not_found(client, valid_signup_payload):
    headers = await _auth_headers(client, valid_signup_payload)
    resp = await _answer(client, headers, uuid4(), "opening.regularity", "never-played")
    assert resp.status_code == 404
    assert resp.json()["code"] == "assessment_not_found"


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
    finished = await _beginner_to_result(client, headers)

    resp = await _get(client, headers, finished["assessment_id"])

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


# --- One read for every sport ---------------------------------------------------
#
# The entry gate asks "is any run unfinished" on every cold launch. Asked one
# sport at a time it cost four requests for an answer that is almost always no.


@pytest.mark.asyncio
async def test_the_collection_answers_for_every_sport_in_one_read(
    client, valid_signup_payload
):
    headers = await _auth_headers(client, valid_signup_payload)
    padel = (await _create(client, headers, "PADEL")).json()
    squash = (await _create(client, headers, "SQUASH")).json()

    resp = await _all_in_progress(client, headers)

    assert resp.status_code == 200, resp.text
    assert resp.json()["assessments"] == [
        {"assessment_id": padel["assessment_id"], "sport": "PADEL"},
        {"assessment_id": squash["assessment_id"], "sport": "SQUASH"},
    ]


@pytest.mark.asyncio
async def test_the_collection_is_empty_rather_than_an_error_when_none_are_open(
    client, valid_signup_payload
):
    # The ordinary state of a new account, and the answer the gate gets on almost
    # every launch. Absence of an unfinished run is not a failure, so it is a 200
    # with an empty list — never the singular form's 204, and never a 404.
    headers = await _auth_headers(client, valid_signup_payload)

    resp = await _all_in_progress(client, headers)

    assert resp.status_code == 200, resp.text
    assert resp.json() == {"assessments": []}


@pytest.mark.asyncio
async def test_the_collection_is_ordered_by_the_sport_registry(
    client, valid_signup_payload
):
    # Started back-to-front on purpose. A caller that wants one run takes the
    # first entry, so the order must be the registry's and not the order the
    # player happened to start them in.
    headers = await _auth_headers(client, valid_signup_payload)
    for sport in ("BADMINTON", "SQUASH", "TENNIS", "PADEL"):
        await _create(client, headers, sport)

    resp = await _all_in_progress(client, headers)

    assert [entry["sport"] for entry in resp.json()["assessments"]] == [
        "PADEL",
        "TENNIS",
        "SQUASH",
        "BADMINTON",
    ]


@pytest.mark.asyncio
async def test_the_collection_holds_only_unfinished_runs(client, valid_signup_payload):
    # Completed and abandoned runs are not unfinished, and the read is about
    # unfinished ones. A completed sport is rated; an abandoned one was decided
    # against. Returning either would send the gate back into a run that ended.
    headers = await _auth_headers(client, valid_signup_payload)
    await _run_to_result(client, headers, "TENNIS")
    abandoned = (await _create(client, headers, "SQUASH")).json()
    await _abandon(client, headers, abandoned["assessment_id"])
    open_run = (await _create(client, headers, "PADEL")).json()

    resp = await _all_in_progress(client, headers)

    assert resp.json()["assessments"] == [
        {"assessment_id": open_run["assessment_id"], "sport": "PADEL"}
    ]


@pytest.mark.asyncio
async def test_the_collection_is_scoped_to_the_player(client, valid_signup_payload):
    alice = await _auth_headers(client, valid_signup_payload)
    hers = (await _create(client, alice, "PADEL")).json()

    bob = await _auth_headers(client, BOB)
    his = (await _create(client, bob, "TENNIS")).json()

    assert (await _all_in_progress(client, alice)).json()["assessments"] == [
        {"assessment_id": hers["assessment_id"], "sport": "PADEL"}
    ]
    assert (await _all_in_progress(client, bob)).json()["assessments"] == [
        {"assessment_id": his["assessment_id"], "sport": "TENNIS"}
    ]


@pytest.mark.asyncio
async def test_the_collection_and_the_per_sport_read_name_the_same_run(
    client, valid_signup_payload
):
    # Two shapes of one question. A gate routing on the collection and a resume
    # reading the sport must never land on different runs.
    headers = await _auth_headers(client, valid_signup_payload)
    await _create(client, headers, "PADEL")
    body = (await _create(client, headers, "TENNIS")).json()
    await _answer_the_outstanding_question(client, headers, body)

    entries = (await _all_in_progress(client, headers)).json()["assessments"]

    for entry in entries:
        resumed = (await _in_progress(client, headers, entry["sport"])).json()
        assert resumed["assessment_id"] == entry["assessment_id"]
    assert {entry["sport"] for entry in entries} == {"PADEL", "TENNIS"}


@pytest.mark.asyncio
async def test_an_entry_carries_only_what_a_router_needs(client, valid_signup_payload):
    # No question, no result, no progress. The caller re-reads the run it routes
    # to, and reproducing four outstanding questions to answer "none" would make
    # the common case pay for data nobody reads.
    headers = await _auth_headers(client, valid_signup_payload)
    await _create(client, headers, "PADEL")

    entry = (await _all_in_progress(client, headers)).json()["assessments"][0]

    assert set(entry) == {"assessment_id", "sport"}


@pytest.mark.asyncio
async def test_supplying_the_sport_still_returns_that_sport_s_step(
    client, valid_signup_payload
):
    # The parameter is optional, not gone: the per-sport read is unchanged, and
    # the fan-out keeps working against it while the client migrates.
    headers = await _auth_headers(client, valid_signup_payload)
    created = (await _create(client, headers, "PADEL")).json()

    resp = await _in_progress(client, headers, "PADEL")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["assessment_id"] == created["assessment_id"]
    assert body["question"]["id"] == created["question"]["id"]
    assert body["questions_asked"] == 0
    assert "assessments" not in body


@pytest.mark.asyncio
async def test_the_collection_read_needs_authentication(client):
    assert (await client.get("/api/v1/assessments/in-progress")).status_code == 401


@pytest.mark.asyncio
async def test_both_in_progress_shapes_are_stated_on_the_operation():
    # A client can only rely on omitting the parameter if the document says so.
    # This is what the generated types and a reader of the contract both see.
    from app.api.contract import build_surface_spec
    from app.api.v1.player import player_api_router

    operation = build_surface_spec("player", player_api_router)["paths"][
        "/api/v1/assessments/in-progress"
    ]["get"]

    sport_param = next(p for p in operation["parameters"] if p["name"] == "sport")
    assert sport_param["required"] is False

    schema = operation["responses"]["200"]["content"]["application/json"]["schema"]
    refs = {option["$ref"].rsplit("/", 1)[-1] for option in schema["anyOf"]}
    assert refs == {"AssessmentStepResponse", "InProgressAssessmentsResponse"}

    entry = build_surface_spec("player", player_api_router)["components"]["schemas"][
        "InProgressAssessmentResponse"
    ]
    assert set(entry["required"]) == {"assessment_id", "sport"}


@pytest.mark.asyncio
async def test_resuming_continues_the_same_stream(
    client, session_factory, valid_signup_payload
):
    headers = await _auth_headers(client, valid_signup_payload)
    created = (await _create(client, headers)).json()

    resumed = (await _in_progress(client, headers, "PADEL")).json()
    await _answer(
        client,
        headers,
        resumed["assessment_id"],
        resumed["question"]["id"],
        "never-played",
    )
    done = (await _complete(client, headers, resumed["assessment_id"])).json()

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
    finished = await _beginner_to_result(client, headers)

    resp = await _abandon(client, headers, finished["assessment_id"])
    assert resp.status_code == 409
    # Jump to the result: the rating already exists. Distinguishable on the wire
    # from `question_not_outstanding`, which asks for the opposite recovery.
    assert resp.json()["code"] == "assessment_already_finished"


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
        await _answer(
            client,
            headers,
            assessment["assessment_id"],
            assessment["question"]["id"],
            "never-played",
        )
        done = (await _complete(client, headers, assessment["assessment_id"])).json()
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


# --- The question counter -------------------------------------------------------
#
# ``questions_asked`` on the step is what the client's "question N" counter reads.
# It counts the answers *behind* the player, so the outstanding question is not in
# it and a fresh run reports 0 — the position shown is one further along. Counting
# the outstanding question here would make the mid-run number and the finished
# result's number, which deliberately share a name, describe two different things.


async def _answer_the_outstanding_question(client, headers, body):
    """Answer whatever is outstanding with its last option, and return the step."""

    resp = await _answer(
        client,
        headers,
        body["assessment_id"],
        body["question"]["id"],
        body["question"]["options"][-1]["id"],
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


@pytest.mark.asyncio
async def test_a_fresh_run_has_no_answers_behind_it(client, valid_signup_payload):
    headers = await _auth_headers(client, valid_signup_payload)
    created = (await _create(client, headers)).json()

    assert created["questions_asked"] == 0


@pytest.mark.asyncio
async def test_each_answer_advances_the_count_by_one(client, valid_signup_payload):
    headers = await _auth_headers(client, valid_signup_payload)
    body = (await _create(client, headers)).json()

    counts = [body["questions_asked"]]
    while body["question"] is not None:
        body = await _answer_the_outstanding_question(client, headers, body)
        counts.append(body["questions_asked"])

    # 0, 1, 2, … — one step per answer, with no gap and no repeat.
    assert counts == list(range(len(counts)))
    assert len(counts) > 2, "a full run asks more than one question"


@pytest.mark.asyncio
async def test_a_resumed_run_reports_the_answers_already_given(
    client, valid_signup_payload
):
    # The defect this closes: a player who answered four questions yesterday came
    # back to their outstanding question and was told they were on question 1,
    # because the count was the client's own tally of what it had shown. The
    # transcript never lived on the device — which is what makes resume survive a
    # force-quit, a reinstall and a new handset — so only the server can answer it.
    headers = await _auth_headers(client, valid_signup_payload)
    body = (await _create(client, headers)).json()
    for _ in range(4):
        body = await _answer_the_outstanding_question(client, headers, body)
        assert body["question"] is not None, "the run ended before four answers"

    # Cold reads: a relaunch, a reinstall, a second handset. Neither knows anything
    # of the exchange above — the count is replayed from the stream.
    resumed = (await _in_progress(client, headers, "PADEL")).json()
    fetched = (await _get(client, headers, body["assessment_id"])).json()

    assert resumed["questions_asked"] == 4
    assert fetched["questions_asked"] == 4


@pytest.mark.asyncio
async def test_answering_and_reading_agree_on_the_count(client, valid_signup_payload):
    headers = await _auth_headers(client, valid_signup_payload)
    created = (await _create(client, headers)).json()

    answered = await _answer_the_outstanding_question(client, headers, created)
    fetched = (await _get(client, headers, created["assessment_id"])).json()

    assert answered["questions_asked"] == 1
    assert fetched["questions_asked"] == answered["questions_asked"]


@pytest.mark.asyncio
async def test_a_resumed_start_reports_the_count_too(client, valid_signup_payload):
    # Starting is idempotent, so a restart mid-run hands back the open run. It is a
    # read of an existing run like any other and must not report it as a fresh one.
    headers = await _auth_headers(client, valid_signup_payload)
    created = (await _create(client, headers)).json()
    await _answer_the_outstanding_question(client, headers, created)

    restarted = await _create(client, headers, "PADEL")

    assert restarted.status_code == 200, restarted.text
    assert restarted.json()["questions_asked"] == 1


@pytest.mark.asyncio
async def test_the_finished_step_agrees_with_its_result(client, valid_signup_payload):
    # The step's count and the result's carry one name because they are one
    # quantity at two moments in a run's life. A count that jumped as the run
    # finished would make that a lie.
    headers = await _auth_headers(client, valid_signup_payload)
    finished = await _run_to_result(client, headers)

    assert finished["questions_asked"] == finished["result"]["questions_asked"]

    fetched = (await _get(client, headers, finished["assessment_id"])).json()
    assert fetched["questions_asked"] == finished["result"]["questions_asked"]


@pytest.mark.asyncio
async def test_an_abandoned_run_reports_what_was_answered_before_it_ended(
    client, valid_signup_payload
):
    headers = await _auth_headers(client, valid_signup_payload)
    created = (await _create(client, headers)).json()
    await _answer_the_outstanding_question(client, headers, created)
    await _abandon(client, headers, created["assessment_id"])

    fetched = (await _get(client, headers, created["assessment_id"])).json()

    assert fetched["status"] == "abandoned"
    assert fetched["question"] is None and fetched["result"] is None
    assert fetched["questions_asked"] == 1


@pytest.mark.asyncio
async def test_a_replayed_answer_after_abandonment_agrees_with_the_read(
    client, valid_signup_payload
):
    """An abandoned run must not carry a question to answer, on either route.

    Reachable by exactly the sequence the replay branch exists to serve: an answer
    whose response was lost in flight, a player who then stops rating that sport,
    and the client's automatic retry arriving after the run has ended. The branch
    is guarded on the question id alone and abandonment leaves that id in place,
    so the retry lands in it.

    The client half is what makes disagreement expensive: the wire mapper treats
    the *question* as what says whether there is something to answer, so a
    question here tells the client to render a step for a run the server considers
    over — and the answer it then submits is rejected.
    """

    headers = await _auth_headers(client, valid_signup_payload)
    created = (await _create(client, headers)).json()
    question = created["question"]
    await _answer_the_outstanding_question(client, headers, created)
    await _abandon(client, headers, created["assessment_id"])

    replayed = await _answer(
        client,
        headers,
        created["assessment_id"],
        question["id"],
        question["options"][-1]["id"],
    )

    assert replayed.status_code == 200, replayed.text
    replayed_body = replayed.json()
    assert replayed_body["status"] == "abandoned"
    assert replayed_body["question"] is None
    assert replayed_body["result"] is None

    # One run, one description: the replay and the read agree field for field.
    fetched = (await _get(client, headers, created["assessment_id"])).json()
    assert replayed_body == fetched


@pytest.mark.asyncio
async def test_the_count_is_not_recorded_a_second_time(
    client, session_factory, valid_signup_payload
):
    # Derived from the replayed transcript, never stored. A counter on the stream
    # would be a second place holding a fact the transcript already holds, and the
    # two would disagree the first time either moved. The completion event keeps
    # its own `questions_asked` — that one is the *result's*, recorded beside the
    # numbers the player was shown.
    headers = await _auth_headers(client, valid_signup_payload)
    body = (await _create(client, headers)).json()
    body = await _answer_the_outstanding_question(client, headers, body)

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

    assert rows
    for row in rows:
        if row.event_type == "rating.assessment_completed":
            continue
        assert "questions_asked" not in row.payload, row.event_type


@pytest.mark.asyncio
async def test_the_step_states_its_count_on_the_player_contract():
    # #34 reads this field and adds one to it. A field the document called optional
    # would push a null check into the client for a number that always exists.
    from app.api.contract import build_surface_spec
    from app.api.v1.player import player_api_router

    schema = build_surface_spec("player", player_api_router)["components"]["schemas"][
        "AssessmentStepResponse"
    ]

    assert "questions_asked" in schema["properties"]
    assert "questions_asked" in schema["required"]


# --- The explained result -------------------------------------------------------

RESULT_KEYS = {
    "mu",
    "sigma",
    "confidence",
    "confidence_ceiling",
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
    result = (await _beginner_to_result(client, headers))["result"]

    # One answer, so one row — and the base confidence branch, because nothing
    # widened the range beyond the floor every onboarding rating sits at.
    assert [factor["key"] for factor in result["factors"]] == ["recent-activity"]
    assert result["uncertainty_factors"] == []
    assert result["confidence_reason"]["key"] == "limited-match-evidence"
    assert result["calibration_priority"] == "standard"


@pytest.mark.asyncio
async def test_the_result_carries_the_ceiling_its_confidence_is_measured_against(
    client, valid_signup_payload
):
    """The ceiling is served, so nothing downstream has to keep a copy of it.

    Expected from the engine's own constants rather than from ``30``: the point
    of serving it is that a retune reaches the client through the response, and a
    test pinning the literal would make the retune look like a regression here
    while the phone quietly went on drawing the old tick.
    """

    from app.engines.racketskill.core import confidence_percent
    from app.engines.racketskill.v3.engine import SIGMA_FLOOR

    headers = await _auth_headers(client, valid_signup_payload)
    result = (await _run_to_result(client, headers))["result"]

    assert result["confidence_ceiling"] == confidence_percent(SIGMA_FLOOR)
    # The relationship the client draws: an arc under a tick, never over it.
    assert result["confidence"] <= result["confidence_ceiling"]


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


# --- The served Transcript ------------------------------------------------------
#
# Every step carries the answers already given, in order, each with the question
# it answered *as that question was asked*. The copy and not the id, because the
# only thing that can render an answered question is its copy and a run resumed on
# a fresh install has nothing stored locally to render from. It is replayed from
# the stream on every read, exactly as the outstanding question is, so there is no
# second representation of a run to keep in step.


def _transcript_ids(body):
    return [entry["question"]["id"] for entry in body["transcript"]]


@pytest.mark.asyncio
async def test_a_fresh_run_carries_an_empty_transcript(client, valid_signup_payload):
    headers = await _auth_headers(client, valid_signup_payload)
    created = (await _create(client, headers)).json()

    # Present and empty, never omitted: a client reads one shape on every step,
    # and "no answers yet" is a length rather than a missing field.
    assert created["transcript"] == []


@pytest.mark.asyncio
async def test_the_transcript_grows_by_one_entry_per_answer(
    client, valid_signup_payload
):
    headers = await _auth_headers(client, valid_signup_payload)
    body = (await _create(client, headers)).json()

    lengths = [len(body["transcript"])]
    asked = []
    while body["question"] is not None:
        asked.append(body["question"]["id"])
        body = await _answer_the_outstanding_question(client, headers, body)
        lengths.append(len(body["transcript"]))

    # 0, 1, 2, … with no gap and no repeat, and the last entry is the answer that
    # ended the run — the finished step serves the evidence it was rated on.
    assert lengths == list(range(len(lengths)))
    assert len(lengths) > 2, "a full run asks more than one question"
    assert _transcript_ids(body) == asked
    assert len(body["transcript"]) == body["questions_asked"]


@pytest.mark.asyncio
async def test_the_transcript_is_the_questions_that_were_actually_asked(
    client, valid_signup_payload
):
    headers = await _auth_headers(client, valid_signup_payload)
    body = (await _create(client, headers)).json()

    asked, chosen = [], []
    for _ in range(4):
        asked.append(body["question"])
        chosen.append(body["question"]["options"][-1]["id"])
        body = await _answer_the_outstanding_question(client, headers, body)

    # Whole questions, byte for byte what the player was shown — not a summary and
    # not a reconstruction the client would have to trust separately.
    assert [entry["question"] for entry in body["transcript"]] == asked
    assert [entry["option_id"] for entry in body["transcript"]] == chosen
    for entry in body["transcript"]:
        assert entry["option_id"] in {
            option["id"] for option in entry["question"]["options"]
        }


@pytest.mark.asyncio
async def test_an_entry_carries_the_whole_question(client, valid_signup_payload):
    headers = await _auth_headers(client, valid_signup_payload)
    body = (await _create(client, headers)).json()
    body = await _answer_the_outstanding_question(client, headers, body)

    (entry,) = body["transcript"]
    question = entry["question"]
    assert set(question) == {
        "id",
        "category",
        "tier",
        "situation",
        "text",
        "qualifier",
        "options",
    }
    assert question["category"] and question["situation"] and question["text"]
    assert question["qualifier"] and question["options"]


@pytest.mark.asyncio
async def test_the_outstanding_question_is_not_in_the_transcript(
    client, valid_signup_payload
):
    headers = await _auth_headers(client, valid_signup_payload)
    body = (await _create(client, headers)).json()
    body = await _answer_the_outstanding_question(client, headers, body)

    # It has been put to the player but not answered, which is the same rule
    # ``questions_asked`` follows — so the two agree by construction.
    assert body["question"]["id"] not in _transcript_ids(body)
    assert len(body["transcript"]) == body["questions_asked"]


@pytest.mark.asyncio
async def test_a_resumed_run_returns_the_full_transcript(client, valid_signup_payload):
    headers = await _auth_headers(client, valid_signup_payload)
    body = (await _create(client, headers)).json()
    for _ in range(3):
        body = await _answer_the_outstanding_question(client, headers, body)
    answering = body["transcript"]

    # The three reads a resuming client can make, and the start it may retry into.
    fetched = (await _get(client, headers, body["assessment_id"])).json()
    resumed = (await _in_progress(client, headers)).json()
    restarted = (await _create(client, headers)).json()

    assert len(answering) == 3
    assert fetched["transcript"] == answering
    assert resumed["transcript"] == answering
    assert restarted["transcript"] == answering


@pytest.mark.asyncio
async def test_the_beginner_run_carries_the_single_answer_that_ended_it(
    client, valid_signup_payload
):
    headers = await _auth_headers(client, valid_signup_payload)
    created = (await _create(client, headers)).json()
    question = created["question"]

    stopped = (
        await _answer(
            client, headers, created["assessment_id"], question["id"], "never-played"
        )
    ).json()
    finished = (await _complete(client, headers, created["assessment_id"])).json()

    # The one answer is in the transcript from the moment it is given — before
    # any rating exists — which is what a review screen is drawn from.
    assert stopped["result"] is None
    assert stopped["transcript"] == finished["transcript"]

    assert finished["result"] is not None
    (entry,) = finished["transcript"]
    assert entry["question"] == question
    assert entry["option_id"] == "never-played"


@pytest.mark.asyncio
async def test_an_abandoned_run_still_carries_what_was_answered(
    client, valid_signup_payload
):
    headers = await _auth_headers(client, valid_signup_payload)
    body = (await _create(client, headers)).json()
    body = await _answer_the_outstanding_question(client, headers, body)
    body = await _answer_the_outstanding_question(client, headers, body)

    await _abandon(client, headers, body["assessment_id"])
    ended = (await _get(client, headers, body["assessment_id"])).json()

    assert ended["status"] == "abandoned"
    assert ended["question"] is None
    assert ended["transcript"] == body["transcript"]


@pytest.mark.asyncio
async def test_a_finished_run_carries_the_evidence_beside_its_result(
    client, valid_signup_payload
):
    headers = await _auth_headers(client, valid_signup_payload)
    finished = await _run_to_result(client, headers)

    refetched = (await _get(client, headers, finished["assessment_id"])).json()

    assert len(finished["transcript"]) == finished["result"]["questions_asked"]
    assert refetched["transcript"] == finished["transcript"]


@pytest.mark.asyncio
async def test_the_transcript_is_replayed_and_not_stored_a_second_time(
    client, session_factory, valid_signup_payload
):
    # The copy is the engine's and the stream holds only the two ids the engine
    # reads. A stored question would be a second place the wording lives, and the
    # two would disagree the first time either moved.
    headers = await _auth_headers(client, valid_signup_payload)
    body = (await _create(client, headers)).json()
    for _ in range(3):
        body = await _answer_the_outstanding_question(client, headers, body)
    shown = body["transcript"][0]["question"]

    async with session_factory() as session:
        rows = (
            (
                await session.execute(
                    select(EventStoreORM).order_by(EventStoreORM.version)
                )
            )
            .scalars()
            .all()
        )

    answers = [row for row in rows if row.event_type == "rating.answer_submitted"]
    assert len(answers) == 3
    for row in answers:
        assert set(row.payload) == {
            "assessment_id",
            "question_id",
            "option_id",
            "occurred_at",
        }
    stored = str([row.payload for row in rows])
    assert shown["text"] not in stored
    assert shown["situation"] not in stored


@pytest.mark.asyncio
async def test_the_transcript_is_stated_on_the_player_contract():
    # The two clients generate from this document, so the field being required
    # rather than defaulted is what makes it non-optional in their wire types. A
    # defaulted list would have generated as `transcript?:` and pushed an absence
    # check into both clients for a field that is always sent.
    from app.api.contract import build_surface_spec
    from app.api.v1.player import player_api_router

    schemas = build_surface_spec("player", player_api_router)["components"]["schemas"]
    step = schemas["AssessmentStepResponse"]

    assert "transcript" in step["properties"]
    assert "transcript" in step["required"]

    entry = schemas["TranscriptEntryResponse"]
    assert set(entry["required"]) == {"question", "option_id"}


# --- Revising an answer ---------------------------------------------------------
#
# Submitting an answer for a question the run has already answered **changes** it:
# the transcript truncates there and the engine is replayed from the prefix. One
# route and one request shape, because a client is not asked to know which of the
# two it is doing (ADR-0020).
#
# The truncation is the whole design and it is what makes revising free. An
# answer's numeric meaning depends on the difficulty tier it was asked at, and
# that tier was chosen from the estimate as it then stood — so an answer that
# outlived a change to an earlier one would mean something the player never said.


async def _straight_through(client, headers, sport="PADEL"):
    """Answer every question with its last option, in one pass, then finish."""

    body = (await _create(client, headers, sport)).json()
    while body["question"] is not None:
        body = await _answer_the_outstanding_question(client, headers, body)
    return (await _complete(client, headers, body["assessment_id"])).json()


async def _by_a_different_road(client, headers, sport="PADEL"):
    """Reach the straight-through transcript, having first answered elsewhere.

    The detour **diverges** deliberately rather than merely differing.
    ``occasional`` is the one genuinely ambiguous regularity answer, so the
    engine follows it with a volume question the straight-through run never sees
    — and that answer is then discarded by the revision. A detour that happened
    to be asked the same questions would test a change that did not matter.
    """

    body = (await _create(client, headers, sport)).json()
    opening = body["question"]

    body = (
        await _answer(
            client, headers, body["assessment_id"], opening["id"], "occasional"
        )
    ).json()
    assert body["question"]["id"] == "recent.volume", "the detour must diverge"
    body = await _answer_the_outstanding_question(client, headers, body)

    # The revision: the opening question again, with the straight run's answer.
    body = (
        await _answer(
            client,
            headers,
            body["assessment_id"],
            opening["id"],
            opening["options"][-1]["id"],
        )
    ).json()
    assert _transcript_ids(body) == [opening["id"]], "the volume answer is discarded"

    while body["question"] is not None:
        body = await _answer_the_outstanding_question(client, headers, body)
    return (await _complete(client, headers, body["assessment_id"])).json()


@pytest.mark.asyncio
async def test_two_players_reaching_one_transcript_are_rated_identically(
    client, valid_signup_payload
):
    """The load-bearing test: revising costs nothing in accuracy.

    One player answers straight through. The other answers the opening question
    differently, changes it, and carries on — landing on the same transcript by a
    different road. ``next_step`` and ``finalize`` are pure functions of the
    transcript (ADR-0015), so a truncated transcript is simply a transcript and
    the two must be rated the same to the digit.

    This is what makes "revising is free" a fact rather than a claim in an ADR.
    **It must never be deleted.**
    """

    alice = await _auth_headers(client, valid_signup_payload)
    bob = await _auth_headers(client, BOB)

    straight = await _straight_through(client, alice)
    revised = await _by_a_different_road(client, bob)

    # The same road, reached two ways.
    assert _transcript_ids(revised) == _transcript_ids(straight)
    assert [entry["option_id"] for entry in revised["transcript"]] == [
        entry["option_id"] for entry in straight["transcript"]
    ]
    # Every field of the result: the numbers, the band, the ceiling, the
    # confidence sentence and both halves of the evidence trail. `ResultResponse`
    # carries no id and no timestamp, so this is the whole payload.
    assert revised["result"] == straight["result"]
    assert revised["questions_asked"] == straight["questions_asked"]

    # And the rating that was stored from it, which is what every later feature
    # reads. `updated_at` is the one field that cannot agree.
    alice_rating = (await client.get("/api/v1/ratings", headers=alice)).json()
    bob_rating = (await client.get("/api/v1/ratings", headers=bob)).json()
    assert {
        key: value
        for key, value in bob_rating["ratings"][0].items()
        if key != "updated_at"
    } == {
        key: value
        for key, value in alice_rating["ratings"][0].items()
        if key != "updated_at"
    }


@pytest.mark.asyncio
async def test_revising_truncates_the_transcript_and_returns_the_next_step(
    client, valid_signup_payload
):
    headers = await _auth_headers(client, valid_signup_payload)
    body = (await _create(client, headers)).json()
    for _ in range(3):
        body = await _answer_the_outstanding_question(client, headers, body)
    first = body["transcript"][0]
    changed_to = first["question"]["options"][-2]["id"]

    resp = await _answer(
        client, headers, body["assessment_id"], first["question"]["id"], changed_to
    )

    assert resp.status_code == 200, resp.text
    revised = resp.json()
    # Every answer after the changed one is gone, and the changed one is changed.
    assert _transcript_ids(revised) == [first["question"]["id"]]
    assert revised["transcript"][0]["option_id"] == changed_to
    assert revised["questions_asked"] == 1
    assert revised["question"] is not None
    assert revised["status"] == "in_progress"

    # And the read route says the same thing, so a client that refetches instead
    # of trusting the mutation response is not shown a different run.
    assert (await _get(client, headers, body["assessment_id"])).json() == revised


@pytest.mark.asyncio
async def test_re_selecting_the_option_already_recorded_records_nothing(
    client, session_factory, valid_signup_payload
):
    # Changing your mind and changing it back is not punished, and a retry after
    # a response lost in flight is free. Both arrive as this exact request.
    headers = await _auth_headers(client, valid_signup_payload)
    body = (await _create(client, headers)).json()
    for _ in range(3):
        body = await _answer_the_outstanding_question(client, headers, body)
    first = body["transcript"][0]

    resp = await _answer(
        client,
        headers,
        body["assessment_id"],
        first["question"]["id"],
        first["option_id"],
    )

    assert resp.status_code == 200, resp.text
    assert resp.json() == body

    async with session_factory() as session:
        rows = (await session.execute(select(EventStoreORM))).scalars().all()
    assert [r.event_type for r in rows].count("rating.answer_revised") == 0


@pytest.mark.asyncio
async def test_revising_the_opening_answer_to_never_played_stops_the_run(
    client, valid_signup_payload
):
    # The beginner fast path is the engine's, and a revision reaches it by the
    # ordinary route: the client must handle a change that *ends* the
    # questionnaire rather than continuing it.
    headers = await _auth_headers(client, valid_signup_payload)
    body = (await _create(client, headers)).json()
    opening = body["question"]["id"]
    for _ in range(3):
        body = await _answer_the_outstanding_question(client, headers, body)

    resp = await _answer(
        client, headers, body["assessment_id"], opening, "never-played"
    )

    assert resp.status_code == 200, resp.text
    stopped = resp.json()
    # Stopped, not rated: the revision reached the beginner fast path and the
    # run now sits where every other stopped run sits, waiting to be finished.
    assert stopped["question"] is None
    assert stopped["result"] is None
    assert stopped["status"] == "in_progress"
    assert _transcript_ids(stopped) == [opening]

    final = (await _complete(client, headers, stopped["assessment_id"])).json()
    assert final["status"] == "completed"
    assert final["result"]["questions_asked"] == 1
    # The same rating a player who said so first time would have got.
    assert final["result"]["mu"] == 1.40
    assert final["result"]["confidence"] == 18


@pytest.mark.asyncio
async def test_revising_the_first_question_from_deep_in_a_run(
    client, valid_signup_payload
):
    headers = await _auth_headers(client, valid_signup_payload)
    body = (await _create(client, headers)).json()
    opening = body["question"]
    while body["question"] is not None and len(body["transcript"]) < 5:
        body = await _answer_the_outstanding_question(client, headers, body)
    assert len(body["transcript"]) == 5, "a run this long is what the test is for"

    resp = await _answer(
        client,
        headers,
        body["assessment_id"],
        opening["id"],
        opening["options"][-2]["id"],
    )

    assert resp.status_code == 200, resp.text
    assert len(resp.json()["transcript"]) == 1


@pytest.mark.asyncio
async def test_revising_repeatedly_works(client, valid_signup_payload):
    headers = await _auth_headers(client, valid_signup_payload)
    body = (await _create(client, headers)).json()
    for _ in range(3):
        body = await _answer_the_outstanding_question(client, headers, body)
    first = body["transcript"][0]["question"]

    for option in (first["options"][-2], first["options"][-3], first["options"][-1]):
        resp = await _answer(
            client, headers, body["assessment_id"], first["id"], option["id"]
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        # Each change lands the run back on one answer and asks again from there.
        assert len(body["transcript"]) == 1
        assert body["transcript"][0]["option_id"] == option["id"]
        body = await _answer_the_outstanding_question(client, headers, body)


@pytest.mark.asyncio
async def test_a_revision_is_appended_and_no_event_is_deleted(
    client, session_factory, valid_signup_payload
):
    """The stream grows; only the projection shortens.

    "A revision shortens the past; it never edits it" is a claim about the
    stream, and the truncated transcript every other test here asserts is exactly
    what a *destructive* implementation would also produce. The record that the
    player changed their mind, and to what, is the thing a future model would
    otherwise learn nothing from.
    """

    headers = await _auth_headers(client, valid_signup_payload)
    body = (await _create(client, headers)).json()
    for _ in range(3):
        body = await _answer_the_outstanding_question(client, headers, body)
    before = _transcript_ids(body)
    first = body["transcript"][0]

    revised = (
        await _answer(
            client,
            headers,
            body["assessment_id"],
            first["question"]["id"],
            first["question"]["options"][-2]["id"],
        )
    ).json()

    async with session_factory() as session:
        rows = (
            (
                await session.execute(
                    select(EventStoreORM)
                    .where(EventStoreORM.aggregate_type == "assessment")
                    .order_by(EventStoreORM.version)
                )
            )
            .scalars()
            .all()
        )

    answered = [r for r in rows if r.event_type == "rating.answer_submitted"]
    assert [r.payload["question_id"] for r in answered] == before
    revisions = [r for r in rows if r.event_type == "rating.answer_revised"]
    assert len(revisions) == 1
    assert revisions[0].payload["question_id"] == first["question"]["id"]
    assert revisions[0].payload["option_id"] == revised["transcript"][0]["option_id"]
    # Appended *after* every answer it supersedes rather than over any of them —
    # the question it then asked is the only thing further along the stream.
    assert revisions[0].version > max(r.version for r in answered)
    # And the stream still replays to the transcript the engine consumed.
    assert _transcript_ids(
        (await _get(client, headers, body["assessment_id"])).json()
    ) == [first["question"]["id"]]


@pytest.mark.asyncio
async def test_revising_once_the_rating_exists_is_refused(client, valid_signup_payload):
    # Its own code, because the recovery is opposite to the other conflicts':
    # there is no question to refetch and re-render, only a rating to show.
    headers = await _auth_headers(client, valid_signup_payload)
    finished = await _straight_through(client, headers)
    first = finished["transcript"][0]

    resp = await _answer(
        client,
        headers,
        finished["assessment_id"],
        first["question"]["id"],
        first["question"]["options"][-2]["id"],
    )

    assert resp.status_code == 409
    assert resp.json()["code"] == "answer_not_revisable"


@pytest.mark.asyncio
async def test_an_abandoned_run_refuses_a_change_with_the_ordinary_conflict(
    client, valid_signup_payload
):
    # No rating to show, so nothing the not-revisable code would say that
    # refetching does not: the client reads the abandoned status and leaves.
    headers = await _auth_headers(client, valid_signup_payload)
    body = (await _create(client, headers)).json()
    for _ in range(2):
        body = await _answer_the_outstanding_question(client, headers, body)
    await _abandon(client, headers, body["assessment_id"])
    first = body["transcript"][0]

    resp = await _answer(
        client,
        headers,
        body["assessment_id"],
        first["question"]["id"],
        first["question"]["options"][-2]["id"],
    )

    assert resp.status_code == 409
    assert resp.json()["code"] == "question_not_outstanding"


@pytest.mark.asyncio
async def test_an_option_the_revised_question_never_offered_is_rejected(
    client, valid_signup_payload
):
    headers = await _auth_headers(client, valid_signup_payload)
    body = (await _create(client, headers)).json()
    for _ in range(2):
        body = await _answer_the_outstanding_question(client, headers, body)

    resp = await _answer(
        client,
        headers,
        body["assessment_id"],
        body["transcript"][0]["question"]["id"],
        "not-an-option",
    )

    assert resp.status_code == 400
    assert resp.json()["code"] == "invalid_answer_option"


@pytest.mark.asyncio
async def test_revising_is_stated_on_the_player_contract():
    # Two clients generate from this document and neither is in this session. The
    # route's shape does not change — a revision is the same request as an answer
    # — so what a client reads to *know it can revise at all* is the description
    # and the conflict code, which makes both part of the contract.
    from app.api.contract import build_surface_spec
    from app.api.v1.player import player_api_router

    spec = build_surface_spec("player", player_api_router)
    operation = spec["paths"]["/api/v1/assessments/{assessment_id}/answers"]["post"]

    assert "revision" in operation["description"].lower()
    assert "answer_not_revisable" in operation["responses"]["409"]["description"]
    assert "question_not_outstanding" in operation["responses"]["409"]["description"]


@pytest.mark.asyncio
async def test_a_revised_run_resumes_to_what_the_change_left_behind(
    client, valid_signup_payload
):
    # Navigation survives a reinstall because the transcript is served rather
    # than accumulated on the device, and a revision is the case where a stale
    # local copy would be *longer* than the truth — the one direction a client
    # cannot detect by counting.
    headers = await _auth_headers(client, valid_signup_payload)
    body = (await _create(client, headers)).json()
    for _ in range(3):
        body = await _answer_the_outstanding_question(client, headers, body)
    first = body["transcript"][0]
    revised = (
        await _answer(
            client,
            headers,
            body["assessment_id"],
            first["question"]["id"],
            first["question"]["options"][-2]["id"],
        )
    ).json()

    resumed = (await _in_progress(client, headers)).json()
    fetched = (await _get(client, headers, body["assessment_id"])).json()

    assert resumed == revised
    assert fetched == revised
    assert len(resumed["transcript"]) == 1


# --- Stopping and completing are two moments ------------------------------------
#
# The questionnaire **stops** when the engine judges no remaining question would
# meaningfully tighten the estimate. That instant used to also create the Skill
# rating, which is what made revisability vanish without warning: the confirm
# control's label is identical on every question — necessarily, because the engine
# decides after the answer arrives — so a player tapped it on the last question
# exactly as they had tapped it on the others and found their rating already made.
#
# Now stopping produces a step with neither a question nor a result, the run sits
# in progress with nothing outstanding, and `POST /completion` is what creates the
# rating (ADR-0020). That is where irreversibility is earned, and what lets a
# review of every answer exist between the two.


@pytest.mark.asyncio
async def test_the_answer_that_stops_the_questionnaire_creates_no_rating(
    client, session_factory, valid_signup_payload
):
    headers = await _auth_headers(client, valid_signup_payload)

    stopped = await _run_to_stop(client, headers)

    assert stopped["question"] is None
    assert stopped["result"] is None
    # Still in progress, with nothing outstanding. No new status was needed: the
    # stop *is* the absence of an outstanding question.
    assert stopped["status"] == "in_progress"
    assert len(stopped["transcript"]) == stopped["questions_asked"] > 1

    # Nothing was rated, and nothing was written to say so.
    assert (await client.get("/api/v1/ratings", headers=headers)).json() == {
        "ratings": []
    }
    async with session_factory() as session:
        rows = (await session.execute(select(EventStoreORM))).scalars().all()
    event_types = [row.event_type for row in rows]
    assert event_types.count("rating.assessment_completed") == 0
    assert event_types.count("rating.rating_initialised") == 0


@pytest.mark.asyncio
async def test_the_completion_request_creates_the_rating_and_returns_it_inline(
    client, session_factory, valid_signup_payload
):
    headers = await _auth_headers(client, valid_signup_payload)
    stopped = await _run_to_stop(client, headers)

    resp = await _complete(client, headers, stopped["assessment_id"])

    assert resp.status_code == 200, resp.text
    finished = resp.json()
    assert finished["status"] == "completed"
    assert finished["question"] is None
    # Inline, because the player is shown their rating on the very next screen.
    assert finished["result"]["mu"] > 0
    assert finished["result"]["questions_asked"] == stopped["questions_asked"]
    # The evidence did not move between the two moments, so neither did the
    # rating: a review screen costs nothing in accuracy.
    assert finished["transcript"] == stopped["transcript"]

    rated = (await client.get("/api/v1/ratings", headers=headers)).json()["ratings"]
    assert [entry["sport"] for entry in rated] == ["PADEL"]

    async with session_factory() as session:
        rows = (await session.execute(select(EventStoreORM))).scalars().all()
    by_type = [(row.aggregate_type, row.event_type) for row in rows]
    # Still one transaction across two aggregates (ADR-0017): only the trigger
    # moved.
    assert ("assessment", "rating.assessment_completed") in by_type
    assert ("skill_rating", "rating.rating_initialised") in by_type


@pytest.mark.asyncio
async def test_completing_twice_returns_the_same_result_and_writes_nothing_new(
    client, session_factory, valid_signup_payload
):
    # The control a player double-taps on a slow connection is the one that makes
    # something irreversible, so a conflict here is one the client would have to
    # translate back into "you already have your rating".
    headers = await _auth_headers(client, valid_signup_payload)
    stopped = await _run_to_stop(client, headers)

    first = (await _complete(client, headers, stopped["assessment_id"])).json()
    resp = await _complete(client, headers, stopped["assessment_id"])

    assert resp.status_code == 200, resp.text
    assert resp.json() == first

    async with session_factory() as session:
        rows = (await session.execute(select(EventStoreORM))).scalars().all()
    event_types = [row.event_type for row in rows]
    assert event_types.count("rating.assessment_completed") == 1
    assert event_types.count("rating.rating_initialised") == 1


@pytest.mark.asyncio
async def test_completing_a_run_that_is_still_asking_is_refused(
    client, valid_signup_payload
):
    headers = await _auth_headers(client, valid_signup_payload)
    body = (await _create(client, headers)).json()
    body = await _answer_the_outstanding_question(client, headers, body)
    assert body["question"] is not None, "the run must still be asking"

    resp = await _complete(client, headers, body["assessment_id"])

    assert resp.status_code == 409, resp.text
    assert resp.json()["code"] == "assessment_not_stopped"
    # Refused, and nothing about the run changed: the question is still there.
    assert (await _get(client, headers, body["assessment_id"])).json() == body


@pytest.mark.asyncio
async def test_completing_an_abandoned_run_is_refused(client, valid_signup_payload):
    headers = await _auth_headers(client, valid_signup_payload)
    stopped = await _run_to_stop(client, headers)
    await _abandon(client, headers, stopped["assessment_id"])

    resp = await _complete(client, headers, stopped["assessment_id"])

    assert resp.status_code == 409, resp.text
    assert resp.json()["code"] == "assessment_not_stopped"


@pytest.mark.asyncio
async def test_abandoning_a_stopped_run_still_works(client, valid_signup_payload):
    # Reaching the end is not being trapped at it: leaving from the stop works
    # exactly as leaving from a question does, and frees the sport.
    headers = await _auth_headers(client, valid_signup_payload)
    stopped = await _run_to_stop(client, headers)

    assert (
        await _abandon(client, headers, stopped["assessment_id"])
    ).status_code == 204

    assert (await _in_progress(client, headers, "PADEL")).status_code == 204
    assert (await _create(client, headers, "PADEL")).status_code == 201


@pytest.mark.asyncio
async def test_completing_another_players_run_is_not_found(
    client, valid_signup_payload
):
    alice = await _auth_headers(client, valid_signup_payload)
    stopped = await _run_to_stop(client, alice)

    bob = await _auth_headers(client, BOB)
    resp = await _complete(client, bob, stopped["assessment_id"])

    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_completing_requires_authentication(client, valid_signup_payload):
    headers = await _auth_headers(client, valid_signup_payload)
    stopped = await _run_to_stop(client, headers)

    resp = await client.post(
        f"/api/v1/assessments/{stopped['assessment_id']}/completion"
    )

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_a_stopped_run_resumes_to_the_stopped_step(client, valid_signup_payload):
    # A force-quit at the review comes back to the review. Nothing about the stop
    # lives on the device, so this holds after a reinstall and on a second
    # handset too — all three reads replay the same stream.
    headers = await _auth_headers(client, valid_signup_payload)
    stopped = await _run_to_stop(client, headers)

    fetched = (await _get(client, headers, stopped["assessment_id"])).json()
    resumed = (await _in_progress(client, headers, "PADEL")).json()
    restarted = await _create(client, headers, "PADEL")
    listed = (await _all_in_progress(client, headers)).json()

    assert fetched == stopped
    assert resumed == stopped
    # Starting the sport again hands back the stopped run rather than opening a
    # second one, exactly as it does mid-questionnaire.
    assert restarted.status_code == 200, restarted.text
    assert restarted.json() == stopped
    # And the entry gate still sees it as unfinished, because it is.
    assert listed["assessments"] == [
        {"assessment_id": stopped["assessment_id"], "sport": "PADEL"}
    ]


@pytest.mark.asyncio
async def test_the_beginner_stops_after_one_answer_rather_than_being_rated(
    client, valid_signup_payload
):
    # One question screen, one review, one result is one rule an agent can apply.
    # A beginner's single answer is the highest-leverage answer in the bank, so
    # it gets the same last look as anybody else's nine.
    headers = await _auth_headers(client, valid_signup_payload)
    created = (await _create(client, headers)).json()

    stopped = (
        await _answer(
            client,
            headers,
            created["assessment_id"],
            created["question"]["id"],
            "never-played",
        )
    ).json()

    assert stopped["question"] is None
    assert stopped["result"] is None
    assert stopped["status"] == "in_progress"
    assert stopped["questions_asked"] == 1

    finished = (await _complete(client, headers, created["assessment_id"])).json()
    assert finished["status"] == "completed"
    assert finished["result"]["questions_asked"] == 1


@pytest.mark.asyncio
async def test_revising_from_a_stopped_run_returns_to_the_questionnaire(
    client, valid_signup_payload
):
    # Changing an answer from the review puts the player back in the
    # questionnaire, and stopping again is reachable — so the review is a real
    # last look rather than a one-way door.
    headers = await _auth_headers(client, valid_signup_payload)
    stopped = await _run_to_stop(client, headers)
    first = stopped["transcript"][0]

    resp = await _answer(
        client,
        headers,
        stopped["assessment_id"],
        first["question"]["id"],
        first["question"]["options"][-2]["id"],
    )

    assert resp.status_code == 200, resp.text
    back = resp.json()
    assert back["question"] is not None, "the run is asking again"
    assert len(back["transcript"]) == 1

    # And on to a second stop, which is where the review is reached again.
    stopped_again = back
    while stopped_again["question"] is not None:
        stopped_again = await _answer_the_outstanding_question(
            client, headers, stopped_again
        )
    assert stopped_again["result"] is None
    assert stopped_again["status"] == "in_progress"
    assert stopped_again["transcript"] != stopped["transcript"]

    finished = (await _complete(client, headers, stopped["assessment_id"])).json()
    assert finished["status"] == "completed"


@pytest.mark.asyncio
async def test_the_completion_is_stated_on_the_player_contract():
    # A client cannot find a behaviour that exists only in prose, and this one is
    # the difference between a rating that appears and a rating that is asked for.
    from app.api.contract import build_surface_spec
    from app.api.v1.player import player_api_router

    spec = build_surface_spec("player", player_api_router)
    path = "/api/v1/assessments/{assessment_id}/completion"
    operation = spec["paths"][path]["post"]

    assert operation["responses"]["200"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("/AssessmentStepResponse")
    assert "assessment_not_stopped" in operation["responses"]["409"]["description"]
    assert "twice" in operation["description"]

    # And the step says what *neither* means, since that is the invariant this
    # change weakened: exactly one of question/result became at most one.
    step = spec["components"]["schemas"]["AssessmentStepResponse"]
    assert "stopped" in step["properties"]["status"]["description"]
