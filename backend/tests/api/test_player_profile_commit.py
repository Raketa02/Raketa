"""The profile commit over HTTP: the contract, the idempotency, the refusals.

Everything here runs against the real routes and the real event store on
in-memory SQLite; only the object store is faked, by `tests/conftest.py`, so no
test needs MinIO running.

The contract these assert is the one the player client generates its wire types
from, and it is what onboarding's second part ends with: **one request carrying
six answers, safe to send twice.**
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.modules.player_profile.domain.search_radius import SEARCH_RADIUS_BOUNDS
from tests.unit import image_fixtures as fixtures

ALICE = {
    "email": "alice.profile@example.com",
    "password1": "hunter22!",
    "password2": "hunter22!",
    "adult_attested": True,
}
BOB = {
    "email": "bob.profile@example.com",
    "password1": "hunter22!",
    "password2": "hunter22!",
    "adult_attested": True,
}

COMMIT_URL = "/api/v1/players/me/profile"


async def auth_headers(client, payload=ALICE) -> dict[str, str]:
    await client.post("/api/v1/users", json=payload)
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password1"]},
    )
    assert login.status_code == 200, login.text
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    # Named, because a record is read back below and an unnamed player has no
    # record identity to read (``docs/adr/0171``): sign-up is credentials only
    # and the naming is the first step of onboarding.
    handle = payload["email"].split("@")[0].replace(".", "_")
    named = await client.put(
        "/api/v1/users/me/name",
        json={"name": handle.replace("_", " ").title(), "nickname": handle},
        headers=headers,
    )
    assert named.status_code == 200, named.text
    return headers


def a_body(**overrides) -> dict:
    body = {
        "social_tag_ids": ["PLAYS_TO_WIN", "HERE_TO_IMPROVE"],
        "photo_ids": [],
        "weekly_hours": [
            {"day": 2, "hour": 19},
            {"day": 6, "hour": 10},
        ],
        "location": {"latitude": 51.5073509, "longitude": -0.1277583},
        "search_radius_km": SEARCH_RADIUS_BOUNDS.default_km,
        "proposals_opt_in": {"accepted": True, "copy_version": "proposals-2026-08"},
        "gender": "WOMAN",
    }
    body.update(overrides)
    return body


async def commit(client, headers, body=None, key="commit-1"):
    return await client.post(
        COMMIT_URL,
        json=a_body() if body is None else body,
        headers={**headers, "Idempotency-Key": key},
    )


async def upload_photo(client, headers) -> str:
    response = await client.post(
        "/api/v1/photos",
        content=fixtures.plain_jpeg(),
        headers={**headers, "Content-Type": "image/jpeg"},
    )
    assert response.status_code == 201, response.text
    return response.json()["photo_id"]


# ---------------------------------------------------------------------------
# The commit
# ---------------------------------------------------------------------------


async def test_a_commit_returns_the_profile_it_created(client):
    headers = await auth_headers(client)

    response = await commit(client, headers)

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["social_tag_ids"] == ["PLAYS_TO_WIN", "HERE_TO_IMPROVE"]
    assert body["search_radius_km"] == SEARCH_RADIUS_BOUNDS.default_km
    assert body["weekly_hours"] == [
        {"day": 2, "hour": 19},
        {"day": 6, "hour": 10},
    ]
    assert body["proposals_opt_in"] == {
        "accepted": True,
        "copy_version": "proposals-2026-08",
        # The surface is the route's own fact, never the body's — this endpoint
        # *is* the end of onboarding, so a client cannot declare otherwise.
        "surface": "ONBOARDING",
        "answered_at": body["proposals_opt_in"]["answered_at"],
    }


async def test_the_location_that_comes_back_is_coarser_than_the_one_sent(client):
    """What a device measured is not what this platform keeps."""

    headers = await auth_headers(client)

    body = (await commit(client, headers)).json()

    assert body["location"] == {"latitude": 51.51, "longitude": -0.13}


async def test_a_commit_with_no_hours_ticked_is_refused(client):
    """The floor of one hour, on the wire, with a code of its own (ADR-0102,
    amended by ADR-0189).

    A 400 with ``weekly_hours_empty`` rather than a shapeless 422: `code` is
    the only half a client may branch on, and *go back and tick an hour* is not
    any other refusal's recovery.
    """

    headers = await auth_headers(client)

    response = await commit(client, headers, a_body(weekly_hours=[]))

    assert response.status_code == 400, response.text
    assert response.json()["code"] == "weekly_hours_empty"


async def test_one_hour_is_enough_to_commit_and_the_week_comes_back_in_order(client):
    """One tick is a real answer. Repeated hours collapse and the week comes back
    in the platform's reading order — day, then hour, nine before ten."""

    headers = await auth_headers(client)

    response = await commit(
        client,
        headers,
        a_body(
            weekly_hours=[
                {"day": 6, "hour": 10},
                {"day": 6, "hour": 9},
                {"day": 6, "hour": 10},
            ]
        ),
    )

    assert response.status_code == 201, response.text
    assert response.json()["weekly_hours"] == [
        {"day": 6, "hour": 9},
        {"day": 6, "hour": 10},
    ]


