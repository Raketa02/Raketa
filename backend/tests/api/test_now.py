"""``GET /api/v1/now`` over HTTP: one request, one answer, three regions.

The regions are empty in v1 and that is the point of the ticket — the client is
unblocked against a *compiled* contract before anything fills them. So what these
assert is the envelope: that it is present and shaped, that the sport rides on the
request and nothing else does, that the server never says *nothing has changed*,
and that a player with nothing gets a shape she recognises rather than an absence
to interpret.
"""

import pytest

ALICE = {
    "email": "alice@example.com",
    "password1": "hunter22!",
    "password2": "hunter22!",
    "nickname": "alice",
}
BOB = {
    "email": "bob@example.com",
    "password1": "hunter22!",
    "password2": "hunter22!",
    "nickname": "bob",
}


async def _auth_headers(client, payload=ALICE) -> dict[str, str]:
    await client.post("/api/v1/users", json=payload)
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password1"]},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def _rate_as_beginner(client, headers, sport: str) -> None:
    """The shortest honest path to a stored rating: answer *never played*."""

    created = (
        await client.post("/api/v1/assessments", json={"sport": sport}, headers=headers)
    ).json()
    stopped = await client.post(
        f"/api/v1/assessments/{created['assessment_id']}/answers",
        json={"question_id": created["question"]["id"], "option_id": "never-played"},
        headers=headers,
    )
    assert stopped.status_code == 200, stopped.text
    done = await client.post(
        f"/api/v1/assessments/{created['assessment_id']}/completion", headers=headers
    )
    assert done.status_code == 200, done.text


async def test_now_needs_a_signed_in_player(client) -> None:
    response = await client.get("/api/v1/now")
    assert response.status_code == 401


async def test_a_player_with_nothing_gets_three_regions_present_and_empty(
    client,
) -> None:
    headers = await _auth_headers(client)
    response = await client.get("/api/v1/now", headers=headers)

    assert response.status_code == 200, response.text
    body = response.json()

    assert list(body) == ["offers", "your_matches", "shelves", "debt"]
    assert body["offers"]["cards"] == []
    assert body["your_matches"]["cards"] == []
    # A *shelf* with nothing in it is absent; a *region* with nothing in it is
    # present and empty, so the client has one code path rather than two.
    assert body["shelves"]["shelves"] == []


async def test_a_player_who_owes_nothing_gets_no_debt_line(client) -> None:
    headers = await _auth_headers(client)
    body = (await client.get("/api/v1/now", headers=headers)).json()

    assert body["debt"] is None


async def test_the_header_is_not_on_this_screen(client) -> None:
    # The greeting and the city come from the *who am I* answer the app already
    # holds. Repeating a fact in two answers is how two answers come to disagree.
    headers = await _auth_headers(client)
    body = (await client.get("/api/v1/now", headers=headers)).json()

    assert "greeting" not in body
    assert "city" not in body
    assert "nickname" not in body


@pytest.mark.parametrize("sport", ["all", "PADEL", "TENNIS", "SQUASH", "BADMINTON"])
async def test_every_chip_on_the_sport_bar_is_accepted(client, sport: str) -> None:
    headers = await _auth_headers(client)
    response = await client.get(f"/api/v1/now?sport={sport}", headers=headers)

    assert response.status_code == 200, response.text


async def test_a_sport_that_is_not_a_chip_is_refused(client) -> None:
    headers = await _auth_headers(client)
    response = await client.get("/api/v1/now?sport=chess", headers=headers)

    assert response.status_code == 422


async def test_the_filter_defaults_to_all(client) -> None:
    headers = await _auth_headers(client)
    without = await client.get("/api/v1/now", headers=headers)
    with_all = await client.get("/api/v1/now?sport=all", headers=headers)

    assert without.status_code == with_all.status_code == 200
    assert list(without.json()) == list(with_all.json())


async def test_all_reads_the_ratings_the_player_holds(client) -> None:
    """`all` is a claim about her, so it is answered from her ratings.

    Nothing on the wire prints the resolved set — the regions are empty — so what
    is asserted here is that composing under `all` for a rated player succeeds
    against the real rating store rather than only against a stub.
    """

    headers = await _auth_headers(client)
    await _rate_as_beginner(client, headers, "PADEL")

    response = await client.get("/api/v1/now?sport=all", headers=headers)
    assert response.status_code == 200, response.text


async def test_the_server_never_answers_nothing_has_changed(client) -> None:
    headers = await _auth_headers(client)
    first = await client.get("/api/v1/now", headers=headers)

    # Whatever the phone claims to be holding, the answer is what is true now.
    # Pull-to-refresh carries a promise a 304 would break.
    conditional = await client.get(
        "/api/v1/now",
        headers={
            **headers,
            "If-None-Match": first.headers.get("etag", '"whatever"'),
            "If-Modified-Since": "Thu, 21 Aug 2026 00:00:00 GMT",
        },
    )

    assert conditional.status_code == 200
    assert conditional.json()["offers"]["cards"] == []


async def test_the_three_regions_of_one_compose_share_a_stamp(client) -> None:
    headers = await _auth_headers(client)
    body = (await client.get("/api/v1/now", headers=headers)).json()

    stamps = {
        body["offers"]["stamp"],
        body["your_matches"]["stamp"],
        body["shelves"]["stamp"],
    }
    assert len(stamps) == 1
    assert all(isinstance(s, int) for s in stamps)


async def test_a_later_compose_never_stamps_lower(client) -> None:
    headers = await _auth_headers(client)
    first = (await client.get("/api/v1/now", headers=headers)).json()
    second = (await client.get("/api/v1/now", headers=headers)).json()

    assert second["offers"]["stamp"] >= first["offers"]["stamp"]


async def test_there_is_no_screen_level_stamp(client) -> None:
    headers = await _auth_headers(client)
    body = (await client.get("/api/v1/now", headers=headers)).json()

    assert "stamp" not in body
    assert "server_time" not in body


async def test_two_players_get_their_own_screens(client) -> None:
    alice = await _auth_headers(client, ALICE)
    bob = await _auth_headers(client, BOB)

    for headers in (alice, bob):
        response = await client.get("/api/v1/now", headers=headers)
        assert response.status_code == 200, response.text
        assert response.json()["your_matches"]["cards"] == []
