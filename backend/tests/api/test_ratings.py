"""HTTP flows for ``GET /api/v1/ratings`` — the ratings a player already holds.

This is the read the client's entry gate turns on, and it is deliberately not a
flag on the user: a rating is per sport, so "is this player rated" is only ever
answerable one sport at a time. The tests therefore care as much about the
*shape* of the absent answer (an empty collection, not a 404) and about isolation
between players and sports as they do about the happy path.
"""

import pytest

from app.engines.racketskill.core import band_for

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


async def _ratings(client, headers):
    return await client.get("/api/v1/ratings", headers=headers)


async def _rate_as_beginner(client, headers, sport):
    """Take the shortest honest path to a stored rating: answer "never played".

    Two calls, because the questionnaire stopping and the assessment completing
    are two moments — the answer ends the questioning and the completion is what
    creates the rating (``docs/adr/0020``).
    """

    created = (
        await client.post(
            "/api/v1/assessments", json={"sport": sport}, headers=headers
        )
    ).json()
    stopped = await client.post(
        f"/api/v1/assessments/{created['assessment_id']}/answers",
        json={"question_id": created["question"]["id"], "option_id": "never-played"},
        headers=headers,
    )
    assert stopped.status_code == 200, stopped.text
    assert stopped.json()["status"] == "in_progress"

    done = await client.post(
        f"/api/v1/assessments/{created['assessment_id']}/completion", headers=headers
    )
    assert done.status_code == 200, done.text
    body = done.json()
    assert body["status"] == "completed"
    return body["result"]


@pytest.mark.asyncio
async def test_an_unrated_player_gets_an_empty_collection(client, valid_signup_payload):
    headers = await _auth_headers(client, valid_signup_payload)

    resp = await _ratings(client, headers)

    # Absence of a rating is the normal state of a new account, so it is a
    # success with nothing in it — a 404 here would make the gate treat "new
    # player" as an error to recover from.
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"ratings": []}


@pytest.mark.asyncio
async def test_requires_authentication(client):
    resp = await client.get("/api/v1/ratings")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_a_rated_sport_is_listed_with_everything_the_gate_needs(
    client, valid_signup_payload
):
    headers = await _auth_headers(client, valid_signup_payload)
    result = await _rate_as_beginner(client, headers, "PADEL")

    resp = await _ratings(client, headers)

    assert resp.status_code == 200, resp.text
    (rating,) = resp.json()["ratings"]
    assert rating["sport"] == "PADEL"
    assert rating["mu"] == result["mu"]
    assert rating["sigma"] == result["sigma"]
    assert rating["confidence"] == result["confidence"]
    assert rating["range"] == result["range"]
    assert rating["band"] == result["band"]
    assert rating["status"] == result["status"]
    assert rating["engine_version"] == result["engine_version"]
    assert rating["updated_at"] is not None


@pytest.mark.asyncio
async def test_the_band_is_the_engine_s_own(client, valid_signup_payload):
    headers = await _auth_headers(client, valid_signup_payload)
    await _rate_as_beginner(client, headers, "PADEL")

    (rating,) = (await _ratings(client, headers)).json()["ratings"]

    # Asked of the engine rather than restated here: the boundaries are
    # deliberately uneven and were wrong once already, so a test that hard-coded
    # them would agree with the bug rather than catch it.
    expected = band_for(rating["mu"])
    assert rating["band"] == {
        "name": expected.label,
        "lower": expected.lower,
        "upper": expected.upper,
    }


@pytest.mark.asyncio
async def test_several_sports_are_listed_independently(client, valid_signup_payload):
    headers = await _auth_headers(client, valid_signup_payload)
    await _rate_as_beginner(client, headers, "PADEL")
    await _rate_as_beginner(client, headers, "TENNIS")

    resp = await _ratings(client, headers)

    assert resp.status_code == 200, resp.text
    body = resp.json()["ratings"]
    assert [entry["sport"] for entry in body] == ["PADEL", "TENNIS"]


@pytest.mark.asyncio
async def test_rating_one_sport_leaves_the_others_unrated(client, valid_signup_payload):
    headers = await _auth_headers(client, valid_signup_payload)
    await _rate_as_beginner(client, headers, "PADEL")

    body = (await _ratings(client, headers)).json()["ratings"]
    listed = {entry["sport"] for entry in body}

    # The whole reason this is a collection and not a flag: rated at padel and
    # unrated at tennis is a normal, indefinite state.
    assert listed == {"PADEL"}


@pytest.mark.asyncio
async def test_a_player_sees_only_their_own_ratings(client, valid_signup_payload):
    alice = await _auth_headers(client, valid_signup_payload)
    await _rate_as_beginner(client, alice, "PADEL")

    bob = await _auth_headers(client, BOB)
    assert (await _ratings(client, bob)).json() == {"ratings": []}
    assert len((await _ratings(client, alice)).json()["ratings"]) == 1


@pytest.mark.asyncio
async def test_an_abandoned_assessment_produces_no_rating(client, valid_signup_payload):
    headers = await _auth_headers(client, valid_signup_payload)
    created = (
        await client.post(
            "/api/v1/assessments", json={"sport": "PADEL"}, headers=headers
        )
    ).json()

    abandoned = await client.post(
        f"/api/v1/assessments/{created['assessment_id']}/abandonment", headers=headers
    )
    assert abandoned.status_code == 204

    assert (await _ratings(client, headers)).json() == {"ratings": []}


@pytest.mark.asyncio
async def test_the_endpoint_is_on_the_emitted_player_surface():
    """A route that is mounted but not *emitted* is a route no client can call.

    `SURFACES` is what `make openapi` writes, so asserting through it — rather
    than through the router directly — is what makes this a claim about the
    document the client generates from.
    """

    from app.api.contract import SURFACES, build_surface_spec

    assert list(SURFACES) == ["player"]
    player = build_surface_spec("player", SURFACES["player"])
    assert "/api/v1/ratings" in player["paths"]