@pytest.mark.parametrize(
    "cell",
    [
        {"day": 2, "hour": 6},
        {"day": 2, "hour": 23},
        {"day": 8, "hour": 19},
        {"day": 2, "part": "EVENING"},
    ],
    ids=["before-seven", "the-hour-after-the-grid", "no-such-day", "a-part-of-the-day"],
)
async def test_a_cell_that_is_not_an_hour_of_the_week_is_refused(client, cell):
    """The week runs 07:00–23:00, so its cells start at 7 through 22 — and a part
    of the day is not a cell at all any more (ADR-0189 §5). A shape refusal: a
    client drawing the served grid cannot produce one."""

    headers = await auth_headers(client)

    response = await commit(client, headers, a_body(weekly_hours=[cell]))

    assert response.status_code == 422, response.text


async def test_photo_ids_are_committed_in_the_order_they_were_arranged(client):
    headers = await auth_headers(client)
    first, second = (
        await upload_photo(client, headers),
        await upload_photo(client, headers),
    )

    response = await commit(client, headers, a_body(photo_ids=[second, first]))

    assert response.status_code == 201, response.text
    assert response.json()["photo_ids"] == [second, first]


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


async def test_the_same_key_twice_creates_one_profile_and_answers_the_same(client):
    headers = await auth_headers(client)

    first = await commit(client, headers, key="draft-7")
    second = await commit(client, headers, key="draft-7")

    assert first.status_code == 201
    assert second.status_code == 200, "a replay, not a creation"
    assert second.json() == first.json()


async def test_a_second_commit_under_a_different_key_conflicts(client):
    headers = await auth_headers(client)
    await commit(client, headers, key="draft-7")

    response = await commit(client, headers, key="draft-8")

    assert response.status_code == 409
    assert response.json()["code"] == "player_profile_already_exists"


async def test_a_commit_without_the_idempotency_key_is_refused(client):
    """Required rather than optional: this is the request that gets
    double-tapped, and a key sent only when a client remembers to is a second
    profile waiting for a bad afternoon."""

    headers = await auth_headers(client)

    response = await client.post(COMMIT_URL, json=a_body(), headers=headers)

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


async def test_one_players_key_says_nothing_about_anothers(client):
    alice = await auth_headers(client, ALICE)
    bob = await auth_headers(client, BOB)
    await commit(client, alice, key="same-key")

    response = await commit(client, bob, key="same-key")

    assert response.status_code == 201, response.text


# ---------------------------------------------------------------------------
# Re-validation, over the wire
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "body, status_code, code",
    [
        (
            {"social_tag_ids": ["PLAYS_TO_WIN"]},
            400,
            "social_tag_selection_out_of_bounds",
        ),
        (
            {
                "social_tag_ids": [
                    "PLAYS_TO_WIN",
                    "HERE_TO_IMPROVE",
                    "QUIET_AND_FOCUSED",
                    "HERE_TO_COMPETE",
                    "STAYS_FOR_A_DRINK",
                    "SHARES_A_LIFT",
                    "WARMS_UP_PROPERLY",
                ]
            },
            400,
            "social_tag_selection_out_of_bounds",
        ),
        (
            {"social_tag_ids": ["PLAYS_TO_WIN", "LOOKING_FOR_A_DATE"]},
            400,
            "unknown_social_tag",
        ),
        (
            {"social_tag_ids": ["PLAYS_TO_WIN", "PLAYS_TO_WIN"]},
            400,
            "duplicate_social_tag",
        ),
        (
            {"search_radius_km": SEARCH_RADIUS_BOUNDS.maximum_km + 1},
            400,
            "search_radius_out_of_bounds",
        ),
        (
            {"search_radius_km": SEARCH_RADIUS_BOUNDS.minimum_km - 1},
            400,
            "search_radius_out_of_bounds",
        ),
        (
            {
                "proposals_opt_in": {
                    "accepted": None,
                    "copy_version": "proposals-2026-08",
                }
            },
            400,
            "proposals_opt_in_not_answered",
        ),
    ],
)
async def test_a_rule_the_client_enforced_is_refused_with_its_own_code(
    client, body, status_code, code
):
    """A disabled button is not a validation. Each of these is something the
    served options let a picker prevent, and each is refused here anyway — with
    the code that says which recovery to attempt."""

    headers = await auth_headers(client)

    response = await commit(client, headers, a_body(**body))

    assert response.status_code == status_code, response.text
    assert response.json()["code"] == code


async def test_a_photo_id_that_does_not_exist_is_refused(client):
    headers = await auth_headers(client)

    response = await commit(client, headers, a_body(photo_ids=[str(uuid4())]))

    assert response.status_code == 404
    assert response.json()["code"] == "photo_not_found"


async def test_another_players_photo_id_is_refused_the_same_way(client):
    """The same answer for *no such photo* and *somebody else's photo* — the
    alternative is an endpoint that confirms a stranger's id is real."""

    alice = await auth_headers(client, ALICE)
    bob = await auth_headers(client, BOB)
    bobs_photo = await upload_photo(client, bob)

    response = await commit(client, alice, a_body(photo_ids=[bobs_photo]))

    assert response.status_code == 404
    assert response.json()["code"] == "photo_not_found"


async def test_a_refused_commit_leaves_no_profile_behind(client):
    headers = await auth_headers(client)

    unanswered = {"accepted": None, "copy_version": "proposals-2026-08"}

    refused = await commit(client, headers, a_body(proposals_opt_in=unanswered))
    assert refused.status_code == 400

    me = await client.get("/api/v1/users/me", headers=headers)
    assert me.json()["has_player_profile"] is False


async def test_the_commit_requires_a_token(client):
    response = await client.post(
        COMMIT_URL, json=a_body(), headers={"Idempotency-Key": "commit-1"}
    )

    assert response.status_code == 401


# ---------------------------------------------------------------------------
# The entry gate's fourth branch
# ---------------------------------------------------------------------------


async def test_a_new_account_reports_no_player_profile(client):
    headers = await auth_headers(client)

    me = await client.get("/api/v1/users/me", headers=headers)

    assert me.status_code == 200
    assert me.json()["has_player_profile"] is False


async def test_the_flag_is_true_immediately_after_the_commit(client):
    """Read from the profile's own stream rather than a projection, which is
    what stops a player who has just finished the social steps being routed
    straight back into them."""

    headers = await auth_headers(client)
    await commit(client, headers)

    me = await client.get("/api/v1/users/me", headers=headers)

    assert me.json()["has_player_profile"] is True


async def test_one_players_profile_does_not_answer_for_another(client):
    alice = await auth_headers(client, ALICE)
    bob = await auth_headers(client, BOB)
    await commit(client, alice)

    assert (await client.get("/api/v1/users/me", headers=alice)).json()[
        "has_player_profile"
    ] is True
    assert (await client.get("/api/v1/users/me", headers=bob)).json()[
        "has_player_profile"
    ] is False


# ---------------------------------------------------------------------------
# Gender, over the wire
# ---------------------------------------------------------------------------


async def test_a_commit_without_a_gender_answer_is_refused(client):
    """Required, and refused as a *shape* rather than with a code.

    That is the opposite of the weekly-hours floor and the opt-in beside it, and
    the difference is that this question has no unanswered state to model:
    ``PREFER_NOT_TO_SAY`` is a real answer a player can choose, so a body with
    no `gender` at all is a client that does not implement the contract, not a
    player who declined (``docs/adr/0096``).
    """

    headers = await auth_headers(client)
    body = a_body()
    del body["gender"]

    response = await commit(client, headers, body)

    assert response.status_code == 422, response.text


async def test_a_gender_this_platform_does_not_serve_is_refused(client):
    """A closed set fixed by the record, not a served vocabulary a client can
    hold a different version of — so there is nothing here for the domain to
    refuse that the type has not already refused."""

    headers = await auth_headers(client)

    response = await commit(client, headers, a_body(gender="OTHER"))

    assert response.status_code == 422, response.text


async def test_prefer_not_to_say_is_accepted_like_any_other_answer(client):
    headers = await auth_headers(client)

    response = await commit(client, headers, a_body(gender="PREFER_NOT_TO_SAY"))

    assert response.status_code == 201, response.text


async def test_a_commit_that_names_no_preference_is_accepted(client):
    """The asymmetry: the answer about oneself is required, the preference over
    others is optional and defaults to `ANY`."""

    headers = await auth_headers(client)
    body = a_body()
    assert "gender_preference" not in body

    response = await commit(client, headers, body)

    assert response.status_code == 201, response.text


async def test_a_narrowed_preference_is_accepted(client):
    headers = await auth_headers(client)

    response = await commit(client, headers, a_body(gender_preference="WOMEN_ONLY"))

    assert response.status_code == 201, response.text


async def test_no_gender_value_ever_comes_back_out(client):
    """``docs/adr/0096`` §6, asserted rather than remembered.

    The body is only ever the caller's own profile, so nothing here would leak a
    third party's answer — but *which* shapes may carry it is a line rather than
    a judgement made per endpoint, and the line is one shape: the owner's own
    read (``docs/adr/0179`` §4). The commit's answer is not it, and the walk in
    ``tests/unit/test_no_response_carries_a_forbidden_fact.py`` holds the
    whole contract to that.
    """

    headers = await auth_headers(client)

    body = (await commit(client, headers, a_body(gender="WOMAN"))).json()

    assert "gender" not in body
    assert "gender_preference" not in body
    assert "WOMAN" not in str(body)


# ---------------------------------------------------------------------------
# The intro (docs/adr/0170) — one field, one code, one coarse reason
# ---------------------------------------------------------------------------


async def test_a_commit_may_carry_one_line_about_oneself(client):
    """Karol writes a line and commits: 201, and the line is stored as its own
    event. The commit body does not echo it — it crosses on the card and on the
    record, and nowhere else (``docs/adr/0170`` §3)."""

    headers = await auth_headers(client)

    response = await commit(
        client, headers, a_body(intro="Moved from Wrocław in May. Needs opponents.")
    )

    assert response.status_code == 201, response.text
    record = await client.get("/api/v1/players/me/record", headers=headers)
    assert record.status_code == 200, record.text
    assert record.json()["intro"] == "Moved from Wrocław in May. Needs opponents."


async def test_a_commit_without_a_line_is_a_commit_without_one(client):
    """Ola skips: no field, no event, and the record omits the key rather than
    sending an empty string."""

    headers = await auth_headers(client)

    response = await commit(client, headers)

    assert response.status_code == 201, response.text
    record = await client.get("/api/v1/players/me/record", headers=headers)
    assert "intro" not in record.json()


@pytest.mark.parametrize(
    "line,reason",
    [
        ("x" * 101, "too_long"),
        ("Moved here in May.\nNeeds opponents.", "multiline"),
        ("WhatsApp me 600 123 456", "contains_contact"),
        ("karol@example.com", "contains_contact"),
        ("https://karol.example.com", "contains_contact"),
        ("insta @karol_plays", "contains_contact"),
    ],
    ids=["101 characters", "a line break", "a phone", "an email", "a URL", "a handle"],
)
async def test_a_line_the_platform_does_not_admit_is_refused_with_its_reason(
    client, line: str, reason: str
):
    """Tomek writes *WhatsApp me 600 123 456* and is refused —
    ``intro_not_admitted``, reason ``contains_contact`` — **before anything is
    stored**. One code and one coarse reason: the client says what to change,
    and the server never explains what it matched."""

    headers = await auth_headers(client)

    response = await commit(client, headers, a_body(intro=line))

    assert response.status_code == 400, response.text
    body = response.json()
    assert body["code"] == "intro_not_admitted"
    assert body["details"] == {"reason": reason}
    # Nothing was stored: the same key commits cleanly once the line is fixed,
    # which it could not if a refused commit had left a profile behind.
    retry = await commit(client, headers, a_body(intro="Three sets, best of five"))
    assert retry.status_code == 201, retry.text


async def test_a_line_about_the_game_is_admitted(client):
    headers = await auth_headers(client)

    response = await commit(client, headers, a_body(intro="Three sets, best of five"))

    assert response.status_code == 201, response.text
